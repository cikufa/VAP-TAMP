# Gemini free-tier VLM backend substitution

Date: 2026-09-15.

The active VAP-TAMP simulation backend is Google Gemini Developer API with
`gemini-3.5-flash-lite`. This is a provider and model substitution, not an exact
reproduction of the released OpenAI `gpt-4-turbo` configuration.

## Preserved request contract

- The same `prompts.txt` and `planning_prompts.txt` content is sent as the
  provider system instruction.
- Predicate questions remain one semicolon-delimited text part.
- Camera observations remain 256x256 PNGs embedded inline as base64.
- Verification and planning output limits remain 50 and 1000 tokens.
- Answers retain the released lowercase and semicolon parsing.
- No temperature, top-p, safety override, tool, or grounding option is added.
- PDDL, verification ordering, failure probabilities, simulator settings, and
  task settings are unchanged.

Gemini 3.5 Flash-Lite uses thinking by default. With the eight-token validation
budget, the API returned HTTP 200 but no text. The adapter sets
`thinkingLevel=minimal`, the closest supported setting to the released
non-reasoning short-answer request. This provider-specific setting is part of
the documented deviation.

## Provider isolation and restoration

`vlm-tamp/vlm_backends.py` converts the existing OpenAI-style internal request
contract into either Gemini `generateContent` or OpenAI Chat Completions.
`VAPTAMP_VLM_PROVIDER=gemini` is the reproduction default. OpenAI can be
restored without changing prompts or parsing by setting:

```text
VAPTAMP_VLM_PROVIDER=openai
VAPTAMP_OPENAI_MODEL=<accessible vision model>
OPENAI_API_KEY=<private key>
```

Gemini configuration uses `GEMINI_API_KEY` and
`VAPTAMP_GEMINI_MODEL=gemini-3.5-flash-lite`. Credentials remain outside Git.

## Selection and validation evidence

Official Google documentation lists Gemini 3.5 Flash-Lite as accepting text and
image inputs with text output and as optimized for high-throughput execution.
Google API errors reported that Gemini 2.5 Flash and Flash-Lite are unavailable
to new users. Gemini 3.6 Flash passed image validation and multiple full-pipeline
queries, but its per-model free request quota was exhausted during debugging;
the active model was moved to the separately metered Flash-Lite model.

The bounded validation sent one inline PNG through the same adapter used by the
episode:

- provider/model: `gemini` / `gemini-3.5-flash-lite`
- HTTP result: 200
- text response present: yes
- exact requested response `image-ok`: yes
- evidence: `results/original/model_access/20260915T234455548337Z/result.json`

No simulator was started during validation. Seventeen local tests cover API
failure handling, secret redaction, request conversion, response preservation,
camera compatibility, and previously validated runtime compatibility.

Sources:

- [Gemini 3.5 Flash-Lite model](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite)
- [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [Gemini image understanding](https://ai.google.dev/gemini-api/docs/image-understanding)
- [Gemini thinking controls](https://ai.google.dev/gemini-api/docs/generate-content/thinking)
