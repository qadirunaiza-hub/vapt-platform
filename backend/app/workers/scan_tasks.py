"""
Scan orchestration using Celery chord pattern.
- orchestrate_scan dispatches tool tasks and exits immediately (no blocking)
- Tool tasks run in parallel across the worker pool
- finalize_scan callback fires automatically when all tools complete
- Every tool task catches all exceptions and returns a result dict — chord always gets a result
"""
import subprocess
import tempfile
import os
import re
import logging
from datetime import datetime, timezone
from urllib.parse import urlparse

from celery import chord
from sqlalchemy.orm import Session

from app.workers.celery_app import celery_app
from app.db.session import SyncSessionLocal
from app.models.scan import Scan, ScanJob
from app.models.finding import Finding
from app.models.target import AuthorizedTarget
from app.core.config import settings
from app.utils.validators import safe_hostname_for_nmap, validate_url
from app.utils.fingerprint import compute_finding_fingerprint
from app.parsers.nmap_parser import NmapParser
from app.parsers.zap_parser import ZAPParser
from app.parsers.trivy_parser import TrivyParser

log = logging.getLogger(__name__)

DOCKER_BIN = "/usr/local/bin/docker"


# ── DB helpers ────────────────────────────────────────────────────────────────

def _update_scan_status(db, scan_id, status, progress=None, error=None):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        return
    scan.status = status
    if progress is not None:
        scan.progress = progress
    if error:
        scan.error_message = error
    if status == "running" and not scan.started_at:
        scan.started_at = datetime.now(timezone.utc)
    if status in ("completed", "failed", "cancelled", "completed_with_errors"):
        scan.completed_at = datetime.now(timezone.utc)
    db.commit()


def _update_job_status(db, job_id, status, raw_output=None, stderr=None,
                       exit_code=None, findings_count=0):
    job = db.query(ScanJob).filter(ScanJob.id == job_id).first()
    if not job:
        return
    job.status = status
    if raw_output is not None:
        job.raw_output = raw_output[:200000]
    if stderr is not None:
        job.stderr_output = stderr[:10000]
    if exit_code is not None:
        job.exit_code = exit_code
    if findings_count:
        job.findings_count = findings_count
    if status == "running" and not job.started_at:
        job.started_at = datetime.now(timezone.utc)
    if status in ("completed", "failed"):
        job.completed_at = datetime.now(timezone.utc)
    db.commit()


def _persist_findings(db, scan_id, target_id, normalized_findings):
    count = 0
    for nf in normalized_findings:
        fp = compute_finding_fingerprint(nf.source_tool, nf.title, nf.affected_resource, nf.cve)
        existing = db.query(Finding).filter(
            Finding.fingerprint == fp,
            Finding.target_id == target_id,
            Finding.status.notin_(["closed", "false_positive"]),
        ).first()
        if existing:
            existing.last_detected = datetime.now(timezone.utc)
            existing.scan_id = scan_id
            db.commit()
            continue
        db.add(Finding(
            scan_id=scan_id, target_id=target_id,
            title=nf.title, description=nf.description,
            severity=nf.severity, original_severity=nf.original_severity or nf.severity,
            confidence=nf.confidence, source_tool=nf.source_tool,
            category=nf.category, cve=nf.cve or None, cwe=nf.cwe or None,
            cvss_score=nf.cvss_score, cvss_vector=nf.cvss_vector or None,
            affected_resource=nf.affected_resource,
            evidence=nf.evidence or None, impact=nf.impact or None,
            recommendation=nf.recommendation or None,
            raw_data=nf.raw_data, status="open", fingerprint=fp,
        ))
        count += 1
    db.commit()
    return count


def _get_target_id(db, scan_id):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    return scan.target_id if scan else ""


# ── Tool tasks ────────────────────────────────────────────────────────────────

