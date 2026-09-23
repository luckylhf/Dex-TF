#!/usr/bin/python3
"""
Tiangong Dex Interactive Joint Control GUI

Qt-based GUI for debugging and controlling the Tiangong Dex robot joints.
- Grouped sliders for the 31 revolute joints present in the URDF
  （手部关节当前【未】接入 URDF，故不显示滑条；详见 HAND_JOINTS 注释）
- Ghost Robot preview via MarkerArray (FK-calculated, semi-transparent overlay)
- Sync-to-Real from /joint_states
- Execute via bodyctrl_msgs/CmdSetMotorPosition on /head/cmd_pos etc.
- Safety confirmation dialog
"""

import sys
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
from sensor_msgs.msg import JointState
from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import Quaternion
from bodyctrl_msgs.msg import CmdSetMotorPosition, SetMotorPosition
from python_qt_binding.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QSlider, QLabel, QPushButton, QScrollArea, QGroupBox, QMessageBox,
)
from python_qt_binding.QtCore import Qt, QTimer
import xml.etree.ElementTree as ET
import os
from ament_index_python.packages import get_package_share_directory
import numpy as np


# ---------------------------------------------------------------------------
# Math helpers
# ---------------------------------------------------------------------------
def euler_to_matrix(r, p, y):
    Rx = np.array([[1, 0, 0],
                   [0, np.cos(r), -np.sin(r)],
                   [0, np.sin(r), np.cos(r)]])
    Ry = np.array([[np.cos(p), 0, np.sin(p)],
                   [0, 1, 0],
                   [-np.sin(p), 0, np.cos(p)]])
    Rz = np.array([[np.cos(y), -np.sin(y), 0],
                   [np.sin(y), np.cos(y), 0],
                   [0, 0, 1]])
    return Rz @ Ry @ Rx


def quaternion_from_matrix(matrix):
    q = Quaternion()
    m = matrix
    trace = np.trace(m)
    if trace > 0:
        s = 0.5 / np.sqrt(trace + 1.0)
        q.w = 0.25 / s
        q.x = (m[2, 1] - m[1, 2]) * s
        q.y = (m[0, 2] - m[2, 0]) * s
        q.z = (m[1, 0] - m[0, 1]) * s
    else:
        if m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
            s = 2.0 * np.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2])
            q.w = (m[2, 1] - m[1, 2]) / s
            q.x = 0.25 * s
            q.y = (m[0, 1] + m[1, 0]) / s
            q.z = (m[0, 2] + m[2, 0]) / s
        elif m[1, 1] > m[2, 2]:
            s = 2.0 * np.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2])
            q.w = (m[0, 2] - m[2, 0]) / s
            q.x = (m[0, 1] + m[1, 0]) / s
            q.y = 0.25 * s
            q.z = (m[1, 2] + m[2, 1]) / s
        else:
            s = 2.0 * np.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1])
            q.w = (m[1, 0] - m[0, 1]) / s
            q.x = (m[0, 2] + m[2, 0]) / s
            q.y = (m[1, 2] + m[2, 1]) / s
            q.z = 0.25 * s
    return q


# ---------------------------------------------------------------------------
# Motor ID ↔ joint name (31 body joints)
# ---------------------------------------------------------------------------
MOTOR_ID_TO_JOINT = {
    1: 'head_yaw_joint', 2: 'head_pitch_joint',
    11: 'shoulder_pitch_l_joint', 12: 'shoulder_roll_l_joint',
    13: 'shoulder_yaw_l_joint', 14: 'elbow_pitch_l_joint',
    15: 'elbow_yaw_l_joint', 16: 'wrist_pitch_l_joint', 17: 'wrist_roll_l_joint',
    21: 'shoulder_pitch_r_joint', 22: 'shoulder_roll_r_joint',
    23: 'shoulder_yaw_r_joint', 24: 'elbow_pitch_r_joint',
    25: 'elbow_yaw_r_joint', 26: 'wrist_pitch_r_joint', 27: 'wrist_roll_r_joint',
    31: 'waist_pitch_joint', 32: 'waist_roll_joint', 33: 'waist_yaw_joint',
    51: 'hip_pitch_l_joint', 52: 'hip_roll_l_joint', 53: 'hip_yaw_l_joint',
    54: 'knee_pitch_l_joint', 55: 'ankle_pitch_l_joint', 56: 'ankle_roll_l_joint',
    61: 'hip_pitch_r_joint', 62: 'hip_roll_r_joint', 63: 'hip_yaw_r_joint',
    64: 'knee_pitch_r_joint', 65: 'ankle_pitch_r_joint', 66: 'ankle_roll_r_joint',
}
JOINT_TO_MOTOR_ID = {v: k for k, v in MOTOR_ID_TO_JOINT.items()}

