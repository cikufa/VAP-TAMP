"""Geometric compatibility corrections for OG 1.0's released primitives."""
import numpy as np


def ignore_copy_self_collisions(context):
    """Restore OG simplified-base-copy semantics when Fetch falls back to original.

    The posture is fixed during base sampling. Only copy-against-copy overlaps
    are filtered; all existing environment collision rules remain intact.
    This mirrors PlanningContext's existing simplified-copy self filtering.
    """
    paths = [mesh.GetPrimPath().pathString
             for meshes in context.robot_copy.meshes[context.robot_copy_type].values()
             for mesh in meshes.values()]
    for ignored in context.disabled_collision_pairs_dict.values():
        ignored.extend(path for path in paths if path not in ignored)
    return len(paths)


def navigation_target_rooms(obj, segmentation_map, point_on_object):
    """Use current location for movable objects; in_rooms is static OG metadata.

    Fixed floors/furniture can span several room segments, so their annotated
    room set remains authoritative. A movable object outside the map remains
    unresolved instead of silently falling back to its obsolete initial room.
    """
    if obj.fixed_base and obj.in_rooms:
        return list(obj.in_rooms)
    point = point_on_object if obj.fixed_base else obj.get_position()
    return [segmentation_map.get_room_instance_by_point(point[:2])]


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
