"""Adapter invariants; these tests do not substitute for native/AP evidence."""
import base64
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vlm-tamp'))
from gpt4v import GPT4VAgent
from paper_sim_adapter import PaperSimVerifier, observed_points, questions_for, existing_support_contacts
from vlm_backends import GeminiBackend


class PaperAdapterChecks(unittest.TestCase):
    def test_support_tolerance_cannot_ignore_new_obstacles_or_arm_contacts(self):
        support = dict(robot_mesh='/World/robot_copy/l_wheel_link', other_body='/World/lawn/base_link')
        ground = {'/World/lawn/base_link'}
        self.assertTrue(existing_support_contacts([support], [support], ground))
        wall = dict(support, other_body='/World/wall/base_link')
        arm = dict(support, robot_mesh='/World/robot_copy/elbow_flex_link')
        self.assertFalse(existing_support_contacts([support], [wall], ground))
        self.assertFalse(existing_support_contacts([wall], [wall], ground))
        self.assertFalse(existing_support_contacts([arm], [arm], ground))
        self.assertFalse(existing_support_contacts([], [support], ground))
        self.assertFalse(existing_support_contacts([support] * 8, [support], ground))

    def test_enum_constraint_does_not_change_prompt_or_image(self):
        source = dict(messages=[dict(role='user', content='question')], max_tokens=50)
        plain = GeminiBackend._convert(source)
        constrained = GeminiBackend._convert(dict(source, response_enum=['yes', 'no']))
        self.assertEqual(plain['contents'], constrained['contents'])
        self.assertNotIn('responseMimeType', plain['generationConfig'])
        self.assertEqual(constrained['generationConfig']['responseMimeType'], 'text/x.enum')
        self.assertEqual(constrained['generationConfig']['responseSchema']['enum'], ['yes', 'no'])

    def test_optical_axis_depth_projects_forward_from_usd_camera(self):
        points = observed_points(np.array([[2.]]), np.array([[True]]),
                                 np.array([1., 2., 3.]), np.eye(3), 100.)
        np.testing.assert_allclose(points, [[1., 2., 1.]])

    def test_invalid_depth_and_unselected_pixels_cannot_enter_object_memory(self):
        depth = np.array([[np.nan, np.inf, -1., 0., 101., 2.]])
        points = observed_points(depth, np.ones_like(depth, dtype=bool), np.zeros(3), np.eye(3), 10.)
        self.assertEqual(len(points), 1)
        np.testing.assert_allclose(points[0], [.5, 0., -2.])

    def test_five_real_request_payloads_share_identical_image_bytes(self):
        payloads = []
        agent = GPT4VAgent.__new__(GPT4VAgent)
        agent.prompt = str(ROOT / 'vlm-tamp/prompts.txt')
        agent.max_tokens, agent.gpt_version, agent.current_round = 50, 'test-model', 0
        agent.responses = {}
        def send(payload, round_number):
            payloads.append(payload)
            return 'yes'
        agent.backend = SimpleNamespace(provider='test', request=send)
        adapter = PaperSimVerifier.__new__(PaperSimVerifier)
        adapter.agent, adapter.log = agent, lambda *args, **kwargs: None
        observation = dict(rgb=np.full((16, 16, 4), 255, np.uint8), index=7, pixel_sha256='test')
        questions = questions_for(['inview', 'agent-n-01_1', 'water_bottle-n-01_2'])
        for question in questions:
            self.assertEqual(adapter.query(observation, question), 'yes')
        self.assertEqual(len(payloads), 5)
        urls = [p['messages'][0]['content'][1]['image_url']['url'] for p in payloads]
        self.assertEqual(len(set(urls)), 1)
        self.assertTrue(base64.b64decode(urls[0].split(',')[1]).startswith(b'\x89PNG'))
        self.assertTrue(all(p['max_tokens'] == 50 for p in payloads))
        self.assertTrue(all(len(p['messages']) == 1 for p in payloads))
        self.assertEqual(agent.current_round, 5)

    def test_unsupported_predicates_do_not_get_invented_queries(self):
        with self.assertRaises(ValueError):
            questions_for(['insertion_clearance', 'connector'])


if __name__ == '__main__':
    unittest.main()
