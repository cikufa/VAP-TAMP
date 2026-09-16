"""Task physical primitives: native Fetch IK, attachment and collision checks.

No condition label or oracle grasp ranking is accepted by this interface.
"""
import numpy as np
from .scene import SPEC


class ConnectorPrimitives:
    def __init__(self, scene, log, frame=None):
        from omnigibson.utils.control_utils import IKSolver
        self.scene, self.robot, self.og = scene, scene.robot, scene.og
        self.log, self.frame = log, frame or (lambda **kw:None)
        self.indices = np.r_[self.robot.trunk_control_idx, self.robot.arm_control_idx['0']]
        self.ik=IKSolver(self.robot.robot_arm_descriptor_yamls['0'], self.robot.urdf_path,
            self.robot.eef_link_names['0'],self.robot.reset_joint_pos[self.indices])
        self.held=None;self.choice=None;self.joint=None

    def eef_pose(self):
        return self.robot.links[self.robot.eef_link_names['0']].get_position_orientation()

    def solve(self, position, orientation):
        from omnigibson.utils.transform_utils import relative_pose_transform
        p,q=relative_pose_transform(np.asarray(position),np.asarray(orientation),*self.robot.get_position_orientation())
        return self.ik.solve(p,q,max_iterations=250,initial_joint_pos=self.robot.get_joint_positions()[self.indices],
                             tolerance_pos=.003,tolerance_quat=.03)

    def candidate_collisions(self):
        from omnigibson.action_primitives.starter_semantic_action_primitives import PlanningContext
        from primitive_compat import ignore_copy_self_collisions
        from paper_sim_adapter import collision_contacts
        with PlanningContext(self.robot,self.scene.ap.robot_copy,'original') as context:
            ignore_copy_self_collisions(context)
            # Intentional grasp contact with the workpiece is permitted, not fixture contact.
            body=self.scene.connector.root_link.prim_path
            for ignored in context.disabled_collision_pairs_dict.values():ignored.append(body)
            return collision_contacts(context,self.og)

    def move_eef(self, position, orientation, check=True):
        old=self.robot.get_joint_positions().copy()
        solution=self.solve(position,orientation)
        if solution is None:
            self.log('motion_failure',reason='unreachable_eef',target_position=np.asarray(position).tolist())
            return False,[]
        self.robot.set_joint_velocities(np.zeros(len(self.indices)),indices=self.indices)
        self.robot.set_joint_positions(solution,indices=self.indices)
        self.robot.set_joint_positions(solution,indices=self.indices,drive=True)
        hits=self.candidate_collisions() if check else []
        if hits:
            self.robot.set_joint_positions(old)
            self.robot.set_joint_positions(old[self.indices],indices=self.indices,drive=True)
            self.log('motion_collision',contacts=hits,target_position=np.asarray(position).tolist())
            return False,hits
        for _ in range(3):self.og.sim.step()
        self.frame()
        return True,[]

    def reset(self):
        if self.joint is not None:
            self.og.sim.stage.RemovePrim(self.joint.GetPath());self.joint=None
        self.held=None;self.choice=None

    def grasp(self,choice):
        from omnigibson.utils.transform_utils import euler2quat,relative_pose_transform
        from omnigibson.utils.usd_utils import create_joint
        if choice not in ('gL','gR'):raise ValueError(choice)
        sign=1 if choice=='gL' else -1
        center=self.scene.connector.get_position().copy()
        q=euler2quat(np.array([np.pi/2,0.,-sign*np.pi/2]))
        target=center+np.array([0.,sign*SPEC['grasp_offset'],0.])
        self.log('grasp_committed',grasp_choice=choice)
        self.robot.set_joint_positions(np.array([.05,.05]),indices=self.robot.gripper_control_idx['0'])
        ok,hits=self.move_eef(target+np.array([0,sign*.04,.06]),q)
        if ok:ok,hits=self.move_eef(target,q)
        if not ok:
            self.log('grasp_complete',grasp_choice=choice,grasp_success=False,approach_success=False,contacts=hits)
            return False
        self.robot.set_joint_positions(np.array([.005,.005]),indices=self.robot.gripper_control_idx['0'])
        cp,cq=self.scene.connector.get_position_orientation();gp,gq=self.eef_pose()
        rp,rq=relative_pose_transform(cp,cq,gp,gq)
        self.joint=create_joint('/World/connector_attachment','FixedJoint',
            body0=self.robot.links[self.robot.eef_link_names['0']].prim_path,
            body1=self.scene.connector.root_link.prim_path,
            joint_frame_in_parent_frame_pos=rp,joint_frame_in_parent_frame_quat=rq,
            joint_frame_in_child_frame_pos=np.zeros(3),joint_frame_in_child_frame_quat=np.array([0,0,0,1.]))
        self.held=self.scene.connector;self.choice=choice;self.relative=(rp,rq)
        ok,hits=self.move_eef(target+np.array([0,0,.135]),q)
        for _ in range(30):self.og.sim.step()
        actual=self.scene.connector.get_position()
        actual_relative=relative_pose_transform(*self.scene.connector.get_position_orientation(),*self.eef_pose())
        hold=float(np.linalg.norm(actual_relative[0]-rp))
        success=bool(ok and actual[2]>center[2]+.08 and hold<.015)
        self.log('grasp_complete',grasp_choice=choice,grasp_success=success,approach_success=True,
                 attachment=bool(self.joint),lift_success=bool(actual[2]>center[2]+.08),stable_hold_error=hold,
                 connector_pose=[x.tolist() for x in self.scene.connector.get_position_orientation()],
                 connector_gripper_transform=[rp.tolist(),rq.tolist()],contacts=hits)
        self.frame()
        return success

    def insert(self):
        from omnigibson.utils.transform_utils import pose_transform,invert_pose_transform
        if self.held is None:
            self.log('insert_complete',insert_success=False,reason='not_held');return False
        target=np.array([SPEC['socket_entry_x']-SPEC['connector_tip_offset']+SPEC['insert_depth'],0.,SPEC['socket_center_z']])
        begin=self.scene.connector.get_position().copy()
        self.log('insert_started',grasp_choice=self.choice)
        goalq=np.array([0.,0.,0.,1.]);contacts=[];maximum_depth=-999.
        # First pre-align at staging X; then perform a straight +X insertion.
        alignment=np.array([begin[0],0.,target[2]])
        for end in (alignment,target):
            start=self.scene.connector.get_position().copy()
            n=max(2,int(np.ceil(np.linalg.norm(end-start)/SPEC['path_step'])))
            for position in np.linspace(start,end,n+1)[1:]:
                ep,eq=pose_transform(position,goalq,*invert_pose_transform(*self.relative))
                ok,contacts=self.move_eef(ep,eq)
                depth=float(self.scene.connector.get_position()[0]+SPEC['connector_tip_offset']-SPEC['socket_entry_x'])
                maximum_depth=max(maximum_depth,depth)
                if not ok:break
            if not ok:break
        error=float(np.linalg.norm(self.scene.connector.get_position()-target))
        success=bool(ok and maximum_depth>=SPEC['insert_depth']-SPEC['depth_tolerance'] and error<SPEC['position_tolerance'])
        self.log('insert_complete',insert_success=success,collision_object=[h['other_body'] for h in contacts],
            maximum_insertion_depth=maximum_depth,terminal_pose_error=error,grasp_choice=self.choice)
        self.frame();return success
