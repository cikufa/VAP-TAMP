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
