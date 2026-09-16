# Bringing-water pilot results

Five new trials completed on 2026-09-16 UTC. No trial was discarded. An initial
two-trial series exposed a stale room-label bug; after an isolated native
regression check, a separately declared three-trial series tested its correction.
Do not pool the two conditions or interpret this small pilot as a benchmark rate.

Provider/model: Gemini `gemini-3.5-flash-lite`, default unconstrained released
verification prompts/parsing, precondition and effect checks enabled, classical
PDDL planner, fixed-view simulation, released stochastic action probabilities.
Scene: cached Wainscott_0_garden. This is a provider/model and scene substitution.

| Condition | Seed | Actions | Planner calls | VLM image requests | Discrepancy events | Seconds | Released score | Physical PDDL goal | Frames per video |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: |
| Before room correction | 1 | 51 | 33 | 54 | 32 | 332.9 | FAIL | FAIL | 88 |
| Before room correction | 2 | 51 | 48 | 50 | 47 | 307.5 | FAIL | FAIL | 60 |
| Current-room navigation | 3 | 51 | 39 | 54 | 38 | 337.5 | FAIL | PASS | 86 |
| Current-room navigation | 4 | 32 | 26 | 34 | 25 | 228.8 | FAIL | PASS | 58 |
| Current-room navigation | 5 | 51 | 43 | 71 | 42 | 363.5 | FAIL | FAIL | 58 |

The released bound checks `action_counter > 50`, permitting 51 executions.
Seed 3 reached the physical goal at that bound. Seed 4 completed its plan with
no final verification mismatch. Seed 5 left bottle 1 in the garden; its final
failure is real, not solely a score problem. No claim of improved success rate
is supported by these few runs and changed seeds.

## What was fixed and demonstrated

- The first series completed without crashes, but seed 2 exhausted 43 navigation
  searches after a bottle's current room differed from its cached room label.
- The isolated replay rejected 1,000 poses with the old label rule and accepted
  its first candidate with current-room lookup. See `moved_object_navigation_fix.md`.
- In the corrected series, live execution navigated back to moved bottles using
  kitchen_0, detected discrepancies, updated PDDL and continued after replanning.
- Both bottles physically satisfy native `OnTop(target kitchen floor)` in seeds
  3 and 4. The released height proxy rejects upright bottle origins above 10 cm;
  it also can accept a fallen bottle in the wrong room. See `bringing_water_goal_scoring.md`.
- All five processes exited 0, each recorded `trial_end`, and all first-/third-
  person videos decoded with the expected frame count. No remaining child
  process was reported. There were no malformed or skipped verification batches.
- Three transient 429 replies across the five runs were retried successfully:
  one in seed 1 and two in seed 5. Observed quota: 15 requests/minute/model/project.

## Artifacts and code provenance

Machine-readable aggregation:
`results/original/pilot/20260916_bringing_water/summary.json`.
Each episode contains run metadata, terminal/Kit logs, raw provider requests and
responses with embedded image inputs, action/state/verification events, final
settled predicates and two MP4 observation-sequence videos. Playback rate is
12 fps; it does not represent wall-clock or simulator time.

| Seed | Episode under `results/original/debug_episode/` | Launch commit |
| --- | --- | --- |
| 1 | `20260916T002557882885Z` | `1ea9f11` |
| 2 | `20260916T003151131775Z` | `472d9dc` |
| 3 | `20260916T004018842917Z` | `cf3f0cf` |
| 4 | `20260916T004611194536Z` | `cf3f0cf` |
| 5 | `20260916T005016382415Z` | `9f2a673` |

All launched with clean worktrees. The code change between seeds 1 and 2 adds
only the offline analyzer; between seeds 4 and 5 it adds only scoring documentation.
The evaluated execution code is identical within each condition. The predeclared
plan and amendment are in `bringing_water_pilot_plan.md`.

Earlier completed seed 0 (`20260915T234514360281Z`, 37 actions, released failure)
remains a debugging run and is excluded from both series. It lacks a final native
goal report, so no retrospective physical success is assigned.

## Remaining method-level work

The fixed-view released pipeline is now exercised through full trials, including
physical task achievement. This does not establish exact reproduction of the
paper's model, scene or reported success rate. The general paper's moving-view
mechanism has a separate optional adapter and component tests; see
`paper_sim_adapter.md`. Its acceptance must be assessed separately before the
connector diagnostic. No connector implementation was added.
