"""Download pinned engine layer from Stanford's OG 1.0.0 image, without Docker.

Only downloads and verifies an archive; does not extract or execute it.
The containing image manifest was audited before this script was written.
"""
import hashlib
import json
from pathlib import Path
import shutil
import urllib.request

REPOSITORY = "stanfordvl/omnigibson"
IMAGE_DIGEST = "sha256:8611bfe0507505d3c5fdaec07c272b12d2a1f8a0a75b73b177da751086f13503"
LAYER_DIGEST = "sha256:a1b1e92d5165bfe6d5ac68453c2bbbb4a000882bc453e35b4a714c8cdae1a2d4"
LAYER_BYTES = 8937203082


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / ".runtime/downloads"
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / "isaac-sim-2023.1.1-layer.tar.gz"
    if target.exists():
        raise FileExistsError(f"Refusing to overwrite existing archive: {target}")
    if shutil.disk_usage(directory).free < LAYER_BYTES + 50 * 1024**3:
        raise RuntimeError("Need archive capacity plus 50 GiB reserved free space")
    url = "https://auth.docker.io/token?service=registry.docker.io&scope=repository:" + REPOSITORY + ":pull"
    with urllib.request.urlopen(url, timeout=30) as response:
        token = json.load(response)["token"]

    def request(path):
        req = urllib.request.Request("https://registry-1.docker.io/v2/" + REPOSITORY + "/" + path)
        req.add_unredirected_header("Authorization", "Bearer " + token)
        return req

    req = request("manifests/" + IMAGE_DIGEST)
    req.add_header("Accept", "application/vnd.docker.distribution.manifest.v2+json")
    with urllib.request.urlopen(req, timeout=30) as response:
        raw = response.read()
    if hashlib.sha256(raw).hexdigest() != IMAGE_DIGEST.split(":")[1]:
        raise RuntimeError("Image manifest digest mismatch")
    manifest = json.loads(raw)
    if not any(x["digest"] == LAYER_DIGEST and x["size"] == LAYER_BYTES for x in manifest["layers"]):
        raise RuntimeError("Pinned engine layer missing from official image")
    digest = hashlib.sha256()
    count = 0
    next_report = 1024**3
    with urllib.request.urlopen(request("blobs/" + LAYER_DIGEST), timeout=60) as response, target.open("xb") as output:
        while chunk := response.read(8 * 1024**2):
            output.write(chunk)
            digest.update(chunk)
            count += len(chunk)
            if count >= next_report:
                print(f"Downloaded {count / 1024**3:.1f} / {LAYER_BYTES / 1024**3:.1f} GiB", flush=True)
                next_report += 1024**3
    if count != LAYER_BYTES or digest.hexdigest() != LAYER_DIGEST.split(":")[1]:
        raise RuntimeError("Archive verification failed; incomplete file retained for inspection")
    receipt = {"image": IMAGE_DIGEST, "layer": LAYER_DIGEST, "bytes": count, "sha256_verified": True}
    target.with_suffix(".receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print("Verified:", target, flush=True)


if __name__ == "__main__":
    main()
