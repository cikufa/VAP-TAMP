# Connector handoff benchmark physical specification

Physical geometry accepted before any live connector VLM evaluation. Source
geometry revision `development-1` is frozen by the release manifest; its name is
historical. Do not tune dimensions, cameras, PDDL, transforms or tolerances using
later live performance.

## Assembly and units

All lengths are metres, quaternions are XYZW, world +X is insertion, world +Y is
the robot's initial left. A keyed connector is acquired from a feed nest and
inserted into a panel socket while remaining held. The condition changes only the
mounting rib's Y sign. Colors, labels, initial state and action order are identical.

The connector is a native dynamic USD rigid body (0.08 kg) with independent visual
and collision boxes: body 0.070×0.060×0.040; tongue 0.080×0.045×0.028 centered
at local (0.065,0,0); polarizing key 0.070×0.010×0.008 at (0.065,0.012,0.018).
The socket has bottom/top 0.150×0.160×0.025 boxes at (0.795,0,0.901/0.979),
and side walls 0.150×0.025×0.053 at (0.795,±0.063,0.940).
Panel: 0.030×0.500×0.450 at (0.910,0,0.920).
Hood: 0.480×0.260×0.018 at (0.700,0,1.040).
Mounting rib: 0.310×0.045×0.080 at (0.745,±0.100,0.980).
Bench: 0.750×0.600×0.060 at (0.630,0,0.635).
Feed supports: 0.012×0.025×0.150 at (0.403,0,0.740) and
0.018×0.025×0.156 at (0.495,0,0.743). A fixed nest constraint holds the
workpiece at the initial pose until gripper attachment; returning reinstates it.
`scene.py` and `assets/connector.usd` are the complete canonical asset definition.

## Physical skills

Fetch position-controlled arm IK uses trunk plus seven arm joints, up to 250 IK
iterations, 0.003 m position and 0.03 quaternion tolerance. Per candidate pose,
apply joints, query native collision copies and roll back a blocked candidate;
accepted poses advance three physics steps. Intentional workpiece/gripper contact
and native floor/self filters are permitted; fixture contact is not ignored.

For gL/gR, EEF pickup position is connector center + (0,±0.095,0); roll π/2,
yaw ∓π/2. Fingers close vertically, leaving the connector key orientation intact.
Open finger joint targets are 0.05 m, closed targets 0.005 m. A native fixed joint
captures the *actual* connector-to-gripper transform, then the nest joint releases.
Lift command: 0.105 m; settle 30 physics steps. Local success requires approach,
height gain >0.080 m, attachment-position drift <0.015 m and orientation change
<15 degrees. Measured transforms are stored per trial, not replaced by nominal ones.
Nominal local connector translation is approximately (0.095,0,0); its local
orientation differs between gL (−0.5,0.5,0.5,0.5) and gR (0.5,0.5,0.5,−0.5).

INSERT first returns to the fixed workstation if AP moved the base, pre-aligns at
current X to Y=0,Z=0.940 with identity object orientation, then translates +X in
0.005 m increments. Terminal body target is (0.665,0,0.940); tongue tip reaches
0.050 m beyond entry X=0.720. Success requires depth ≥0.044 m, position error
<0.008 m and orientation error ≤5 degrees. The native collision query stops the
incompatible wrist/fingers against the rib. `minimum_clearance` is diagnostic
unsigned AABB separation, not a signed penetration depth or contact-offset-aware
safety guarantee; actual collision-body results determine blockage.

Return is an ordinary task action: workstation approach, retract, lower into
feed nest, release, verify placement. No custom recovery policy selects it; FD
chooses it from the corrected PDDL state. There is no hidden condition branch in
grasp/insert and no online compatibility-table access.

## Repeatability before freeze

| Condition | gL local | gR local | INSERT after gL | INSERT after gR |
|---|---:|---:|---:|---:|
| LEFT_CONSTRAINED | 5/5 | 5/5 | 0/5 | 5/5 |
| RIGHT_CONSTRAINED | 5/5 | 5/5 | 5/5 | 0/5 |

Twenty deterministic-reset trials, seeds 1000–1004, no injected pose/motor noise.
Successful terminal position errors were 0.005186–0.005439 m. Incompatible paths
reported `/World/fixture/base_link` collision bodies. This is an engineering
repeatability check, not population success-rate estimation. Full poses,
attachment transforms, holds, approach/lift results, clearance and depths are in
`results/custom_connector/benchmark_validation/physics/acceptance01`.

## Camera and observability

Fetch native RGB/depth/instance camera is 256×256. Initial base is (0.1,0,0),
identity orientation, initial trunk 0.28 m, head aimed at (0.46,0,0.86).
The exact settled camera extrinsics and joints are in the table/JSON below.
The viewer camera is at (1.6,−1.8,1.75), aimed at (0.5,0,0.85), 960×640.
Only the robot camera is supplied to the VLM. All images are real RTX renders.