@celery_app.task(bind=True, max_retries=0, name="app.workers.scan_tasks.run_nmap")
def run_nmap(self, scan_id, job_id, target_address, intensity="normal"):
    db = SyncSessionLocal()
    try:
        _update_job_status(db, job_id, "running")
        _update_scan_status(db, scan_id, "running")

        address = (target_address or "").strip()
        # Web/API targets store full URLs — extract just the hostname for nmap
        if address.startswith(("http://", "https://")):
            address = urlparse(address).hostname or address

        validated = safe_hostname_for_nmap(address)

        intensity_flags = {
            "passive":    ["-sV", "-T2", "--open"],
            "normal":     ["-sV", "-sC", "-T3", "--open", "-p-"],
            "aggressive": ["-sV", "-sC", "-T4", "--open", "-p-", "-A"],
        }
        flags = intensity_flags.get(intensity, intensity_flags["normal"])

        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False, dir="/tmp") as tmp:
            xml_path = tmp.name

        result = subprocess.run(
            ["nmap"] + flags + ["-oX", xml_path, validated],
            capture_output=True, text=True, timeout=settings.NMAP_TIMEOUT,
        )

        xml_output = ""
        if os.path.exists(xml_path):
            with open(xml_path) as f:
                xml_output = f.read()
            os.unlink(xml_path)

        normalized = NmapParser().parse(xml_output)
        count = _persist_findings(db, scan_id, _get_target_id(db, scan_id), normalized)

        _update_job_status(db, job_id, "completed", raw_output=xml_output,
                           stderr=result.stderr, exit_code=result.returncode,
                           findings_count=count)
        return {"status": "completed", "findings": count}

    except subprocess.TimeoutExpired:
        _update_job_status(db, job_id, "failed", stderr="Nmap scan timed out", exit_code=-1)
        return {"status": "failed", "error": "timeout"}
    except Exception as exc:
        log.error("run_nmap [%s]: %s", scan_id, exc, exc_info=True)
        _update_job_status(db, job_id, "failed", stderr=str(exc), exit_code=-1)
        return {"status": "failed", "error": str(exc)}
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=0, name="app.workers.scan_tasks.run_zap")
def run_zap(self, scan_id, job_id, target_url, intensity="normal"):
    db = SyncSessionLocal()
    try:
        _update_job_status(db, job_id, "running")

        url = (target_url or "").strip()
        if validate_url(url) is None:
            raise ValueError(f"Invalid or unsafe URL for ZAP: {url!r}")

        if not os.path.exists(DOCKER_BIN):
            raise FileNotFoundError(
                f"Docker CLI not found at {DOCKER_BIN}. "
                "ZAP requires Docker. Rebuild the backend image."
            )

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, dir="/tmp") as tmp:
            report_path = tmp.name

        scan_type = "full" if intensity == "aggressive" else "baseline"
        result = subprocess.run(
            [
                DOCKER_BIN, "run", "--rm",
                "--memory", settings.SCANNER_MEMORY_LIMIT,
                "-v", f"{os.path.dirname(report_path)}:/zap/wrk",
                "ghcr.io/zaproxy/zaproxy:stable",
                "zap.sh", "-cmd",
                f"-{scan_type}", url,
                "-J", f"/zap/wrk/{os.path.basename(report_path)}",
                "-I",
            ],
            capture_output=True, text=True, timeout=settings.ZAP_TIMEOUT,
        )

        json_output = ""
        if os.path.exists(report_path):
            with open(report_path) as f:
                json_output = f.read()
            os.unlink(report_path)

        normalized = ZAPParser().parse(json_output)
        count = _persist_findings(db, scan_id, _get_target_id(db, scan_id), normalized)

        _update_job_status(db, job_id, "completed", raw_output=json_output,
                           stderr=result.stderr, exit_code=result.returncode,
                           findings_count=count)
        return {"status": "completed", "findings": count}

    except subprocess.TimeoutExpired:
        _update_job_status(db, job_id, "failed", stderr="ZAP scan timed out", exit_code=-1)
        return {"status": "failed", "error": "timeout"}
    except Exception as exc:
        log.error("run_zap [%s]: %s", scan_id, exc, exc_info=True)
        _update_job_status(db, job_id, "failed", stderr=str(exc), exit_code=-1)
        return {"status": "failed", "error": str(exc)}
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=0, name="app.workers.scan_tasks.run_trivy")
def run_trivy(self, scan_id, job_id, target_image, intensity="normal"):
    db = SyncSessionLocal()
    try:
        _update_job_status(db, job_id, "running")

        image = (target_image or "").strip()
        if not re.match(r"^[a-z0-9][a-z0-9._\-/:]*(:[a-z0-9._\-]+)?$", image, re.IGNORECASE):
            raise ValueError(f"Invalid Docker image name: {image!r}")

        result = subprocess.run(
            ["trivy", "image", "--format", "json", "--quiet", image],
            capture_output=True, text=True, timeout=settings.TRIVY_TIMEOUT,
        )

        normalized = TrivyParser().parse(result.stdout)
        count = _persist_findings(db, scan_id, _get_target_id(db, scan_id), normalized)

        _update_job_status(db, job_id, "completed", raw_output=result.stdout,
                           stderr=result.stderr, exit_code=result.returncode,
                           findings_count=count)
        return {"status": "completed", "findings": count}

    except subprocess.TimeoutExpired:
        _update_job_status(db, job_id, "failed", stderr="Trivy scan timed out", exit_code=-1)
        return {"status": "failed", "error": "timeout"}
    except Exception as exc:
        log.error("run_trivy [%s]: %s", scan_id, exc, exc_info=True)
        _update_job_status(db, job_id, "failed", stderr=str(exc), exit_code=-1)
        return {"status": "failed", "error": str(exc)}
    finally:
        db.close()


