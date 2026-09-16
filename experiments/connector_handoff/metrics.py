"""Offline first-handoff metrics, temporal attribution and separate recovery results."""
import json,math
from pathlib import Path
from .media import events
from .task_binding import questions_for


def evaluate(path,compatibility=None,counterfactual=None):
    path=Path(path);e=events(path)
    first=lambda kind:next((x for x in e if x['event']==kind),None)
    meta=first('episode_start') or {};end=first('episode_end')
    grasp=first('grasp_committed');grasp_end=first('grasp_complete');insert=first('insert_started')
    requests=[x for x in e if x['event']=='vlm_request']
    def successor_request(x):
        payload=x.get('source_contract',x.get('payload',{}));text=json.dumps(payload.get('messages',[]))
        return any(q in text for side in ('left','right') for q in questions_for(['side_clear_'+side,'socket']))
    query=next((x for x in requests if successor_request(x)),None)
    observations=[x for x in e if x['event']=='paper_sensor_observation']
    obs_by_id={x['index']:x for x in observations}
    motions=[x for x in e if x['event']=='paper_motion_executed']
    bindings={x['round']:x['observation'] for x in e if x['event']=='paper_query_observation'}
    inspected={bindings.get(x['round']) for x in requests if successor_request(x)}
    queried_ids=set(inspected)
    # The literal baseline can acquire a final image without voting on it.
    # Count that acquisition if the preceding AP move inspected a successor region,
    # and report whether it was ever queried separately.
    for motion in motions:
        vote=next((x for x in reversed(e[:motion['sequence']]) if x['event']=='paper_votes_raw'),None)
        if vote and any(str(v).startswith('side_clear_') for v in vote.get('predicate',[])):
            following=next((x for x in observations if x['sequence']>motion['sequence']),None)
            if following:inspected.add(following['index'])
    # Require an inspected successor region, geometric visibility and an AP move.
    # Generic movement/connector checks never qualify.
    view=next((x for x in observations if x['index'] in inspected and x.get('evaluation_only',{}).get('visually_relevant') and
               any(m['sequence']<x['sequence'] for m in motions)),None)
    t=lambda x:None if x is None else x['seconds']
    tg,ti,tv=t(grasp),t(insert),t(view)
    if tv is None:timing='NONE'
    elif tg is None or tv<tg:timing='PROSPECTIVE'
    elif ti is None or tv<ti:timing='REACTIVE'
    else:timing='VERY_LATE'
    later=[x for x in e if x['event']=='grasp_committed' and grasp and x['sequence']>grasp['sequence']]
    stop=later[0]['sequence'] if later else float('inf')
    first_results=[x for x in e if x['event']=='insert_complete' and x['sequence']<stop]
    first_attempts=[x for x in e if x['event']=='insert_started' and x['sequence']<stop]
    y1=bool(grasp_end and grasp_end['grasp_success']) if grasp else None
    # Operational first-handoff Y2: abandonment is zero, but never called a collision.
    y2=any(x.get('insert_success',False) for x in first_results) if grasp_end else None
    final=bool(end and end.get('physical_success'))
    plans=[x for x in e if x['event']=='plan'];initial_choice=None
    if plans:
        initial_choice=next((a[0] for a in plans[0].get('plan') or [] if a[0].startswith('grasp_connector_')),None)
    chosen=grasp.get('grasp_choice') if grasp else None
    initial_choice={'grasp_connector_left':'gL','grasp_connector_right':'gR'}.get(initial_choice)
    condition=meta.get('evaluation_only',{}).get('scene_condition')
    values=(compatibility or {}).get(condition,{})
    value=values.get(chosen);best=max(values.values()) if values else None
    corrections=[x for x in e if x['event']=='verification' and (x.get('unmatched_effects') or x.get('unmatched_preconditions'))]
    # Temporal trace attribution, not experimental proof of causation.
    changed=bool(timing=='PROSPECTIVE' and initial_choice and chosen and initial_choice!=chosen and
                 any(tv<=x['seconds']<tg for x in corrections) and any(tv<=x['seconds']<tg for x in plans))
    base_path=sum(math.dist(x['position_before'],x['position_after']) for x in motions)
    camera_path=sum(math.dist(a['camera_position'],b['camera_position']) for a,b in zip(observations,observations[1:]))
    response_times={}
    for x in e:
        if x['event']=='vlm_response':response_times[x['round']]=x['seconds']
    vlm_time=sum(max(0,response_times.get(x['round'],x['seconds'])-x['seconds']) for x in requests)
    directions=[x for x in e if x['event']=='paper_direction']
    motion_time=sum(x['seconds']-max((d['seconds'] for d in directions if d['sequence']<x['sequence']),default=x['seconds']) for x in motions)
    perception_errors=[]
    for x in e:
        if x['event']!='paper_predicate_result':continue
        fact=x.get('fact',[])
        if not fact or not fact[0].startswith('side_clear_'):continue
        obs=obs_by_id.get(x.get('voted_observation'),{})
        side=fact[0].split('_')[-1]
        expected=condition!=side.upper()+'_CONSTRAINED'
        if obs.get('evaluation_only',{}).get('visually_relevant') and bool(x['value'])!=expected:
            perception_errors.append(x['sequence'])
    actual_failed=bool(first_attempts and first_results and not y2)
    alternate=(counterfactual or {}).get('alternate_insert_success')
    motion_failed=any(x['event']=='motion_failure' for x in e)
    # Mutually exclusive primary attribution; supporting flags remain available.
    if not end or end.get('infrastructure_error'):category='J'
    elif end.get('planning_failed'):category='I'
    elif best==0:category='F'
    elif grasp_end and not y1:category='H'
    elif final and later:category='C'
    elif final and timing=='PROSPECTIVE' and value==best==1:category='A'
    elif final:category='B'
    elif actual_failed and alternate is True:category='E'
    elif perception_errors:category='G'
    elif motion_failed:category='H'
    elif timing in ('REACTIVE','VERY_LATE'):category='D'
    else:category='UNCLASSIFIED_PENDING_EVIDENCE'
    return dict(episode=str(path),mode=meta.get('mode'),seed=meta.get('seed'),condition=condition,
        completed=end is not None,category=category,Y1=y1,Y2=y2,first_insert_attempted=bool(first_attempts),
        physical_failed_first_insert=actual_failed,first_handoff_abandoned=bool(y1 and not first_attempts),
        final_success=final,grasp_choice=chosen,initial_planner_grasp=initial_choice,decision_changed=changed,
        decision_change_attribution='Temporal observation → correction → plan → different executed grasp; not causal intervention',
        T_grasp=tg,T_successor_query=t(query),T_successor_view=tv,T_insert=ti,timing=timing,
        successor_relevant_view=view is not None,successor_view_was_queried=bool(view and view['index'] in queried_ids),
        late_after_failed_insert=bool(timing=='VERY_LATE' and any(x['seconds']<tv and not x.get('insert_success') for x in first_results)),
        chosen_handoff_value=value,oracle_best_handoff_value=best,
        handoff_regret=None if best is None or value is None else best-value,
        compatible_grasp=None if value is None else value==best and best>0,
        replans=max(0,len(plans)-1),regrasps=len(later),recovery_attempted=bool(later or corrections),
        recovered=bool((later or corrections) and final),perception_error_events=perception_errors,
        new_views=len(motions),base_path_metres=base_path,camera_path_metres=camera_path,
        sensing_seconds=vlm_time+motion_time,vlm_seconds=vlm_time,motion_seconds=motion_time,
        vlm_queries=len(requests),total_seconds=t(end),counterfactual=counterfactual,scientific=meta.get('mode')=='LIVE')


