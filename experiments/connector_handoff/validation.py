"""Native pre-freeze engineering checks; no live scientific evaluation."""
import json
import numpy as np
from pathlib import Path
from PIL import Image
from .primitives import ConnectorPrimitives
from .scene import CONDITIONS,SPEC


def run(mode,scene,out,log):
    if mode=='counterfactual':
        from .counterfactual import run as replay
        replay(scene,out,log);return
    if mode in ('physics_validation','grasp_validation'):
        from .physics_validation import run as physics
        physics(scene,out,log,mode=='grasp_validation');return
    if mode in ('mock_straight','mock_replan','live'):
        import os
        from .pipeline import run as pipeline
        boundary='LIVE' if mode=='live' else 'MOCK'
        script=mode.removeprefix('mock_')
        condition=os.getenv('CONNECTOR_CONDITION','RIGHT_CONSTRAINED' if script=='straight' else 'LEFT_CONSTRAINED')
        pipeline(scene,out/'episode',boundary,script,int(os.getenv('CONNECTOR_SEED','0')),condition);return
    if mode=='observability':
        from .observability import run as observe
        observe(scene,out,log);return
    primitive=ConnectorPrimitives(scene,log)
    if mode=='clearance':
        hits=primitive.candidate_collisions();log('clearance_diagnostic',minimum_clearance=primitive.minimum_clearance,contacts=hits)
        assert np.isfinite(primitive.minimum_clearance) and 0<=primitive.minimum_clearance<3
        return
    if mode=='ik':
        from omnigibson.utils.transform_utils import euler2quat
        for sign in (1,-1):
            for x,z in ((.43,.805),(.43,.94),(.76,.94)):
                p=np.array([x,sign*SPEC['grasp_offset'],z]);q=euler2quat(np.array([0,0,-sign*np.pi/2]))
                solution=primitive.solve(p,q)
                log('ik_diagnostic',position=p.tolist(),orientation=q.tolist(),solution=solution,
                    reachable=solution is not None)
                if solution is not None:
                    scene.robot.set_joint_positions(solution,indices=primitive.indices)
                    for _ in range(2):scene.og.sim.render()
                    log('eef_geometry',eef_pose=primitive.eef_pose(),
                        links={k:dict(position=v.get_position().tolist(),aabb=[a.tolist() for a in v.aabb])
                        for k,v in scene.robot.links.items() if 'gripper' in k or 'finger' in k},
                        contacts=primitive.candidate_collisions())
                    third,robot=scene.capture();Image.fromarray(third).save(out/f'ik_{sign}_{x}_{z}.png')
        return
    if mode=='physics_debug':
        for condition in CONDITIONS:
            for choice in ('gL','gR'):
                primitive.reset();scene.reset(condition,0)
                folder=out/f'{condition}_{choice}';folder.mkdir()
                index=0
                def frame(**kw):
                    nonlocal index
                    third,robot=scene.capture()
                    Image.fromarray(third).save(folder/f'{index:04d}.png');index+=1
                primitive.frame=frame
                y1=primitive.grasp(choice);y2=primitive.insert() if y1 else False
                log('physics_combination',evaluation_only={'scene_condition':condition},grasp_choice=choice,Y1=y1,Y2=y2)
        return
    raise ValueError(mode)
