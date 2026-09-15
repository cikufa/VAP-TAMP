# Missing Ihlen firewood instance audit

Audit date: 2026-09-15. Starting checkpoint: c28bf5b. Upstream remains
39a52b0e10427ce91ddf3c1a177d3f4f782a61c3.

## Finding

The absent artifact is `Ihlen_0_int_task_store_firewood_0_0_template.json`,
expected under `og_dataset/scenes/Ihlen_0_int/json/`. It is a serialized
scene/task initialization: object instantiation information, object identities,
initial poses/state, and BDDL-instance-to-scene-object mapping. It is not a
missing PDDL domain/problem or missing BDDL activity definition. The base
Ihlen scene, general simulator config, robot assets and firewood models exist.
The precise object models and poses selected by the absent task JSON cannot
be verified. A separate RGB-D scene graph is not required by this released
simulation loader. Generating new poses would create a new task instance.

## Bounded public search

| Source | Check and result |
| --- | --- |
| All tracked files | `git ls-files` / recursive upstream tree; no cached Ihlen task JSON |
| Complete public Git history | Non-shallow clone, all 11 upstream commits; object-path inventory and text-reference search; no historical cached task file |
| Branches and tags | `git ls-remote --heads --tags origin` plus GitHub API: only main; zero tags |
| Release assets | GitHub releases API: zero releases/assets |
| Submodules | No gitlinks in root index. Nested manifests refer to vendored planner/validator and real-robot perception dependencies, not an OG task cache |
| Git LFS | Inspected small Git blobs for actual LFS pointer headers: 189 pointers; none to JSON. LFS attributes cover weights, recordings and ROS bags; no cached task reference |
| Download scripts | Tracked download scripts target Detic/checkpoints/other perception data; no Ihlen task-instance downloader |
| README/config/evaluation paths | README delegates OG/BEHAVIOR installation to Stanford; eval hard-codes Ihlen/store_firewood/definition 0/instance 0 with offline sampling. No custom cache URL |
| BDDL 3.5.0 | store_firewood activity definition/problem0 exists. It specifies relationships and three firewood objects, not the release's exact poses |
| Versioned dataset metadata | Verified full 1.0.0 archive inventory: Ihlen scene exists; required task cache absent; Merom firewood cache exists |
| Public web search | Exact filename, task+scene and VAP-TAMP asset queries found no downloadable missing artifact. Stanford lists Ihlen as a compatible scene, which is not a cached initialization |

Machine-readable evidence: `.runtime/missing_ihlen_evidence.json`,
`.runtime/public_{branches,tags,releases}.json`, and
`.runtime/dataset_inventory.json`. No credential contents were searched or logged.

**Recoverability:** not recoverable from the checked public release, complete
public history, or installed versioned bundle. This is a bounded negative search,
not proof that no author-held or unindexed copy exists. Further recovery requires
an author-provided cache or exact dataset provenance. No author was contacted.
Do not reconstruct this solely to match the benchmark.

## Fidelity decision and alternative

The paper names S5 Gather Kindling but no scene ID; the release selects Ihlen.
Keep that fact and preserve the default configuration. Do not substitute Merom.

The next validation candidate is released `bringing_water` (S2 Retrieve Bottles)
using its supplied `Wainscott_0_garden` task cache. PDDL references both bottles,
both floors and the agent; all appear in its cached BDDL object mapping. Released
primitives include find/grasp/place_on_floor, VLM verification, state correction
and Fast Downward replanning. This avoids the additional liquid/heating machinery
of boil-water/pie and split-object handling of halve-egg. Runtime validity remains
to be demonstrated; cache presence alone is not a PASS.

The evaluator's commented bringing_water scene is house_single_floor, so the
available cached Wainscott scene is also an explicit initialization deviation.
This is authorized by the revised task as alternative released-task validation:

> Pipeline/method reproduction on an alternative released VAP-TAMP task because the exact released Ihlen firewood task instance is absent from the public artifact.

It is **not exact task-level reproduction of the paper**. The fixed-view release
and general paper Algorithm 2 remain separate modes; the latter still requires
minimum integration plus documented unspecified parameters.

Sources: [official repository](https://github.com/aoloo-r/VAP-TAMP),
[paper](https://arxiv.org/html/2604.26988v1),
[Stanford firewood task compatibility](https://behavior.stanford.edu/knowledgebase/synsets/firewood.n.01.html).

The alternative task's six task-relevant DatasetObject model directories and
USD assets were also checked and are present (both bottles, both floors,
cabinet and lawn). The cached robot is Fetch. Inventory evidence:
`results/original/bringing_water_asset_inventory.json`. This remains a file
availability check, not a successful load.