# ── Finalization callback (called by chord when ALL tools complete) ────────────

@celery_app.task(name="app.workers.scan_tasks.finalize_scan")
def finalize_scan(results, scan_id):
    db = SyncSessionLocal()
    try:
        results = results or []
        completed = sum(1 for r in results if r and r.get("status") == "completed")
        failed = len(results) - completed

        if failed == 0:
            final = "completed"
        elif completed == 0:
            final = "failed"
        else:
            final = "completed_with_errors"

        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if scan:
            target = db.query(AuthorizedTarget).filter(AuthorizedTarget.id == scan.target_id).first()
            if target:
                target.last_scanned_at = datetime.now(timezone.utc)
                db.commit()

        _update_scan_status(db, scan_id, final, progress=100)
        log.info("Scan %s finalized: %s (%d completed, %d failed)", scan_id, final, completed, failed)
        return {"status": final, "completed": completed, "failed": failed}

    except Exception as exc:
        log.error("finalize_scan [%s]: %s", scan_id, exc, exc_info=True)
        _update_scan_status(db, scan_id, "failed", error=str(exc))
        return {"error": str(exc)}
    finally:
        db.close()


# ── Orchestrator ──────────────────────────────────────────────────────────────

@celery_app.task(name="app.workers.scan_tasks.orchestrate_scan")
def orchestrate_scan(scan_id):
    """
    Dispatches one Celery task per tool using a chord.
    Exits immediately after dispatch — no blocking wait.
    finalize_scan fires automatically when all tool tasks complete.
    """
    db = SyncSessionLocal()
    try:
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            return {"error": "scan not found"}

        target = db.query(AuthorizedTarget).filter(AuthorizedTarget.id == scan.target_id).first()
        if not target or not target.authorization_confirmed:
            _update_scan_status(db, scan_id, "failed", error="Target not authorized for scanning")
            return {"error": "unauthorized"}

        _update_scan_status(db, scan_id, "running", progress=5)

        tool_map = {"nmap": run_nmap, "zap": run_zap, "trivy": run_trivy}
        address = (target.address or "").strip()
        sigs = []

        for job in scan.jobs:
            fn = tool_map.get(job.tool)
            if not fn:
                _update_job_status(db, job.id, "failed",
                                   stderr=f"Unsupported tool: {job.tool}")
                continue

            kw = {"scan_id": scan_id, "job_id": job.id, "intensity": scan.intensity}
            if job.tool == "nmap":
                kw["target_address"] = address
            elif job.tool == "zap":
                kw["target_url"] = address
            elif job.tool == "trivy":
                kw["target_image"] = address

            sigs.append(fn.s(**kw))

        db.commit()

        if not sigs:
            _update_scan_status(db, scan_id, "failed",
                                error="No runnable tools for this scan configuration")
            return {"status": "failed"}

        chord(sigs)(finalize_scan.s(scan_id=scan_id))
        log.info("Scan %s dispatched %d tool task(s)", scan_id, len(sigs))
        return {"status": "dispatched", "tasks": len(sigs)}

    except Exception as exc:
        log.error("orchestrate_scan [%s]: %s", scan_id, exc, exc_info=True)
        _update_scan_status(db, scan_id, "failed", error=str(exc))
        return {"error": str(exc)}
    finally:
        db.close()
