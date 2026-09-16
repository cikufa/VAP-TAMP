"""Read-only release gates over native artifacts and source provenance; no API."""
import json,hashlib,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.connector_handoff.audit import image_requests
from experiments.connector_handoff.media import events
from experiments.connector_handoff.metrics import evaluate,aggregate

def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
    base=ROOT/'results/custom_connector';physics=base/'benchmark_validation/physics/acceptance01'
    observation=base/'benchmark_validation/observability/acceptance01';mock=base/'mock_validation/acceptance01'
    gates={};evidence={}
    matrix=read(physics/'validation.json');gates['physical_crossover']=matrix['valid'] and matrix['repeats']>=5
    measured={c:{g:v['insert_successes']/v['trials'] for g,v in x.items()} for c,x in matrix['matrix'].items()}
    assert measured==read(ROOT/'experiments/connector_handoff/compatibility.json')
    gates['four_oracle_videos']=len(list(physics.glob('00_*/episode.mp4')))==4
    visibility=read(observation/'validation.json');gates['visual']=all(visibility[k] for k in ('initial_fixture_hidden','connector_visible','informative_reachable','informative_within_two_moves'))
    gates['observability_matrix']=(observation/'connector_observability_matrix.png').exists()
    physical_files=['scene.py','primitives.py','assets/geometry.json','assets/connector.usd']
    physical_hashes=read(physics/'source_hashes.json')
    gates['physical_source_unchanged']=all(physical_hashes['experiments/connector_handoff/'+p]==sha(ROOT/'experiments/connector_handoff'/p) for p in physical_files)
    gates['baseline_source_unchanged']=not subprocess.check_output(['git','diff','--name-only','c315720','--','vlm-tamp'],cwd=ROOT,text=True).strip()
    rows=[]
    for name in ('straight','replan'):
        episode=mock/'trial_logs'/name/'episode';trace=events(episode);meta=read(episode/'episode.json')
        result=image_requests(episode);evidence[name+'_images']=result
        gates[name+'_native']=meta['physical_success'] and not meta['infrastructure_error'] and meta['mode']=='MOCK'
        gates[name+'_labels']=all(e.get('label')=='NON-SCIENTIFIC MOCK VLM RUN' for e in trace)
        gates[name+'_media']=all((episode/file).stat().st_size>1000 for file in ('episode.mp4','episode_contact_sheet.png','episode_timeline.png'))
        gates[name+'_planning_logs']=all((episode/'pddl'/name).exists() for name in ('000_problem.pddl','000_plan.txt','000_fd_stdout.log','000_val_stdout.log'))
        gates[name+'_initial_state']=(episode/'initial_state.pkl').exists()
        gates[name+'_symbolic_diffs']=bool(list((episode/'scene_graphs').glob('*_diff.json')))
        rows.append(evaluate(episode,measured))
        sources=read(episode.parent/'source_hashes.json')
        inputs=['pipeline.py','frozen_pipeline.py','task_binding.py','mock_backend.py','recording.py']+physical_files
        gates[name+'_executed_sources']=all(sources['experiments/connector_handoff/'+p]==sha(ROOT/'experiments/connector_handoff'/p) for p in inputs)
        if name=='replan':
            motion=next(e for e in trace if e['event']=='paper_motion_executed')
            new=next(e for e in trace if e['event']=='paper_sensor_observation' and e['sequence']>motion['sequence'])
            old=[e for e in trace if e['event']=='paper_sensor_observation' and e['sequence']<motion['sequence']][-1]
            correction=next(e for e in trace if e['event']=='verification' and e['sequence']>new['sequence'] and e['unmatched_preconditions'])
            replan=next(e for e in trace if e['event']=='plan' and e['sequence']>correction['sequence'])
            gates['native_AP_correction_replan_execution']=new['pixel_sha256']!=old['pixel_sha256'] and any(e['event']=='action_start' and e['sequence']>replan['sequence'] for e in trace)
    gates['mock_not_scientific']=aggregate(rows)['scientific_metrics_computed'] is False
    cf=next((base/'mock_validation/counterfactual_acceptance02').glob('*/counterfactual.json'))
    counter=read(cf);gates['exact_counterfactual_replay']=counter['exact_saved_state_loaded'] and counter['alternate_grasp_success'] and counter['alternate_insert_success'] and counter['source_mode']=='MOCK'
    gates['counterfactual_video']=(cf.parent/'episode/episode.mp4').exists()
    gates['pddl_VAL']=len(read(base/'benchmark_validation/pddl/validation.json'))==3
    gates['unit_tests']='Ran 41 tests' in (base/'unit_tests.log').read_text() and '\nOK\n' in (base/'unit_tests.log').read_text()
    seeds=read(ROOT/'experiments/connector_handoff/eval_seeds.json')
    gates['frozen_balanced_seeds']=len(seeds['trials'])==20 and all(sum(t['condition']==c for t in seeds['trials'])==10 for c in ('LEFT_CONSTRAINED','RIGHT_CONSTRAINED'))
    runs=[physics,observation,mock/'trial_logs/straight',mock/'trial_logs/replan',cf.parent]
    gates['native_process_cleanup']=all(read(r/'run_metadata.json')['success'] and not read(r/'run_metadata.json')['remaining_processes'] and not read(r/'run_metadata.json')['external_changes'] for r in runs)
    evidence.update(physics=matrix,observability=visibility,counterfactual=counter,
        artifacts={str(p.relative_to(ROOT)):sha(p) for p in [physics/'validation.json',physics/'physics_validation.csv',observation/'validation.json',observation/'observability.json',mock/'validation.json',cf,base/'unit_tests.log']})
    result=dict(ready=all(gates.values()),gates=gates,evidence=evidence,
        baseline_sha=subprocess.check_output(['git','rev-parse','c315720'],cwd=ROOT,text=True).strip(),
        evaluated_code_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        scientific_connector_trials_run=0,interpretation='No scientific conclusion from mock runs')
    (base/'acceptance_audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(ready=result['ready'],gates=gates),indent=2))
    if not result['ready']:raise SystemExit(1)
if __name__=='__main__':main()
