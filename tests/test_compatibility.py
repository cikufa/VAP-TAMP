"""Narrow checks for API and observation compatibility, without launching OG.

The upstream eval module runs experiments at import time. Compile only the
actual functions under test from its AST rather than importing that entrypoint.
These checks make no claim about physics or VLM accuracy.
"""
import ast
import base64
from pathlib import Path
from types import SimpleNamespace
import unittest
import sys
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vlm-tamp'))
from vlm_backends import BackendRequestError, GeminiBackend, OpenAIBackend


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
        backend = OpenAIBackend(api_key="test-placeholder", model="test-model")
        payload = {"model": "test-model", "messages": [], "max_tokens": 2}
        with patch('vlm_backends.requests.post', return_value=response):
            return backend.request(payload, 1)

    def test_http_error_cannot_become_affirmative_evidence(self):
        with self.assertRaisesRegex(BackendRequestError, "HTTP 429"):
            self.request(SimpleNamespace(ok=False, text="rate limit", status_code=429,
                                         json=lambda: {"error":{"code":"rate_limit"}}))

    def test_empty_response_cannot_become_affirmative_evidence(self):
        with self.assertRaisesRegex(BackendRequestError, "HTTP 200"):
            self.request(SimpleNamespace(ok=True, text="", status_code=200,
                                         json=lambda: {}))

    def test_error_body_cannot_echo_credential_into_trace(self):
        with patch('repro_trace.record') as record:
            with self.assertRaises(RuntimeError):
                self.request(SimpleNamespace(ok=False,text='Invalid key test-placeholder',status_code=401,
                                             json=lambda: {"error":{"code":"invalid_key"}}))
        self.assertNotIn('test-placeholder',record.call_args_list[-1].kwargs['body'])

    def test_successful_answers_are_preserved(self):
        response = SimpleNamespace(ok=True, text="response", status_code=200,
                                   json=lambda: {"choices": [{"message": {"content": "yes;no;skip"}}]})
        self.assertEqual(self.request(response), "yes;no;skip")

    def test_gemini_adapter_preserves_prompt_image_and_token_limit(self):
        encoded = base64.b64encode(b'png').decode('ascii')
        source = {"model":"ignored", "messages":[
            {"role":"system", "content":"system prompt"},
            {"role":"user", "content":[
                {"type":"text", "text":"q1;q2"},
                {"type":"image_url", "image_url":{"url":"data:image/png;base64,"+encoded}},
            ]}], "max_tokens":50}
        payload = GeminiBackend._convert(source)
        self.assertEqual(payload["systemInstruction"]["parts"][0]["text"], "system prompt")
        self.assertEqual(payload["contents"][0]["parts"][0]["text"], "q1;q2")
        self.assertEqual(payload["contents"][0]["parts"][1]["inlineData"]["data"], encoded)
        self.assertEqual(payload["generationConfig"]["maxOutputTokens"], 50)
        self.assertEqual(payload["generationConfig"]["thinkingConfig"]["thinkingLevel"], "minimal")

    def test_gemini_response_text_is_preserved(self):
        backend = GeminiBackend(api_key="test-placeholder", model="gemini-test")
        response = SimpleNamespace(ok=True, text="response", status_code=200,
            json=lambda:{"candidates":[{"content":{"parts":[{"text":"yes;no;skip"}]}}]})
        source = {"model":"ignored", "messages":[
            {"role":"system", "content":"prompt"},
            {"role":"user", "content":[{"type":"text", "text":"question"}]}],
            "max_tokens":50}
        with patch('vlm_backends.requests.post', return_value=response):
            self.assertEqual(backend.request(source, 1), "yes;no;skip")

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
            "robot": robot, "env": env, "np": SimpleNamespace(unique=lambda a: set(a)),
            '_fpv_camera_key': load_definition('vlm-tamp/eval.py','_fpv_camera_key',{})})
        self.assertTrue(function("target"))
        env.task.object_scope["target"].wrapped_obj.name = "other-stick"
        self.assertFalse(function("target"))

    def test_cached_robot_camera_uses_registry_name(self):
        choose=load_definition('vlm-tamp/eval.py','_fpv_camera_key',{})
        self.assertEqual(choose({'robot0:eyes:Camera:0':{}}),'robot0:eyes:Camera:0')
        with self.assertRaises(RuntimeError):
            choose({'robot0:eyes:Camera:0':{},'robot0:wrist:Camera:0':{}})


if __name__ == "__main__":
    unittest.main()
