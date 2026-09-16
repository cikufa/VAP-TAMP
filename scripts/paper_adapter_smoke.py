"""Bounded live component check from a recorded natural verification failure."""
import json
import os
from pathlib import Path


def run(root, work, env, scope, event):
    import numpy as np
    from gpt4v import GPT4VAgent
    from paper_sim_adapter import PaperSimVerifier
    from fetch_camera_compat import pose, camera_sensor
    from repro_trace import record

    fixture = Path(os.environ['VAPTAMP_PAPER_AP_FIXTURE']).resolve()
    if not fixture.is_relative_to(root):
        raise ValueError('Use a project trial trace as the view fixture')
    source_events = [json.loads(line) for line in fixture.read_text().splitlines()]
    collision_only = os.getenv('VAPTAMP_PROBE_PAPER_COLLISION') == '1'
    last_action = None
    for item in source_events:
        if item['event'] == 'action_end':
            last_action = item
        if collision_only:
            if item['event'] == 'paper_motion_rejected' and last_action:
                break
            continue
        if (item['event'] == 'verification' and last_action
                and last_action['action'][0] == 'find'
                and last_action['action'][2] == 'water_bottle-n-01_2'
                and 'no' in item['visual_answers']):
            break
    else:
        raise ValueError('Fixture has no natural failed bottle-2 visibility check')

    state = last_action['simulator_state']
    for name in ('water_bottle.n.01_1', 'water_bottle.n.01_2', 'agent.n.01_1'):
        saved = state['objects'][name]
        env.task.object_scope[name].set_position_orientation(
            np.array(saved['position']), np.array(saved['orientation']))
    env.robots[0].set_joint_positions(np.array(state['robot_joint_positions']))
    pose(camera_sensor(env.robots[0]))
    os.environ['VAPTAMP_TRACE_DIR'] = str(work / 'trace')
    def combined(name, **fields):
        event(name, **fields)
        record(name, **fields)
    scope['record'] = combined
    combined('paper_view_fixture', trace=str(fixture), action_event=last_action['sequence'],
             verification_event=item['sequence'], recorded_answers=item.get('visual_answers'),
             scientific_trial=False, purpose='replay an observed visibility disagreement')

    agent = GPT4VAgent()
    agent.prompt = str(root / 'vlm-tamp/prompts.txt')
    verifier = PaperSimVerifier(scope, agent, work / 'paper_views',
                               budget_k=2, consistent_votes=4, motion_metres=.25)
    scope.update(vlm_agent=agent, paper_verifier=verifier,
                 CHECK_PRECONDITION=True, CHECK_EFFECT=True)
    if collision_only:
        from unittest.mock import patch
        observation = verifier.observe()
        verifier.refresh(observation, verifier.graph)
        with patch('paper_sim_adapter.ignore_copy_self_collisions', lambda context: None):
            old_moved = verifier.navigate(item['direction'], ['inview', 'agent-n-01_1', 'water_bottle-n-01_2'])
        assert not old_moved, 'Fixture did not reproduce the copy self-collision'
        moved = verifier.navigate(item['direction'], ['inview', 'agent-n-01_1', 'water_bottle-n-01_2'])
        assert moved, 'Filtering only copy self-collisions did not permit the requested path'
        after = verifier.observe()
        verifier.refresh(after, verifier.graph)
        assert observation['pixel_sha256'] != after['pixel_sha256'], 'No new visual observation after motion'
        combined('paper_collision_probe_completed', moved=moved, direction=item['direction'],
                 old_moved=old_moved, distinct_images=2,
                 live_requests=agent.current_round, scientific_trial=False)
        return
    previous = Path.cwd()
    try:
        os.chdir(work)
        planner = scope['pddlsim'](str(root / 'vlm-tamp/domains/bringing_water/domain.pddl'))
        problem = str(root / 'vlm-tamp/domains/bringing_water/problem.pddl')
        plan = planner.plan(problem)
        states = planner.get_intermediate_states(problem, 'pddl_output.txt')
        assert plan[0][0] == 'find' and plan[0][2] == 'water_bottle-n-01_2'
        # The fixture is the actual post-find view, so use the expected state
        # after that same action. Query only the current grasp preconditions.
        preconditions = planner.get_preconditions_by_action(plan[1])
        combined('paper_current_action', current_action=plan[1], preconditions=preconditions)
        changed, updated, _ = scope['check_states_and_update_problem'](
            states[1], [], preconditions, problem, states[0], next_action=plan[1])
        next_plan = planner.plan(updated)
        combined('paper_planner_after_verification', discrepancy=changed, plan=next_plan,
                 updated_problem=Path(updated).read_text())
        assert next_plan, 'No continuation plan after paper verification'
        action = next_plan[0]
        params = scope['format_action_params'](action)
        method = {'find': 'goto', 'grasp': 'grasp', 'place_on_floor': 'place_on_floor'}[action[0]]
        returned = scope[method](params[1], oracle=False)
        combined('paper_continued_execution', action=action, returned=returned,
                 simulator_state=scope['simulator_state'](env, scope['obj_held'], scope['onfloor_relationships']))
        trace = [json.loads(line) for line in (work / 'trace/events.jsonl').read_text().splitlines()]
        views = [item for item in trace if item['event'] == 'paper_sensor_observation']
        motions = [item for item in trace if item['event'] == 'paper_motion_executed']
        predicates = [item for item in trace if item['event'] == 'paper_predicate_result']
        combined('paper_adapter_probe_completed', live_requests=agent.current_round,
                 executed_view_motions=len(motions), distinct_images=len({item['pixel_sha256'] for item in views}),
                 predicate_results=predicates, discrepancy=changed,
                 scope='component replay plus replanning/one continuation; not a full AP episode')
    finally:
        os.chdir(previous)
