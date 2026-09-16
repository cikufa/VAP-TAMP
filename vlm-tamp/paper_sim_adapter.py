"""Opt-in Algorithm 2 embodiment adapter; distinct from fixed-view simulation.

The paper leaves metric motion, agreement and K unspecified. Callers must pass
them. Cached task poses initialize object memory, as in the released simulator;
new geometry comes from actual RGB-D/instance observations. No goal predicates
or successor actions are supplied to view selection.
"""
import hashlib
from pathlib import Path

import numpy as np
from PIL import Image

from paper_verification import verify_predicate


def questions_for(fact):
    fact = fact[1:] if fact[0] == 'not' else fact
    predicate = fact[0]
    label = lambda value: value.split('-')[0].replace('_', ' ')
    if predicate == 'inview':
        x = label(fact[2])
        return (f'Is the {x} visible in this image?', f'Can you see the {x} in this view?',
                f'Is the {x} present and visible in this image?',
                f'Does this image contain the {x}?', f'Is the {x} observable from this viewpoint?')
    if predicate in ('ontop', 'onfloor'):
        x, y = label(fact[1]), label(fact[2])
        return (f'Is the {x} on the {y}?', f'Is the {x} resting on the {y} surface?',
                f'Is the {x} placed on top of the {y}?', f'Is the {x} positioned on the {y}?',
                f'Is the {x} sitting on the {y}?')
    raise ValueError(f'No audited paper paraphrases for {predicate}')


def observed_points(depth, mask, position, rotation, focal_pixels):
    """Project linear camera-Z depth into world XYZ (USD camera looks down -Z)."""
    height, width = depth.shape
    rows, cols = np.nonzero(mask & np.isfinite(depth) & (depth > 0) & (depth < 100))
    z = depth[rows, cols]
    local = np.column_stack(((cols + .5 - width / 2) * z / focal_pixels,
                             -(rows + .5 - height / 2) * z / focal_pixels, -z))
    return local @ rotation.T + position


