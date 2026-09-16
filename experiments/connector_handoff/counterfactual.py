"""Offline alternate grasp replay. Never imported by online decision-making code."""
import json,os,pickle
from pathlib import Path
from .recording import Recorder
from .primitives import ConnectorPrimitives

def run(scene,out,log):
    request=json.loads(Path(os.environ['CONNECTOR_REPLAY_REQUEST']).read_text())
    scene.reset(request['condition'],request['seed'])
    original=Path(request['initial_state'])
    # Only locally generated simulator state files from this experiment are accepted.
    if not original.resolve().is_relative_to(Path(__file__).resolve().parents[2]/'results/custom_connector'):
        raise ValueError('Replay state must be a local custom_connector artifact')
    with original.open('rb') as stream:saved=pickle.load(stream)
    scene.og.sim.load_state(saved['state'],serialized=False)
    scene.robot.set_joint_positions(saved['drive_targets'],drive=True)
    source_mode=json.loads((Path(request['original_episode'])/'episode.json').read_text())['mode']
    rec=Recorder(Path(out)/'episode',scene,'MOCK' if source_mode=='MOCK' else 'COUNTERFACTUAL',request['seed'],request['condition'])
    rec.log('counterfactual_reset',source_state=str(original),original_episode=request['original_episode'],source_mode=source_mode,
            alternate_grasp=request['alternate_grasp'],exact_saved_state_loaded=True)
    primitive=ConnectorPrimitives(scene,rec.log,rec.frame);rec.frame()
    y1=primitive.grasp(request['alternate_grasp']);y2=primitive.insert() if y1 else False
    rec.finish(physical_success=y2,infrastructure_error=False)
    result=dict(original_episode=request['original_episode'],source_mode=source_mode,alternate_grasp=request['alternate_grasp'],
        alternate_grasp_success=y1,alternate_insert_success=y2,exact_saved_state_loaded=True,
        informative_pregrasp_view_exists=True,observability_evidence=request['observability_evidence'],
        original_insert_attempted=request['original_insert_attempted'],mode='OFFLINE COUNTERFACTUAL')
    (Path(out)/'counterfactual.json').write_text(json.dumps(result,indent=2)+'\n')
    log('counterfactual_complete',**result)