def aggregate(rows):
    if any(x['mode']=='MOCK' for x in rows):
        if any(x['mode']=='LIVE' for x in rows):raise ValueError('Cannot mix mock and live trials')
        return dict(label='NON-SCIENTIFIC MOCK VLM RUN',scientific_metrics_computed=False,plumbing_episodes=rows)
    usable=[x for x in rows if x['completed'] and x['category']!='J'];n=len(usable)
    rate=lambda pred:sum(bool(pred(x)) for x in usable)/n if n else None
    mean=lambda key:sum(vals)/len(vals) if (vals:=[x[key] for x in usable if x.get(key) is not None]) else None
    n_y1=sum(x['Y1'] is True for x in usable);n_recovery=sum(x['recovery_attempted'] for x in usable)
    return dict(planned_trials=20,completed_eligible=n,missing_trials=max(0,20-len(rows)),
        infrastructure_or_incomplete=sum(x['category']=='J' for x in rows),
        denominator='Completed non-infrastructure trials; incomplete attempts and missing seeds reported separately',
        current_skill_success=rate(lambda x:x['Y1']),handoff_failure=rate(lambda x:x['Y1'] and not x['Y2']),
        conditional_successor_success=(sum(bool(x['Y1'] and x['Y2']) for x in usable)/n_y1 if n_y1 else None),
        first_chain_end_to_end_success=rate(lambda x:x['Y1'] and x['Y2']),final_success_after_recovery=rate(lambda x:x['final_success']),
        sensing_rates={t:rate(lambda x:x['timing']==t) for t in ('PROSPECTIVE','REACTIVE','VERY_LATE','NONE')},
        late_after_failed_insert_rate=rate(lambda x:x['late_after_failed_insert']),
        compatible_grasp_rate=mean('compatible_grasp'),mean_handoff_regret=mean('handoff_regret'),
        decision_change_rate=rate(lambda x:x['decision_changed']),replanning_rate=rate(lambda x:x['replans']>0),
        regrasp_rate=rate(lambda x:x['regrasps']>0),recovery_rate=rate(lambda x:x['recovery_attempted']),
        recovery_success=(sum(x['recovered'] for x in usable)/n_recovery if n_recovery else None),
        sensing_cost_means={k:mean(k) for k in ('new_views','base_path_metres','camera_path_metres','sensing_seconds','vlm_queries','total_seconds')},
        categories={c:sum(x['category']==c for x in rows) for c in sorted({x['category'] for x in rows})},trials=rows)
