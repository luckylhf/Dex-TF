#!/usr/bin/env python3
# Copyright 2026 Walker Tienkung Dex Project Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# 从 URDF 生成 docs/joints.md（关节限位表 / 电机 ID 映射表）。
#
# 用法:
#   python3 scripts/gen_joint_docs.py                     # 写入 docs/joints.md
#   python3 scripts/gen_joint_docs.py --check             # 只校验是否与文档一致
#   python3 scripts/gen_joint_docs.py -m path/to/model.urdf -o docs/joints.md

import argparse
import math
import os
import sys
import xml.etree.ElementTree as ET

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_URDF = os.path.join(
    REPO_ROOT, 'src', 'tiangong3_urdf', 'urdf', 'tiangong3.urdf')
DEFAULT_OUT = os.path.join(REPO_ROOT, 'docs', 'joints.md')

# 电机 ID → 关节名（与 scripts/joint_state_publisher.py 保持一致）
MOTOR_ID_TO_JOINT = {
    1: 'head_yaw_joint', 2: 'head_pitch_joint',
    11: 'shoulder_pitch_l_joint', 12: 'shoulder_roll_l_joint',
    13: 'shoulder_yaw_l_joint', 14: 'elbow_pitch_l_joint',
    15: 'elbow_yaw_l_joint', 16: 'wrist_pitch_l_joint',
    17: 'wrist_roll_l_joint',
    21: 'shoulder_pitch_r_joint', 22: 'shoulder_roll_r_joint',
    23: 'shoulder_yaw_r_joint', 24: 'elbow_pitch_r_joint',
    25: 'elbow_yaw_r_joint', 26: 'wrist_pitch_r_joint',
    27: 'wrist_roll_r_joint',
    31: 'waist_pitch_joint', 32: 'waist_roll_joint', 33: 'waist_yaw_joint',
    51: 'hip_pitch_l_joint', 52: 'hip_roll_l_joint', 53: 'hip_yaw_l_joint',
    54: 'knee_pitch_l_joint', 55: 'ankle_pitch_l_joint',
    56: 'ankle_roll_l_joint',
    61: 'hip_pitch_r_joint', 62: 'hip_roll_r_joint', 63: 'hip_yaw_r_joint',
    64: 'knee_pitch_r_joint', 65: 'ankle_pitch_r_joint',
    66: 'ankle_roll_r_joint',
}

JOINT_TO_MOTOR_ID = {v: k for k, v in MOTOR_ID_TO_JOINT.items()}

# 展示分组（顺序即文档顺序）
GROUPS = [
    ('左腿', ['hip_pitch_l_joint', 'hip_roll_l_joint', 'hip_yaw_l_joint',
              'knee_pitch_l_joint', 'ankle_pitch_l_joint',
              'ankle_roll_l_joint']),
    ('右腿', ['hip_pitch_r_joint', 'hip_roll_r_joint', 'hip_yaw_r_joint',
              'knee_pitch_r_joint', 'ankle_pitch_r_joint',
              'ankle_roll_r_joint']),
    ('腰部', ['waist_yaw_joint', 'waist_roll_joint', 'waist_pitch_joint']),
    ('头部', ['head_yaw_joint', 'head_pitch_joint']),
    ('左臂', ['shoulder_pitch_l_joint', 'shoulder_roll_l_joint',
              'shoulder_yaw_l_joint', 'elbow_pitch_l_joint',
              'elbow_yaw_l_joint', 'wrist_pitch_l_joint',
              'wrist_roll_l_joint']),
    ('右臂', ['shoulder_pitch_r_joint', 'shoulder_roll_r_joint',
              'shoulder_yaw_r_joint', 'elbow_pitch_r_joint',
              'elbow_yaw_r_joint', 'wrist_pitch_r_joint',
              'wrist_roll_r_joint']),
]


def fmt(value, ndigits=6):
    """去掉浮点尾巴，保持可读。"""
    if value is None:
        return '-'
    out = f'{value:.{ndigits}f}'.rstrip('0').rstrip('.')
    return out if out not in ('', '-0') else '0'


def deg(rad):
    return fmt(math.degrees(rad), 2)


