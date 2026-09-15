# VLM model provenance and access gate

Current active backend: Gemini 3.6 Flash free tier. See
`gemini_backend_substitution.md`. The OpenAI history below is retained to show
why the provider substitution was required and how OpenAI can be restored.

The exact released simulation request identifier is `gpt-4-turbo`, sent to
OpenAI Chat Completions by `vlm-tamp/gpt4v.py`. The paper's real-robot setup
names Gemini Vision, without making it the model for this released simulation.
The user approved substituting an accessible model on 2026-09-15. The selected
replacement is the pinned `gpt-4o-2024-05-13` snapshot.

Official OpenAI documentation checked 2026-09-15 lists `gpt-4-turbo` and its
`gpt-4-turbo-2024-04-09` snapshot, with image input. The deprecations page
lists shutdown on **October 23, 2026**. Thus deprecation alone does not prove
it unavailable on this audit date. Account access and actual image requests
still require authenticated tests. The alias remains unchanged; record the
returned model identifier in each raw response when trials run.

`OPENAI_API_KEY` is now configured and authentication is verified as of
2026-09-15 21:43 UTC. `scripts/check_released_model.py` reads only the inherited
environment and local ignored `.env`,
checks the exact model without fallback, and stores HTTP status/model ID or
error code, never credentials or error-message text. A successful model GET is
not proof of image-query execution or predicate accuracy.

### Authenticated check after credential setup

- `GET /v1/models`: HTTP **200**; authentication works.
- Neither `gpt-4-turbo` nor `gpt-4-turbo-2024-04-09` appears in that account's
  returned model list.
- `GET /v1/models/gpt-4-turbo`: HTTP **404**, `model_not_found`.
- A minimal `POST /v1/chat/completions` with the exact released identifier:
  HTTP **404**, `model_not_found`; no completion returned.
- Sanitized evidence:
  `results/original/model_access/20260915T214338284812Z/endpoint_diagnosis.json`.

This established an exact-model availability/access blocker with the configured
credential, not a missing key or simulator failure. It does not establish global
model unavailability. No replacement model was queried and no simulator episode
was started during this check. Continuing requires a credential/project with
access to the released model or a documented model deviation. The latter was
subsequently approved.

### Approved replacement

`gpt-4o-2024-05-13` is selected because it is the earliest dated GPT-4o
snapshot available to this account. Pinning the snapshot avoids alias drift.
Official OpenAI documentation confirms GPT-4o accepts text and image inputs and
supports Chat Completions, so the repository's 256x256 image request structure
does not require an endpoint or schema change. The documentation marks this
snapshot deprecated; that lifecycle risk is retained in the audit.

This is a scientific fidelity deviation from the released `gpt-4-turbo`, not a
claim of model equivalence. `VAPTAMP_OPENAI_MODEL` may explicitly select a
different model for a separately labeled experiment; the default remains the
pinned approved snapshot. `scripts/check_released_model.py` now verifies both
model lookup and a real image-input completion without writing the image or API
response text to its sanitized result.

Authenticated replacement check at 2026-09-15 23:14 UTC:

- Model lookup: HTTP **200**, returned `gpt-4o-2024-05-13`.
- Real image-input Chat Completions request: HTTP **429**,
  `credit_balance_exhausted`; no model answer was returned.
- Sanitized evidence:
  `results/original/model_access/20260915T231432952819Z/result.json`.

The model substitution and request schema are therefore resolved, while API
billing currently blocks VLM execution. Retrying other models cannot resolve an
account credit-balance error, so no simulator episode was started after this
result.

If access fails, distinguish authentication, billing/rate limiting, and missing
model errors. Do not silently migrate. Re-check current replacements and obtain
explicit model-substitution approval before scientific trials. The official
shutdown notice currently recommends `gpt-5.6-sol`; this is not an approved
scientific substitute and has not been installed, selected, or queried.

Sources, fetched through the OpenAI Docs skill:
[released model documentation](https://developers.openai.com/api/docs/models/gpt-4-turbo),
[replacement model documentation](https://developers.openai.com/api/docs/models/gpt-4o),
[deprecation schedule](https://developers.openai.com/api/docs/deprecations).
