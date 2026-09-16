# Shallow terrain contact in optional AP motion

The full AP attempt `20260916T011746398025Z`, event 496, rejected a requested
closer view for bottle 1. Unlike the earlier robot-copy self-collision, this
overlap involved the base and wheels against `/World/lawn_qaedpx_0/base_link`.
The same overlap existed at the unchanged standing pose.

OG's `PlanningContext._construct_disabled_collision_pairs` ignores objects in
category `floors`, but the outdoor support asset is fixed category `lawn`.
We did not globally disable lawn collisions.

## Isolated evidence

`results/original/startup/20260916T013144167274Z` replayed the exact prior robot
and bottle poses without model calls. At standing, 20% and 100% of the requested
path, the unshifted copy overlapped only lawn. Raising the planning copy by
0.01 m cleared all three queries. Additional 0.02/0.05/0.10 m diagnostic offsets
also cleared; the actual robot was not lifted or moved in this audit.
Duration 38.377 seconds; clean exit, zero monitored external file changes.

## Narrow repair and its limits

Only the optional paper adapter now tolerates a collision when:

1. All standing contacts are base/wheel contacts with fixed lawn.
2. Candidate contact pairs are a subset of those same standing contacts.
3. Neither contact list is truncated.
4. A full collision query at the candidate pose with the copy raised by 0.01 m
   is clear. All environment filters remain otherwise active.

The actual motion command keeps its original height. Furniture, new contact
pairs, arm contacts, deeper terrain overlap and truncated queries remain
rejected. This is a 1 cm execution tolerance inferred from the native failure,
**not a parameter specified by the paper**. It does not prove general terrain
traversability or continuous swept-volume safety; the adapter still checks five
discrete base-path samples and uses released kinematic execution semantics.
No modification was made to the default fixed-view navigation sampler for this
repair.

`results/original/startup/20260916T013442406210Z` replayed the same failure with
the new rule disabled and enabled: disabled rejected; enabled moved from
`[-9.16823, -9.40541, -0.02222]` to `[-8.91813, -9.40980, -0.02267]` and rendered
a distinct image, followed by RGB-D object-memory refresh. Zero API requests,
40.405 seconds, clean exit, zero monitored external file changes. Source copies
and phase logs are retained in each probe directory.

A focused unit test verifies rejection of new obstacles, arm contacts, missing
standing support, and truncated contact lists. Existing native overlap checks
enforce the 1 cm depth bound. The full episode has not been rerun after this
repair because daily Gemini quota is exhausted. Its earlier outcome must not
be attributed to the repaired revision.