# 手部关节定义（电机 ID → (关节名, 角度上限 rad)）
# ⚠️ 这些关节名当前【不存在于 URDF 中】，因此：
#    1) 不会出现在 joint_limits → GUI 不会为它们创建滑条
#    2) 不下发（SEND_HAND_COMMANDS=False）
#    保留定义是为了后续接入手部模型（命名必须与 URDF 完全一致）。
HAND_JOINTS = {
    'left': {
        1: ('left_little_1_joint', 1.333), 2: ('left_ring_1_joint', 1.333),
        3: ('left_middle_1_joint', 1.333), 4: ('left_index_1_joint', 1.333),
        5: ('left_thumb_2_joint', 0.48), 6: ('left_thumb_1_joint', 1.246165),
    },
    'right': {
        1: ('right_little_1_joint', 1.333), 2: ('right_ring_1_joint', 1.333),
        3: ('right_middle_1_joint', 1.333), 4: ('right_index_1_joint', 1.333),
        5: ('right_thumb_2_joint', 0.48), 6: ('right_thumb_1_joint', 1.246165),
    },
}

FINGER_COUPLING = {
    'left_thumb_2_joint': ['left_thumb_3_joint', 'left_thumb_4_joint'],
    'left_index_1_joint': ['left_index_2_joint'],
    'left_middle_1_joint': ['left_middle_2_joint'],
    'left_ring_1_joint': ['left_ring_2_joint'],
    'left_little_1_joint': ['left_little_2_joint'],
    'right_thumb_2_joint': ['right_thumb_3_joint', 'right_thumb_4_joint'],
    'right_index_1_joint': ['right_index_2_joint'],
    'right_middle_1_joint': ['right_middle_2_joint'],
    'right_ring_1_joint': ['right_ring_2_joint'],
    'right_little_1_joint': ['right_little_2_joint'],
}

HAND_DISPLAY = {
    'left_thumb_1_joint': 'left_thumb_rotation',
    'left_thumb_2_joint': 'left_thumb',
    'left_index_1_joint': 'left_index',
    'left_middle_1_joint': 'left_middle',
    'left_ring_1_joint': 'left_ring',
    'left_little_1_joint': 'left_little',
    'right_thumb_1_joint': 'right_thumb_rotation',
    'right_thumb_2_joint': 'right_thumb',
    'right_index_1_joint': 'right_index',
    'right_middle_1_joint': 'right_middle',
    'right_ring_1_joint': 'right_ring',
    'right_little_1_joint': 'right_little',
}

GROUPS = {
    "Head": ['head_yaw_joint', 'head_pitch_joint'],
    "Waist": ['waist_pitch_joint', 'waist_roll_joint', 'waist_yaw_joint'],
    "Left Arm": ['shoulder_pitch_l_joint', 'shoulder_roll_l_joint',
                 'shoulder_yaw_l_joint', 'elbow_pitch_l_joint',
                 'elbow_yaw_l_joint', 'wrist_pitch_l_joint', 'wrist_roll_l_joint'],
    "Right Arm": ['shoulder_pitch_r_joint', 'shoulder_roll_r_joint',
                  'shoulder_yaw_r_joint', 'elbow_pitch_r_joint',
                  'elbow_yaw_r_joint', 'wrist_pitch_r_joint', 'wrist_roll_r_joint'],
    "Left Leg": ['hip_pitch_l_joint', 'hip_roll_l_joint', 'hip_yaw_l_joint',
                 'knee_pitch_l_joint', 'ankle_pitch_l_joint', 'ankle_roll_l_joint'],
    "Right Leg": ['hip_pitch_r_joint', 'hip_roll_r_joint', 'hip_yaw_r_joint',
                  'knee_pitch_r_joint', 'ankle_pitch_r_joint', 'ankle_roll_r_joint'],
    "Left Hand": ['left_little_1_joint', 'left_ring_1_joint', 'left_middle_1_joint',
                  'left_index_1_joint', 'left_thumb_1_joint', 'left_thumb_2_joint'],
    "Right Hand": ['right_little_1_joint', 'right_ring_1_joint', 'right_middle_1_joint',
                   'right_index_1_joint', 'right_thumb_1_joint', 'right_thumb_2_joint'],
}

