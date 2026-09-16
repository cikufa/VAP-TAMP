"""Offline connector media renderer."""
import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.connector_handoff.media import render_video
p=argparse.ArgumentParser();p.add_argument("episode",type=Path);a=p.parse_args()
print(render_video(a.episode))
