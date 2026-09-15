"""Narrow checks for API and observation compatibility, without launching OG.

The upstream eval module runs experiments at import time. Compile only the
actual functions under test from its AST rather than importing that entrypoint.
These checks make no claim about physics or VLM accuracy.
"""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
import sys
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vlm-tamp'))


def load_definition(path, name, namespace, class_name=None):
    tree = ast.parse((ROOT / path).read_text())
    nodes = tree.body
    if class_name:
        nodes = next(n for n in nodes if isinstance(n, ast.ClassDef) and n.name == class_name).body
    node = next(n for n in nodes if isinstance(n, ast.FunctionDef) and n.name == name)
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), namespace)
    return namespace[name]


class CompatibilityChecks(unittest.TestCase):
    def request(self, response):
        requests = SimpleNamespace(post=Mock(return_value=response))
        function = load_definition("vlm-tamp/gpt4v.py", "_request_gpt4v", {"requests": requests}, "GPT4VAgent")
        agent = SimpleNamespace(api_key="test-placeholder", current_round=1, responses={}, errors={})
        return function(agent, {"model": "gpt-4-turbo"})

    def test_http_error_cannot_become_affirmative_evidence(self):
        with self.assertRaisesRegex(RuntimeError, "HTTP 429"):
            self.request(SimpleNamespace(ok=False, text="rate limit", status_code=429))

    def test_empty_response_cannot_become_affirmative_evidence(self):
        with self.assertRaisesRegex(RuntimeError, "HTTP 200"):
            self.request(SimpleNamespace(ok=True, text="", status_code=200))

    def test_successful_answers_are_preserved(self):
        response = SimpleNamespace(ok=True, text="response", status_code=200,
                                   json=lambda: {"choices": [{"message": {"content": "yes;no;skip"}}]})
        self.assertEqual(self.request(response), ("yes;no;skip", False))

    def test_camera_unpacking_preserves_pixel_data(self):
        function = load_definition("vlm-tamp/eval.py", "_observation_data", {})
        data = {"rgb": object()}
        self.assertIs(function(data), data)
        self.assertIs(function((data, {"metadata": "example"})), data)

    def test_registry_visibility_does_not_use_scene_list_order(self):
        # ID 71 cannot sensibly index a one-object scene. OG supplies its name.
        robot = SimpleNamespace(get_obs=lambda: (
            {"fetch:eyes_Camera_sensor": {"seg_instance": [0, 71]}},
            {"fetch:eyes_Camera_sensor": {"seg_instance": {0: "background", 71: "stick"}}},
        ))
        env = SimpleNamespace(task=SimpleNamespace(object_scope={
            "target": SimpleNamespace(wrapped_obj=SimpleNamespace(name="stick"))}))
        function = load_definition("vlm-tamp/eval.py", "inview", {
            "robot": robot, "env": env, "np": SimpleNamespace(unique=lambda a: set(a))})
        self.assertTrue(function("target"))
        env.task.object_scope["target"].wrapped_obj.name = "other-stick"
        self.assertFalse(function("target"))


if __name__ == "__main__":
    unittest.main()
