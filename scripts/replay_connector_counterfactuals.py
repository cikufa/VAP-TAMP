"""Replay alternate grasps from exact saved local initial states, outside online VAP-TAMP."""
import argparse,json,sys,datetime
from pathlib import Path
from connector_entry import ROOT,native
sys.path.insert(0,str(ROOT))
from experiments.connector_handoff.metrics import evaluate
from experiments.connector_handoff.media import render_all

def replay(episode,output,observability,timeout=180):
    episode=Path(episode).resolve();metric=evaluate(episode)
    if not (metric['Y1'] and metric['Y2'] is False):return None
    output=Path(output).resolve()
    if (output/'counterfactual.json').exists():return json.loads((output/'counterfactual.json').read_text())
    canonical=output
    if output.exists():
        output=canonical/('retry_'+datetime.datetime.now().strftime('%Y%m%dT%H%M%S'))
    req=output.parent/(output.name+'_request.json');req.parent.mkdir(parents=True,exist_ok=True)
    req.write_text(json.dumps(dict(condition=metric['condition'],seed=metric['seed'],original_episode=str(episode),
        initial_state=str(episode/'initial_state.pkl'),alternate_grasp='gR' if metric['grasp_choice']=='gL' else 'gL',
        original_insert_attempted=metric['first_insert_attempted'],observability_evidence=str(observability)),indent=2)+'\n')
    if not (episode/'initial_state.pkl').exists():raise RuntimeError('Exact saved initial scene state is required')
    evidence=json.loads(Path(observability).read_text())
    if not any(x['condition']==metric['condition'] and x['view']!='initial' and x['visibility_evidence']['visually_relevant'] and all(x['executed_moves']) for x in evidence):
        raise RuntimeError('No validated informative pregrasp view')
    if native('counterfactual',output,timeout,{'CONNECTOR_REPLAY_REQUEST':req}):raise RuntimeError(f'Replay failed: {output}')
    render_all(output/'episode');result=json.loads((output/'counterfactual.json').read_text())
    result['replay_artifacts']=str(output)
    if canonical!=output:(canonical/'counterfactual.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,default=ROOT/'results/custom_connector/counterfactuals')
    p.add_argument('--observability',type=Path,default=ROOT/'results/custom_connector/benchmark_validation/observability/acceptance01/observability.json');a=p.parse_args()
    episodes=[a.input] if (a.input/'episode.json').exists() else sorted(x.parent for x in a.input.rglob('episode.json'))
    for episode in episodes:
        import hashlib
        key=hashlib.sha256(str(episode.resolve()).encode()).hexdigest()[:12]
        replay(episode,a.output/key,a.observability)
