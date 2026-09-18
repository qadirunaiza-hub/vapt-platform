import hashlib


def compute_finding_fingerprint(tool: str, title: str, affected_resource: str, cve: str = "") -> str:
    """
    Deterministic fingerprint for deduplication.
    Two findings with the same fingerprint represent the same issue on the same asset.
    """
    raw = f"{tool}|{title.lower().strip()}|{affected_resource.lower().strip()}|{cve.lower().strip()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