The final 2×4 contact sheet shows grasp-visible initial images and clear oblique
fixture geometry. Both initial fixture masks have zero pixels; mean paired RGB
absolute difference is 1.724/255 (rendering/settling variation, not a side label).
Depth visibility establishes informative views within two existing 0.25 m AP
moves in each direction/condition. Third oblique steps are also shown for an
especially clear human-review illustration; they do not change the online K=2.
No view ranking, new direction candidate or inspection trigger is supplied online.

## Canonical numerical parameters

```json
{
  "revision": "development-1",
  "units": "metres",
  "connector_size": [
    0.07,
    0.06,
    0.04
  ],
  "connector_initial": [
    0.43,
    0.0,
    0.835
  ],
  "connector_staging": [
    0.43,
    0.0,
    0.94
  ],
  "socket_entry_x": 0.72,
  "socket_center_z": 0.94,
  "insert_depth": 0.05,
  "grasp_offset": 0.095,
  "fixture_y": 0.1,
  "fixture_size": [
    0.31,
    0.045,
    0.08
  ],
  "fixture_x": 0.745,
  "robot_position": [
    0.1,
    0,
    0
  ],
  "robot_orientation": [
    0,
    0,
    0,
    1
  ],
  "initial_look_target": [
    0.46,
    0.0,
    0.86
  ],
  "position_tolerance": 0.008,
  "depth_tolerance": 0.006,
  "path_step": 0.005,
  "connector_tip_offset": 0.105,
  "initial_trunk_position": 0.28,
  "orientation_tolerance_degrees": 5.0,
  "fixture_z": 0.98,
  "grasp_lift": 0.105
}
```

## Measured camera poses

| Condition | View | Position | Rotation matrix |
|---|---|---|---|
| LEFT_CONSTRAINED | initial | [0.22194704413414018, -0.0003845253959297905, 1.283115863800049] | [[-0.001314741590976387, 0.8723396002508229, -0.48889865339227856], [-0.9999991220338084, -0.0012278089571648443, 0.0004984142625661658], [-0.00016548764721460718, 0.48889887944175026, 0.872340448617648]] |
| LEFT_CONSTRAINED | left | [0.39465865492820745, 0.5180066823959351, 1.3139002323150637] | [[-0.7974698460404326, 0.260112441883321, -0.5444110232478261], [-0.6030071421195926, -0.37439662913310756, 0.7044214297184095], [-0.020596873767896262, 0.8900385843721961, 0.4554196824026462]] |
| LEFT_CONSTRAINED | right | [0.3943236470222473, -0.5182001590728759, 1.3140624761581423] | [[0.7973061482193586, 0.26026933347076864, -0.5445757799115676], [-0.603226846685185, 0.3742555622025918, -0.7043082745493413], [0.020500669497814483, 0.890052048037138, 0.45539771006784563]] |
| RIGHT_CONSTRAINED | initial | [0.2222012877464296, -0.00016547783161511136, 1.283146142959595] | [[0.0034162189418409095, 0.8723399469106793, -0.4888878669715735], [-0.9999941647063132, 0.0029795299990957314, -0.001671213423706519], [-1.2101634768446612e-06, 0.4888907233982437, 0.8723450352777149]] |
| RIGHT_CONSTRAINED | left | [0.39457684755325323, 0.5179022550582886, 1.3139265775680544] | [[-0.7973524602950829, 0.2602129283056026, -0.5445349263399017], [-0.6031623050573061, -0.3743837417954346, 0.7042954263923676], [-0.02059824796763282, 0.8900146323639141, 0.4554664272575875]] |
| RIGHT_CONSTRAINED | right | [0.39428451657295227, -0.518217623233795, 1.3140883445739748] | [[0.7972881847977233, 0.26028302845186685, -0.5445955338431232], [-0.6032505022232415, 0.37425487008401387, -0.7042883811236736], [0.020503218024459813, 0.8900483342596192, 0.4554048536547661]] |

## Symbolic and experiment freeze

`pddl/domain.pddl` defines two GRASPs, two configuration-specific INSERTs, return
and find. GRASP requires only availability, empty hand and connector visibility.
INSERT has its own side-clearance requirement. The same nominal problem assumes
both clearances and both object views in each condition; visual verification can
correct it. FD's fixed nominal gL choice and action ordering are retained.
See `docs/connector_pddl_model.md` for complete rationale and unary syntax adapter.

`eval_seeds.json` fixes two non-metric debug episodes and 20 live episodes (10 per
condition). `compatibility.json` is offline evaluation only. Metrics and
counterfactual definitions are in `docs/connector_metrics.md`. Baseline is
`c315720`; provider remains the accepted Gemini model substitution. Full release
SHA, source hashes and acceptance evidence are recorded at final release.
