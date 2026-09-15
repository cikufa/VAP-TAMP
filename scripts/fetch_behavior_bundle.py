"""Fetch only pinned OG 1.0.0 bundles approved for this reproduction.

The dataset bundle exceeds 20 GB. User approved it in this session after
compatibility/disk checks. The script checks archive capacity and retains a
60 GiB reserve. Extraction has a separate inventory/capacity gate.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

BUNDLES = {
    "dataset": ("og_dataset_1_0_0.tar.gz", "1710728899224755", 22321609648,
                "f6f00da7882fad9dd0f4a205d74a539d"),
    "assets": ("og_assets_1_0_0.tar.gz", "1710734129808291", 663239083,
               "c4a62555ff2f23687d5e914c968cb2e4"),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", choices=BUNDLES)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()
    name, generation, size, expected_md5 = BUNDLES[args.bundle]
    root = Path(__file__).resolve().parents[1]
    target = root / ".runtime/downloads" / name
    if target.exists() and not args.resume:
        raise FileExistsError(f"Refusing to overwrite {target}")
    if not 1 <= args.workers <= 8:
        raise ValueError("workers must be between 1 and 8")
    if target.with_suffix(".receipt.json").exists():
        raise FileExistsError("Already verified; no download required")
    progress_path = target.with_suffix(".progress.json")
    if progress_path.exists():
        progress = json.loads(progress_path.read_text())
        if progress["generation"] != generation:
            raise RuntimeError("Resume generation mismatch")
    else:
        progress = {"generation": generation, "prefix": target.stat().st_size if target.exists() else 0, "completed": []}
    if progress["prefix"] > size:
        raise RuntimeError("Existing prefix larger than bundle")
    if shutil.disk_usage(target.parent).free < size - progress["prefix"] + 60 * 1024**3:
        raise RuntimeError("Insufficient archive space plus 60 GiB reserve")
    url = f"https://storage.googleapis.com/gibson_scenes/{name}?generation={generation}"
    block_size = 256 * 1024**2
    ranges = [(start, min(start + block_size, size) - 1)
              for start in range(progress["prefix"], size, block_size)]
    lock = threading.Lock()
    if not target.exists():
        target.touch(exist_ok=False)
    progress_path.write_text(json.dumps(progress))

    def fetch(index):
        start, end = ranges[index]
        request = urllib.request.Request(url, headers={"Range": f"bytes={start}-{end}"})
        with urllib.request.urlopen(request, timeout=60) as response, target.open("r+b") as output:
            if response.status != 206 or response.headers.get("Content-Range") != f"bytes {start}-{end}/{size}":
                raise RuntimeError("Server did not return the requested pinned range")
            output.seek(start)
            remaining = end - start + 1
            while remaining:
                chunk = response.read(min(8 * 1024**2, remaining))
                if not chunk:
                    raise RuntimeError("Truncated range response")
                output.write(chunk)
                remaining -= len(chunk)
            output.flush()
        with lock:
            progress["completed"].append(index)
            progress_path.write_text(json.dumps(progress))
            complete = progress["prefix"] + sum(ranges[i][1] - ranges[i][0] + 1 for i in progress["completed"])
            print(f"{args.bundle}: {complete / 1024**3:.2f} / {size / 1024**3:.2f} GiB", flush=True)

    pending = [i for i in range(len(ranges)) if i not in progress["completed"]]
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        for future in as_completed([executor.submit(fetch, i) for i in pending]):
            future.result()
    md5, sha256 = hashlib.md5(), hashlib.sha256()
    count = 0
    with target.open("rb") as downloaded:
        while chunk := downloaded.read(8 * 1024**2):
            md5.update(chunk)
            sha256.update(chunk)
            count += len(chunk)
    if count != size or md5.hexdigest() != expected_md5:
        raise RuntimeError("Bundle integrity check failed; file retained for inspection")
    receipt = {"url": url, "bytes": count, "md5": md5.hexdigest(),
               "sha256": sha256.hexdigest(), "verified": True}
    target.with_suffix(".receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print("Verified:", target, flush=True)


if __name__ == "__main__":
    main()
