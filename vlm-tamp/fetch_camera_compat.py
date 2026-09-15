"""Fetch embodiment adapter for the released target-directed lookat primitive.

OG 1.0's private head solver only supports Tiago. Here the existing target is
converted to Fetch pan/tilt joint positions using its actual link/camera poses.
This supplies motor kinematics, not a viewpoint-selection policy.
"""
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation


def pose(item):
    position, quaternion = item.get_position_orientation()
    return np.asarray(position, dtype=float), Rotation.from_quat(quaternion).as_matrix()


def camera_sensor(robot):
    return next(sensor for sensor in robot.sensors.values() if 'rgb' in sensor.modalities)


def look_at_fetch(robot, target):
    """Set only Fetch's head joints toward target; clamp to physical limits."""
    joints = [robot.joints[name] for name in ('head_pan_joint', 'head_tilt_joint')]
    q0 = np.array([joint.get_state()[0][0] for joint in joints], dtype=float)
    lower = np.array([joint.lower_limit for joint in joints])
    upper = np.array([joint.upper_limit for joint in joints])
    pan_p, pan_r = pose(robot.links['head_pan_link'])
    tilt_p, tilt_r = pose(robot.links['head_tilt_link'])
    camera_p, camera_r = pose(camera_sensor(robot))
    # Fetch URDF axes: pan about local +Z, tilt about local +Y.
    pan_zero_r = pan_r @ Rotation.from_euler('z', -q0[0]).as_matrix()
    tilt_offset = pan_r.T @ (tilt_p - pan_p)
    tilt_zero_r = pan_r.T @ tilt_r @ Rotation.from_euler('y', -q0[1]).as_matrix()
    camera_offset = tilt_r.T @ (camera_p - tilt_p)
    camera_local_r = tilt_r.T @ camera_r
    target = np.asarray(target, dtype=float)

    def residual(q):
        rp = pan_zero_r @ Rotation.from_euler('z', q[0]).as_matrix()
        rt = rp @ tilt_zero_r @ Rotation.from_euler('y', q[1]).as_matrix()
        cp = pan_p + rp @ tilt_offset + rt @ camera_offset
        cr = rt @ camera_local_r
        direction = cr.T @ (target - cp)
        norm = np.linalg.norm(direction)
        if norm < 1e-8:
            raise ValueError('Lookat target coincides with the camera')
        # USD cameras look down their local -Z axis.
        return direction / norm - np.array([0., 0., -1.])

    # Initialize yaw toward the target even when the current camera faces away.
    # This avoids a flat gradient at a target almost exactly behind the camera.
    relative = pan_zero_r.T @ (target - pan_p)
    initial = np.array([np.arctan2(relative[1], relative[0]), q0[1]])
    solution = least_squares(residual, np.clip(initial, lower, upper),
                             bounds=(lower, upper), max_nfev=200)
    if not solution.success or not np.isfinite(solution.x).all():
        raise RuntimeError('Fetch head kinematics did not converge')
    command = robot.get_joint_positions().copy()
    for joint, value in zip(joints, solution.x):
        command[list(joint.dof_indices)] = value
    robot.set_joint_positions(command)
    # Refresh PhysX -> USD before rendering marks the pose cache valid.
    pose(camera_sensor(robot))
    return dict(joints_before=q0.tolist(), joints_target=solution.x.tolist(),
                direction_error=float(np.linalg.norm(residual(solution.x))))
