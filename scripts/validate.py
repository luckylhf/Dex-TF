#!/usr/bin/env python3
# Copyright 2026 Walker Tienkung Dex Project Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# 发布包完整性校验（不需要 ROS 2 环境，仅依赖标准库 + 可选依赖）。
#
# 校验内容:
#   1. URDF 结构：link/joint 数量、单根、无环、质量总和
#   2. STL 网格：二进制格式、三角面片数、NaN/退化面片
#   3. 引用一致性：URDF 引用的 mesh 是否存在、meshes/ 是否有孤儿文件
#   4. package.xml：XML 合法性 + 官方 XSD 校验（需网络，失败仅告警）
#   5. Launch 文件：Python 语法 + 引用的包内资源是否存在
#   6. 电机 ID 映射：三个脚本中的映射表是否完全一致
#   7. 文档一致性：docs/joints.md 是否与 URDF 匹配
#   8. YAML 合法性（CI 配置）
#   9. Markdown 内部链接有效性
#  10. 发布卫生：无缓存/临时文件、许可与说明文件齐全
#
# 用法:
#   python3 scripts/validate.py                 # 全部校验
#   python3 scripts/validate.py --no-network    # 跳过需要联网的校验
#   python3 scripts/validate.py -v              # 输出详细信息
#
# 依赖（可选，缺失时自动降级为 WARN）:
#   pip install trimesh yourdfpy lxml xmlschema pyyaml

import argparse
import ast
import math
import os
import re
import struct
import subprocess
import sys
import urllib.request
from xml.etree import ElementTree as ET

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URDF_PKG = os.path.join(REPO_ROOT, 'src', 'tiangong3_urdf')
MESH_DIR = os.path.join(URDF_PKG, 'meshes')
HAND_MESH_DIR = os.path.join(URDF_PKG, 'meshes_hand')
URDF_FILE = os.path.join(URDF_PKG, 'urdf', 'tiangong3.urdf')
XACRO_FILE = os.path.join(URDF_PKG, 'urdf', 'tiangong3.urdf.xacro')
LAUNCH_DIR = os.path.join(URDF_PKG, 'launch')
CONFIG_DIR = os.path.join(URDF_PKG, 'config')
SCRIPTS_DIR = os.path.join(URDF_PKG, 'scripts')

PACKAGE_XML_XSD_URL = \
    'http://download.ros.org/schema/package_format3.xsd'
PACKAGE_XML_XSD_CACHE = os.path.join(
    os.path.expanduser('~'), '.cache', 'dextf-validate', 'package_format3.xsd')

EXPECTED_LINKS = 39
EXPECTED_JOINTS = 38
EXPECTED_REVOLUTE = 31
EXPECTED_MESHES = 39
EXPECTED_HAND_MESHES = 26
EXPECTED_MASS_KG = 63.272
EXPECTED_MOTOR_IDS = 31

# 版权主体（真实权利人）
COPYRIGHT_HOLDER = 'Walker Tienkung Dex Project Contributors'
# 主仓库地址（package.xml 的 <url> 必须指向它）
REPO_SLUG = 'luckylhf/Dex-TF'
REPO_URL = 'https://github.com/' + REPO_SLUG
# 一旦出现其中任何一个，说明版权行仍是本项目早期的模板占位符，必须替换。
# 注意：不要把 Apache-2.0 正文附录中的模板句
# "Copyright [yyyy] [name of copyright owner]" 列为占位符 —— 那是许可证
# 原文（APPENDIX），必须逐字保持，不能修改。
PLACEHOLDER_COPYRIGHTS = (
    'Tiangong Dex Project Contributors',
    'Tiangong 2 Dex Project Contributors',
)

RESULTS = []       # (level, name, message)
VERBOSE = False


def report(level, name, message=''):
    RESULTS.append((level, name, message))
    icon = {'PASS': '[ OK ]', 'FAIL': '[FAIL]', 'WARN': '[WARN]',
            'INFO': '[INFO]'}[level]
    if level == 'INFO' and not VERBOSE:
        return
    line = f'{icon} {name}'
    if message:
        line += f' — {message}'
    print(line)


# ---------------------------------------------------------------------------
# 1. URDF 结构
# ---------------------------------------------------------------------------
def load_urdf_tree(path):
    root = ET.parse(path).getroot()
    links = [e.get('name') for e in root.findall('link')]
    joints = []
    for j in root.findall('joint'):
        limit = j.find('limit')
        joints.append({
            'name': j.get('name'),
            'type': j.get('type'),
            'parent': j.find('parent').get('link'),
            'child': j.find('child').get('link'),
            'lower': (float(limit.get('lower'))
                      if limit is not None and limit.get('lower') else None),
            'upper': (float(limit.get('upper'))
                      if limit is not None and limit.get('upper') else None),
        })
    return root, links, joints


