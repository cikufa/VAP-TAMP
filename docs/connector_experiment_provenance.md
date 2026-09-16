# Connector experiment provenance

Baseline frozen by explicit user instruction at `c315720` on branch
`vaptamp-handoff-experiment`. The working tree was clean before creating
`vaptamp-connector-handoff`. Existing history is preserved; no remote push.
The interrupted Gemini episode is an acknowledged baseline limitation, not a
block on this task's implementation. No baseline rerun/reinstallation is planned.

This task implements geometry, primitives, task predicates/PDDL, interface
bindings, diagnostics and mock API-boundary tests. It must not modify baseline
AP decisions, voting, sufficiency thresholds, planner costs, state correction,
verification ordering or recovery policy. The baseline source hashes will be
checked at freeze. Task vocabulary extensions are kept in new task files.

Physics and observability validation may tune task geometry before freeze.
No live model results may guide that tuning. Mock outputs validate plumbing only;
all mock artifacts are labelled NON-SCIENTIFIC MOCK VLM RUN.

Inherited caveats: OG/Kit compatibility corrections; alternative released scene;
Gemini 3.5 Flash-Lite provider/model substitution; reconstructed Algorithm 2
adapter and its documented embodiment assumptions. This is not exact artifact-level
reproduction of the original paper. The new connector scene is a custom benchmark.

## Task integration boundaries

`frozen_pipeline.py` loads the actual baseline eval AST and substitutes only the
primitive dispatcher and plotting callback. Its verification helpers and inner
plan/execute/check/correct/replan loop come from unchanged baseline source.
`task_binding.py` loads a private instance of the unchanged paper adapter and binds
only connector predicate paraphrases. It keeps K=2, five questions, four consistent
votes, the existing sufficiency/direction prompts, and 0.25 m view moves.
The separate heuristic exploration module remains disabled as in the accepted
paper-adapter baseline. The `paper_verifier` pathway is enabled.

`holding`, `handempty`, `held_left_configuration`, `held_right_configuration` and
`available` are task-local proprioceptive/fixture bookkeeping predicates, evaluated
like baseline imperceivable predicates. Socket clearance is always visual online.
The fixture condition is never an online symbolic fact or scene-graph object.
Physics collision queries naturally see scene geometry; that is not oracle
selection of a grasp. No pre-emptive inspection, successor ranking, or recovery
selector was added. A normal PDDL `return_connector` action permits the unchanged
planner to select release/regrasp when its corrected state requires it.

The new physical skills use native Fetch IK, collision queries and a physical
fixed-joint attachment abstraction. They do not inherit the released task skills'
synthetic failure injection. This is a declared new-task primitive assumption,
not a change to VAP-TAMP decision-making. The connector feed nest constrains the
initial workpiece until acquired; both grasps retain its keyed insertion orientation.
The task terminal condition is an inserted connector still held by the robot.

The accepted Algorithm 2 adapter iterates inclusively over k=0..K. With K=2 it
can request three moves and acquire a final, unvoted image on budget exhaustion.
This literal baseline behavior is preserved. Evaluation distinguishes acquiring
that useful image from actually querying it. The connector observability check
also found useful geometry within the first two moves, without relying on the
final unvoted observation.