# 是否在点击 Execute 时一并下发手部指令。
#
# 当前状态: URDF 中【没有任何手部 link/joint】（meshes_hand/ 为预留资产，
# 未接入），因此：
#   - joint_limits 中不含手部关节 → GUI 不会为手部创建滑条；
#   - 手部关节在 joint_positions 中仅有初始值 0.0 / 或有状态时的同步值。
# 若无条件下发，在【未收到手部状态或未同步】时会把 rad=0.0 换算成
# 归一化 1.0（= 完全张开）发给真机，属于非预期的运动指令。
#
# 因此默认关闭。等你接入手部模型（见 docs/model.md#手部模型接入预留）、
# 并确认 /inspire_hand/state/* 正常后，再改为 True。
SEND_HAND_COMMANDS = False


# ---------------------------------------------------------------------------
# ROS node
# ---------------------------------------------------------------------------
class InteractiveGuiNode(Node):
    def __init__(self):
        super().__init__('interactive_gui_node')
        self.is_robot_online = False

        self.ghost_pub = self.create_publisher(JointState, 'ghost/joint_states', 10)
        self.marker_pub = self.create_publisher(MarkerArray, 'ghost/markers', 10)

        # Command publishers (bodyctrl_msgs, same topics as ros_pro_tf)
        self.head_cmd_pub = self.create_publisher(
            CmdSetMotorPosition, '/head/cmd_pos', 10)
        self.waist_cmd_pub = self.create_publisher(
            CmdSetMotorPosition, '/waist/cmd_pos', 10)
        self.arm_cmd_pub = self.create_publisher(
            CmdSetMotorPosition, '/arm/cmd_pos', 10)
        self.leg_cmd_pub = self.create_publisher(
            CmdSetMotorPosition, '/leg/cmd_pos', 10)
        self.left_hand_pub = self.create_publisher(
            JointState, '/inspire_hand/ctrl/left_hand', 10)
        self.right_hand_pub = self.create_publisher(
            JointState, '/inspire_hand/ctrl/right_hand', 10)

        self.status_sub = self.create_subscription(
            Bool, '/robot_online_status', self.status_callback, 10)
        self.real_joint_sub = self.create_subscription(
            JointState, 'joint_states', self.real_joint_callback, 10)
        self.real_joint_states = {}

        self.joint_limits = {}
        self.joint_positions = {}
        self.links = {}
        self.joints = {}
        self.child_to_parent = {}

        self._load_urdf()

        # Init hand joints explicitly
        for side in HAND_JOINTS.values():
            for _, (jname, _) in side.items():
                if jname not in self.joint_positions:
                    self.joint_positions[jname] = 0.0

        self.publish_ghost()
        self.timer = self.create_timer(0.1, self.publish_ghost)
        self.conn_timer = self.create_timer(1.0, self.log_connection_status)

    def status_callback(self, msg):
        self.is_robot_online = msg.data

    def log_connection_status(self):
        if not self.is_robot_online:
            self.get_logger().warn('无法连接到真实机器人...')

    def real_joint_callback(self, msg):
        for name, pos in zip(msg.name, msg.position):
            self.real_joint_states[name] = pos

    def sync_to_real(self):
        for name, pos in self.real_joint_states.items():
            if name in self.joint_positions:
                self.joint_positions[name] = pos
        self.publish_ghost()

    # ---- URDF ----
    def _load_urdf(self):
        try:
            pkg_path = get_package_share_directory('tiangong3_urdf')
            urdf_path = os.path.join(pkg_path, 'urdf', 'tiangong3.urdf')
            tree = ET.parse(urdf_path)
            root = tree.getroot()

            for joint in root.findall('joint'):
                name = joint.get('name')
                joint_type = joint.get('type')
                parent = joint.find('parent').get('link')
                child = joint.find('child').get('link')

                origin = joint.find('origin')
                xyz = [0.0, 0.0, 0.0]
                rpy = [0.0, 0.0, 0.0]
                if origin is not None:
                    xyz = [float(x) for x in origin.get('xyz', '0 0 0').split()]
                    rpy = [float(x) for x in origin.get('rpy', '0 0 0').split()]

                axis = [1.0, 0.0, 0.0]
                if joint_type in ['revolute', 'continuous', 'prismatic']:
                    axis_elem = joint.find('axis')
                    if axis_elem is not None:
                        axis = [float(x) for x in
                                axis_elem.get('xyz', '1 0 0').split()]

                self.joints[name] = {
                    'parent': parent, 'child': child,
                    'origin_xyz': xyz, 'origin_rpy': rpy,
                    'axis': axis, 'type': joint_type,
                }
                self.child_to_parent[child] = (parent, name)

                limit = joint.find('limit')
                if limit is not None:
                    lower = float(limit.get('lower', -3.14))
                    upper = float(limit.get('upper', 3.14))
                    self.joint_limits[name] = (lower, upper)
                    if name not in self.joint_positions:
                        self.joint_positions[name] = 0.0

            for link in root.findall('link'):
                link_name = link.get('name')
                self.links[link_name] = []
                for visual in link.findall('visual'):
                    geometry = visual.find('geometry')
                    if geometry is not None:
                        mesh = geometry.find('mesh')
                        if mesh is not None:
                            mesh_path = mesh.get('filename')
                            origin = visual.find('origin')
                            xyz = [0.0, 0.0, 0.0]
                            rpy = [0.0, 0.0, 0.0]
                            if origin is not None:
                                xyz = [float(x) for x in
                                       origin.get('xyz', '0 0 0').split()]
                                rpy = [float(x) for x in
                                       origin.get('rpy', '0 0 0').split()]
                            self.links[link_name].append((mesh_path, xyz, rpy))
        except Exception as e:
            self.get_logger().error(f'Failed to load URDF: {e}')

    # ---- FK ----
    def get_transform(self, joint_info, theta):
        xyz = joint_info['origin_xyz']
        rpy = joint_info['origin_rpy']
        axis = np.array(joint_info['axis'])
        j_type = joint_info['type']

        R_origin = euler_to_matrix(rpy[0], rpy[1], rpy[2])
        T_origin = np.eye(4)
        T_origin[:3, :3] = R_origin
        T_origin[:3, 3] = xyz

        T_joint = np.eye(4)
        if j_type in ['revolute', 'continuous']:
            c = np.cos(theta)
            s = np.sin(theta)
            K = np.array([[0, -axis[2], axis[1]],
                          [axis[2], 0, -axis[0]],
                          [-axis[1], axis[0], 0]])
            R_joint = np.eye(3) + s * K + (1 - c) * (K @ K)
            T_joint[:3, :3] = R_joint

        return T_origin @ T_joint

    def calculate_fk(self):
        link_transforms = {'pelvis': np.eye(4)}

        def get_link_transform_recursive(link_name):
            if link_name in link_transforms:
                return link_transforms[link_name]
            if link_name not in self.child_to_parent:
                return np.eye(4)
            parent, joint_name = self.child_to_parent[link_name]
            parent_T = get_link_transform_recursive(parent)
            joint_info = self.joints[joint_name]
            theta = self.joint_positions.get(joint_name, 0.0)
            T_rel = self.get_transform(joint_info, theta)
            T_global = parent_T @ T_rel
            link_transforms[link_name] = T_global
            return T_global

        for link_name in self.links.keys():
            get_link_transform_recursive(link_name)
        return link_transforms

    def publish_ghost(self):
        link_transforms = self.calculate_fk()
        ma_msg = MarkerArray()
        zero_stamp = rclpy.time.Time().to_msg()
        idx = 0

        for link_name, visuals in self.links.items():
            if link_name not in link_transforms:
                continue
            T_link_global = link_transforms[link_name]
            for mesh_path, xyz, rpy in visuals:
                marker = Marker()
                marker.header.frame_id = 'pelvis'
                marker.header.stamp = zero_stamp
                marker.ns = 'ghost'
                marker.id = idx
                idx += 1
                marker.type = Marker.MESH_RESOURCE
                marker.action = Marker.ADD
                marker.mesh_resource = mesh_path

                R_visual = euler_to_matrix(rpy[0], rpy[1], rpy[2])
                T_visual = np.eye(4)
                T_visual[:3, :3] = R_visual
                T_visual[:3, 3] = xyz

                T_final = T_link_global @ T_visual
                marker.pose.position.x = T_final[0, 3]
                marker.pose.position.y = T_final[1, 3]
                marker.pose.position.z = T_final[2, 3]
                q = quaternion_from_matrix(T_final[:3, :3])
                marker.pose.orientation = q

                marker.scale.x = 1.0
                marker.scale.y = 1.0
                marker.scale.z = 1.0
                marker.color.r = 0.0
                marker.color.g = 1.0
                marker.color.b = 1.0
                marker.color.a = 0.6
                ma_msg.markers.append(marker)

        self.marker_pub.publish(ma_msg)

    # ---- Execute ----
    def execute_commands(self):
        self.get_logger().info('Executing commands...')
        now = self.get_clock().now().to_msg()

        def build_cmd(joint_list):
            msg = CmdSetMotorPosition()
            msg.header.stamp = now
            for jn in joint_list:
                if jn in JOINT_TO_MOTOR_ID:
                    cmd = SetMotorPosition()
                    cmd.name = JOINT_TO_MOTOR_ID[jn]
                    cmd.pos = float(self.joint_positions[jn])
                    # 注意: spd 的单位以 bodyctrl_msgs/SetMotorPosition.msg 的
                    # 协议定义为准（该文件标注为 rpm）。此处曾注释为 rad/s，
                    # 与协议不一致，故不再断言单位；实际语义请与固件确认。
                    cmd.spd = 0.2
                    cmd.cur = 8.0  # current limit A
                    msg.cmds.append(cmd)
            return msg

        self.head_cmd_pub.publish(build_cmd(GROUPS['Head']))
        self.waist_cmd_pub.publish(build_cmd(GROUPS['Waist']))
        self.arm_cmd_pub.publish(
            build_cmd(GROUPS['Left Arm'] + GROUPS['Right Arm']))
        self.leg_cmd_pub.publish(
            build_cmd(GROUPS['Left Leg'] + GROUPS['Right Leg']))

        # Hands
        # 默认不下发手部指令（见模块常量 SEND_HAND_COMMANDS 的说明）：
        # 当前 URDF 未接入手部 link，GUI 中也没有手部滑条，故 hand 关节的
        # 目标值只是 joint_positions 里的初始值/同步值。若无条件下发，
        # 在未收到手部状态时会把"归一化 1.0（完全张开）"发给真机。
        if SEND_HAND_COMMANDS:
            for side in ('left', 'right'):
                msg = JointState()
                msg.header.stamp = now
                msg.name = ['1', '2', '3', '4', '5', '6']
                positions = [0.0] * 6
                for motor_id, (jname, limit) in HAND_JOINTS[side].items():
                    rad = self.joint_positions.get(jname, 0.0)
                    percentage = 1.0 - (rad / limit)
                    positions[motor_id - 1] = percentage
                msg.position = positions
                if side == 'left':
                    self.left_hand_pub.publish(msg)
                else:
                    self.right_hand_pub.publish(msg)
        else:
            self.get_logger().debug(
                'SEND_HAND_COMMANDS=False，本次未下发手部指令')


