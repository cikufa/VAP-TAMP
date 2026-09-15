"""Run one sanitized text-and-image request through the selected VLM backend."""
from datetime import datetime, timezone
import base64
import json
import os
from pathlib import Path
import sys

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vlm-tamp"))

from vlm_backends import BackendRequestError, build_backend  # noqa: E402


def main():
    load_dotenv(ROOT / ".env", override=False)
    out = (ROOT / "results/original/model_access" /
           datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    out.mkdir(parents=True, exist_ok=False)
    os.environ["VAPTAMP_TRACE_DIR"] = str(out / "trace")
    result = {"checked_utc": datetime.now(timezone.utc).isoformat(),
              "scope": "one text-and-inline-PNG request; simulator not started"}
    try:
        backend = build_backend()
        result.update(provider=backend.provider, requested_model=backend.model)
        png = base64.b64encode(base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwC"
            "AAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )).decode("ascii")
        chat_input = {
            "model": backend.model,
            "messages": [
                {"role": "system", "content": "Follow the user's output format exactly."},
                {"role": "user", "content": [
                    {"type": "text", "text": "Reply with exactly: image-ok"},
                    {"type": "image_url", "image_url": {
                        "url": "data:image/png;base64," + png}},
                ]},
            ],
            "max_tokens": 8,
        }
        answer = backend.request(chat_input, 0)
        result.update(status="pass", response_present=bool(answer),
                      exact_response=answer.strip().lower() == "image-ok")
    except BackendRequestError as error:
        result.update(status="fail", provider=error.provider,
                      http_status=error.status_code, error_code=error.error_code)
    except (RuntimeError, ValueError) as error:
        result.update(status="fail", configuration_error=str(error))
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))
    print("Evidence:", out)
    if result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