def parse_model(path):
    root = ET.parse(path).getroot()
    joints = {}
    for joint in root.findall('joint'):
        name = joint.get('name')
        limit = joint.find('limit')
        axis = joint.find('axis')
        origin = joint.find('origin')
        joints[name] = {
            'name': name,
            'type': joint.get('type'),
            'parent': joint.find('parent').get('link'),
            'child': joint.find('child').get('link'),
            'axis': axis.get('xyz') if axis is not None else '-',
            'xyz': origin.get('xyz') if origin is not None else '-',
            'rpy': origin.get('rpy') if origin is not None else '-',
            'lower': float(limit.get('lower')) if limit is not None
                     and limit.get('lower') is not None else None,
            'upper': float(limit.get('upper')) if limit is not None
                     and limit.get('upper') is not None else None,
            'effort': float(limit.get('effort')) if limit is not None
                      and limit.get('effort') is not None else None,
            'velocity': float(limit.get('velocity')) if limit is not None
                        and limit.get('velocity') is not None else None,
        }
    total_mass = 0.0
    for link in root.findall('link'):
        inertial = link.find('inertial')
        if inertial is not None:
            mass = inertial.find('mass')
            if mass is not None:
                total_mass += float(mass.get('value'))
    # 根 link = 从未作为 child 出现的 link
    children = {j['child'] for j in joints.values()}
    roots = [link.get('name') for link in root.findall('link')
             if link.get('name') not in children]
    return {
        'robot_name': root.get('name'),
        'root': roots[0] if roots else '-',
        'links': root.findall('link'),
        'joints': joints,
        'n_links': len(root.findall('link')),
        'n_joints': len(root.findall('joint')),
        'total_mass': total_mass,
    }


