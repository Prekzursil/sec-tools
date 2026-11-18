"""Repository content validation (fleet bare-repo CI).

Checks every tracked file that is not a known binary format decodes as
UTF-8, and every ``*.json`` file parses. Exits non-zero on the first
kind of failure, listing all offending files.
"""

import json
import subprocess
import sys

BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip",
    ".gz", ".tgz", ".bz2", ".xz", ".7z", ".woff", ".woff2", ".ttf",
    ".otf", ".eot", ".mp3", ".mp4", ".webm", ".ogg", ".wav", ".avi",
    ".mov", ".exe", ".dll", ".so", ".dylib", ".bin", ".class", ".jar",
    ".pyc", ".wasm", ".svgz",
}


def tracked_files():
    out = subprocess.run(
        ["git", "ls-files", "-z"], capture_output=True, check=True
    ).stdout
    return [f for f in out.decode("utf-8").split("\0") if f]


def main():
    failures = []
    json_failures = []
    for path in tracked_files():
        ext = "." + path.rsplit(".", 1)[-1].lower() if "." in path.rsplit("/", 1)[-1] else ""
        if ext in BINARY_EXTENSIONS:
            continue
        try:
            data = open(path, "rb").read()
        except OSError as exc:
            failures.append(f"{path}: unreadable ({exc})")
            continue
        try:
            data.decode("utf-8")
        except UnicodeDecodeError as exc:
            failures.append(f"{path}: not valid UTF-8 ({exc})")
        if ext == ".json":
            try:
                json.loads(data.decode("utf-8"))
            except (ValueError, UnicodeDecodeError) as exc:
                json_failures.append(f"{path}: invalid JSON ({exc})")

    for label, items in (("encoding", failures), ("json", json_failures)):
        if items:
            print(f"[FAIL] {label} check: {len(items)} file(s):")
            for item in items:
                print(f"  - {item}")
    if failures or json_failures:
        return 1
    print("[OK] all tracked text files are valid UTF-8; all JSON files parse")
    return 0


if __name__ == "__main__":
    sys.exit(main())
