# Connector domain choices

Both GRASP actions require only availability, an empty gripper and connector
visibility. Their effects describe actual attachment and which side of the
connector the gripper occupies. No socket predicate occurs in either GRASP.

INSERT has two grounded physical applicability variants: the same straight-line
primitive starting from a left or right attachment transform needs clearance on
that occupied side of the socket. This is not a good/bad-grasp predicate. The
planner sees both variants and the entire plan, with unchanged unit action costs.

The terminal task is seated insertion while held, before gripper release; therefore
INSERT adds `inserted` but does not claim the connector has been released. A normal
`return_connector` action returns an uninserted held workpiece to its pickup nest,
allowing ordinary PDDL replanning to change attachment. No online recovery rule
selects this action. `find` restores visibility when its nominal fact is corrected.

The initial nominal state assumes both sides clear and both task objects visible,
identically for both hidden conditions. This follows the release's optimistic
state followed by visual correction. The ground-truth condition is never used to
write that problem. Clearance observations may correct either nominal assumption.
This choice is explicit; it is not an oracle map or a closed-world omission of
legitimate successor dependencies.

Task-local vocabulary adds five paraphrases per visual predicate without changing
the frozen query/sufficiency/direction templates. Immediate hand/configuration
bookkeeping follows the release's proprioceptive/GT-predicate boundary; socket
clearance and inserted predicates are visual. Fixture labels and offline compatibility
values are evaluation-only. Existing effect-plus-successor-precondition verification
order is preserved, including any prospective behavior it may naturally produce.

Domain ordering is fixed at first creation. Fast Downward tie-breaking will be
recorded without randomizing or reordering actions in response to outcomes.
