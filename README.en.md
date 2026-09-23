# Walker Tienkung Dex ROS 2 Toolchain

**Package: `tiangong3_urdf`** ｜ Workspace: `Dex-TF`

[![CI](https://github.com/luckylhf/Dex-TF/actions/workflows/ci.yml/badge.svg)](https://github.com/luckylhf/Dex-TF/actions/workflows/ci.yml)
[![ROS 2](https://img.shields.io/badge/ROS%202-Humble-22314E?logo=ros&logoColor=white)](https://docs.ros.org/en/humble/)
[![Platform](https://img.shields.io/badge/Ubuntu-22.04%20%7C%20x86__64-E95420?logo=ubuntu&logoColor=white)](https://releases.ubuntu.com/22.04/)
[![Package](https://img.shields.io/badge/package-tiangong3__urdf-informational.svg)](src/tiangong3_urdf)
[![License](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](LICENSE)
[![Model Assets](https://img.shields.io/badge/Model%20Assets-Proprietary-orange.svg)](NOTICE)

ROS 2 description, visualization and teleoperation tooling for the
**Tiangong Dex** humanoid robot.

> 🇨🇳 中文完整文档请见 [`README.md`](README.md) — this English document is a
> condensed translation; the Chinese README is the primary reference.

> ## ⚠️ Safety Notice
> This repository contains a GUI that **commands a real robot to move**.
> Read [`SECURITY.md`](SECURITY.md) before use: make sure the E-Stop is reachable
> and that nobody is inside the workspace. Never operate the real robot unattended.

> ## 📌 Where it runs
> This project is designed to run on a **remote operator PC** (the control side),
> not on the robot's onboard computer.

> ## 🏷️ Naming & provenance (important)
> - **Package name**: `tiangong3_urdf` — unified with the Tiangong Dex ecosystem
>   (`Dex-URDF/Tienkung_Dex_Model_All`, the Tiangong 3.0 Dex V3 asset pack, also
>   uses `package://tiangong3_urdf/...`).
> - **Model data**: the URDF structure, inertias and mesh geometry currently come from
>   [`Open-X-Humanoid/TienKung_URDF`](https://github.com/Open-X-Humanoid/TienKung_URDF)
>   directory `tiangong2dex_urdf`, i.e. **Tiangong 2 Dex EVT2**.
> - So: **the name is unified, the geometry is still EVT2 data.** To switch to a real
>   Tiangong 3 Dex model, see [`docs/model.md`](docs/model.md#命名与模型数据来源) —
>   both generations share the exact same link/joint names (39 links / 38 joints),
>   so **only the URDF and meshes need replacing; launch / GUI / bridge code is unchanged**.
> - ⚠️ The external Tiangong 3.0 Dex pack is itself a ROS package named
>   `tiangong3_urdf`; do **not** put both in the same colcon workspace
>   (duplicate package name ⇒ ambiguous `package://` mesh resolution).

---

## Overview

A standard **colcon workspace** containing two packages:

| Package | Type | Purpose |
|---------|------|---------|
| [`tiangong3_urdf`](src/tiangong3_urdf) | `ament_cmake` | Robot URDF/Xacro model, RViz configs, launch files, status bridge, interactive Qt GUI |
| [`bodyctrl_msgs`](src/bodyctrl_msgs) | `rosidl` interface package | Body-control protocol: motor status feedback, position/speed/current commands, calibration & upgrade services |

```text
Robot ──(bodyctrl_msgs topics)──> bridge ──(JointState)──> robot_state_publisher ──> TF / RViz
  ▲                                                                                       │
  └─────────────────(CmdSetMotorPosition)───────── interactive GUI ◄──── sliders + Ghost preview
```

## Features

- **Full robot description** — 39 links / 38 joints (31 revolute + 7 fixed) with inertial data.
- **TF tree publishing** — integrated `robot_state_publisher`.
- **RViz visualization** — two presets (`display.rviz`, `interactive.rviz`).
- **Real-robot status bridge** — aggregates 4 body `MotorStatusMsg` topics (plus 2 hand topics)
  into `/joint_states`.
- **Ghost Robot preview** — a cyan semi-transparent preview drawn with `MarkerArray`,
  computed by a built-in forward-kinematics solver, **without polluting the TF tree**.
- **Offline alert** — no data for 1 s ⇒ all links are overlaid with red meshes.
- **Safe execution** — "Sync to Real" aligns sliders with the real robot; "Execute"
  requires an explicit collision-risk confirmation and is disabled while offline.

## Robot Specifications

| Item | Value |
|------|-------|
| DOF | **31 revolute joints** (2×7-DOF arms, 2×6-DOF legs, 3-DOF waist, 2-DOF head) |
| Fixed frames | 7 (head camera, radar, 2 IMUs, chest camera, left/right TCP) |
| Total model mass | ≈ **63.27 kg** (hands excluded) |
| Root link | `pelvis` |
| Units | m / rad / kg |

## Requirements

- Ubuntu 22.04 LTS, **ROS 2 Humble**
- Python 3.10, `python3-numpy`
- `ros-humble-python-qt-binding` — provides the `python_qt_binding` module used by
  the GUI (`python3-pyqt5` alone is **not** enough)
- Same DDS domain / network segment as the robot for real-robot use
- OpenGL 3.3+ capable GPU (RViz + Qt GUI)

## Install & Build

```bash
# 0. Clone the repository
git clone https://github.com/luckylhf/Dex-TF.git
cd Dex-TF

# 1. Install ROS 2 Humble (see official docs), then:
sudo apt install -y ros-humble-desktop

# 2. Resolve dependencies
cd /path/to/Dex-TF
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y

# 3. Build
colcon build --symlink-install
source install/setup.bash
```

`--symlink-install` symlinks `launch/`, `urdf/`, `meshes/`, `config/` and `scripts/`,
so edits take effect without rebuilding.

## Quick Start

```bash
bash run.sh              # build + interactive control (DEFAULT — commands the real robot!)
bash run.sh display      # build + offline model view (safe, no robot needed)
bash run.sh status       # build + model driven by real robot status (read-only)
bash run.sh interactive  # build + interactive control
```

Start with `display` if you are new — it never sends anything to the robot.

### Launches

| Launch | Nodes | Robot involved |
|--------|-------|----------------|
| `display.launch.py` | `robot_state_publisher` + `joint_state_publisher_gui` + `rviz2` | No — fully offline |
| `display_with_status.launch.py` | `robot_state_publisher` + `joint_state_publisher.py` + `rviz2` | Read-only status |
| `interactive_control.launch.py` | `robot_state_publisher` + bridge + `interactive_gui.py` + `rviz2` | **Yes — sends commands** |

```bash
ros2 launch tiangong3_urdf display.launch.py
ros2 launch tiangong3_urdf display_with_status.launch.py
ros2 launch tiangong3_urdf interactive_control.launch.py
```

## Topics

### Subscribed from the robot

| Topic | Type | Content |
|-------|------|---------|
| `/head/status` | `bodyctrl_msgs/MotorStatusMsg` | Head joints (motor ID 1–2) |
| `/waist/status` | `bodyctrl_msgs/MotorStatusMsg` | Waist joints (ID 31–33) |
| `/arm/status` | `bodyctrl_msgs/MotorStatusMsg` | Both arms (ID 11–17, 21–27) |
| `/leg/status` | `bodyctrl_msgs/MotorStatusMsg` | Both legs (ID 51–56, 61–66) |
| `/inspire_hand/state/{left,right}_hand` | `sensor_msgs/JointState` | Hand joint states (normalized 0–1) |

### Published to the robot

| Topic | Type |
|-------|------|
| `/head/cmd_pos`, `/waist/cmd_pos`, `/arm/cmd_pos`, `/leg/cmd_pos` | `bodyctrl_msgs/CmdSetMotorPosition` |
| `/inspire_hand/ctrl/{left,right}_hand` | `sensor_msgs/JointState` |

### Published by this repository

| Topic | Type | Content |
|-------|------|---------|
| `/joint_states` | `sensor_msgs/JointState` | Aggregated joint states for the TF tree |
| `/robot_online_status` | `std_msgs/Bool` | Robot online flag (1 s timeout) |
| `/ghost/markers` | `visualization_msgs/MarkerArray` | Ghost robot preview |
| `/offline_robot_markers` | `visualization_msgs/MarkerArray` | Red offline overlay |

Full field definitions: [`docs/protocol.md`](docs/protocol.md).

## Motor ID ↔ Joint Mapping

```text
Head:     1 = head_yaw_joint,       2 = head_pitch_joint
Waist:   31 = waist_pitch_joint,   32 = waist_roll_joint,  33 = waist_yaw_joint
L Arm:   11..17 = shoulder_pitch/roll/yaw_l, elbow_pitch/yaw_l, wrist_pitch/roll_l
R Arm:   21..27 = same order, _r suffix
L Leg:   51..56 = hip_pitch/roll/yaw_l, knee_pitch_l, ankle_pitch/roll_l
R Leg:   61..66 = same order, _r suffix
Hand L/R: 1..6 = little, ring, middle, index, thumb_2, thumb_1
```

Full table with limits, effort and velocity: [`docs/joints.md`](docs/joints.md).

## Model Assets

| Asset | Path | Notes |
|-------|------|-------|
| `tiangong3.urdf` | `src/tiangong3_urdf/urdf/` | Parsed by the GUI and the bridge node |
| `tiangong3.urdf.xacro` | `src/tiangong3_urdf/urdf/` | Loaded by default in launch files (currently **uses no xacro macros**) |
| Body meshes | `meshes/*.STL` | 39 binary STLs, **decimated** visualization meshes (~26 MB) |
| Hand meshes | `meshes_hand/*.STL` | 26 binary STLs, **not referenced** by the current URDF (~14 MB) |

The two model files share identical geometry but differ in **some joint limits**
(the `.urdf` uses slightly tightened bounds). See [`docs/model.md`](docs/model.md).

> ⚠️ The URDF and mesh assets are **NOT** covered by the Apache-2.0 license.
> See [`NOTICE`](NOTICE) before redistributing.

## Validation

`scripts/validate.py` checks the whole repository **without a ROS 2 environment**
(27 checks across 12 categories: URDF structure, STL integrity, mesh references,
`package.xml` XSD, launch resources, motor-ID mapping consistency, model-pair diff
vs. docs, documentation values, Markdown links, release metadata, unfinished
placeholders, release hygiene):

```bash
pip install trimesh numpy lxml xmlschema pyyaml     # optional, degrades gracefully
python3 scripts/validate.py -v
```

## Documentation

| Document | Content |
|----------|---------|
| [`docs/architecture.md`](docs/architecture.md) | System architecture and data flow |
| [`docs/usage.md`](docs/usage.md) | Step-by-step usage and troubleshooting |
| [`docs/protocol.md`](docs/protocol.md) | Full `bodyctrl_msgs` protocol reference |
| [`docs/joints.md`](docs/joints.md) | Joint / motor ID / limit tables |
| [`docs/model.md`](docs/model.md) | URDF and mesh asset details |
| [`SECURITY.md`](SECURITY.md) | Safety and network security requirements |
| [`CHANGELOG.md`](CHANGELOG.md) | Revision history |

## License

Software code is licensed under [Apache-2.0](LICENSE).
Robot model and mesh assets are **proprietary** and excluded from that license — see [`NOTICE`](NOTICE).

```
Copyright 2026 Walker Tienkung Dex Project Contributors
```

---

<sub>This project is not officially affiliated with the robot manufacturer.
All trademarks belong to their respective owners.</sub>
