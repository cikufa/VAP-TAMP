"""Offline renderers for real simulator frames, traces, and temporal attribution."""
import json,textwrap
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import cv2
import numpy as np

FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def font(size):return ImageFont.truetype(FONT,size)
def events(path):return [json.loads(l) for l in (Path(path)/'events.jsonl').read_text().splitlines()]
def image_at(path,index,kind):
    p=Path(path)/'frames'/kind/f'{index:05d}.png'
    return Image.open(p).convert('RGB') if p.exists() else Image.new('RGB',(640,400),'#ddd')

def render_video(path):
    path=Path(path);e=events(path);rows=[x for x in e if x['event']=='frame']
    if not rows:raise ValueError('No native frames to render')
    output=path/'episode.mp4';writer=cv2.VideoWriter(str(output),cv2.VideoWriter_fourcc(*'mp4v'),12,(1280,720))
    if not writer.isOpened():raise RuntimeError('Video encoder unavailable')
    for row in rows:
        canvas=Image.new('RGB',(1280,720),'#eff1f3');d=ImageDraw.Draw(canvas)
        canvas.paste(image_at(path,row['index'],'third_person').resize((900,600)),(0,70))
        canvas.paste(image_at(path,row['index'],'robot_camera').resize((320,320)),(930,70))
        title=f"{row['label']} | {path.name} | seed={e[0].get('seed')} | t={row['seconds']:.2f}s"
        d.text((18,16),title,font=font(20),fill='black')
        c=row.get('context',{});lines=[]
        for key in ('phase','current_action','plan','predicate','vote','sufficient','active_perception','direction','grasp_choice','Y1','Y2','replan_count'):
            lines.extend(textwrap.wrap(f'{key}: {c.get(key)}',43)[:3])
        for j,line in enumerate(lines[:21]):d.text((915,400+j*14),line,font=font(12),fill='black')
        d.text((16,687),'Native OmniGibson observations; 12 fps observation sequence, not wall-clock playback.',font=font(15),fill='black')
        writer.write(cv2.cvtColor(np.asarray(canvas),cv2.COLOR_RGB2BGR))
    writer.release()
    cap=cv2.VideoCapture(str(output));n=0
    while cap.read()[0]:n+=1
    cap.release()
    if n!=len(rows):raise RuntimeError('Encoded video did not decode completely')
    return output

def render_contact_sheet(path):
    path=Path(path);e=events(path)
    grasp=next((x['seconds'] for x in e if x['event']=='grasp_committed'),float('inf'))
    selectors=[('Initial third-person',lambda x:x['event']=='frame','third_person'),
      ('Initial robot camera',lambda x:x['event']=='frame','robot_camera'),
      ('GRASP verification',lambda x:x['event']=='verification' and x['seconds']<grasp,'robot_camera'),
      ('Pre-GRASP active view',lambda x:x['event']=='paper_motion_executed' and x['seconds']<grasp,'robot_camera'),
      ('Grasp committed',lambda x:x['event']=='grasp_committed','third_person'),
      ('Post-GRASP state',lambda x:x['event']=='grasp_complete','third_person'),
      ('INSERT preconditions',lambda x:x['event']=='paper_votes_raw' and any('clear' in t for t in x.get('predicate',[])),'robot_camera'),
      ('Relevant observation',lambda x:x['event']=='paper_sensor_observation' and x.get('evaluation_only',{}).get('visually_relevant'),'robot_camera'),
      ('Symbolic correction',lambda x:x['event']=='verification' and (x.get('unmatched_effects') or x.get('unmatched_preconditions')),'third_person'),
      ('Replanned plan',lambda x:x['event']=='plan' and x['seconds']>grasp,'third_person'),
      ('Insertion attempt',lambda x:x['event']=='insert_started','third_person'),
      ('Final outcome',lambda x:x['event']=='episode_end','third_person')]
    canvas=Image.new('RGB',(1280,1080),'white');d=ImageDraw.Draw(canvas)
    label=e[0].get('label','');d.text((15,12),label+' | '+path.name,font=font(20),fill='black')
    for i,(caption,test,kind) in enumerate(selectors):
        row=next((x for x in e if test(x)),None);x=(i%4)*320;y=55+(i//4)*335
        index=row['frame_index'] if row else 0
        if row and row['event'] in ('grasp_complete','insert_complete','insert_started','grasp_committed'):
            following=next((r for r in e if r['event']=='frame' and r['sequence']>row['sequence']),None)
            if following:index=following['index']
        im=image_at(path,index,kind) if row else Image.new('RGB',(320,270),'#e0e0e0')
        im.thumbnail((310,275));canvas.paste(im,(x+(310-im.width)//2,y))
        d.text((x+7,y+280),caption,font=font(15),fill='black')
        detail=f"t={row['seconds']:.2f}s / event {row['sequence']}" if row else 'Not observed in this episode'
        d.text((x+7,y+303),detail,font=font(12),fill='black')
    output=path/'episode_contact_sheet.png';canvas.save(output);return output

def render_timeline(path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    path=Path(path);e=events(path)
    kinds=['action_start','plan','paper_votes_raw','paper_vote','paper_sufficiency_raw','paper_motion_executed',
           'paper_sensor_observation','grasp_committed','grasp_complete','verification','replan','insert_started','episode_end']
    fig,ax=plt.subplots(figsize=(16,7))
    for j,kind in enumerate(kinds):
        subset=[x for x in e if x['event']==kind]
        if kind=='replan':subset=[x for x in e if x['event']=='plan'][1:]
        if kind=='verification':subset=[x for x in subset if x.get('unmatched_effects') or x.get('unmatched_preconditions')]
        if kind=='paper_sensor_observation':subset=[x for x in subset if x.get('evaluation_only',{}).get('visually_relevant')]
        ax.scatter([x['seconds'] for x in subset],[j]*len(subset),s=35)
        if kind in ('action_start','plan','replan','paper_motion_executed','episode_end'):
            for x in subset:
                label=x.get('action',x.get('plan',x.get('direction','success='+str(x.get('physical_success')))))
                if isinstance(label,list):label=' → '.join(a[0] if isinstance(a,list) else str(a) for a in label)
                ax.annotate(str(label)[:95],(x['seconds'],j),xytext=(3,-12),textcoords='offset points',fontsize=6)
    for kind,label,color in [('grasp_committed','GRASP COMMITTED','#b22222'),('grasp_complete','GRASP COMPLETE','#157a35'),('insert_started','INSERT ATTEMPT','#274c9b')]:
        row=next((x for x in e if x['event']==kind),None)
        if row:ax.axvline(row['seconds'],color=color,linewidth=2,label=label)
    ax.set_yticks(range(len(kinds)),[k.replace('_',' ') for k in kinds]);ax.invert_yaxis()
    ax.set_xlabel('Elapsed wall time (seconds)');ax.set_title(e[0].get('label','')+' | '+path.name)
    ax.grid(axis='x',alpha=.25)
    if ax.get_legend_handles_labels()[0]:ax.legend(loc='upper right')
    fig.tight_layout();output=path/'episode_timeline.png';fig.savefig(output,dpi=140);plt.close(fig);return output

def render_all(path):return [str(f(path)) for f in (render_video,render_contact_sheet,render_timeline)]
