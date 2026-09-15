"""Geometric compatibility corrections for OG 1.0's released primitives."""
import numpy as np


def sample_aabb_side(target_obj):
    """OG's side-face sampler with full-extent/half-extent error corrected.

    Same random choices and sampling method as StarterSemanticActionPrimitives;
    the center-to-face distance is half of max_corner - min_corner.
    """
    center, extent = target_obj.aabb_center, target_obj.aabb_extent
    axis = np.random.choice([0, 1])
    direction = np.random.choice([-1, 1])
    face_center = center + np.eye(3)[axis] * extent * direction / 2
    lateral = 0 if axis == 1 else 1
    lateral_half = np.eye(3)[lateral] * extent / 2
    vertical_half = np.eye(3)[2] * extent / 2
    return np.random.uniform(face_center - vertical_half - lateral_half,
                             face_center + vertical_half + lateral_half)
