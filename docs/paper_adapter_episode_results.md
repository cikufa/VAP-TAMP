# Moving-view bringing_water debug episode

Recorded 2026-09-16 UTC. **The live recovery mechanism worked; the full episode
is incomplete because Gemini's daily free-tier quota was exhausted.** This is
an optional reconstruction of general Algorithm 2, separate from the paper's
fixed-view simulation experiment and the five-trial pilot.

## Attempt and outcome

| Item | Recorded value |
| --- | --- |
| Episode | `results/original/debug_episode/20260916T011746398025Z` |
| Launch commit | `a25bee90a57872e55edda782c624248611493e5e`, clean worktree |
| Task/scene | bringing_water / Wainscott_0_garden |
| Model | Gemini Developer API `gemini-3.5-flash-lite`, free tier |
| Mode | paper-adapter; five paraphrases, K=2, agreement 4/5, 0.25 m requested displacement |
| Bound / actual duration | 1200 seconds / 555.296 seconds |
| Completed actions / planner calls | 8 / 4 |
| Completed verification batches / discrepancies | 11 / 3 |
| Completed five-query voting rounds | 18 |
| Sufficiency queries / direction requests | 15 / 6 |
| Executed / rejected view motions | 5 / 1 |
| Captured RGB-D observations and memory refreshes | 19 |
| Logical VLM requests / HTTP attempts | 112 / 120 |
| HTTP 200 / 429 responses | 111 / 9 |
| Completed trials | **0**; no `trial_end` or final goal diagnostic |
| Cleanup | No remaining child processes |

The last request's structured quota violation is
`GenerateRequestsPerDayPerProjectPerModel-FreeTier`, value `500`.
The limit applies to project/model daily usage, including earlier experiments;
it is not a count of requests in this episode. Six earlier per-minute 429s
recovered. The daily failure was unnecessarily retried twice because Google
also supplied short RetryInfo delays. A subsequent transport-only fix now
stops immediately on structured daily exhaustion, preserves the error event,
and retains bounded retries for per-minute throttling. Its regression test
uses the observed quota structure without consuming more requests.

Kit returned process exit code 0 despite the Python traceback. The launcher
correctly returned failure because no trial completed. Do not infer scientific
success or episode completion from Kit's exit status.

## Direct mechanism evidence

Event numbers refer to the immutable `trace/events.jsonl`:

1. Events 29–39: five negative votes on one image, sufficiency **no**, VLM
   direction **closer**, actual base motion.
2. Events 40–64: new image hash, RGB-D instance-memory refresh, five new votes,
   sufficiency **yes**, returned false predicate. A valid inspection need not
   turn a predicate true.
3. Events 89–94: symbolic state correction, discrepancy record, new Fast
   Downward plan, and continued primitive execution.
4. Events 203–269: negative votes with insufficiency, two requested/executed
   movements (`front`, `closer`), new views, then five positive votes and
   sufficient evidence. All viewpoints are real rendered observations.
5. Events 350–383: a 3/5 split on floor visibility triggers a rightward move;
   the new view yields 5/5 positive votes and sufficiency. The first bottle
   is subsequently placed, and event 438 returns a positive onfloor predicate.

No answers, insufficiency decisions, directions, failures or success labels
were fabricated to force this chain. The original stochastic primitive failure
settings remain active. Model errors and contradictory answers are preserved.
The run stopped during another visibility query after action 8, while working
on the second bottle. It has no final task success score.

The one rejected motion (event 496) involved shallow standing base/wheel contact
with fixed lawn. A later API-free native audit and old/new comparison validated
a narrow support tolerance; see [the separate repair](lawn_support_collision_fix.md).
This later code was not present in the recorded episode, so full current-revision
completion still requires a fresh episode.

## Review artifacts

- `analysis.json`: offline counts, HTTP outcomes and quota details.
- `artifact_integrity.json`: all four videos decode to their recorded frame
  counts; all 18 HTML vote images exist; no remaining child process was recorded.
- `paper_verification_report.html`: all 18 complete voting rounds paired with
  the actual voted image, questions, answers and following decisions.
- `artifacts/1789521468.5512514/0/paper_views/first_person.mp4` and
  `third_person.mp4`: 19 captured views each.
- `artifacts/1789521468.5512514/0/first_person.mp4` and `third_person.mp4`:
  16 ordinary action/verification frames each.
- Raw PNG/NPZ observations, request/response events, PDDL artifacts, terminal
  traceback, Kit log and run metadata are retained.

Videos play observation sequences at 12 fps; they are not wall-clock recordings.
The legacy action figure may show a later view than an earlier AP vote. Use
the HTML report or raw query-to-observation bindings for evidence attribution.

## Next bounded validation

After quota reset, rerun seed 6 from the initial scene with the same model,
parameters and current compatibility fixes. Preserve this incomplete attempt;
do not splice later responses into it or pool it with completed fixed-view trials.
Google documents that daily quotas reset at midnight Pacific time and apply
per project, not per key: [official rate-limit documentation](https://ai.google.dev/gemini-api/docs/rate-limits)
(checked 2026-09-16 UTC). At the observed failure time the next documented reset
was 2026-09-16 07:00 UTC / 03:00 America/New_York. Actual availability must still
be checked; quotas are not guaranteed capacity.

```bash
source scripts/engine_runtime.sh
.runtime/envs/vaptamp-repro/bin/python scripts/run_original_episode.py \
  --task bringing_water --seed 6 --trials 1 \
  --verification-mode paper-adapter --paper-budget-k 2 \
  --paper-consistent-votes 4 --timeout-seconds 1200
```

The environment must already contain the local Gemini key. No billing change,
credential replacement or model rotation is needed for this next validation.
See [adapter fidelity boundaries](paper_sim_adapter.md) and the
[baseline acceptance report](baseline_acceptance_report.md) before interpreting
this as reproduction evidence. The connector experiment remains unstarted.
