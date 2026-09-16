"""Immutable-source preflight used only before execution, never in action selection."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
MANIFEST=Path(__file__).parent/'freeze_manifest.json'

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def verify_release():
    data=json.loads(MANIFEST.read_text())
    if data.get('status')!='FROZEN CONNECTOR BENCHMARK':raise RuntimeError('Benchmark acceptance is not frozen')
    changed=[name for name,value in data['sha256'].items() if not (ROOT/name).exists() or digest(ROOT/name)!=value]
    if changed:raise RuntimeError('Frozen inputs changed: '+', '.join(changed))
    altered=subprocess.check_output(['git','diff','--name-only','c315720','--','vlm-tamp'],cwd=ROOT,text=True).strip()
    if altered:raise RuntimeError('Baseline source differs from c315720: '+altered)
    return data
