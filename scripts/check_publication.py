"""Check Git-selected publication files without printing matched private values.

Complements visual review and a dedicated secret scanner; not a complete audit.
Use --staged to check exact index contents before committing.
"""
import argparse
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_DIRS = {"data", "local", "backups", ".venv", "venv", ".claude",
                ".codex", ".playwright-mcp", "node_modules", "logs"}
PRIVATE_SUFFIXES = {".db", ".sqlite", ".sqlite3", ".pem", ".key", ".pfx",
                    ".p12", ".pickle", ".log"}
PATTERNS = {
    "personal filesystem path": re.compile(rb"[A-Za-z]:[\\/](?:Users|Documents and Settings)[\\/][A-Za-z0-9_.-]+"),
    "private LAN address": re.compile(rb"\b(?:192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3})\b"),
    "private key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "provider token": re.compile(rb"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|sk-(?:proj-|ant-api\d+-)?[A-Za-z0-9_-]{24,})\b"),
}


def inspect(staged=False):
    args = ["git", "ls-files", "-z"]
    if not staged:
        args += ["--cached", "--others", "--exclude-standard"]
    names = sorted(set(subprocess.check_output(args, cwd=ROOT).decode().split("\0")) - {""})
    findings = []
    checked = 0
    for name in names:
        path = Path(name)
        if not staged and not (ROOT / path).exists():
            continue
        checked += 1
        private = (bool(set(path.parts) & PRIVATE_DIRS)
                   or path.suffix.lower() in PRIVATE_SUFFIXES
                   or (path.name.startswith(".env") and path.name != ".env.example")
                   or path.name in {"credentials.json", "token.json"}
                   or name.startswith("docs/Research Documentatiopn/"))
        if private:
            findings.append((name, "private artifact or original research capture"))
            continue
        if (ROOT / path).is_symlink():
            findings.append((name, "symbolic link requires review"))
            continue
        raw = (subprocess.check_output(["git", "show", ":" + name], cwd=ROOT)
               if staged else (ROOT / path).read_bytes())
        for kind, pattern in PATTERNS.items():
            if pattern.search(raw):
                findings.append((name, kind))
    return checked, findings


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staged", action="store_true")
    count, findings = inspect(parser.parse_args().staged)
    for name, kind in findings:
        print(f"{name}: {kind}")
    print(f"Publication check: {count} files, {len(findings)} findings; matched values withheld.")
    raise SystemExit(bool(findings))
