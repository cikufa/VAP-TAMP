"""Native pre-freeze engineering checks; no live scientific evaluation."""
import json
import numpy as np
from pathlib import Path
from PIL import Image
from .primitives import ConnectorPrimitives
from .scene import CONDITIONS,SPEC


def run(mode,scene,out,log):
    if mode=='observability':
        from .observability import run as observe
        observe(scene,out,log);return
    primitive=ConnectorPrimitives(scene,log)
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
