"""Connector task execution through frozen VAP-TAMP control flow and API boundary."""
import os,sys,json,hashlib
from pathlib import Path
from .recording import Recorder
from .primitives import ConnectorPrimitives
from .task_binding import questions_for,verifier_class
from .observability import scope_for
from .frozen_pipeline import compile_loop,LoggedPlanner,ROOT


def run(scene,out,mode,script,seed,condition):
    import repro_trace
    from gpt4v import GPT4VAgent
    import numpy as np
    scene.reset(condition,seed)
    rec=Recorder(out,scene,mode,seed,condition)
    import pickle
    with (Path(out)/'initial_state.pkl').open('wb') as stream:
        pickle.dump(dict(state=scene.og.sim.dump_state(serialized=False),drive_targets=scene.initial_joints),stream)
    primitive=ConnectorPrimitives(scene,rec.log,rec.frame)
    previous_record=repro_trace.record;repro_trace.record=rec.log
    if mode=='MOCK':
        from .mock_backend import MockBackend
        agent=GPT4VAgent.__new__(GPT4VAgent);agent.backend=MockBackend(script,rec.log)
        agent.max_tokens=50;agent.current_round=0;agent.responses={};agent.errors={};agent.gpt_version=agent.backend.model
    elif mode=='LIVE':agent=GPT4VAgent()
    else:raise ValueError('Only explicit LIVE or MOCK API boundary modes are allowed')
    agent.prompt=str(ROOT/'vlm-tamp/prompts.txt')
    scope=scope_for(scene,rec.log)
    # This task uses a native fixed joint, so base teleports already carry the
    # connector. Keep the verifier's compatibility-only held-object translation
    # disabled; physical holding state still comes from primitive.held below.
    scope['obj_held']=None
    gt_predicates=['handempty','holding','held_left_configuration','held_right_configuration','available']
    def gt(facts):
        result=[]
        for fact in facts:
            f=fact[1:] if fact[0]=='not' else fact
            value={'handempty':primitive.held is None,'holding':primitive.held is not None,
                'held_left_configuration':primitive.held is not None and primitive.choice=='gL',
                'held_right_configuration':primitive.held is not None and primitive.choice=='gR',
                'available':primitive.held is None and np.linalg.norm(scene.connector.get_position()-np.array(__import__('experiments.connector_handoff.scene',fromlist=['SPEC']).SPEC['connector_initial']))<.015}[f[0]]
            result.append('yes' if value else 'no')
        return result
    def dispatch(action):
        name=action[0]
        rec.frame()
        if name.startswith('grasp_connector_'):primitive.grasp('gL' if name.endswith('left') else 'gR')
        elif name.startswith('insert_from_'):primitive.insert()
        elif name=='return_connector':primitive.return_connector()
        elif name=='find':primitive.find(action[2])
        else:raise ValueError('Unmapped task primitive '+name)
        scope['obj_held']=None
        rec.frame()
    def simulator_state(*args):
        return dict(connector_pose=[v.tolist() for v in scene.connector.get_position_orientation()],
                    robot_pose=[v.tolist() for v in scene.robot.get_position_orientation()],
                    robot_joints=scene.robot.get_joint_positions().tolist(),holding=primitive.held is not None,
                    grasp_configuration=primitive.choice)
    out=Path(out).resolve()
    for name in ('downward','VAL'):
        (out/name).symlink_to(ROOT/'vlm-tamp'/name)
    problem=out/'initial_problem.pddl';problem.write_bytes((ROOT/'experiments/connector_handoff/pddl/problem.pddl').read_bytes())
    domain=ROOT/'experiments/connector_handoff/pddl/domain.pddl'
    rec.log('initial_symbolic_state',problem=problem.read_text(),domain_sha256=hashlib.sha256(domain.read_bytes()).hexdigest(),
            fixture_ground_truth_in_online_problem=False)
    scope.update(dict(IMPERCEIVABLE_PREDS=gt_predicates,GT_PREDS=gt_predicates,CHECK_IN_NL=False,
        CHECK_EFFECT=True,CHECK_PRECONDITION=True,USE_ACTIVE_PERCEPTION=False,active_perception_module=None,
        VLM_PLANNING=False,vlm_agent=agent,check_gt_facts=gt,translate_fact_to_question=lambda f:questions_for(f)[0],
        get_fpv_rgb=lambda:scene.sensor.get_obs()[0]['rgb'],get_tpv_rgb=lambda:scene.og.sim.viewer_camera.get_obs()[0]['rgb'],
        trial_counter=0,action_counter=0,MAX_NUM_ACTION=50,terminate=False,invalid_epi=False,
        problem_file=str(problem),domain_file=str(domain),planner=LoggedPlanner(domain,out/'pddl',rec.log),
        dispatch=dispatch,diagnostic_frame=rec.frame,simulator_state=simulator_state,onfloor_relationships=[],
        is_oracle=False,os=os))
    scope['paper_verifier']=verifier_class()(scope,agent,out/'paper_views',budget_k=2,consistent_votes=4,motion_metres=.25)
    loop=compile_loop(scope);previous=Path.cwd();os.chdir(out)
    rec.frame()
    try:
        exec(loop,scope)
        state=primitive.terminal_state()
        rec.finish(physical_success=state['success'],terminal_physics=state,actions=scope['action_counter'],
                   planning_failed=not scope.get('plan') and not state['success'],infrastructure_error=False)
    except Exception as exc:
        rec.log('episode_exception',error_type=type(exc).__name__,message=str(exc))
        rec.finish(physical_success=False,infrastructure_error=True,error_type=type(exc).__name__,error=str(exc))
        raise
    finally:
        os.chdir(previous);repro_trace.record=previous_record
    return rec
