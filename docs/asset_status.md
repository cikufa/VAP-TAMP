# Verified assets and baseline scene blocker

The user approved the 22.32 GB download after compatibility/disk checks and
explicitly accepted the BEHAVIOR license for non-commercial academic research.
No dataset or decryption key is committed.

- Version: OG dataset 1.0.0, GCS generation 1710728899224755.
- Compressed bytes: 22321609648.
- MD5 verified: `f6f00da7882fad9dd0f4a205d74a539d`.
- SHA256: `e6c1f75504c1f3b7a10b2fc744648c7e4d263fdf07155856afbea6e052c759e4`.
- Expanded regular-file bytes: 28572351606 in 66320 files.
- Free bytes before expansion: 147172098048.
- Extraction: Python tarfile data filter, no prior target overwritten.
- Location: `.runtime/data/og_dataset`.
- Engine, supplementary assets and key are also installed project-locally.

## Missing released task instance

The upstream default config requires:
`Ihlen_0_int_task_store_firewood_0_0_template.json`.
The pinned dataset lacks this file. With `online_object_sampling=False`,
`BehaviorTask.verify_scene_and_task_config` constructs this exact filename;
`Scene._load_objects_from_scene_file` opens it directly. There is no automatic
sampling fallback. A running engine cannot repair this missing scene instance.

The dataset supplies `Merom_0_int_task_store_firewood_0_0_template.json`, with
three firewood objects, a floor, table and robot. This is a different scene.
The paper Section V-B describes S5 as collecting two sticks onto a table but
does not name an OmniGibson scene ID. Neither Ihlen nor Merom occurs in the
paper text. The release is the available evidence for the scene selection.

The user requested “use whatever was used in the paper” when offered Merom.
Therefore no Merom substitution or online resampling is authorized as the
baseline. The original cached instance or author-confirmed scene/dataset
provenance is needed to claim the requested reproduction. No message has
been sent to the authors.

Other cached original task names exist in this bundle, but their scenes also
differ from the configured/commented release scenes; switching tasks alone
does not establish fidelity to the paper's initialization.

Source: [paper Section V-B](https://arxiv.org/html/2604.26988v1), pinned release
`vlm-tamp/eval.py`, and installed pinned OG `behavior_task.py` / `scene_base.py`.
