"""Repeated native primitive validation; oracle choices are offline only."""
import csv,json,os
from pathlib import Path
from .scene import CONDITIONS
from .primitives import ConnectorPrimitives
from .recording import Recorder

FIELDS=('seed','scene_condition','grasp_choice','grasp_success','connector_gripper_transform',
        'insert_started','minimum_clearance','collision_object','maximum_insertion_depth',
        'terminal_pose_error','insert_success')

def run(scene,out,log,grasps_only=False):
    repeats=int(os.getenv('CONNECTOR_REPEATS','5'));rows=[]
    primitive=ConnectorPrimitives(scene,log)
    for rep in range(repeats):
        for condition in CONDITIONS:
            for choice in ('gL','gR'):
                primitive.reset();scene.reset(condition,1000+rep)
                directory=Path(out)/f'{rep:02d}_{condition}_{choice}'
                rec=Recorder(directory,scene,'PHYSICS',1000+rep,condition)
                primitive.log=rec.log;primitive.frame=rec.frame
                rec.frame();y1=primitive.grasp(choice)
                y2=primitive.insert() if y1 and not grasps_only else None
                rec.finish(physical_success=y2,grasp_success=y1,infrastructure_error=False)
                events=[json.loads(line) for line in (directory/'events.jsonl').read_text().splitlines()]
                grasp=next(e for e in events if e['event']=='grasp_complete')
                ins=next((e for e in events if e['event']=='insert_complete'),{})
                row=dict(seed=1000+rep,scene_condition=condition,grasp_choice=choice,grasp_success=y1,
                    connector_gripper_transform=grasp.get('connector_gripper_transform'),
                    insert_started=any(e['event']=='insert_started' for e in events),
                    **{key:ins.get(key) for key in FIELDS[6:]})
                rows.append(row)
                with (Path(out)/'physics_validation.csv').open('w') as stream:
                    writer=csv.DictWriter(stream,fieldnames=FIELDS);writer.writeheader()
                    writer.writerows({k:json.dumps(v) if isinstance(v,(list,dict)) else v for k,v in r.items()} for r in rows)
                log('physics_combination',**row)
    matrix={condition:{choice:dict(grasp_successes=sum(r['grasp_success'] for r in rows if r['scene_condition']==condition and r['grasp_choice']==choice),
        insert_successes=sum(bool(r['insert_success']) for r in rows if r['scene_condition']==condition and r['grasp_choice']==choice),trials=repeats)
        for choice in ('gL','gR')} for condition in CONDITIONS}
    valid=all(v['grasp_successes']/repeats>=.9 for c in matrix.values() for v in c.values())
    if not grasps_only:
        valid &= all(matrix[c][g]['insert_successes']==(repeats if (c=='LEFT_CONSTRAINED')==(g=='gR') else 0) for c in CONDITIONS for g in ('gL','gR'))
    (Path(out)/'validation.json').write_text(json.dumps(dict(valid=bool(valid),repeats=repeats,matrix=matrix,
        regime='Repeated deterministic scene reset with seeded RNG; no injected pose or motor noise'),indent=2)+'\n')
    if not valid:raise RuntimeError('Physical benchmark validity gate failed; see measured matrix')