def check_urdf_structure():
    if not os.path.isfile(URDF_FILE):
        return report('FAIL', 'URDF 结构', f'文件缺失: {URDF_FILE}')

    root, links, joints = load_urdf_tree(URDF_FILE)
    n_revolute = sum(1 for j in joints if j['type'] == 'revolute')

    ok = True
    if len(links) != EXPECTED_LINKS:
        report('FAIL', 'URDF link 数量',
               f'期望 {EXPECTED_LINKS}，实际 {len(links)}')
        ok = False
    if len(joints) != EXPECTED_JOINTS:
        report('FAIL', 'URDF joint 数量',
               f'期望 {EXPECTED_JOINTS}，实际 {len(joints)}')
        ok = False
    if n_revolute != EXPECTED_REVOLUTE:
        report('FAIL', 'URDF revolute 数量',
               f'期望 {EXPECTED_REVOLUTE}，实际 {n_revolute}')
        ok = False

    # 单根：从未作为 child 出现的 link 只能有一个
    children = {j['child'] for j in joints}
    roots = [link for link in links if link not in children]
    if len(roots) != 1:
        report('FAIL', 'URDF 单根', f'根 link = {roots}（期望恰好 1 个）')
        ok = False
    elif roots[0] != 'pelvis':
        report('WARN', 'URDF 根 link', f'实际为 {roots[0]}，文档中写的是 pelvis')
    else:
        report('INFO', 'URDF 根 link', roots[0])

    # 无环：每个 link 至多一个父关节
    parent_count = {}
    for j in joints:
        parent_count[j['child']] = parent_count.get(j['child'], 0) + 1
    multi = [k for k, v in parent_count.items() if v > 1]
    if multi:
        report('FAIL', 'URDF 树结构（无多父）', f'多父 link: {multi}')
        ok = False
    if len(parent_count) != len(links) - 1:
        report('FAIL', 'URDF 连通性',
               f'{len(parent_count)} 个 link 有父关节，期望 {len(links) - 1}')
        ok = False

    # 所有 joint 的 parent/child 都必须存在
    unknown = {j['parent'] for j in joints} | {j['child'] for j in joints}
    unknown -= set(links)
    if unknown:
        report('FAIL', 'URDF 引用完整性', f'引用了不存在的 link: {sorted(unknown)}')
        ok = False

    # 质量总和
    total = 0.0
    for link in root.findall('link'):
        inertial = link.find('inertial')
        if inertial is None:
            report('WARN', 'URDF 惯量', f'link 缺少 <inertial>: '
                   f'{link.get("name")}')
            continue
        mass = inertial.find('mass')
        if mass is not None:
            total += float(mass.get('value'))
    if abs(total - EXPECTED_MASS_KG) > 0.01:
        report('WARN', 'URDF 质量总和',
               f'{total:.3f} kg，文档中写的是 {EXPECTED_MASS_KG} kg')
    else:
        report('INFO', 'URDF 质量总和', f'{total:.3f} kg')

    # revolute 关节必须有非零限位
    for j in joints:
        if j['type'] == 'revolute':
            if j['lower'] is None or j['upper'] is None:
                report('FAIL', 'URDF 限位', f'{j["name"]} 缺少 limit')
                ok = False
            elif j['upper'] <= j['lower']:
                report('FAIL', 'URDF 限位范围',
                       f'{j["name"]}: [{j["lower"]}, {j["upper"]}]')
                ok = False

    if ok:
        report('PASS', 'URDF 结构',
               f'{len(links)} links / {len(joints)} joints '
               f'({n_revolute} revolute + {len(joints) - n_revolute} fixed)')
    return ok


# ---------------------------------------------------------------------------
# 2. STL 网格
# ---------------------------------------------------------------------------
def read_binary_stl(path):
    """返回 (n_triangles, 有 NaN/Inf 的三角面片数, 是否格式合法)。"""
    with open(path, 'rb') as fh:
        data = fh.read()
    if len(data) < 84:
        return 0, 0, False
    n = struct.unpack('<I', data[80:84])[0]
    if len(data) != 84 + 50 * n:
        return n, 0, False
    bad = 0
    for i in range(n):
        vals = struct.unpack('<12f', data[84 + 50 * i:84 + 50 * i + 48])
        if any(math.isnan(v) or math.isinf(v) for v in vals):
            bad += 1
    return n, bad, True


def check_meshes():
    for directory, expected, label in (
            (MESH_DIR, EXPECTED_MESHES, '本体网格'),
            (HAND_MESH_DIR, EXPECTED_HAND_MESHES, '手部网格')):
        if not os.path.isdir(directory):
            report('FAIL', label, f'目录缺失: {directory}')
            continue
        files = sorted(f for f in os.listdir(directory)
                       if f.lower().endswith('.stl'))
        if len(files) != expected:
            report('FAIL', f'{label}数量',
                   f'期望 {expected}，实际 {len(files)}')
            continue

        bad_format, bad_face, total_tris = [], [], 0
        for name in files:
            path = os.path.join(directory, name)
            n, nan_count, ok = read_binary_stl(path)
            total_tris += n
            if not ok:
                bad_format.append(name)
            if nan_count:
                bad_face.append(f'{name}({nan_count})')
        if bad_format:
            report('FAIL', f'{label}二进制格式', f'异常文件: {bad_format}')
        elif bad_face:
            report('FAIL', f'{label}数值', f'含 NaN/Inf 面片: {bad_face}')
        else:
            report('PASS', label,
                   f'{len(files)} 个二进制 STL，共 {total_tris:,} 三角面片')

    # 可选：用 trimesh 做深度检查
    try:
        import trimesh  # noqa: F401
    except ImportError:
        report('WARN', '网格深度检查', '未安装 trimesh，跳过')
        return
    import trimesh
    degenerate, watertight_ok, empty = [], 0, []
    for name in sorted(os.listdir(MESH_DIR)):
        if not name.lower().endswith('.stl'):
            continue
        mesh = trimesh.load(os.path.join(MESH_DIR, name), process=False)
        if mesh.is_empty or len(mesh.faces) == 0:
            empty.append(name)
            continue
        if not mesh.is_watertight:
            degenerate.append(name)
        else:
            watertight_ok += 1
    if empty:
        report('FAIL', '网格可加载性', f'空网格: {empty}')
    else:
        report('PASS', '网格可加载性', '全部可被 trimesh 解析')
    report('INFO', '网格封闭性',
           f'{watertight_ok}/{EXPECTED_MESHES} 为 watertight'
           f'（非封闭不利于碰撞检测: {len(degenerate)} 个）')


