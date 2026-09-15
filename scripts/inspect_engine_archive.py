"""Inventory a verified native-engine archive without extracting/executing it."""
import json
from pathlib import Path, PurePosixPath
import tarfile


def main():
    root = Path(__file__).resolve().parents[1]
    archive = root / ".runtime/downloads/isaac-sim-2023.1.1-layer.tar.gz"
    receipt = json.loads(archive.with_suffix(".receipt.json").read_text())
    if not receipt["sha256_verified"] or archive.stat().st_size != receipt["bytes"]:
        raise RuntimeError("Verified archive receipt required")
    total = 0
    count = 0
    metadata = {}
    with tarfile.open(archive, mode="r|gz") as bundle:
        for member in bundle:
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts or path.parts[0] != "isaac-sim":
                raise RuntimeError(f"Unexpected archive member: {member.name}")
            if member.isfile():
                total += member.size
                count += 1
                wanted = (
                    member.name in ("isaac-sim/VERSION", "isaac-sim/SHORT_VERSION",
                                    "isaac-sim/setup_conda_env.sh", "isaac-sim/setup_python_env.sh")
                    or member.name.endswith("/torch/version.py")
                    or (member.name.endswith("/METADATA") and any(
                        "/" + package + "-" in member.name for package in ("torch", "torchvision", "numpy")))
                )
                if wanted and member.size < 100_000:
                    text = bundle.extractfile(member).read().decode("utf-8", errors="replace")
                    if member.name.endswith("/METADATA"):
                        text = "\n".join(line for line in text.splitlines() if line.startswith(("Name:", "Version:")))
                    metadata[member.name] = text
    result = {"regular_file_bytes": total, "regular_file_count": count, "metadata": metadata}
    (root / ".runtime/engine_inventory.json").write_text(json.dumps(result, indent=2) + "\n")
    print("Uncompressed regular file bytes:", total)
    print("Regular file count:", count)
    for name, value in metadata.items():
        if not name.endswith(".sh"):
            print(name, value[:400])


if __name__ == "__main__":
    main()
