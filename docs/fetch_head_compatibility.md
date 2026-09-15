# Fetch lookat compatibility

OG 1.0's private `_get_head_goal_q` is Tiago-specific, but the released
simulation config selects Fetch and calls that helper unconditionally.
`vlm-tamp/fetch_camera_compat.py` now supplies the Fetch branch of `lookat`.
The existing target object is retained. The original Tiago path is unchanged.

The adapter uses Fetch's pan-about-Z and tilt-about-Y axes, actual world link
poses, actual camera mount transform, and joint limits. A bounded two-joint
kinematic solve aligns the camera's USD -Z optical axis with the target.
Only head joint values change. This is a class-B embodiment compatibility fix,
not a new active-perception decision rule; no successor knowledge, view score,
or alternative target is introduced. Targets outside the reachable range
produce a bounded best-effort head pose and a recorded nonzero direction error.
Such a result is not evidence that the target became visible.

After writing joint positions, the adapter reads the camera pose to trigger
OG's PhysX-to-USD synchronization before rendering marks the pose cache valid.
The first calibration showed unchanged camera orientation without that sync;
after the sync, the physical camera points at the calibration target.

Evidence under `results/original/startup/`:

* `20260915T205308580155Z`: first head calibration, stale rendered pose;
  10.1765-degree error, correctly rejected.
* `20260915T205443982287Z`: pose sync yields 0.0000105-degree calibration error;
  distant bottle solve failed convergence and was rejected.
* `20260915T205549704771Z`: explicit pose sync after calibration reset and a
  target-directed yaw initialization yield a clean pass. Non-head joints stay
  unchanged in the calibration. The actual bottle lies outside the initial
  head range; pan reaches its 1.57-radian limit, which is logged rather than
  interpreted as visibility. RGB after motion is saved and shutdown succeeds.

No VLM request, voting, sufficiency or full active-perception validation occurs
in these head-motion tests.