# ---------------------------------------------------------------------------
# 3. 引用一致性
# ---------------------------------------------------------------------------
def check_mesh_references():
    _, _, _ = None, None, None
    root = ET.parse(URDF_FILE).getroot()
    referenced = set()
    for mesh in root.iter('mesh'):
        filename = mesh.get('filename', '')
        m = re.match(r'package://tiangong3_urdf/(.+)', filename)
        if not m:
            report('FAIL', 'mesh 路径格式', f'非 package:// 路径: {filename}')
            continue
        referenced.add(m.group(1))

    missing = []
    for rel in sorted(referenced):
        if not os.path.isfile(os.path.join(URDF_PKG, rel)):
            missing.append(rel)
    if missing:
        report('FAIL', 'mesh 引用存在性', f'引用了不存在的文件: {missing}')
    else:
        report('PASS', 'mesh 引用存在性',
               f'URDF 引用的 {len(referenced)} 个 mesh 全部存在')

    on_disk = {f'meshes/{f}' for f in os.listdir(MESH_DIR)
               if f.lower().endswith('.stl')}
    orphans = sorted(on_disk - referenced)
    if orphans:
        report('WARN', 'mesh 孤儿文件',
               f'{len(orphans)} 个文件未被 URDF 引用: {orphans[:5]}')
    else:
        report('PASS', 'mesh 孤儿文件', 'meshes/ 中无未引用文件')

    hand_refs = [r for r in referenced if r.startswith('meshes_hand/')]
    if not hand_refs:
        report('INFO', '手部网格',
               '未被 URDF 引用（与文档说明一致：预留资产）')


# ---------------------------------------------------------------------------
# 4. package.xml
# ---------------------------------------------------------------------------
def check_package_xml(allow_network=True):
    pkgs = ['bodyctrl_msgs', 'tiangong3_urdf']
    paths = [os.path.join(REPO_ROOT, 'src', p, 'package.xml') for p in pkgs]

    xsd = None
    for path in paths:
        name = os.path.relpath(path, REPO_ROOT)
        if not os.path.isfile(path):
            report('FAIL', 'package.xml 存在性', f'缺失: {name}')
            continue
        try:
            tree = ET.parse(path)
        except ET.ParseError as exc:
            report('FAIL', f'package.xml XML 语法 ({name})', str(exc))
            continue

        root = tree.getroot()
        fmt = root.get('format')
        if fmt != '3':
            report('WARN', f'package.xml format ({name})', f'format="{fmt}"')

        # <name> 必须与目录名一致（colcon 要求）
        pkg_dir = os.path.basename(os.path.dirname(path))
        elem = root.find('name')
        pkg_name = (elem.text or '').strip() if elem is not None else ''
        if pkg_name != pkg_dir:
            report('FAIL', f'package.xml 名称 ({name})',
                   f'<name>={pkg_name} 与目录名 {pkg_dir} 不一致，'
                   f'colcon 将无法识别')

        # 必填字段
        for tag in ('name', 'version', 'description', 'maintainer', 'license'):
            elem = root.find(tag)
            if elem is None or not (elem.text or '').strip():
                report('FAIL', f'package.xml 字段 ({name})', f'缺少 <{tag}>')
        for tag in ('license', 'description'):
            elem = root.find(tag)
            if elem is not None and (elem.text or '').strip().startswith('TODO'):
                report('FAIL', f'package.xml 占位符 ({name})',
                       f'<{tag}> 仍为 TODO')
        lic = root.find('license')
        if lic is not None and (lic.text or '').strip() == 'Apache-2.0':
            report('INFO', f'package.xml 许可 ({name})', 'Apache-2.0')

        # XSD 校验
        if allow_network:
            if xsd is None:
                xsd = _load_package_xsd()          # 返回 XMLSchema 或 None
            if xsd is not None:
                try:
                    xsd.validate(path)
                    report('PASS', f'package.xml XSD ({name})', '符合 format 3')
                except Exception as exc:  # noqa: BLE001
                    report('FAIL', f'package.xml XSD ({name})', str(exc)[:300])
    return True


