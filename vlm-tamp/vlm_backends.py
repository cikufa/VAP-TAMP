"""Provider adapters for the VAP-TAMP chat-and-image request contract."""
import base64
import json
import os
import re
import time
from types import SimpleNamespace
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_PROVIDER = "gemini"
DEFAULT_GEMINI_MODEL = "gemini-3.5-flash-lite"
DEFAULT_OPENAI_MODEL = "gpt-4o-2024-05-13"


def _post_json(url, headers, payload, timeout=30):
    """POST JSON without importing either Conda's or Kit's requests stack."""
    request = Request(url, data=json.dumps(payload).encode("utf-8"),
                      headers=headers, method="POST")
    try:
        with urlopen(request, timeout=timeout) as response:
            text = response.read().decode("utf-8")
            status = response.status
    except HTTPError as error:
        text = error.read().decode("utf-8", errors="replace")
        status = error.code
    return SimpleNamespace(status_code=status, text=text, ok=200 <= status < 300,
                           json=lambda: json.loads(text) if text else {})


class BackendRequestError(RuntimeError):
    def __init__(self, provider, status_code, error_code=None):
        self.provider = provider
        self.status_code = status_code
        self.error_code = error_code
        suffix = f", {error_code}" if error_code else ""
        super().__init__(f"{provider} VLM request failed (HTTP {status_code}{suffix})")


def _error_code(response):
    try:
        error = response.json().get("error", {})
        return error.get("status") or error.get("code")
    except (AttributeError, ValueError):
        return None


def _retry_delay(response):
    try:
        details = response.json().get("error", {}).get("details", [])
        for detail in details:
            if detail.get("@type", "").endswith("RetryInfo"):
                value = detail.get("retryDelay", "")
                match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)s", value)
                if match:
                    return min(float(match.group(1)) + 1.0, 60.0)
    except (AttributeError, ValueError):
        pass
    return 10.0


class OpenAIBackend:
    provider = "openai"

    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model or os.getenv("VAPTAMP_OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is required for the OpenAI VLM backend")

    def request(self, chat_input, round_number):
        from repro_trace import record
        payload = dict(chat_input, model=self.model)
        record("vlm_request", round=round_number, provider=self.provider,
               model=self.model, payload=payload)
        response = _post_json(
            "https://api.openai.com/v1/chat/completions",
            {"Content-Type": "application/json",
             "Authorization": f"Bearer {self.api_key}"},
            payload,
        )
        record("vlm_response", round=round_number, provider=self.provider,
               model=self.model, http_status=response.status_code,
               body=response.text.replace(self.api_key, "[REDACTED_API_KEY]"))
        if not response.ok or not response.text:
            raise BackendRequestError(self.provider, response.status_code,
                                      _error_code(response))
        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            raise BackendRequestError(self.provider, response.status_code,
                                      _error_code(response) or "empty_choices")
        return choices[0]["message"]["content"]


class GeminiBackend:
    provider = "gemini"

    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
        self.model = model or os.getenv("VAPTAMP_GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is required for the Gemini VLM backend")
        if not re.fullmatch(r"[A-Za-z0-9._-]+", self.model):
            raise ValueError("Invalid Gemini model identifier")

    @staticmethod
    def _convert(chat_input):
        system_parts = []
        user_parts = []
        for message in chat_input["messages"]:
            content = message["content"]
            if message["role"] == "system":
                system_parts.append({"text": content})
                continue
            if isinstance(content, str):
                content = [{"type": "text", "text": content}]
            for part in content:
                if part["type"] == "text":
                    user_parts.append({"text": part["text"]})
                elif part["type"] == "image_url":
                    url = part["image_url"]["url"]
                    prefix = "data:image/png;base64,"
                    if not url.startswith(prefix):
                        raise ValueError("Gemini adapter requires an inline PNG image")
                    encoded = url[len(prefix):]
                    base64.b64decode(encoded, validate=True)
                    user_parts.append({"inlineData": {"mimeType": "image/png", "data": encoded}})
                else:
                    raise ValueError(f"Unsupported chat content type: {part['type']}")
        payload = {
            "contents": [{"role": "user", "parts": user_parts}],
            "generationConfig": {
                "maxOutputTokens": chat_input["max_tokens"],
                # Gemini 3.6 otherwise spends the released short answer budget
                # on hidden reasoning. Minimal most closely matches the
                # non-reasoning Chat Completions contract used by VAP-TAMP.
                "thinkingConfig": {"thinkingLevel": "minimal"},
            },
        }
        if system_parts:
            payload["systemInstruction"] = {"parts": system_parts}
        return payload

    def request(self, chat_input, round_number):
        from repro_trace import record
        payload = self._convert(chat_input)
        record("vlm_request", round=round_number, provider=self.provider,
               model=self.model, source_contract=chat_input, payload=payload)
        response = None
        for attempt in range(3):
            try:
                response = _post_json(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent",
                    {"Content-Type": "application/json", "x-goog-api-key": self.api_key},
                    payload,
                )
            except (TimeoutError, URLError, OSError):
                record("vlm_transport_error", round=round_number,
                       provider=self.provider, model=self.model, attempt=attempt + 1)
                if attempt < 2:
                    time.sleep(2.0)
                    continue
                raise BackendRequestError(self.provider, 0, "transport_error") from None
            record("vlm_response", round=round_number, provider=self.provider,
                   model=self.model, attempt=attempt + 1,
                   http_status=response.status_code,
                   body=response.text.replace(self.api_key, "[REDACTED_API_KEY]"))
            if response.status_code != 429 or _error_code(response) != "RESOURCE_EXHAUSTED":
                break
            if attempt < 2:
                delay = _retry_delay(response)
                record("vlm_rate_limit_retry", round=round_number,
                       provider=self.provider, model=self.model, delay_seconds=delay)
                time.sleep(delay)
        if response is None:
            raise BackendRequestError(self.provider, 0, "transport_error")
        if not response.ok or not response.text:
            raise BackendRequestError(self.provider, response.status_code,
                                      _error_code(response))
        data = response.json()
        candidates = data.get("candidates", [])
        if not candidates:
            block = data.get("promptFeedback", {}).get("blockReason", "empty_candidates")
            raise BackendRequestError(self.provider, response.status_code, block)
        parts = candidates[0].get("content", {}).get("parts", [])
        answer = "".join(part.get("text", "") for part in parts).strip()
        if not answer:
            raise BackendRequestError(self.provider, response.status_code, "empty_text")
        return answer


def build_backend(provider=None):
    selected = (provider or os.getenv("VAPTAMP_VLM_PROVIDER", DEFAULT_PROVIDER)).lower()
    if selected == "gemini":
        return GeminiBackend()
    if selected == "openai":
        return OpenAIBackend()
    raise ValueError(f"Unsupported VAPTAMP_VLM_PROVIDER: {selected}")