def render(model, urdf_rel, xacro_rel):
    joints = model['joints']
    revolute = [j for j in joints.values() if j['type'] != 'fixed']
    fixed = [j for j in joints.values() if j['type'] == 'fixed']

    out = []
    add = out.append
    add('# 关节规格与电机 ID 映射表\n')
    add('> 本文件由 [`scripts/gen_joint_docs.py`](../scripts/gen_joint_docs.py) '
        '从\n> `{}` 自动生成，**请勿手工编辑**。\n'.format(urdf_rel))
    add('## 0. 模型概要\n')
    add('| 项目 | 数值 |')
    add('|------|------|')
    add(f'| robot 名称 | `{model["robot_name"]}` |')
    add(f'| 根 link | `{model["root"]}` |')
    add(f'| link 总数 | {model["n_links"]} |')
    add(f'| joint 总数 | {model["n_joints"]} '
        f'（revolute {len(revolute)} + fixed {len(fixed)}） |')
    add(f'| 模型总质量 | {fmt(model["total_mass"], 3)} kg |')
    add('| 长度单位 | m |')
    add('| 角度单位 | rad |')
    add('')
    add(f'模型文件：`{urdf_rel}`（GUI / 桥接节点解析用）、'
        f'`{xacro_rel}`（launch 默认加载）。')
    add('两份文件的几何完全一致，部分关节限位不同，见 '
        '[`model.md`](model.md#两套模型文件的差异)。\n')

    add('## 1. 电机 ID ↔ 关节名映射\n')
    add('| 部位 | 电机 ID | 关节名 |')
    add('|------|---------|--------|')
    part_labels = [
        ('头部', [1, 2]),
        ('腰部', [31, 32, 33]),
        ('左臂', list(range(11, 18))),
        ('右臂', list(range(21, 28))),
        ('左腿', list(range(51, 57))),
        ('右腿', list(range(61, 67))),
    ]
    for label, ids in part_labels:
        for i, motor_id in enumerate(ids):
            joint = MOTOR_ID_TO_JOINT[motor_id]
            add(f'| {label if i == 0 else ""} | {motor_id} | `{joint}` |')
    add('')
    add('> 灵巧手为独立控制器，ID 与关节名映射如下（归一化角度 0–1，'
        '`1.0` 为完全张开）：\n')
    add('| 手 | 电机 ID | 关节名 | 角度上限 (rad) |')
    add('|----|---------|--------|----------------|')
    hand = [
        (1, 'little_1_joint', '1.333'), (2, 'ring_1_joint', '1.333'),
        (3, 'middle_1_joint', '1.333'), (4, 'index_1_joint', '1.333'),
        (5, 'thumb_2_joint', '0.48'), (6, 'thumb_1_joint', '1.246165'),
    ]
    for side, prefix in (('左手', 'left'), ('右手', 'right')):
        for motor_id, suffix, limit in hand:
            add(f'| {side} | {motor_id} | `{prefix}_{suffix}` | {limit} |')
    add('')

    add('## 2. revolute 关节限位表\n')
    add('> 数据来源：`{}`。`下限 / 上限` 同时给出弧度与角度制值。\n'
        .format(urdf_rel))
    for group_name, joint_names in GROUPS:
        add(f'### {group_name}\n')
        add('| 关节 | 电机 ID | 父 link | 子 link | 轴向 | 下限 (rad) | '
            '上限 (rad) | 下限 (°) | 上限 (°) | 力矩 (N·m) | 速度 (rad/s) |')
        add('|------|---------|---------|---------|------|-----------|'
            '-----------|----------|----------|------------|--------------|')
        for name in joint_names:
            j = joints.get(name)
            if j is None:
                add(f'| `{name}` | - | **缺失** | | | | | | | | |')
                continue
            motor_id = JOINT_TO_MOTOR_ID.get(name, '-')
            add('| `{}` | {} | `{}` | `{}` | `{}` | {} | {} | {} | {} | {} | {} |'
                .format(name, motor_id, j['parent'], j['child'], j['axis'],
                        fmt(j['lower']), fmt(j['upper']),
                        deg(j['lower']), deg(j['upper']),
                        fmt(j['effort'], 1), fmt(j['velocity'])))
        add('')

    add('## 3. fixed（固定）关节表\n')
    add('| 关节 | 父 link | 子 link | origin xyz (m) | origin rpy (rad) |')
    add('|------|---------|---------|----------------|------------------|')
    for j in fixed:
        add('| `{}` | `{}` | `{}` | `{}` | `{}` |'
            .format(j['name'], j['parent'], j['child'], j['xyz'], j['rpy']))
    add('')

    add('## 4. TF 树结构\n')
    add('```text')
    lines = []

    def walk(link, depth):
        lines.append('  ' * depth + link)
        for j in joints.values():
            if j['parent'] == link:
                kind = 'F' if j['type'] == 'fixed' else 'R'
                lines.append('  ' * (depth + 1) + f'└─[{kind}] {j["name"]}')
                walk(j['child'], depth + 2)

    walk(model['root'], 0)
    add('\n'.join(lines))
    add('```')
    add('')
    add('> `[R]` = revolute（31 个，会随 `/joint_states` 变化），'
        '`[F]` = fixed（7 个，静态变换）。')
    add('')
    return '\n'.join(out)


def main():
    parser = argparse.ArgumentParser(
        description='从 URDF 生成 docs/joints.md')
    parser.add_argument('-m', '--model', default=DEFAULT_URDF,
                        help='输入 URDF 路径')
    parser.add_argument('-o', '--output', default=DEFAULT_OUT,
                        help='输出 Markdown 路径')
    parser.add_argument('--check', action='store_true',
                        help='仅校验输出是否与磁盘上的文档一致（CI 用）')
    args = parser.parse_args()

    model = parse_model(args.model)
    content = render(model,
                     os.path.relpath(args.model, REPO_ROOT).replace(os.sep, '/'),
                     'src/tiangong3_urdf/urdf/tiangong3.urdf.xacro')

    if args.check:
        if not os.path.exists(args.output):
            print(f'[FAIL] 文档不存在: {args.output}', file=sys.stderr)
            return 1
        with open(args.output, encoding='utf-8') as fh:
            if fh.read() != content:
                print(f'[FAIL] {args.output} 与生成的表格不一致，'
                      f'请运行 scripts/gen_joint_docs.py 重新生成', file=sys.stderr)
                return 1
        print(f'[ OK ] {args.output} 与模型一致')
        return 0

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as fh:
        fh.write(content)
    print(f'[ OK ] 已生成 {args.output} '
          f'({model["n_links"]} links / {model["n_joints"]} joints)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
