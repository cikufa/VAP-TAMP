# Connector training statement

No model is trained in this experiment. The existing frozen VLM backend,
pretrained OmniGibson robot assets and baseline verification implementation are
reused. There is no PPO, behavior cloning, task-specific neural training,
successor classifier, learned competence model or view-value model.

The native controller uses inverse kinematics and fixed geometric primitives.
Mock responses are deterministic API-boundary fixtures for integration testing,
not training data or scientific observations. Physics validation estimates the
binary grasp-to-insertion mapping offline; that mapping is never supplied to
the online planner, verifier or active-view selector.
