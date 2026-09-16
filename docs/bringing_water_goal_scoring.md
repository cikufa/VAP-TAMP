# Bringing-water: three distinct success criteria

The released score is retained unchanged in `exp_results.json`. It is not a
reliable geometric goal test for this cached scene and these object models.

| Criterion | What it checks | Role |
| --- | --- | --- |
| Released Python score | Both object origins have 0 < z < 0.1 m and both names occur in `onfloor_relationships` | Historical output, preserved |
| Physical realization of released PDDL | Each bottle satisfies native `OnTop` with `floor.n.01_1` | Additional diagnostic, not fed to planning |
| Native BEHAVIOR goal | Both bottles are inside the kitchen cabinet | A different BDDL goal; not substituted for the released floor goal |

`OnTop` in pinned OG 1.0 checks contact and vertical adjacency. It is stronger
than using height or the bookkeeping list alone. Final diagnostics are captured
after the released 200 settling steps and retain positions, orientations, AABBs,
room identities, model identifiers, and native predicates.

## Observed counterexamples

Seed 1 (`results/original/debug_episode/20260916T002557882885Z`) demonstrates
both problems with the released height proxy:

- Bottle 1 lies in garden_0 at origin z=0.02134 m. Its height and bookkeeping
  checks pass, but `OnTop(target kitchen floor)` is false.
- Bottle 2 is upright on the target kitchen floor at origin z=0.13696 m.
  Native `OnTop` is true, but the height check fails.

Seed 3 (`results/original/debug_episode/20260916T004018842917Z`) is a completed
episode with both bottles physically on the target kitchen floor. Both native
`OnTop` predicates are true; the origins are 0.14010 and 0.13696 m. Both fail
the released height check. The trial reached the released action limit (51
executions), so this is physical goal achievement at the bound, not evidence
that final visual verification declared the task complete.

Do not tip bottles, lower their origins, change assets or relax a threshold to
make the historical score pass. Report both scores. Do not retroactively score
seed 0 as a physical success: its saved last-action positions support a similar
hypothesis, but it lacks a final settled native predicate report.

The native BDDL cabinet goal remains false in these runs, as expected for the
different floor-goal plan. This difference also prevents interpreting these
outputs as unmodified BEHAVIOR benchmark results.
