# Gemini free-tier VLM backend substitution

Date: 2026-09-15.

The active VAP-TAMP simulation backend is Google Gemini Developer API with
`gemini-3.6-flash`. This is a provider and model substitution, not an exact
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

Gemini 3.6 uses dynamic thinking by default. With the eight-token validation
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
`VAPTAMP_GEMINI_MODEL=gemini-3.6-flash`. Credentials remain outside Git.

## Selection and validation evidence

Official Google documentation lists Gemini 3.6 Flash as accepting text and
image inputs with text output. Its standard API input and output are free of
charge on the free tier as of the audit date. Google API errors reported that
Gemini 2.5 Flash and Flash-Lite are unavailable to new users, so neither is the
active model.

The bounded validation sent one inline PNG through the same adapter used by the
episode:

- provider/model: `gemini` / `gemini-3.6-flash`
- HTTP result: 200
- text response present: yes
- exact requested response `image-ok`: yes
- evidence: `results/original/model_access/20260915T232808888894Z/result.json`

No simulator was started during validation. Seventeen local tests cover API
failure handling, secret redaction, request conversion, response preservation,
camera compatibility, and previously validated runtime compatibility.

Sources:

- [Gemini 3.6 Flash model](https://ai.google.dev/gemini-api/docs/models/gemini-3.6-flash)
- [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [Gemini image understanding](https://ai.google.dev/gemini-api/docs/image-understanding)
- [Gemini thinking controls](https://ai.google.dev/gemini-api/docs/generate-content/thinking)