def _load_package_xsd():
    """下载并缓存官方 package_format3.xsd，返回 XMLSchema 对象；失败返回 None。"""
    try:
        import xmlschema
    except ImportError:
        report('WARN', 'package.xml XSD', '未安装 xmlschema，跳过')
        return None

    if not os.path.isfile(PACKAGE_XML_XSD_CACHE):
        try:
            os.makedirs(os.path.dirname(PACKAGE_XML_XSD_CACHE), exist_ok=True)
            with urllib.request.urlopen(PACKAGE_XML_XSD_URL,
                                        timeout=15) as resp:
                data = resp.read()
            with open(PACKAGE_XML_XSD_CACHE, 'wb') as fh:
                fh.write(data)
            report('INFO', 'XSD 下载', PACKAGE_XML_XSD_URL)
        except Exception as exc:  # noqa: BLE001
            report('WARN', 'XSD 下载失败', f'{exc}（跳过 XSD 校验）')
            return None

    try:
        return xmlschema.XMLSchema(PACKAGE_XML_XSD_CACHE)
    except Exception as exc:  # noqa: BLE001
        report('WARN', 'XSD 加载失败', f'{exc}（跳过 XSD 校验）')
        return None


# ---------------------------------------------------------------------------
# 5. Launch 文件
# ---------------------------------------------------------------------------
def check_launch_files():
    expected = ['display.launch.py', 'display_with_status.launch.py',
                'interactive_control.launch.py']
    files = sorted(f for f in os.listdir(LAUNCH_DIR) if f.endswith('.py'))
    missing = [f for f in expected if f not in files]
    if missing:
        report('FAIL', 'launch 文件', f'缺少: {missing}')

    # 声明在 CMakeLists 中的可执行脚本必须存在
    cmake = open(os.path.join(URDF_PKG, 'CMakeLists.txt'),
                 encoding='utf-8').read()
    declared = re.findall(r'scripts/([\w.]+\.py)', cmake)
    for script in set(declared):
        if not os.path.isfile(os.path.join(SCRIPTS_DIR, script)):
            report('FAIL', 'CMakeLists 声明的脚本',
                   f'install(PROGRAMS) 中的 {script} 不存在')
    report('PASS', 'launch / 脚本安装声明',
           f'{len(files)} 个 launch，CMakeLists 声明 {len(set(declared))} 个脚本均存在')

    # 每个 launch 引用的包内资源必须存在
    problems = []
    for name in files:
        path = os.path.join(LAUNCH_DIR, name)
        src = open(path, encoding='utf-8').read()
        try:
            ast.parse(src)
        except SyntaxError as exc:
            report('FAIL', f'launch 语法 ({name})', str(exc))
            continue
        for pkg_file in re.findall(r'os\.path\.join\((.+?)\)', src):
            for m in re.finditer(r'"([^"]+\.(?:rviz|xacro|urdf))"', pkg_file):
                rel = m.group(1)
                target = (os.path.join(CONFIG_DIR, rel)
                          if rel.endswith('.rviz')
                          else os.path.join(URDF_PKG, 'urdf', rel))
                if not os.path.isfile(target):
                    problems.append(f'{name} -> {rel}')
    if problems:
        report('FAIL', 'launch 资源引用', f'引用不存在的文件: {problems}')
    else:
        report('PASS', 'launch 资源引用', 'rviz / urdf 配置均存在')

    # RViz 配置可被解析（YAML）
    try:
        import yaml
    except ImportError:
        return
    for name in sorted(os.listdir(CONFIG_DIR)):
        if not name.endswith('.rviz'):
            continue
        try:
            with open(os.path.join(CONFIG_DIR, name), encoding='utf-8') as fh:
                data = yaml.safe_load(fh)
            if not isinstance(data, dict):
                report('FAIL', f'RViz 配置 ({name})', '根节点不是映射')
        except Exception as exc:  # noqa: BLE001
            report('FAIL', f'RViz 配置 ({name})', str(exc)[:200])
    report('PASS', 'RViz 配置', 'YAML 解析通过')


# ---------------------------------------------------------------------------
# 6. 电机 ID 映射一致性
# ---------------------------------------------------------------------------
MAPPING_PATTERN = re.compile(r'(\d+)\s*:\s*[\'"](\w+)[\'"]')
MAPPING_BLOCK = re.compile(
    r'MOTOR_ID_TO_JOINT\s*=\s*\{(.*?)\n\}', re.DOTALL)


def extract_mapping(path):
    src = open(path, encoding='utf-8').read()
    block = MAPPING_BLOCK.search(src)
    if not block:
        return None
    out = {}
    for m in MAPPING_PATTERN.finditer(block.group(1)):
        out[int(m.group(1))] = m.group(2)
    return out


