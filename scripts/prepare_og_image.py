"""Reconstruct the pinned OG image in a fresh project directory, without Docker."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / '.runtime'
DEST = RUNTIME / 'og-image-rootfs'
BLOBS = RUNTIME / 'downloads/og-image-layers'
REPO = 'stanfordvl/omnigibson'
DIGEST = '8611bfe0507505d3c5fdaec07c272b12d2a1f8a0a75b73b177da751086f13503'
raw = (RUNTIME/'og-image-manifest.json').read_bytes()
assert hashlib.sha256(raw).hexdigest() == DIGEST
manifest = json.loads(raw)
assert not DEST.exists(), 'Refusing to overwrite an existing root filesystem'
assert shutil.disk_usage(RUNTIME).free > 45 * 1024**3
BLOBS.mkdir(exist_ok=True)
with urllib.request.urlopen('https://auth.docker.io/token?service=registry.docker.io&scope=repository:'+REPO+':pull', timeout=30) as response:
    token = json.load(response)['token']

def fetch(layer):
    digest = layer['digest'].split(':')[1]
    if digest.startswith('a1b1e92d'):
        path = RUNTIME/'downloads/isaac-sim-2023.1.1-layer.tar.gz'
    else:
        path = BLOBS/(digest+'.tar.gz')
        if not path.exists():
            req = urllib.request.Request('https://registry-1.docker.io/v2/'+REPO+'/blobs/'+layer['digest'])
            req.add_unredirected_header('Authorization', 'Bearer '+token)
            with urllib.request.urlopen(req, timeout=60) as response, path.open('xb') as output:
                shutil.copyfileobj(response, output, 8*1024**2)
    assert path.stat().st_size == layer['size'], str(path)
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8*1024**2), b''): h.update(chunk)
    assert h.hexdigest() == digest, str(path)
    print('VERIFIED',digest,layer['size'],flush=True)
    return digest, path
unique = {l['digest']:l for l in manifest['layers']}
with ThreadPoolExecutor(max_workers=4) as pool:
    archives = dict(pool.map(fetch, unique.values()))
DEST.mkdir()

def inside(path):
    assert path.resolve().is_relative_to(DEST), str(path)
    return path

def remove(path):
    # Only entries in this newly created image, for OCI whiteouts/replacements.
    inside(path.parent)
    if path.is_symlink() or path.is_file(): path.unlink()
    elif path.is_dir(): shutil.rmtree(path)

for index, layer in enumerate(manifest['layers']):
    print('EXTRACT',index,flush=True)
    with tarfile.open(archives[layer['digest'].split(':')[1]], 'r|gz') as archive:
        for member in archive:
            rel = PurePosixPath(member.name)
            assert not rel.is_absolute() and '..' not in rel.parts
            path = DEST / str(rel)
            inside(path.parent)
            if rel.name == '.wh..wh..opq':
                if path.parent.exists():
                    for child in path.parent.iterdir(): remove(child)
                continue
            if rel.name.startswith('.wh.'):
                remove(path.with_name(rel.name[4:]))
                continue
            if member.isdir():
                if path.is_symlink() or path.is_file(): remove(path)
                path.mkdir(parents=True,exist_ok=True)
                continue
            path.parent.mkdir(parents=True,exist_ok=True)
            if member.issym():
                remove(path)
                target = DEST/member.linkname.lstrip('/') if member.linkname.startswith('/') else path.parent/member.linkname
                inside(target)
                path.symlink_to(os.path.relpath(target, path.parent))
            elif member.islnk():
                remove(path)
                os.link(inside(DEST/member.linkname.lstrip('/')),path)
            elif member.isfile():
                inside(path)
                if path.is_symlink(): remove(path)
                with archive.extractfile(member) as source, path.open('wb') as output:
                    shutil.copyfileobj(source,output,1024**2)
                path.chmod(member.mode & 0o777)  # no setuid bits on host
            # Device nodes are supplied by the execution namespace, never created here.
(DEST/'IMAGE_RECEIPT.json').write_text(json.dumps({'manifest_sha256':DIGEST,'layers':len(manifest['layers']),'absolute_symlinks':'equivalent relative targets','ownership':'current user','setuid_bits':'stripped'},indent=2))
print('IMAGE_READY',DEST,flush=True)
