"""Restore losslessly split archives from the published Git tree."""
import hashlib
import json
import os
from pathlib import Path
import tempfile


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def restore_large_files(root=None):
    root = Path(root or Path(__file__).resolve().parents[1]).resolve()
    manifest = root / "provenance/large_files.json"
    if not manifest.exists():
        return []
    verified = []
    for item in json.loads(manifest.read_text())["files"]:
        target = (root / item["path"]).resolve()
        if not target.is_relative_to(root):
            raise ValueError("Archive path leaves the project")
        if target.exists():
            if target.stat().st_size != item["size_bytes"] or digest(target) != item["sha256"]:
                raise ValueError("Existing archive differs: " + item["path"])
            verified.append(item["path"])
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=target.parent, prefix=target.name + ".restore-", delete=False) as out:
                temporary = Path(out.name)
                for part in item["parts"]:
                    source = (root / part["path"]).resolve()
                    if not source.is_relative_to(root) or source.stat().st_size != part["size_bytes"] or digest(source) != part["sha256"]:
                        raise ValueError("Archive part differs: " + part["path"])
                    with source.open("rb") as stream:
                        for block in iter(lambda: stream.read(1024 * 1024), b""):
                            out.write(block)
            if temporary.stat().st_size != item["size_bytes"] or digest(temporary) != item["sha256"]:
                raise ValueError("Reconstructed archive differs: " + item["path"])
            os.replace(temporary, target)
            verified.append(item["path"])
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()
    return verified


if __name__ == "__main__":
    for name in restore_large_files():
        print("Verified archive:", name)