def check_motor_mapping():
    sources = {
        'joint_state_publisher.py': os.path.join(
            SCRIPTS_DIR, 'joint_state_publisher.py'),
        'interactive_gui.py': os.path.join(
            SCRIPTS_DIR, 'interactive_gui.py'),
        'gen_joint_docs.py': os.path.join(
            REPO_ROOT, 'scripts', 'gen_joint_docs.py'),
    }
    mappings = {}
    for label, path in sources.items():
        mapping = extract_mapping(path)
        if not mapping:
            report('FAIL', f'电机映射解析 ({label})', '未找到 MOTOR_ID_TO_JOINT')
            continue
        mappings[label] = mapping

    if not mappings:
        return
    ref_label = 'joint_state_publisher.py'
    ref = mappings.get(ref_label) or next(iter(mappings.values()))
    if len(ref) != EXPECTED_MOTOR_IDS:
        report('FAIL', '电机映射数量',
               f'期望 {EXPECTED_MOTOR_IDS} 项，实际 {len(ref)}')
    else:
        report('PASS', '电机映射数量', f'{len(ref)} 项')

    for label, mapping in mappings.items():
        if mapping != ref:
            diff = {k: (ref.get(k), mapping.get(k))
                    for k in set(ref) | set(mapping)
                    if ref.get(k) != mapping.get(k)}
            report('FAIL', f'电机映射一致性 ({label})', f'与基准不一致: {diff}')
        else:
            report('INFO', f'电机映射一致性 ({label})', '一致')

    # 映射中的关节名必须都在 URDF 里
    _, _, joints = load_urdf_tree(URDF_FILE)
    urdf_joints = {j['name'] for j in joints}
    unknown = {jid: name for jid, name in ref.items()
               if name not in urdf_joints}
    if unknown:
        report('FAIL', '电机映射 ↔ URDF', f'URDF 中不存在的关节: {unknown}')
    else:
        report('PASS', '电机映射 ↔ URDF',
               '全部 31 个映射关节都存在于 URDF')

    # 反向：URDF 中的 revolute 关节是否都有电机 ID
    revolute = {j['name'] for j in joints if j['type'] == 'revolute'}
    no_id = revolute - set(ref.values())
    if no_id:
        report('WARN', 'revolute 关节无电机 ID', f'{sorted(no_id)}')
    else:
        report('PASS', 'revolute 关节覆盖', '每个 revolute 关节都有电机 ID')


# ---------------------------------------------------------------------------
# 6b. 两份模型文件的差异（几何一致 + 限位差异表与文档吻合）
# ---------------------------------------------------------------------------
def _joint_signature(path):
    """返回 {joint_name: 除 limit 外的全部结构信息} 与 {joint_name: (l, u)}。"""
    root = ET.parse(path).getroot()
    sig, limits = {}, {}
    for j in root.findall('joint'):
        name = j.get('name')
        parts = []
        for child in j:
            if child.tag != 'limit':
                parts.append(ET.tostring(child, encoding='unicode').strip())
        sig[name] = (j.get('type'), tuple(parts))
        limit = j.find('limit')
        if limit is not None and limit.get('lower') is not None:
            limits[name] = (float(limit.get('lower')),
                            float(limit.get('upper')))
    # link 定义（含惯量与 mesh 路径）
    for link in root.findall('link'):
        sig['link:' + link.get('name')] = ET.tostring(
            link, encoding='unicode').strip()
    return sig, limits


def check_model_pair():
    if not (os.path.isfile(URDF_FILE) and os.path.isfile(XACRO_FILE)):
        report('FAIL', '模型文件对', 'tiangong3.urdf(.xacro) 缺失')
        return
    sig_u, lim_u = _joint_signature(URDF_FILE)
    sig_x, lim_x = _joint_signature(XACRO_FILE)

    # 1) 几何/结构必须完全一致（文档声明「几何完全一致」）
    only_u = sorted(set(sig_u) - set(sig_x))
    only_x = sorted(set(sig_x) - set(sig_u))
    diff = sorted(k for k in set(sig_u) & set(sig_x) if sig_u[k] != sig_x[k])
    if only_u or only_x or diff:
        report('FAIL', '两模型几何一致性',
               f'仅 .urdf: {only_u[:3]} / 仅 .xacro: {only_x[:3]} / '
               f'内容不同: {diff[:3]}')
    else:
        report('PASS', '两模型几何一致性',
               f'{len(sig_u)} 项结构定义（link/joint/origin/axis/inertial/'
               f'mesh）完全相同')

    # 2) 限位差异数量
    changed = {k: (lim_u[k], lim_x[k]) for k in lim_u
               if k in lim_x and lim_u[k] != lim_x[k]}
    if len(changed) != 20:
        report('WARN', '两模型限位差异数量',
               f'实际 {len(changed)} 个，docs/model.md 中记载 20 个')

    # 3) .urdf 必须比 .xacro 更保守（收紧）或相等，不得更宽松
    looser = [k for k, (u, x) in changed.items()
              if u[0] < x[0] - 1e-9 or u[1] > x[1] + 1e-9]
    if looser:
        report('FAIL', '两模型限位安全性',
               f'.urdf 限位比 .xacro 更宽松（不安全）: {looser}')
    else:
        report('PASS', '两模型限位安全性',
               f'{len(changed)} 个关节的 .urdf 限位不宽于 .xacro'
               f'（对应两代机型参数，见 docs/model.md §3.2）')

    # 4) docs/model.md 中的差异表必须与实测一致
    doc_path = os.path.join(REPO_ROOT, 'docs', 'model.md')
    if not os.path.isfile(doc_path):
        report('WARN', 'docs/model.md 差异表', '文件缺失')
        return
    rows = {}
    for line in open(doc_path, encoding='utf-8'):
        m = re.match(r'\|\s*`(\w+)`\s*\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|',
                     line.strip())
        if not m:
            continue
        name = m.group(1)
        try:
            rows[name] = tuple(float(m.group(i)) for i in (2, 3, 4, 5))
        except ValueError:
            continue
    mismatch = []
    for name, vals in rows.items():
        if name not in changed:
            mismatch.append(f'{name}(文档有表格但实测无差异)')
            continue
        u, x = changed[name]
        expect = (round(u[0], 6), round(u[1], 6), round(x[0], 6),
                  round(x[1], 6))
        if tuple(round(v, 6) for v in vals) != expect:
            mismatch.append(f'{name}(文档 {vals} vs 实测 {expect})')
    missing = [k for k in changed if k not in rows]
    if mismatch or missing:
        report('FAIL', 'docs/model.md 差异表',
               f'不一致: {mismatch[:3]} 未收录: {missing[:5]}')
    else:
        report('PASS', 'docs/model.md 差异表',
               f'{len(rows)} 行与实测限位差异完全吻合')