# ---------------------------------------------------------------------------
# Qt GUI
# ---------------------------------------------------------------------------
class RobotControlGui(QMainWindow):
    def __init__(self, node: InteractiveGuiNode):
        super().__init__()
        self.node = node
        self.setWindowTitle('Tiangong Dex - Robot Joint Control')
        self.resize(650, 900)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)

        self.sliders = {}
        self.joint_labels = {}

        for group_name, joint_names in GROUPS.items():
            group_box = QGroupBox(group_name)
            group_layout = QVBoxLayout()
            is_hand = 'Hand' in group_name
            n_sliders = 0

            for jname in joint_names:
                if jname not in self.node.joint_limits:
                    continue
                n_sliders += 1
                lower, upper = self.node.joint_limits[jname]

                h_layout = QHBoxLayout()
                display_name = HAND_DISPLAY.get(jname, jname)
                if is_hand:
                    label = QLabel(f'{display_name}: 1.00')
                else:
                    label = QLabel(f'{display_name}: 0.00')
                slider = QSlider(Qt.Horizontal)
                slider.setMinimum(-1000)
                slider.setMaximum(1000)
                slider.setValue(1000 if is_hand else 0)

                def make_callback(name, lbl, gname):
                    def callback(val):
                        low, upp = self.node.joint_limits[name]
                        is_h = 'Hand' in gname
                        if is_h:
                            ratio = (1000 - val) / 2000.0
                            pos = low + ratio * (upp - low)
                            self.node.joint_positions[name] = pos
                            display_n = HAND_DISPLAY.get(name, name)
                            lbl.setText(f'{display_n}: {1.0 - ratio:.2f}')
                            if name in FINGER_COUPLING:
                                for follower in FINGER_COUPLING[name]:
                                    if follower in self.node.joint_limits:
                                        f_low, f_upp = self.node.joint_limits[follower]
                                        f_pos = f_low + ratio * (f_upp - f_low)
                                        self.node.joint_positions[follower] = f_pos
                        else:
                            ratio = (val + 1000) / 2000.0
                            pos = low + ratio * (upp - low)
                            self.node.joint_positions[name] = pos
                            lbl.setText(f'{name}: {pos:.2f}')
                        self.node.publish_ghost()
                    return callback

                slider.valueChanged.connect(make_callback(jname, label, group_name))
                h_layout.addWidget(label)
                h_layout.addWidget(slider)
                group_layout.addLayout(h_layout)
                self.sliders[jname] = slider
                self.joint_labels[jname] = label

            if n_sliders == 0:
                # 该组的所有关节都不在 URDF 中（当前即 Left/Right Hand），
                # 跳过整个分组框，避免界面上出现两个空框。
                continue

            group_box.setLayout(group_layout)
            self.scroll_layout.addWidget(group_box)

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        btn_layout = QHBoxLayout()
        self.btn_sync = QPushButton('Sync to Real')
        self.btn_sync.clicked.connect(self.sync_sliders_to_real)
        btn_layout.addWidget(self.btn_sync)
        self.btn_execute = QPushButton('Execute')
        self.btn_execute.clicked.connect(self.confirm_and_execute)
        btn_layout.addWidget(self.btn_execute)
        self.btn_print = QPushButton('Print Joint Values')
        self.btn_print.clicked.connect(self.print_joint_values)
        btn_layout.addWidget(self.btn_print)
        layout.addLayout(btn_layout)

        self.ros_timer = QTimer()
        self.ros_timer.timeout.connect(self.spin_ros)
        self.ros_timer.start(10)

    def spin_ros(self):
        if not rclpy.ok():
            self.ros_timer.stop()
            self.close()
            return
        try:
            rclpy.spin_once(self.node, timeout_sec=0)
            current = self.node.is_robot_online
            if getattr(self, 'last_status', None) != current:
                self.last_status = current
                status_text = 'CONNECTED' if current else 'DISCONNECTED'
                self.setWindowTitle(
                    f'Tiangong Dex - Robot Joint Control - [{status_text}]')
                self.btn_sync.setEnabled(current)
                self.btn_execute.setEnabled(current)
        except (KeyboardInterrupt, Exception):
            self.ros_timer.stop()
            QApplication.quit()

    def closeEvent(self, event):
        self.ros_timer.stop()
        event.accept()

    def sync_sliders_to_real(self):
        self.node.sync_to_real()
        for jname, slider in self.sliders.items():
            if jname in self.node.joint_positions:
                pos = self.node.joint_positions[jname]
                low, upp = self.node.joint_limits[jname]
                if abs(upp - low) > 1e-6:
                    is_hand = any(k in jname.lower() for k in
                                  ('hand', 'thumb', 'index', 'middle', 'ring', 'little'))
                    if is_hand:
                        ratio = (pos - low) / (upp - low)
                        val = int(1000 - ratio * 2000)
                    else:
                        val = int((pos - low) / (upp - low) * 2000 - 1000)
                    slider.blockSignals(True)
                    slider.setValue(val)
                    slider.blockSignals(False)
                    if jname in self.joint_labels:
                        display_name = HAND_DISPLAY.get(jname, jname)
                        if is_hand:
                            lbl_val = 1.0 - (pos - low) / (upp - low)
                            self.joint_labels[jname].setText(
                                f'{display_name}: {lbl_val:.2f}')
                        else:
                            self.joint_labels[jname].setText(
                                f'{jname}: {pos:.2f}')

    def confirm_and_execute(self):
        if not self.node.is_robot_online:
            QMessageBox.warning(
                self, '未连接',
                '当前未连接到真实机器人，无法执行指令。\n请检查机器人连接。',
                QMessageBox.Ok)
            return
        reply = QMessageBox.warning(
            self, '！！安全确认！！',
            '当前操作将会真实【移动】机器人，轨迹和目标点均存在【碰撞】风险。\n'
            '请在确认周边环境安全的情况下点击 Yes 开始执行。',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.node.execute_commands()

    def print_joint_values(self):
        print('\n--- Current Joint Positions ---')
        for jname in sorted(self.node.joint_positions.keys()):
            pos = self.node.joint_positions[jname]
            print(f'{jname}: {pos:.4f}')
        print('-------------------------------\n', flush=True)


def main():
    try:
        rclpy.init()
        node = InteractiveGuiNode()
        app = QApplication(sys.argv)
        gui = RobotControlGui(node)
        gui.sync_sliders_to_real()
        gui.show()
        exit_code = app.exec_()
        node.destroy_node()
        rclpy.shutdown()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f'Error in main: {e}')


if __name__ == '__main__':
    main()
