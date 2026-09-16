"""Native OG assembly geometry. Hidden condition is consumed only at reset."""
import json
from pathlib import Path
import numpy as np

SPEC_PATH = Path(__file__).parent / 'assets/geometry.json'
SPEC = json.loads(SPEC_PATH.read_text())
CONDITIONS = ('LEFT_CONSTRAINED', 'RIGHT_CONSTRAINED')


def cube(name, size, position, color, fixed=True):
    return dict(type='PrimitiveObject', name=name, category='object', primitive_type='Cube',
                size=1.0, scale=size, position=position, rgba=[*color, 1.],
                fixed_base=fixed, visual_only=False, mass=.08 if not fixed else None)


def configuration():
    z = SPEC['socket_center_z']
    objects = [
        dict(cube('assembly_floor', [8.,8.,.06], [0,0,-.03], [.65,.65,.65]), category='floors'),
        cube('grasp_nest', [.012,.025,.22], [.403,0,.775], [.5,.5,.5]),
        cube('tongue_nest', [.018,.025,.226], [.495,0,.778], [.5,.5,.5]),
        cube('bench', [.75, .60, .06], [.63, 0, .635], [.32, .34, .36]),
        cube('bench_leg_left', [.07, .07, .72], [.75, .25, .36], [.25, .27, .30]),
        cube('bench_leg_right', [.07, .07, .72], [.75, -.25, .36], [.25, .27, .30]),
        dict(type='USDObject',name='connector',category='object',usd_path=str(Path(__file__).parent/'assets/connector.usd'),fixed_base=False,position=SPEC['connector_initial']),
        cube('socket_bottom', [.15, .16, .025], [.795, 0, z-.039], [.48, .50, .52]),
        cube('socket_top', [.15, .16, .025], [.795, 0, z+.039], [.48, .50, .52]),
        cube('socket_left', [.15, .025, .053], [.795, .063, z], [.48, .50, .52]),
        cube('socket_right', [.15, .025, .053], [.795, -.063, z], [.48, .50, .52]),
        cube('panel', [.03, .50, .45], [.91, 0, .92], [.37, .40, .43]),
        cube('fixture', SPEC['fixture_size'], [SPEC['fixture_x'], SPEC['fixture_y'], z], [.40, .42, .44]),
        cube('hood_roof', [.42, .44, .018], [.73, 0, 1.04], [.42, .44, .46]),
    ]
    return dict(scene=dict(type='Scene', use_skybox=False, use_floor_plane=False),
                robots=[dict(type='Fetch', name='robot0', position=SPEC['robot_position'],
                    orientation=SPEC['robot_orientation'], obs_modalities=['rgb', 'depth_linear', 'seg_instance'],
                    self_collision=False, grasping_mode='physical', default_reset_mode='tuck',
                    controller_config={'arm_0':dict(name='JointController',motor_type='position',use_delta_commands=False)},
                    sensor_config={'VisionSensor': {'sensor_kwargs': {'image_height': 256, 'image_width': 256}}})],
                objects=objects, render=dict(viewer_width=960, viewer_height=640))


class ConnectorScene:
    def __init__(self, log):
        import omnigibson as og
        from fetch_camera_compat import look_at_fetch, camera_sensor
        from omnigibson.action_primitives.starter_semantic_action_primitives import StarterSemanticActionPrimitives
        self.og, self.log = og, log
        log('scene_loading')
        self.env = og.Environment(configs=configuration())
        from omnigibson import lazy
        light=lazy.pxr.UsdLux.DomeLight.Define(og.sim.stage, '/World/assembly_light')
        light.CreateIntensityAttr(1000.)
        self.robot = self.env.robots[0]
        self.objects = {obj.name: obj for obj in self.env.scene.objects}
        self.connector = self.objects['connector']
        self.sensor = camera_sensor(self.robot)
        self.ap = StarterSemanticActionPrimitives(self.env)
        self.env.reset()
        self.robot.set_position_orientation(np.array(SPEC['robot_position']), np.array(SPEC['robot_orientation']))
        self.robot.set_joint_positions(np.array([SPEC['initial_trunk_position']]),indices=self.robot.trunk_control_idx)
        self.robot.set_joint_positions(np.array([SPEC['initial_trunk_position']]),indices=self.robot.trunk_control_idx,drive=True)
        for _ in range(10): og.sim.step()
        look_at_fetch(self.robot, np.array(SPEC['initial_look_target']))
        self.initial_joints = self.robot.get_joint_positions().copy()
        self.set_viewer()
        self.saved = og.sim.dump_state(serialized=False)
        log('scene_ready', object_poses={k:v.get_position().tolist() for k,v in self.objects.items()}, objects=list(self.objects), joints=list(self.robot.joints),
            eef_link=self.robot.eef_link_names, eef_pose=[x.tolist() for x in self.robot.get_eef_position_orientation('0')]
            if hasattr(self.robot,'get_eef_position_orientation') else None)

    def set_viewer(self):
        from omnigibson.utils.transform_utils import euler2quat
        from scipy.spatial.transform import Rotation
        p=np.array([1.6, -1.8, 1.75]); target=np.array([.5,0,.85])
        forward=(target-p)/np.linalg.norm(target-p)
        right=np.cross(forward,[0,0,1]); right/=np.linalg.norm(right)
        up=np.cross(right,forward)
        q=Rotation.from_matrix(np.column_stack([right,up,-forward])).as_quat()
        self.og.sim.viewer_camera.set_position_orientation(p,q)

    def reset(self, condition, seed):
        if condition not in CONDITIONS: raise ValueError(condition)
        self.og.sim.load_state(self.saved, serialized=False)
        # The condition is never stored on the scene object consumed by online code.
        side = 1 if condition == CONDITIONS[0] else -1
        self.objects['fixture'].set_position(np.array([SPEC['fixture_x'], side*SPEC['fixture_y'], SPEC['socket_center_z']]))
        for _ in range(5): self.og.sim.step()
        self.log('scene_reset', evaluation_only={'scene_condition': condition, 'seed':seed})

    def capture(self):
        for _ in range(4): self.og.sim.render()
        data,_=self.sensor.get_obs()
        third,_=self.og.sim.viewer_camera.get_obs()
        return np.asarray(third['rgb'])[...,:3], np.asarray(data['rgb'])[...,:3]