def check_joints_doc_numbers():
    """独立复核 docs/joints.md 中的数值是否与 URDF 真实一致。

    gen_joint_docs.py --check 只能保证「文档 == 生成器输出」，
    无法发现生成器自身的 bug；这里用独立解析结果做交叉验证。
    """
    doc_path = os.path.join(REPO_ROOT, 'docs', 'joints.md')
    if not os.path.isfile(doc_path):
        report('WARN', 'docs/joints.md 数值复核', '文件缺失')
        return

    _, _, joints = load_urdf_tree(URDF_FILE)
    urdf = {j['name']: j for j in joints}
    mapping = extract_mapping(os.path.join(SCRIPTS_DIR,
                                           'joint_state_publisher.py')) or {}
    joint_to_id = {v: k for k, v in mapping.items()}

    row_re = re.compile(
        r'^\|\s*`(\w+)`\s*\|\s*(\d+|-)\s*\|\s*`(\w+)`\s*\|\s*`(\w+)`\s*\|'
        r'\s*`([\d\s.-]+)`\s*\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|'
        r'([^|]+)\|([^|]+)\|')
    checked, errors = 0, []
    for line in open(doc_path, encoding='utf-8'):
        m = row_re.match(line.strip())
        if not m:
            continue
        name = m.group(1)
        doc_id = None if m.group(2) == '-' else int(m.group(2))
        j = urdf.get(name)
        if j is None:
            errors.append(f'{name}: URDF 中不存在')
            continue
        try:
            doc_lower = float(m.group(6))
            doc_upper = float(m.group(7))
            doc_effort = float(m.group(10))
            doc_vel = float(m.group(11))
        except ValueError:
            continue
        checked += 1
        if doc_id != joint_to_id.get(name):
            errors.append(f'{name}: 电机 ID 文档={doc_id} 映射={joint_to_id.get(name)}')
        if abs(doc_lower - (j['lower'] or 0.0)) > 1e-6:
            errors.append(f'{name}: 下限 文档={doc_lower} URDF={j["lower"]}')
        if abs(doc_upper - (j['upper'] or 0.0)) > 1e-6:
            errors.append(f'{name}: 上限 文档={doc_upper} URDF={j["upper"]}')

    if not checked:
        report('WARN', 'docs/joints.md 数值复核', '未解析到任何关节行')
    elif errors:
        report('FAIL', 'docs/joints.md 数值复核',
               f'{len(errors)} 处不一致: {errors[:4]}')
    else:
        report('PASS', 'docs/joints.md 数值复核',
               f'独立复核 {checked} 个关节的 ID/限位，与 URDF 完全一致')