class PaperSimVerifier:
    def __init__(self, scope, agent, output, *, budget_k, consistent_votes, motion_metres):
        from fetch_camera_compat import camera_sensor
        self.scope, self.agent = scope, agent
        self.robot, self.env, self.og = scope['robot'], scope['env'], scope['og']
        self.log = scope['record']
        self.output = Path(output)
        self.output.mkdir(parents=True, exist_ok=False)
        self.budget_k, self.consistent_votes = budget_k, consistent_votes
        if not 0 < motion_metres <= .5:
            raise ValueError('Inspection motion must be between zero and 0.5 metres')
        self.motion_metres = motion_metres
        self.sensor = camera_sensor(self.robot)
        self.robot.add_obs_modality('depth_linear')
        self.env.load_observation_space()
        self.index = 0
        self.graph = {'objects': {}, 'facts': []}
        self.scope_to_name = {}
        for name, entity in self.env.task.object_scope.items():
            if entity.exists and hasattr(entity, 'get_position'):
                self.scope_to_name[name] = entity.name
                self.graph['objects'][entity.name] = {
                    'anchor': entity.get_position().tolist(), 'source': 'cached_task_pose'}
        self.log('paper_adapter_initialized', budget_k=budget_k,
                 consistent_votes=consistent_votes, motion_metres=motion_metres,
                 viewpoint_frame='target-relative horizontal directions; above raises torso',
                 fidelity='paper Algorithm 2 adaptation; not released fixed-view experiment')

    def observe(self):
        from fetch_camera_compat import pose
        for _ in range(10):
            self.og.sim.render()
        data, info = self.sensor.get_obs()
        rgb = np.asarray(data['rgb']).copy()
        depth = np.asarray(data['depth_linear']).squeeze().copy()
        segmentation = np.asarray(data['seg_instance']).copy()
        position, rotation = pose(self.sensor)
        focal = rgb.shape[1] * self.sensor.focal_length / self.sensor.horizontal_aperture
        observed = {}
        for identifier, name in info['seg_instance'].items():
            if name not in self.graph['objects']:
                continue
            points = observed_points(depth, segmentation == int(identifier), position, rotation, focal)
            if len(points):
                observed[name] = dict(anchor=np.median(points, axis=0).tolist(),
                                      observed_points=len(points), source='sensor_depth_instance_mask',
                                      observation=self.index)
        path = self.output / f'view_{self.index:03d}.png'
        Image.fromarray(rgb).save(path)
        np.savez_compressed(self.output / f'view_{self.index:03d}.npz', depth=depth,
                            instance_segmentation=segmentation, camera_position=position,
                            camera_rotation=rotation, focal_pixels=focal)
        observation = dict(rgb=rgb, index=self.index, objects=observed, image=str(path),
                           pixel_sha256=hashlib.sha256(rgb.tobytes()).hexdigest())
        self.log('paper_sensor_observation', index=self.index, image=str(path),
                 pixel_sha256=observation['pixel_sha256'], camera_position=position.tolist(),
                 camera_rotation=rotation.tolist(), observed_objects=observed)
        self.index += 1
        return observation

    def refresh(self, observation, graph):
        before = {name: graph['objects'].get(name) for name in observation['objects']}
        graph['objects'].update(observation['objects'])
        self.log('paper_object_memory_updated', observation=observation['index'],
                 before=before, after=observation['objects'])
        return graph

    def request(self, observation, prompt, choices):
        self.agent.current_round += 1
        payload = self.agent._prepare_samples(observation['rgb'], prompt)
        # Appendix queries are complete instructions; retain the same image
        # preparation/transport/token bound, without the release's skip prompt.
        payload['messages'] = payload['messages'][1:]
        if self.agent.backend.provider == 'gemini':
            payload['response_enum'] = list(choices)
        self.log('paper_query_observation', round=self.agent.current_round,
                 observation=observation['index'], pixel_sha256=observation['pixel_sha256'])
        answer, _ = self.agent._request_gpt4v(payload)
        return answer

    def query(self, observation, question):
        return self.request(observation, 'Analyze this image carefully.\n'
                            f'Question: {question}\nRespond with only "yes" or "no".', ('yes', 'no'))

    def sufficiency(self, observation, fact):
        return self.request(observation,
            'You are assessing whether this camera view provides sufficient information '
            'to answer the following question:\n'
            f'"{questions_for(fact)[0]}"\n'
            'Consider:\n- Is the target object clearly visible?\n'
            '- Are relevant spatial relationships observable?\n'
            '- Is the view free from significant occlusion?\n'
            'Respond "yes" if the current view is sufficient.\n'
            'Respond "no" if a different viewpoint would provide clearer evidence.\nAnswer:', ('yes', 'no'))

    def direction(self, observation, fact):
        target = self.target(fact).split('.')[0].replace('_', ' ')
        answer = self.request(observation,
            f'The robot is trying to verify:\n"{questions_for(fact)[0]}"\n'
            'The current view does not provide sufficient visual evidence. Suggest '
            f'which direction the robot should move to get a clearer view of the {target}.\n'
            'Options: left, right, front, behind, above, closer\nChoose the single best direction:',
            ('left', 'right', 'front', 'behind', 'above', 'closer'))
        direction = answer.strip().lower()
        if direction not in ('left', 'right', 'front', 'behind', 'above', 'closer'):
            raise ValueError('VLM returned an unsupported inspection direction; raw response retained')
        return direction

    @staticmethod
    def target(fact):
        positive = fact[1:] if fact[0] == 'not' else fact
        value = positive[2] if positive[0] == 'inview' else positive[1]
        return value.replace('-', '.').replace('__', '-')

    def navigate(self, direction, fact):
        from fetch_camera_compat import look_at_fetch, pose
        target = self.graph['objects'][self.scope_to_name[self.target(fact)]]['anchor']
        target = np.asarray(target, dtype=float)
        before, orientation = self.robot.get_position_orientation()
        joints_before = self.robot.get_joint_positions().copy()
        before = before.copy()
        if direction == 'above':
            joint = self.robot.joints['torso_lift_joint']
            current = float(joint.get_state()[0][0])
            raised = min(float(joint.upper_limit), current + self.motion_metres)
            if raised - current < 1e-4:
                self.log('paper_motion_rejected', direction=direction, reason='torso_at_upper_limit')
                return False
            command = joints_before.copy()
            command[list(joint.dof_indices)] = raised
            self.robot.set_joint_positions(command)
        else:
            toward = target[:2] - before[:2]
            norm = np.linalg.norm(toward)
            if norm < 1e-4:
                raise ValueError('Inspection target and robot have coincident horizontal positions')
            toward /= norm
            vectors = dict(front=toward, closer=toward, behind=-toward,
                           left=np.array([-toward[1], toward[0]]),
                           right=np.array([toward[1], -toward[0]]))
            offset = np.r_[self.motion_metres * vectors[direction], 0.]
            # Reject the requested path when blocked; no alternative-view search.
            with self.scope['PlanningContext'](self.robot, self.scope['ap'].robot_copy, 'simplified') as context:
                for fraction in np.linspace(.2, 1., 5):
                    if self.scope['set_base_and_detect_collision'](context, (before + offset * fraction, orientation)):
                        self.log('paper_motion_rejected', direction=direction, reason='path_collision')
                        return False
            self.robot.set_position_orientation(before + offset, orientation)
            held = self.scope['obj_held']
            if held is not None:
                held.set_position(held.get_position() + offset)
            for _ in range(20):
                self.og.sim.step()
        look_at_fetch(self.robot, target)
        pose(self.sensor)
        after = self.robot.get_position()
        joints_after = self.robot.get_joint_positions()
        self.log('paper_motion_executed', direction=direction, target_anchor=target.tolist(),
                 position_before=before.tolist(), position_after=after.tolist(),
                 joints_before=joints_before.tolist(), joints_after=joints_after.tolist())
        return True

    def verify_many(self, facts, states):
        self.graph['facts'] = list(states)
        answers = []
        for fact in facts:
            observation = self.observe()
            self.refresh(observation, self.graph)
            result = verify_predicate(fact, observation, self.graph,
                budget_k=self.budget_k, consistent_votes=self.consistent_votes,
                paraphrases=questions_for, query=self.query, confirm_sufficiency=self.sufficiency,
                suggest_direction=self.direction, navigate=lambda direction: self.navigate(direction, fact),
                observe=self.observe, update_from_observation=self.refresh, log=self.log)
            self.graph = result.graph
            self.log('paper_predicate_result', fact=fact, value=result.value, sufficient=result.sufficient,
                     budget_exhausted=result.budget_exhausted, moves_attempted=result.moves_attempted,
                     voted_observation=result.voted_observation['index'],
                     terminal_observation=result.observation['index'])
            answers.append('yes' if result.value else 'no')
        return answers
