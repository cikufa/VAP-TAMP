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
        self.held=None;self.choice=None;self.joint=None;self.insert_success=False;self.minimum_clearance=float("inf")

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
            from omnigibson import lazy
            fixture_position=self.scene.objects['fixture'].get_position()
            lo=fixture_position-np.array(SPEC['fixture_size'])/2
            hi=fixture_position+np.array(SPEC['fixture_size'])/2
            for name,meshes in context.robot_copy.meshes[context.robot_copy_type].items():
                if 'gripper' not in name and 'wrist' not in name:continue
                for mesh in meshes.values():
                    points=mesh.GetAttribute('points').Get()
                    if points is None or not len(points):
                        boundable=lazy.pxr.UsdGeom.Boundable(mesh)
                        extent=boundable.ComputeExtent(lazy.pxr.Usd.TimeCode.Default()) if boundable else None
                        if extent is None or len(extent)!=2:
                            raise RuntimeError(f'Missing bounds for {mesh.GetPath()} type={mesh.GetTypeName()}')
                        import itertools
                        points=np.array(list(itertools.product(*zip(extent[0],extent[1]))))
                    matrix=np.asarray(lazy.pxr.UsdGeom.Xformable(mesh).ComputeLocalToWorldTransform(lazy.pxr.Usd.TimeCode.Default()))
                    world=np.c_[np.asarray(points),np.ones(len(points))]@matrix
                    gap=np.maximum(np.maximum(lo-world[:,:3].max(0),world[:,:3].min(0)-hi),0.)
                    self.minimum_clearance=min(self.minimum_clearance,float(np.linalg.norm(gap)))
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
        self.held=None;self.choice=None;self.insert_success=False;self.minimum_clearance=float('inf')
        self.robot._ag_obj_in_hand['0']=None

    def grasp(self,choice):
        from omnigibson.utils.transform_utils import euler2quat,relative_pose_transform
        from omnigibson.utils.usd_utils import create_joint
        if choice not in ('gL','gR'):raise ValueError(choice)
        self.insert_success=False
        sign=1 if choice=='gL' else -1
        center=self.scene.connector.get_position().copy()
        q=euler2quat(np.array([np.pi/2,0.,-sign*np.pi/2]))
        target=center+np.array([0.,sign*SPEC['grasp_offset'],0.])
        self.log('grasp_committed',grasp_choice=choice)
        if not self.station():
            self.log('grasp_complete',grasp_choice=choice,grasp_success=False,approach_success=False);return False
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
        self.scene.nest_joint.GetAttribute('physics:jointEnabled').Set(False)
        self.held=self.scene.connector;self.choice=choice;self.relative=(rp,rq)
        self.robot._ag_obj_in_hand['0']=self.held
        ok,hits=self.move_eef(target+np.array([0,0,SPEC['grasp_lift']]),q)
        for _ in range(30):self.og.sim.step()
        actual=self.scene.connector.get_position()
        actual_relative=relative_pose_transform(*self.scene.connector.get_position_orientation(),*self.eef_pose())
        hold=float(np.linalg.norm(actual_relative[0]-rp))
        from scipy.spatial.transform import Rotation
        grasp_angle=float(np.degrees((Rotation.from_quat(cq).inv()*Rotation.from_quat(self.scene.connector.get_orientation())).magnitude()))
        success=bool(ok and actual[2]>center[2]+.08 and hold<.015 and grasp_angle<15.)
        self.log('grasp_complete',grasp_choice=choice,grasp_success=success,approach_success=True,
                 attachment=bool(self.joint),lift_success=bool(actual[2]>center[2]+.08),stable_hold_error=hold,orientation_change_degrees=grasp_angle,
                 connector_pose=[x.tolist() for x in self.scene.connector.get_position_orientation()],
                 connector_gripper_transform=[rp.tolist(),rq.tolist()],contacts=hits)
        self.frame()
        return success

    def insert(self):
        from omnigibson.utils.transform_utils import pose_transform,invert_pose_transform
        if self.held is None:
            self.log('insert_complete',insert_success=False,reason='not_held');return False
        if not self.station():
            self.log('insert_complete',insert_success=False,reason='station_unreachable');return False
        self.minimum_clearance=float('inf')
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
                contacts=self.workpiece_collisions(position)
                if contacts:
                    ok=False;self.log('motion_collision',contacts=contacts,target_position=position.tolist());break
                ep,eq=pose_transform(position,goalq,*invert_pose_transform(*self.relative))
                ok,contacts=self.move_eef(ep,eq)
                depth=float(self.scene.connector.get_position()[0]+SPEC['connector_tip_offset']-SPEC['socket_entry_x'])
                maximum_depth=max(maximum_depth,depth)
                if not ok:break
            if not ok:break
        error=float(np.linalg.norm(self.scene.connector.get_position()-target))
        from scipy.spatial.transform import Rotation
        rotation=Rotation.from_quat(self.scene.connector.get_orientation())
        angle=float(np.degrees(rotation.magnitude()))
        terminal_depth=float((self.scene.connector.get_position()+rotation.apply([SPEC['connector_tip_offset'],0,0]))[0]-SPEC['socket_entry_x'])
        success=bool(ok and terminal_depth>=SPEC['insert_depth']-SPEC['depth_tolerance'] and error<SPEC['position_tolerance'] and angle<=SPEC['orientation_tolerance_degrees'])
        self.insert_success=success
        self.log('insert_complete',insert_success=success,collision_object=[h['other_body'] for h in contacts],
            maximum_insertion_depth=maximum_depth,terminal_pose_error=error,terminal_depth=terminal_depth,
            terminal_angle_error_degrees=angle,minimum_clearance=self.minimum_clearance,
            clearance_definition='conservative AABB separation of native wrist/finger collision copies from fixture',grasp_choice=self.choice)
        self.frame();return success

    def workpiece_collisions(self,position):
        hits=[]
        ignored={link.prim_path for link in self.robot.links.values()}|{self.scene.connector.root_link.prim_path}
        components=[('body',[0,0,0],[.070,.060,.040]),('tongue',[.065,0,0],[.080,.045,.028]),
                    ('key',[.065,.012,.018],[.070,.010,.008])]
        for name,offset,size in components:
            def report(hit):
                if hit.rigid_body not in ignored:hits.append(dict(robot_mesh='connector/'+name,other_body=hit.rigid_body))
                return len(hits)<8
            self.og.sim.psqi.overlap_box(halfExtent=np.array(size)/2,pos=np.asarray(position)+offset,
                                        rot=np.array([0.,0.,0.,1.]),reportFn=report)
        return hits

    def station(self):
        target=np.array(SPEC['robot_position']);target_orientation=np.array(SPEC['robot_orientation'])
        before,before_orientation=self.robot.get_position_orientation()
        if np.linalg.norm(target-before)<.01:
            self.robot.set_position_orientation(target,target_orientation)
            return True
        # Fixed work-station approach, independent of fixture state and grasp choice.
        for point in np.linspace(before,target,max(2,int(np.ceil(np.linalg.norm(target-before)/.025)))+1)[1:]:
            old,old_orientation=self.robot.get_position_orientation()
            self.robot.set_position_orientation(point,target_orientation)
            hits=self.candidate_collisions()
            if hits:
                self.robot.set_position_orientation(old,old_orientation)
                self.log('motion_failure',reason='station_path_collision',contacts=hits);return False
            self.og.sim.step()
        self.log('station_approach',position_before=before.tolist(),position_after=self.robot.get_position().tolist())
        self.frame();return True

    def return_connector(self):
        from omnigibson.utils.transform_utils import pose_transform,invert_pose_transform
        self.log('release_started')
        if self.held is None:return True
        if not self.station():return False
        initial=np.array(SPEC['connector_initial']);current=self.held.get_position().copy()
        for goal in (np.array([initial[0],0,current[2]]),initial):
            start=self.held.get_position().copy()
            for point in np.linspace(start,goal,max(2,int(np.ceil(np.linalg.norm(goal-start)/SPEC['path_step'])))+1)[1:]:
                ep,eq=pose_transform(point,np.array([0.,0.,0.,1.]),*invert_pose_transform(*self.relative))
                ok,hits=self.move_eef(ep,eq)
                if not ok:return False
        self.og.sim.stage.RemovePrim(self.joint.GetPath());self.joint=None
        self.scene.nest_joint.GetAttribute('physics:jointEnabled').Set(True)
        self.robot._ag_obj_in_hand['0']=None;self.held=None;self.choice=None;self.insert_success=False
        self.robot.set_joint_positions(np.array([.05,.05]),indices=self.robot.gripper_control_idx['0'])
        for _ in range(10):self.og.sim.step()
        error=float(np.linalg.norm(self.scene.connector.get_position()-initial))
        self.log('release_complete',success=error<.01,pose_error=error);self.frame();return error<.01

    def find(self,target):
        from fetch_camera_compat import look_at_fetch
        position=self.scene.connector.get_position() if target=='connector' else self.scene.objects['socket_top'].get_position()
        look_at_fetch(self.robot,position)
        self.log('task_find',target=target);self.frame();return True

    def terminal_state(self):
        from scipy.spatial.transform import Rotation
        p=self.scene.connector.get_position();r=Rotation.from_quat(self.scene.connector.get_orientation())
        target=np.array([SPEC['socket_entry_x']-SPEC['connector_tip_offset']+SPEC['insert_depth'],0.,SPEC['socket_center_z']])
        depth=float((p+r.apply([SPEC['connector_tip_offset'],0,0]))[0]-SPEC['socket_entry_x'])
        error=float(np.linalg.norm(p-target));angle=float(np.degrees(r.magnitude()))
        return dict(insertion_depth=depth,position_error=error,angle_error_degrees=angle,
                    success=bool(depth>=SPEC['insert_depth']-SPEC['depth_tolerance'] and error<SPEC['position_tolerance'] and angle<=SPEC['orientation_tolerance_degrees']))