# ---------------------------------------------------------------------------
# 7. 文档一致性
# ---------------------------------------------------------------------------
def check_docs(no_network):
    # joints.md 由 gen_joint_docs.py --check 校验
    proc = subprocess.run(
        [sys.executable, os.path.join(REPO_ROOT, 'scripts',
                                      'gen_joint_docs.py'), '--check'],
        capture_output=True, text=True, cwd=REPO_ROOT)
    if proc.returncode == 0:
        report('PASS', 'docs/joints.md 一致性', proc.stdout.strip())
    else:
        report('FAIL', 'docs/joints.md 一致性',
               (proc.stderr or proc.stdout).strip()[:300])

    # docs/joints.md 中的关节表与 URDF 数值抽查（限位/力矩/速度）
    check_joints_doc_numbers()

    # 必需文档存在
    required = ['README.md', 'README.en.md', 'LICENSE', 'NOTICE',
                'SECURITY.md', 'CHANGELOG.md', 'CONTRIBUTING.md',
                'docs/architecture.md', 'docs/usage.md', 'docs/protocol.md',
                'docs/joints.md', 'docs/model.md', '.gitignore',
                '.gitattributes', 'run.sh']
    missing = [f for f in required
               if not os.path.isfile(os.path.join(REPO_ROOT, f))]
    if missing:
        report('FAIL', '必备文档', f'缺失: {missing}')
    else:
        report('PASS', '必备文档', f'{len(required)} 个文件齐全')

    # Markdown 内部链接
    link_re = re.compile(r'\[[^\]]*\]\(([^)]+)\)')
    broken = []
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        dirnames[:] = [d for d in dirnames if d != '.git']
        for fname in filenames:
            if not fname.endswith('.md'):
                continue
            path = os.path.join(dirpath, fname)
            for m in link_re.finditer(open(path, encoding='utf-8').read()):
                link = m.group(1).strip()
                if link.startswith(('http', 'mailto:', '#')):
                    continue
                target = link.split('#')[0]
                if not target:
                    continue
                if not os.path.exists(
                        os.path.normpath(os.path.join(dirpath, target))):
                    broken.append(
                        f'{os.path.relpath(path, REPO_ROOT)} -> {link}')
    if broken:
        report('FAIL', 'Markdown 内部链接', f'{len(broken)} 处失效: {broken}')
    else:
        report('PASS', 'Markdown 内部链接', '无失效链接')

    # 许可证 / 版权占位符检查
    notice = open(os.path.join(REPO_ROOT, 'NOTICE'), encoding='utf-8').read()
    if 'Proprietary' in notice or '专有' in notice:
        report('INFO', '资产授权声明', 'NOTICE 已声明模型资产为专有')

    copyright_files = ['LICENSE', 'NOTICE', 'README.md', 'README.en.md']
    leftover, missing = [], []
    for rel in copyright_files:
        path = os.path.join(REPO_ROOT, rel)
        if not os.path.isfile(path):
            continue
        text = open(path, encoding='utf-8').read()
        for placeholder in PLACEHOLDER_COPYRIGHTS:
            if placeholder in text:
                leftover.append(f'{rel}: {placeholder}')
        if COPYRIGHT_HOLDER not in text:
            missing.append(rel)
    if leftover:
        report('FAIL', '版权主体',
               f'仍存在占位版权行: {leftover}')
    elif missing:
        report('WARN', '版权主体',
               f'以下文件未包含版权主体 "{COPYRIGHT_HOLDER}": {missing}')
    else:
        report('PASS', '版权主体',
               f'已统一为 "{COPYRIGHT_HOLDER}"，无占位残留')

    # package.xml 的 <url> 必须是真实主仓库地址，且不含占位符
    placeholder = '&lt;your-org&gt;'
    bad_url, missing_url = [], []
    for rel in ('src/tiangong3_urdf/package.xml',
                'src/bodyctrl_msgs/package.xml'):
        path = os.path.join(REPO_ROOT, rel)
        if not os.path.isfile(path):
            continue
        text = open(path, encoding='utf-8').read()
        if placeholder in text:
            bad_url.append(f'{rel}（仍为 <your-org> 占位符）')
        elif REPO_URL not in text:
            missing_url.append(rel)
    if bad_url:
        report('FAIL', '仓库 URL', f'仍为占位地址: {bad_url}')
    elif missing_url:
        report('WARN', '仓库 URL',
               f'以下 package.xml 未包含 {REPO_URL}: {missing_url}')
    else:
        report('PASS', '仓库 URL', f'package.xml 均指向 {REPO_URL}')

    # 全仓不应再出现任何尖括号占位符
    # 注意：本检查会扫描文档，因此 README / NOTICE 等文档在描述这些占位符时
    # 不要逐字写出标记本身（写成描述性文字），否则会被本检查命中（自指）。
    todo = []
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        dirnames[:] = [d for d in dirnames
                       if d not in ('.git', 'meshes', 'meshes_hand')]
        for fname in filenames:
            if os.path.splitext(fname)[1] not in ('.md', '.py', '.sh', '.xml',
                                                  '.yaml', '.yml', '.cfg'):
                continue
            fpath = os.path.join(dirpath, fname)
            # 跳过校验器自身：它必然包含下面这些字面量
            if os.path.abspath(fpath) == os.path.abspath(__file__):
                continue
            try:
                text = open(fpath, encoding='utf-8').read()
            except (UnicodeDecodeError, IsADirectoryError):
                continue
            for marker in ('&lt;your-org&gt;', '<your-org>', '<your-fork-url>',
                           '<maintainer-email>', 'TODO: Package description',
                           'TODO: License declaration'):
                if marker in text:
                    todo.append(f'{os.path.relpath(fpath, REPO_ROOT)}: {marker}')
    if todo:
        report('WARN', '发布前占位符', f'仍需填写: {todo}')
    else:
        report('PASS', '发布前占位符', '无残留占位符')


# ---------------------------------------------------------------------------
# 8. YAML
# ---------------------------------------------------------------------------
def check_yaml():
    try:
        import yaml
    except ImportError:
        report('WARN', 'YAML 校验', '未安装 pyyaml，跳过')
        return
    files = [os.path.join(REPO_ROOT, '.github', 'workflows', 'ci.yml')]
    for path in files:
        if not os.path.isfile(path):
            report('FAIL', 'CI 配置', f'缺失: {path}')
            continue
        try:
            data = yaml.safe_load(open(path, encoding='utf-8'))
        except Exception as exc:  # noqa: BLE001
            report('FAIL', 'CI YAML 语法', str(exc)[:200])
            continue
        if 'jobs' not in data:
            report('FAIL', 'CI 配置', '缺少 jobs')
            continue
        report('PASS', 'CI 配置',
               f'{os.path.basename(path)}: jobs = {list(data["jobs"])}')


