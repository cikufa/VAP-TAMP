"""Explicit live-only, resumable 2-debug then frozen 20-seed evaluation."""
import argparse,datetime,json,os,sys
from pathlib import Path
from connector_entry import ROOT,native
sys.path.insert(0,str(ROOT))
from experiments.connector_handoff.release import verify_release,digest
from experiments.connector_handoff.media import events,render_all


def accepted_attempt(directory):
    for ep in sorted(directory.glob('attempt_*/episode/episode.json')):
        meta=json.loads(ep.read_text())
        if meta.get('mode')=='LIVE' and not meta.get('infrastructure_error',True):return ep.parent
    return None

def image_contract_check(episode,model=None):
    from experiments.connector_handoff.audit import image_requests
    result=image_requests(episode,live=True)
    if not result['requests']:raise RuntimeError('No actual live image requests')
    if model and (result['provider']!=['gemini'] or result['models']!=[model]):
        raise RuntimeError('Recorded provider/model differs from frozen evaluation')
    if not any(x['event']=='verification' for x in events(episode)):raise RuntimeError('No parsed predicate verification')
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--live-vlm',action='store_true',required=True)
    p.add_argument('--seeds',type=Path,default=ROOT/'experiments/connector_handoff/eval_seeds.json')
    p.add_argument('--output',type=Path,default=ROOT/'results/custom_connector/live_trials')
    p.add_argument('--timeout',type=int,default=1800);a=p.parse_args()
    freeze=verify_release()
    if digest(a.seeds)!=freeze['sha256']['experiments/connector_handoff/eval_seeds.json']:raise RuntimeError('Seed list differs from freeze')
    # Credentials are read from the inherited shell only and never printed or stored.
    if not (os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')):raise RuntimeError('Export GEMINI_API_KEY in this shell before live evaluation')
    data=json.loads(a.seeds.read_text())
    for phase,rows in [('debug',data['debug_trials']),('trial_logs',data['trials'])]:
        for row in rows:
            trial=a.output/phase/row['trial_id']
            done=accepted_attempt(trial)
            if done:
                meta=json.loads((done/'episode.json').read_text())
                if meta['seed']!=row['seed'] or meta['evaluation_only']['scene_condition']!=row['condition']:
                    raise RuntimeError('Existing trial directory does not match its frozen seed/condition')
                image_contract_check(done,freeze['vlm_model']);continue
            trial.mkdir(parents=True,exist_ok=True)
            attempt=trial/('attempt_'+datetime.datetime.now().strftime('%Y%m%dT%H%M%S'))
            print(f"LIVE {phase} {row['trial_id']} seed={row['seed']}",flush=True)
            code=native('live',attempt,a.timeout,dict(CONNECTOR_CONDITION=row['condition'],CONNECTOR_SEED=row['seed'],
                VAPTAMP_VLM_PROVIDER='gemini',VAPTAMP_GEMINI_MODEL=freeze['vlm_model']))
            episode=attempt/'episode'
            if (episode/'events.jsonl').exists():
                try:render_all(episode)
                except Exception as exc:(attempt/'media_error.txt').write_text(str(exc))
            if code:
                raise RuntimeError(f'Infrastructure/API interruption preserved at {attempt}. Stopped; rerun the same command to resume with a new attempt.')
            image_contract_check(episode,freeze['vlm_model'])
            # Completed task failures remain results; never retry to select successes.
    print('Frozen 20-seed evaluation completed. Debug episodes are excluded from metrics.')
if __name__=='__main__':main()
