# Gemini free-tier VLM backend substitution

Updated: 2026-09-16.

Five fixed-view trial results: `bringing_water_pilot_results.md`. The separate
optional paper adapter changes query formatting and uses enum output constraints;
see `paper_sim_adapter.md`. The preserved contract below describes the default
released simulation path.

The active VAP-TAMP simulation backend is Google Gemini Developer API with
`gemini-3.5-flash-lite`. This is a provider and model substitution, not an exact
reproduction of the released OpenAI `gpt-4-turbo` configuration.

The later moving-view attempt exhausted the observed 500-request daily project/model
quota after 111 successful requests in that episode. It is preserved as incomplete;
see `paper_adapter_episode_results.md`. Structured daily-quota errors now stop
immediately even if the service supplies a short RetryInfo hint. Per-minute
throttling retains the existing two bounded retries; no key/model rotation or
billing change was made.

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

During the earlier Gemini 3.6 Flash validation, an eight-token output budget
returned HTTP 200 without visible text. The adapter sets
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

No simulator was started during the isolated validation. Eighteen local tests cover API
failure handling, secret redaction, request conversion, response preservation,
camera compatibility, and previously validated runtime compatibility.

## Bounded end-to-end result

Seed 0 of `bringing_water` completed from scene startup through clean shutdown
in 268.5 seconds:

- 37 executed actions and 24 planning events;
- 41 Gemini image requests and 42 HTTP responses (one bounded 429 retry);
- 61 verification events, including 23 with unmatched effects or preconditions;
- state correction and replanning after real visual discrepancies and a released
  injected grasp failure;
- 59-frame first-person and third-person videos;
- released task result: 0 success, 1 failed.

Evidence:
`results/original/debug_episode/20260915T234514360281Z/run_metadata.json` and
the sibling `trace/events.jsonl`. The pipeline completion passes the execution
gate; the task failure is retained and does not support a success-rate claim.

Kit's bundled Python packages conflicted with Conda `requests/urllib3`, so the
provider adapters use Python's standard HTTPS client. This changes transport
implementation only; request payloads and response parsing are unchanged.

Sources:

- [Gemini 3.5 Flash-Lite model](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite)
- [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [Gemini image understanding](https://ai.google.dev/gemini-api/docs/image-understanding)
- [Gemini thinking controls](https://ai.google.dev/gemini-api/docs/generate-content/thinking)
