"""Two native integration episodes; only VLM responses are mocked."""
import argparse,datetime,json,sys
from pathlib import Path
from connector_entry import ROOT,native
sys.path.insert(0,str(ROOT))
from experiments.connector_handoff.audit import image_requests
from experiments.connector_handoff.media import events,render_all
from experiments.connector_handoff.metrics import evaluate,aggregate

def validate(episode,script):
    trace=events(episode);kinds=[e['event'] for e in trace]
    meta=json.loads((episode/'episode.json').read_text())
    assert meta['mode']=='MOCK' and meta['physical_success'] and not meta['infrastructure_error']
    assert all(e['label']=='NON-SCIENTIFIC MOCK VLM RUN' for e in trace)
    assert sum(k=='grasp_complete' for k in kinds)==(1 if script=='straight' else 2)
    assert image_requests(episode)['requests']>0
    if script=='replan':
        motion=next(e for e in trace if e['event']=='paper_motion_executed')
        before=[e for e in trace if e['event']=='paper_sensor_observation' and e['sequence']<motion['sequence']][-1]
        after=next(e for e in trace if e['event']=='paper_sensor_observation' and e['sequence']>motion['sequence'])
        assert before['pixel_sha256']!=after['pixel_sha256']
        correction=next(e for e in trace if e['event']=='verification' and e['sequence']>after['sequence'] and e['unmatched_preconditions'])
        replan=next(e for e in trace if e['event']=='plan' and e['sequence']>correction['sequence'])
        assert any(e['event']=='action_start' and e['sequence']>replan['sequence'] for e in trace)
    render_all(episode)
    return evaluate(episode)

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'results/custom_connector/mock_validation/acceptance01');a=p.parse_args()
    rows=[]
    for script in ('straight','replan'):
        directory=a.output/'trial_logs'/script
        if native('mock_'+script,directory,180):raise RuntimeError(f'Mock native failure: {directory}')
        rows.append(validate(directory/'episode',script))
    (a.output/'validation.json').write_text(json.dumps(aggregate(rows),indent=2)+'\n')
    print('NON-SCIENTIFIC MOCK VLM RUN: both native integration paths passed')
if __name__=='__main__':main()
