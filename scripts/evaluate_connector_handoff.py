"""Evaluate one recorded episode; no API or simulator needed."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.connector_handoff.metrics import evaluate
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--compatibility',type=Path);p.add_argument('--counterfactual',type=Path);a=p.parse_args()
 load=lambda p:json.loads(p.read_text()) if p else None
 print(json.dumps(evaluate(a.input,load(a.compatibility),load(a.counterfactual)),indent=2))
