"""Evaluation-only trace and frame storage. No recorded oracle field is returned online."""
import json,time,hashlib
from pathlib import Path
import numpy as np
from PIL import Image

MOCK_LABEL='NON-SCIENTIFIC MOCK VLM RUN'

class Recorder:
    def __init__(self,out,scene,mode,seed,condition):
        self.out=Path(out);self.out.mkdir(parents=True,exist_ok=True)
        self.scene=scene;self.mode=mode;self.start=time.monotonic();self.sequence=0;self.frames=0
        self.observations={};self.bindings={};self.active_move_seen=False
        self.context=dict(phase='PRE-GRASP',current_action=None,plan=[],grasp_choice=None,Y1=None,Y2=None,replan_count=0)
        self.meta=dict(mode=mode,label=MOCK_LABEL if mode=='MOCK' else mode,seed=seed,
                       baseline_sha='c315720',evaluation_only={'scene_condition':condition})
        for name in ('third_person','robot_camera'):(self.out/'frames'/name).mkdir(parents=True,exist_ok=True)
        self.log('episode_start',**self.meta)
    def log(self,event,**data):
        if event=='plan':
            if self.context['plan']:self.context['replan_count']+=1
            self.context['plan']=data.get('plan') or []
        if event=='action_start':self.context['current_action']=data['action']
        if event=='grasp_committed':self.context.update(phase='GRASP',grasp_choice=data['grasp_choice'])
        if event=='grasp_complete':self.context.update(phase='POST-GRASP',Y1=data['grasp_success'])
        if event=='insert_started':self.context['phase']='INSERT'
        if event=='insert_complete':self.context['Y2']=data['insert_success']
        if event=='release_started':self.context['phase']='RECOVERY'
        if event=='paper_votes_raw':self.context.update(predicate=data['predicate'],direction=None,sufficient=None,active_perception=False)
        if event=='paper_vote':self.context['vote']=data['value']
        if event=='paper_sufficiency_raw':self.context['sufficient']=data['answer']
        if event=='paper_direction':self.context.update(direction=data['direction'],active_perception=True)
        if event=='paper_predicate_result':self.context['active_perception']=False
        if event=='paper_sensor_observation':
            # Read-only evaluation of the exact current sensor sample. Never supplied to the verifier.
            obs,info=self.scene.sensor.get_obs()
            seg=np.asarray(obs['seg_instance'])
            ids=[int(k) for k,v in info['seg_instance'].items() if v=='fixture']
            count=int(np.isin(seg,ids).sum())
            from .visibility import evidence
            focal=obs['rgb'].shape[1]*self.scene.sensor.focal_length/self.scene.sensor.horizontal_aperture
            data['evaluation_only']=evidence(obs['depth_linear'],data['camera_position'],data['camera_rotation'],focal,count)
        if event=='paper_sensor_observation':self.observations[data['index']]=data['evaluation_only']
        if event=='paper_motion_executed':self.active_move_seen=True
        if event=='paper_query_observation':self.bindings[data['round']]=data['observation']
        if event=='vlm_request':
            from .task_binding import questions_for
            contract=data.get('source_contract',data.get('payload',{}))
            texts=' '.join(p.get('text','') for m in contract.get('messages',[]) if isinstance(m.get('content'),list) for p in m['content'])
            successor=any(q in texts for side in ('left','right') for q in questions_for(['side_clear_'+side,'socket']))
            obs=self.observations.get(self.bindings.get(data['round']),{})
            data['evaluation_only']=dict(successor_predicate_query=successor,
                successor_relevant_view=bool(successor and self.active_move_seen and obs.get('visually_relevant')))
        if event=='verification':
            data['evaluation_only']=dict(proprioceptive_facts=data.pop('ground_truth_facts',[]),
                                         proprioceptive_answers=data.pop('ground_truth_answers',[]))
        row=dict(sequence=self.sequence,seconds=time.monotonic()-self.start,event=event,mode=self.mode,
                 label=self.meta['label'],frame_index=(self.frames if event in ('paper_sensor_observation','paper_vote','paper_sufficiency_raw') else max(0,self.frames-1)))
        row.update(data);row.update(mode=self.mode,label=self.meta['label'])
        with (self.out/'events.jsonl').open('a') as f:f.write(json.dumps(row,default=lambda x:x.tolist())+'\n')
        if event in ('initial_symbolic_state','verification','plan','paper_symbolic_state_updated'):
            folder=self.out/'scene_graphs';folder.mkdir(exist_ok=True)
            (folder/f'{self.sequence:05d}_{event}.json').write_text(json.dumps(row,default=lambda x:x.tolist(),indent=2)+'\n')
            if event=='verification':
                before=set(x.strip() for x in data['input_states']);after=set(x.strip() for x in data['updated_states'])
                diff={'added':sorted(after-before),'removed':sorted(before-after),'changed_relationships':sorted((after-before)|(before-after))}
                (folder/f'{self.sequence:05d}_diff.json').write_text(json.dumps(diff,indent=2)+'\n')
        self.sequence+=1
        if event=='paper_sensor_observation':
            self.last_voted_image=data['image'];self.frame(robot_image=data['image'])
        elif event in ('paper_vote','paper_sufficiency_raw'):
            self.frame(robot_image=getattr(self,'last_voted_image',None))
    def frame(self,**kw):
        third,robot=self.scene.capture()
        if kw.get('robot_image'):robot=np.asarray(Image.open(kw['robot_image']).convert('RGB'))
        for name,im in [('third_person',third),('robot_camera',robot)]:
            Image.fromarray(im).save(self.out/'frames'/name/f'{self.frames:05d}.png')
        self.log('frame',index=self.frames,context=dict(self.context),robot_sha256=hashlib.sha256(robot.tobytes()).hexdigest())
        self.frames+=1
    def finish(self,**result):
        self.frame();self.log('episode_end',**result)
        (self.out/'episode.json').write_text(json.dumps(dict(self.meta,**result),indent=2)+'\n')
