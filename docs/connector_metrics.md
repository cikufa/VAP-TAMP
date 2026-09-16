# Frozen connector evaluation definitions

The episode is the unit of analysis. The 20 frozen seeds are balanced across the
two physical conditions. Two separate live debug episodes and every mock episode
are excluded. Seeds initialize Python/NumPy RNG; the geometry is deterministic,
with no injected noise. Repeated engineering trials establish repeatability,
not an estimated generalization rate over unseen assemblies.

## First handoff and recovery

Y1 is the first executed grasp's measured lift/hold success. Operational Y2 is
successful INSERT under that first grasp, before a second grasp. If that handoff
is abandoned without INSERT, Y2=0 and `first_handoff_abandoned=true`;
`first_insert_attempted=false` prevents calling it a physical collision failure.
A failed native INSERT requires both an attempt and a failed result. Final
physical success after recovery is reported separately from first-chain success.

Metrics include P(Y1), P(Y1 and not Y2), P(Y2|Y1), P(Y1 and Y2), final task success,
compatible-grasp rate, empirical binary handoff regret, sensing timing and costs,
replanning, recovery and regrasp rates. Recovery success is conditional on recovery
attempts. Rates use completed non-infrastructure episodes; API interruptions,
missing seeds, incomplete attempts and unclassified cases are reported separately.
A completed task failure is retained, never retried to select a success.

## Temporal attribution

- T_grasp: native `grasp_committed` event, before approach/closure.
- T_successor_query: first actual VLM request containing a socket-side-clearance
  predicate question, not the later aggregate-vote timestamp.
- T_successor_view: acquisition time of the first geometrically useful camera
  observation, after an actual AP move, that is bound to a successor-predicate
  image request. Connector-only checks and movement alone never count.
- T_insert: first native `insert_started` event.

PROSPECTIVE means T_view < T_grasp; REACTIVE means grasp < view < insert (or no
insert attempted yet); VERY_LATE means view follows an insertion attempt; NONE
means no qualifying view. `late_after_failed_insert` additionally requires a
recorded failed insertion result before the view. If no grasp is ever committed,
a useful successor inspection is marked prospective-to-any-grasp and the missing
grasp remains explicit; it cannot become a prospective-success category.

A relevant view requires either at least 24 native fixture-instance pixels or
visibility of one fixed candidate rib region, including when that region is empty.
The latter uses native linear depth: at least 20 unoccluded sampled surface points
occupying at least 24 distinct pixels. Both possible regions are evaluated, without
using the hidden condition. This is an **offline visibility audit**, never an
online sufficiency heuristic. The initial and oblique views validate this criterion.
It measures available geometric evidence, not correctness of VLM interpretation.

Decision change requires a different executed grasp from the initial FD plan,
with a relevant pre-grasp observation followed by symbolic correction and replan
before commitment. This is temporal trace attribution, not an intervention proving
causation. No decision-change mechanism is added online.

## Costs and offline replay

Count executed new views, cumulative base translation from AP motion events,
camera-center path across acquired observations, request-to-last-response latency,
AP direction-to-motion time, their summed sensing time, VLM requests and total wall
time. Camera path includes camera movement during execution; base path is AP-only.
Sensing time is this operational interval sum, not GPU profiler time. Rendering and
logging overhead remain in task wall time and are not paper runtime comparisons.

Regret is the validated best binary handoff value minus that of the first chosen
grasp. Counterfactuals load the original saved initial simulator state and run the
alternate grasp with the identical INSERT primitive. They never feed the online
state. An avoidable *physical* handoff failure requires original Y1, a failed
INSERT attempt and successful alternate grasp/INSERT. Abandoned handoffs can also
be replayed, but are not relabeled as original collision failures.

## Mutually exclusive primary categories

The classifier retains supporting evidence and uses this explicit precedence:
J infrastructure/incomplete; I planner failure; F both validated grasps fail;
H failed local grasp; C final success after regrasp; A prospective compatible
first-grasp success; B remaining final success; E failed physical first INSERT
with successful alternate replay; G incorrect clearance judgment from useful
view; H recorded execution motion failure; D remaining reactive/late failure.
Cases without sufficient evidence remain `UNCLASSIFIED_PENDING_EVIDENCE` rather
than assigning an unsupported cause. The report shows these separately; they
must be reviewed before a scientific interpretation.

No automatic report chooses the hypothesized gap as its conclusion. Evidence
must also be assessed for physical, perception and reproduction confounds. The
four eventual interpretation labels are GAP FALSIFIED AT THIS LEVEL, PARTIAL GAP,
HYPOTHESIZED REACTIVE GAP OBSERVED and INCONCLUSIVE.
