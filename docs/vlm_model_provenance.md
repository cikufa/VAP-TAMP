# VLM model provenance and access gate

The exact released simulation request identifier is `gpt-4-turbo`, sent to
OpenAI Chat Completions by `vlm-tamp/gpt4v.py`. The paper's real-robot setup
names Gemini Vision, without making it the model for this released simulation.
No replacement is selected or permitted automatically.

Official OpenAI documentation checked 2026-09-15 lists `gpt-4-turbo` and its
`gpt-4-turbo-2024-04-09` snapshot, with image input. The deprecations page
lists shutdown on **October 23, 2026**. Thus deprecation alone does not prove
it unavailable on this audit date. Account access and actual image requests
still require authenticated tests. The alias remains unchanged; record the
returned model identifier in each raw response when trials run.

`OPENAI_API_KEY` is currently absent from the inherited environment and local
ignored `.env`. `scripts/check_released_model.py` reads only those sources,
checks the exact model without fallback, and stores HTTP status/model ID or
error code, never credentials or error-message text. A successful model GET is
not proof of image-query execution or predicate accuracy.

If access fails, distinguish authentication, billing/rate limiting, and missing
model errors. Do not silently migrate. Re-check current replacements and obtain
explicit model-substitution approval before scientific trials. The official
shutdown notice currently recommends `gpt-5.6-sol`; this is not an approved
scientific substitute and has not been installed, selected, or queried.

Sources, fetched through the OpenAI Docs skill:
[model documentation](https://developers.openai.com/api/docs/models/gpt-4-turbo),
[deprecation schedule](https://developers.openai.com/api/docs/deprecations).
