"""Inventory the verified dataset, check expansion space, optionally extract safely."""
import argparse
import json
from pathlib import Path, PurePosixPath
import shutil
import tarfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--extract', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    archive = root / '.runtime/downloads/og_dataset_1_0_0.tar.gz'
    receipt = json.loads(archive.with_suffix('.receipt.json').read_text())
    if not receipt['verified'] or archive.stat().st_size != receipt['bytes']:
        raise RuntimeError('Verified download receipt required')
    total = count = 0
    roots = set()
    scene_members = []
    with tarfile.open(archive, mode='r|gz') as bundle:
        for member in bundle:
            path = PurePosixPath(member.name)
            if path.is_absolute() or '..' in path.parts:
                raise RuntimeError('Unsafe member path')
            roots.add(path.parts[0])
            if member.isfile():
                total += member.size
                count += 1
            if 'Ihlen_0_int' in member.name:
                scene_members.append(member.name)
    free = shutil.disk_usage(root).free
    result = dict(regular_file_bytes=total, regular_file_count=count,
                  roots=sorted(roots), original_scene_members=scene_members,
                  free_bytes_before_extraction=free)
    (root / '.runtime/dataset_inventory.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'original_scene_members'}), flush=True)
    print('Original scene members:', len(scene_members), flush=True)
    if args.extract:
        if len(roots) != 1 or not scene_members:
            raise RuntimeError('Unexpected dataset root or absent original scene')
        if free < total + 15 * 1024**3:
            raise RuntimeError('Insufficient space for expansion plus 15 GiB reserve')
        target = root / '.runtime/data' / next(iter(roots))
        if target.exists():
            raise RuntimeError('Extraction target already exists; no overwrite')
        with tarfile.open(archive, mode='r|gz') as bundle:
            bundle.extractall(root / '.runtime/data', filter='data')
        print('DATASET_EXTRACTED', target, flush=True)


if __name__ == '__main__':
    main()
