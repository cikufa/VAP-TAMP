"""Explicit live-only, resumable 2-debug then frozen 20-seed evaluation."""
import argparse,datetime,hashlib,json,os,sys
from pathlib import Path
from connector_entry import ROOT,native
sys.path.insert(0,str(ROOT))
from experiments.connector_handoff.release import verify_release,digest
from experiments.connector_handoff.media import events,render_all


def trace_digest(episode):
    return hashlib.sha256((episode/'events.jsonl').read_bytes()).hexdigest()

def debug_contract_check(episode,model=None):
    image_result=image_contract_check(episode,model)
    trace=events(episode)
    successful_responses=[x for x in trace if x['event']=='vlm_response' and x.get('http_status')==200]
    parsed_votes=[x for x in trace if x['event']=='paper_vote']
    verifications=[x for x in trace if x['event']=='verification']
    missing=[]
    if not successful_responses:missing.append('successful Gemini response')
    if not parsed_votes:missing.append('parsed predicate vote')
    if not verifications:missing.append('parsed verification')
    if missing:raise RuntimeError('Debug plumbing incomplete: '+', '.join(missing))
    meta=json.loads((episode/'episode.json').read_text())
    result=dict(passed=True,non_metric=True,trace_sha256=trace_digest(episode),
        task_complete=bool(meta.get('physical_success')),infrastructure_error=bool(meta.get('infrastructure_error')),
        image_contract=image_result,successful_vlm_responses=len(successful_responses),
        parsed_votes=len(parsed_votes),verifications=len(verifications))
    (episode/'debug_validation.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

def accepted_attempt(directory,phase,model):
    for ep in sorted(directory.glob('attempt_*/episode/episode.json'),reverse=True):
        meta=json.loads(ep.read_text())
        if meta.get('mode')!='LIVE':continue
        if phase=='debug':
            try:debug_contract_check(ep.parent,model)
            except (AssertionError,KeyError,RuntimeError,FileNotFoundError):continue
            return ep.parent
        if not meta.get('infrastructure_error',True):return ep.parent
    return None

def image_contract_check(episode,model=None):
    from experiments.connector_handoff.audit import image_requests
    result=image_requests(episode,live=True)
    if not result['requests']:raise RuntimeError('No actual live image requests')
    if model and (result['provider']!=['gemini'] or result['models']!=[model]):
        raise RuntimeError('Recorded provider/model differs from frozen evaluation')
    if not any(x['event']=='verification' for x in events(episode)):raise RuntimeError('No parsed predicate verification')
    return result

def debug_suite_check(episodes,output):
    trace=[row for episode in episodes for row in events(episode)]
    corrections=[x for x in trace if x['event']=='verification' and
        (x.get('unmatched_effects') or x.get('unmatched_preconditions'))]
    correction_sequences=[x['sequence'] for x in corrections]
    replans=[x for x in trace if x['event']=='planner_call' and
        any(x['sequence']>sequence for sequence in correction_sequences)]
    result=dict(passed=bool(corrections and replans and any(x['event']=='paper_motion_executed' for x in trace)),
        non_metric=True,episodes=[str(x) for x in episodes],
        camera_motions=sum(x['event']=='paper_motion_executed' for x in trace),
        symbolic_corrections=len(corrections),replans_after_correction=len(replans))
    if not result['passed']:
        raise RuntimeError('Two-episode debug gate lacks camera motion, symbolic correction, or replanning')
    output.mkdir(parents=True,exist_ok=True)
    (output/'debug_validation.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--live-vlm',action='store_true',required=True)
    p.add_argument('--seeds',type=Path,default=ROOT/'experiments/connector_handoff/eval_seeds.json')
    p.add_argument('--output',type=Path,default=ROOT/'results/custom_connector/live_trials')
    p.add_argument('--timeout',type=int,default=1800)
    p.add_argument('--debug-timeout',type=int,default=900)
    p.add_argument('--debug-only',action='store_true');a=p.parse_args()
    freeze=verify_release()
    if digest(a.seeds)!=freeze['sha256']['experiments/connector_handoff/eval_seeds.json']:raise RuntimeError('Seed list differs from freeze')
    # Credentials are read from the inherited shell only and never printed or stored.
    if not (os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')):raise RuntimeError('Export GEMINI_API_KEY in this shell before live evaluation')
    data=json.loads(a.seeds.read_text())
    debug_episodes=[]
    phases=[('debug',data['debug_trials'])]
    if not a.debug_only:phases.append(('trial_logs',data['trials']))
    for phase,rows in phases:
        for row in rows:
            trial=a.output/phase/row['trial_id']
            done=accepted_attempt(trial,phase,freeze['vlm_model'])
            if done:
                meta=json.loads((done/'episode.json').read_text())
                if meta['seed']!=row['seed'] or meta['evaluation_only']['scene_condition']!=row['condition']:
                    raise RuntimeError('Existing trial directory does not match its frozen seed/condition')
                image_contract_check(done,freeze['vlm_model'])
                if phase=='debug':debug_episodes.append(done)
                continue
            trial.mkdir(parents=True,exist_ok=True)
            attempt=trial/('attempt_'+datetime.datetime.now().strftime('%Y%m%dT%H%M%S'))
            print(f"LIVE {phase} {row['trial_id']} seed={row['seed']}",flush=True)
            timeout=a.debug_timeout if phase=='debug' else a.timeout
            code=native('live',attempt,timeout,dict(CONNECTOR_CONDITION=row['condition'],CONNECTOR_SEED=row['seed'],
                VAPTAMP_VLM_PROVIDER='gemini',VAPTAMP_GEMINI_MODEL=freeze['vlm_model']))
            episode=attempt/'episode'
            if (episode/'events.jsonl').exists():
                try:render_all(episode)
                except Exception as exc:(attempt/'media_error.txt').write_text(str(exc))
            if phase=='debug':
                try:debug_contract_check(episode,freeze['vlm_model'])
                except (AssertionError,KeyError,RuntimeError,FileNotFoundError):
                    if code:raise RuntimeError(f'Infrastructure/API interruption preserved at {attempt}. Stopped; rerun the same command to resume with a new attempt.')
                    raise
                debug_episodes.append(episode)
                continue
            if code:
                raise RuntimeError(f'Infrastructure/API interruption preserved at {attempt}. Stopped; rerun the same command to resume with a new attempt.')
            image_contract_check(episode,freeze['vlm_model'])
            # Completed task failures remain results; never retry to select successes.
        if phase=='debug':debug_suite_check(debug_episodes,a.output/'debug')
    if a.debug_only:
        print('Two non-metric live debug episodes passed; scientific trials were not started.')
        return
    print('Frozen 20-seed evaluation completed. Debug episodes are excluded from metrics.')
if __name__=='__main__':main()
