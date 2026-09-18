import os
from datetime import datetime, timezone
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML as WeasyHTML
from app.core.config import settings

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
REPORTS_DIR = Path(settings.REPORTS_DIR)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def _env() -> Environment:
    return Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)


def generate_pdf(scan, target, findings, generated_by: str, executive_summary: str | None) -> str:
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "informational": 0}
    for f in findings:
        sev = f.severity.lower()
        if sev in counts:
            counts[sev] += 1

    env = _env()
    tmpl = env.get_template("report.html")
    html_content = tmpl.render(
        scan=scan,
        target=target,
        findings=findings,
        counts=counts,
        generated_by=generated_by,
        executive_summary=executive_summary,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )

    file_path = str(REPORTS_DIR / f"report_{scan.id}_{int(datetime.now(timezone.utc).timestamp())}.pdf")
    WeasyHTML(string=html_content).write_pdf(file_path)
    return file_path