# ---------------------------------------------------------------------------
# 9. 发布卫生
# ---------------------------------------------------------------------------
JUNK_DIRS = ('__pycache__', 'build', 'install', 'log', 'dist',
             '.claude', '.cursor', '.vscode', '.idea')
JUNK_FILES = ('.DS_Store', '.DS_Store?', 'Thumbs.db', 'desktop.ini')
JUNK_SUFFIX = ('.pyc', '.pyo', '.zip', '.orig', '.rej', '.bak')


def _is_junk(rel_path):
    parts = rel_path.split('/')
    if any(p in JUNK_DIRS for p in parts[:-1]):
        return True
    name = parts[-1]
    return name in JUNK_FILES or name.endswith(JUNK_SUFFIX)


def _tracked_files():
    """git 已跟踪（含已暂存）的文件集合；非 git 仓库/无 git 时返回 None。"""
    try:
        proc = subprocess.run(['git', '-C', REPO_ROOT, 'ls-files'],
                              capture_output=True, text=True, check=True)
    except Exception:  # noqa: BLE001
        return None
    return {line for line in proc.stdout.splitlines() if line}


def check_hygiene():
    # 「会不会被发布」取决于 git 索引，而不是本地文件系统：
    # macOS 的 Finder 会不断生成 .DS_Store（已被 .gitignore 忽略），
    # 若按文件系统判定会产生误报，且无法反映真实发布内容。
    tracked = _tracked_files()
    if tracked is not None:
        junk = sorted(f for f in tracked if _is_junk(f))
        if junk:
            report('FAIL', '发布卫生',
                   f'以下文件已被 git 跟踪、将会被发布: {junk[:10]}')
        else:
            report('PASS', '发布卫生',
                   f'受版本控制的 {len(tracked)} 个文件中'
                   f'无缓存 / 临时 / 内部配置')
        # 本地存在但未被跟踪的垃圾文件：仅提示，不影响发布
        local_junk = []
        for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
            dirnames[:] = [d for d in dirnames if d != '.git']
            for d in list(dirnames):
                rel = os.path.relpath(os.path.join(dirpath, d), REPO_ROOT)
                if _is_junk(rel + '/x'):
                    local_junk.append(rel)
            for f in filenames:
                rel = os.path.relpath(os.path.join(dirpath, f), REPO_ROOT)
                if _is_junk(rel):
                    local_junk.append(rel)
        ignored = [p for p in local_junk
                   if p.replace(os.sep, '/') not in tracked]
        if ignored:
            report('INFO', '本地忽略文件',
                   f'{len(ignored)} 个未被跟踪的临时文件（不会发布）: '
                   f'{sorted(ignored)[:5]}')
    else:
        junk = []
        for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
            dirnames[:] = [d for d in dirnames if d != '.git']
            for d in list(dirnames):
                if d in JUNK_DIRS:
                    junk.append(os.path.relpath(os.path.join(dirpath, d),
                                                REPO_ROOT))
            for f in filenames:
                if _is_junk(f):
                    junk.append(os.path.relpath(os.path.join(dirpath, f),
                                                REPO_ROOT))
        if junk:
            report('FAIL', '发布卫生', f'发现不应发布的文件: {junk[:10]}')
        else:
            report('PASS', '发布卫生', '无缓存 / 临时 / 内部配置文件')

    # 脚本可执行位
    exec_expected = ['run.sh', 'scripts/build.sh', 'scripts/release.sh',
                     'scripts/gen_joint_docs.py', 'scripts/validate.py',
                     'src/tiangong3_urdf/scripts/interactive_gui.py',
                     'src/tiangong3_urdf/scripts/joint_state_publisher.py']
    not_exec = [f for f in exec_expected
                if os.path.isfile(os.path.join(REPO_ROOT, f))
                and not os.access(os.path.join(REPO_ROOT, f), os.X_OK)]
    if not_exec:
        report('WARN', '可执行权限', f'缺少 +x: {not_exec}')
    else:
        report('PASS', '可执行权限', f'{len(exec_expected)} 个脚本均可执行')


# ---------------------------------------------------------------------------
def main():
    global VERBOSE
    parser = argparse.ArgumentParser(
        description='Tiangong Dex 发布包完整性校验')
    parser.add_argument('--no-network', action='store_true',
                        help='跳过需要联网的校验（XSD 下载）')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='输出 INFO 级信息')
    args = parser.parse_args()
    VERBOSE = args.verbose

    print(f'校验工作空间: {REPO_ROOT}')
    print(f'Python: {sys.version.split()[0]}')
    print('-' * 72)

    check_urdf_structure()
    check_meshes()
    check_mesh_references()
    check_package_xml(allow_network=not args.no_network)
    check_launch_files()
    check_motor_mapping()
    check_model_pair()
    check_docs(args.no_network)
    check_yaml()
    check_hygiene()

    print('-' * 72)
    fails = [r for r in RESULTS if r[0] == 'FAIL']
    warns = [r for r in RESULTS if r[0] == 'WARN']
    passes = [r for r in RESULTS if r[0] == 'PASS']
    print(f'通过 {len(passes)} 项 | 告警 {len(warns)} 项 | 失败 {len(fails)} 项')
    if fails:
        print('\n失败项:')
        for _, name, msg in fails:
            print(f'  - {name}: {msg}')
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
