# Optional paper Algorithm 2 simulation adapter

This is a separate adaptation of the general paper mechanism. It is **not**
the paper's fixed-view simulation experiment, and it is not enabled in the
five recorded fixed-view trials. Source: [paper Algorithms 1–2 and Appendix I](https://arxiv.org/html/2604.26988v1).

## Implemented boundary

- Five appendix paraphrases of the current predicate, sent separately with
  identical captured pixels; majority vote, agreement gate, sufficiency query,
  and a VLM-selected direction. The implemented task vocabulary is inview,
  ontop and onfloor. Unsupported predicates fail explicitly.
- Same modular Gemini/OpenAI transport, 256x256 image preparation and 50-token
  response bound. Appendix instructions replace the release's batched skip
  prompt only on this optional path. No model swap accompanies this test.
- Actual Fetch base/torso/head motion, collision checks, new rendered RGB-D,
  and instance-labelled object memory refresh from observed surface points.
- The released state correction and PDDL writer consume the resulting predicate
  values. Existing ground-truth handling for handempty/inhand/etc. is retained.
  The fixed-view effect/successor-precondition order is not rewritten.

## Explicit embodiment and reconstruction assumptions

These are not numerical settings identified in the paper:

1. High agreement means at least 4/5; K=2 in the component check. The existing
   Algorithm 2 component preserves the printed inclusive loop, potentially
   making K+1 moves and returning the last vote even after a final unvoted view.
2. A direction becomes a 0.25 m target-relative displacement. Front and closer
   move toward the current target; behind moves away; left/right move laterally.
   Above raises the torso subject to its joint limit. The head points toward
   that same target using the already validated Fetch kinematics.
3. Check five intermediate path samples; reject a colliding requested direction.
   No candidate search, alternative direction policy, information-gain score,
   successor objective or handoff-specific logic is added. Rejected motion
   consumes the printed algorithm's iteration budget and is logged explicitly.
4. Base displacement retains the release's kinematic simulation style; it is
   not a physical mobile-base trajectory controller. Held objects follow the
   base as in the released magic-grasp primitive.
5. Cached task poses initialize object memory. New anchors are medians of
   actual depth pixels bearing that object's instance label, projected using
   camera pose and focal length/aperture. Raw RGB, depth, labels and calibration
   are retained. This is a small task-object memory, not the paper's complete
   voxel-map construction pipeline. OG instance labels remain privileged
   perception inputs, consistent with the existing simulation boundary.
6. Positive predicate paraphrases also handle a negated expected fact; the
   existing mismatch updater handles its sign. onfloor maps to the appendix's
   on(object, floor) template. Object names follow the release's category-level
   wording; no instance labels are drawn onto the image.
7. Nonbinary/unknown output raises an error. The sufficiency template ends in
   `Answer:`; an observed provider reply was `Answer: no`. Accept that optional
   field label only when followed by exactly yes or no. Preserve the raw reply;
   explanations, alternatives, skip, and uncertainty remain errors.
8. A second live response was a truncated explanation rather than a binary
   answer. The optional Gemini path now requests `text/x.enum` with the paper's
   allowed answer vocabulary via `responseSchema`. This is documented in
   [Google's GenerationConfig reference](https://ai.google.dev/api/generate-content).
   It constrains output format without changing question text, image bytes or
   token bound, but remains a provider adaptation that can affect generation.
   The released fixed-view path does not set this constraint. OpenAI remains
   restorable for the released path; this experimental enum control is Gemini-specific.

## Component validation plan and evidence

Replay an actual failed bottle-visibility check from seed 4, including native
robot/bottle poses and head joints. This is a diagnostic replay of a natural
failure, not a newly designed failure injection or a counted task trial.

Then exercise current grasp precondition verification, object-memory refresh,
symbolic state correction, a planner call, and one continuation primitive.
The 400-second process bound includes native startup and API rate-limit waits.
Raw source snapshots are saved with the probe because the adapter is under
development. No simultaneous simulator processes are used.

- First probe: `results/original/startup/20260916T005730435593Z`.
  Five actual paraphrase queries completed. The sufficiency reply `Answer: no`
  was rejected by the original strict parser. Clean exit/cleanup; failed probe
  retained, no AP success claim.
- Second probe changed only acceptance of the exact binary `Answer:` field
  prefix. Its source snapshots and logs are in
  `results/original/startup/20260916T005905078593Z`.
  It failed on a long explanation; no truth value was inferred from that text.
- A standalone image request with the enum constraint passed using the same
  failed sufficiency request: `results/original/model_access/20260916T010231213543Z`.
- 27 local tests pass, including camera projection, invalid-depth rejection,
  identical image bytes across five requests and strict response handling.

Live moving-view results and full-episode acceptance remain to be assessed.
