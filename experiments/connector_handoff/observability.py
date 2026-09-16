"""Offline view reachability/occlusion audit using the frozen AP movement method."""
from pathlib import Path
from types import SimpleNamespace
import json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from .scene import CONDITIONS

class Entity:
    exists=True
    def __init__(self,obj):self.obj=obj
    def __getattr__(self,name):return getattr(self.obj,name)

def scope_for(scene,log):
    from omnigibson.action_primitives.starter_semantic_action_primitives import PlanningContext
    from omnigibson.utils.motion_planning_utils import set_base_and_detect_collision
    scene.env.task.object_scope={'connector':Entity(scene.connector),'socket':Entity(scene.objects['socket_top']),
                                 'robot':Entity(scene.robot)}
    return dict(env=scene.env,robot=scene.robot,og=scene.og,ap=scene.ap,record=log,obj_held=None,
        PlanningContext=PlanningContext,set_base_and_detect_collision=set_base_and_detect_collision,
        get_tpv_rgb=lambda:scene.capture()[0])

def run(scene,out,log):
    from paper_sim_adapter import PaperSimVerifier
    from fetch_camera_compat import pose
    out=Path(out);rows=[];images={}
    for condition in CONDITIONS:
        for direction in ('initial','left','right'):
            scene.reset(condition,0)
            adapter=PaperSimVerifier(scope_for(scene,log),None,out/f'{condition}_{direction}',
                                    budget_k=2,consistent_votes=4,motion_metres=.25)
            moves=[];intermediate=[]
            if direction!='initial':
                for i in range(3):
                    moves.append(adapter.navigate(direction,['side_clear_left','socket']))
                    sample=adapter.observe()
                    data_step,info_step=scene.sensor.get_obs();pos_step,rot_step=pose(scene.sensor)
                    from .visibility import evidence
                    focal_step=data_step['rgb'].shape[1]*scene.sensor.focal_length/scene.sensor.horizontal_aperture
                    intermediate.append(dict(move=i+1,executed=moves[-1],camera_position=pos_step.tolist(),
                        camera_rotation=rot_step.tolist(),image=sample['image'],
                        visibility=evidence(data_step['depth_linear'],pos_step,rot_step,focal_step)))
            obs=adapter.observe();adapter.refresh(obs,adapter.graph)
            data,info=scene.sensor.get_obs();seg=np.asarray(data['seg_instance'])
            def pixels(name):
                ids=[int(k) for k,v in info['seg_instance'].items() if v==name]
                return int(np.isin(seg,ids).sum())
            camera_position,camera_rotation=pose(scene.sensor)
            log('instance_registry',mapping={str(k):v for k,v in info['seg_instance'].items()})
            row=dict(condition=condition,view=direction,intermediate_views=intermediate,executed_moves=moves,fixture_pixels=pixels('fixture'),
                connector_pixels=pixels('connector'),camera_position=camera_position.tolist(),camera_rotation=camera_rotation.tolist(),
                robot_position=scene.robot.get_position().tolist(),robot_joints=scene.robot.get_joint_positions().tolist())
            from .visibility import evidence
            focal=data['rgb'].shape[1]*scene.sensor.focal_length/scene.sensor.horizontal_aperture
            row['visibility_evidence']=evidence(data['depth_linear'],camera_position,camera_rotation,focal,pixels('fixture'))
            rows.append(row);log('observability_sample',evaluation_only=row)
            target=out/f'{condition.lower()}_{direction if direction=="initial" else direction+"_oblique"}.png'
            Image.fromarray(obs['rgb']).save(target);images[condition,direction]=Image.open(target).convert('RGB')
            if direction=='initial':
                images[condition,'third']=Image.fromarray(scene.capture()[0]);images[condition,'third'].save(out/f'{condition.lower()}_third.png')
    canvas=Image.new('RGB',(1440,830),'white');d=ImageDraw.Draw(canvas)
    f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
    d.text((16,10),'OFFLINE OBSERVABILITY VALIDATION — GROUND TRUTH FOR EVALUATION ONLY',fill='black',font=f)
    for i,condition in enumerate(CONDITIONS):
        for j,view in enumerate(('initial','left','right','third')):
            image=images[condition,view].copy();image.thumbnail((350,330));x=j*360;y=65+i*380
            canvas.paste(image,(x+(350-image.width)//2,y))
            d.text((x+6,y+335),condition.replace('_CONSTRAINED','')+' | '+view,fill='black',font=f)
    canvas.save(out/'connector_observability_matrix.png')
    (out/'observability.json').write_text(json.dumps(rows,indent=2)+'\n')
    a=np.asarray(images[CONDITIONS[0],'initial']).astype(float);b=np.asarray(images[CONDITIONS[1],'initial']).astype(float)
    gate=dict(initial_mean_absolute_pixel_difference=float(np.abs(a-b).mean()),
        initial_fixture_hidden=all(r['fixture_pixels']==0 and not r['visibility_evidence']['visually_relevant'] for r in rows if r['view']=='initial'),
        connector_visible=all(r['connector_pixels']>=100 for r in rows if r['view']=='initial'),
        informative_reachable=all(all(r['executed_moves']) and r['visibility_evidence']['visually_relevant'] for r in rows if r['view']!='initial'),
        informative_within_two_moves=all(any(v['visibility']['visually_relevant'] for v in r['intermediate_views'][:2]) for r in rows if r['view']!='initial'))
    (out/'validation.json').write_text(json.dumps(gate,indent=2)+'\n')
    assert gate['initial_fixture_hidden'] and gate['connector_visible'] and gate['informative_reachable'],gate
    return rows
