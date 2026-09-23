# Walker Tienkung Dex ROS 2 工具链

**包名：`tiangong3_urdf`** ｜ 工作空间：`Dex-TF`

[![ROS 2](https://img.shields.io/badge/ROS%202-Humble-22314E?logo=ros&logoColor=white)](https://docs.ros.org/en/humble/)
[![Platform](https://img.shields.io/badge/Ubuntu-22.04%20%7C%20x86__64-E95420?logo=ubuntu&logoColor=white)](https://releases.ubuntu.com/22.04/)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Package](https://img.shields.io/badge/package-tiangong3__urdf-informational.svg)](src/tiangong3_urdf)
[![License](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](LICENSE)
[![Model Assets](https://img.shields.io/badge/Model%20Assets-Proprietary-orange.svg)](NOTICE)
[![Status](https://img.shields.io/badge/Model-EVT2-yellow.svg)](CHANGELOG.md)

天工 Dex（Tiangong Dex）人形机器人的 **ROS 2 描述、可视化与遥操作调试工具链**。

> ## ⚠️ 安全提示
> 本项目包含**可向真实机器人下发运动指令**的交互界面。
> 使用前请务必阅读 [`SECURITY.md`](SECURITY.md)，确认急停可用、执行区域无人。
> 所有涉及真机的操作必须有人在场监护。

> ## 📌 运行位置说明
> 本项目设计为在**控制端 PC（上位机）**上运行，通过 DDS 与机器人本体通信，
> 用于远程监控与指令下发。**它并不直接运行在机器人本体的控制计算机上。**

> ## 🏷️ 命名与溯源（重要）
>
> ### 称谓对照
>
> 本文档及本项目中出现的以下名称**指同一个对象**，统一称谓为
> **Walker Tienkung Dex**：
>
> | 出现形式 | 说明 |
> |----------|------|
> | **Walker Tienkung Dex** | 统一称谓（本项目与机器人整机） |
> | `Tiangong Dex`、`Tiangong 2 Dex` | 同一对象的英文写法（厂商 / 上游文档用），含早期版本后缀 |
> | `Tienkung Dex`、`TienKung`、`Tienkung` | 同一对象的英文写法（上游仓库 Open-X-Humanoid 用） |
> | 天工 Dex、天工 2 Dex | 同一对象的中文写法 |
> | `tiangong3_urdf`、`tiangong3.urdf` | **技术标识符**（ROS 2 包名 / 模型文件名），非品牌名 |
>
> 读文档时若见 `Tiangong Dex`、`Tienkung Dex`、`天工 Dex` 等，均可按
> **Walker Tienkung Dex** 理解；反之亦然。仓库内暂未统一改写这些文案
> （避免与上游仓库名、溯源记录、技术标识符混淆），故以本表为准。
>
> ### 包名与模型数据来源
>
> - **包名**：`tiangong3_urdf`，采用与 Walker Tienkung Dex 生态一致的统一命名
>   （同目录 `Dex-URDF/Tienkung_Dex_Model_All`（即上游「天工 3.0 Dex V3」资源包，
>   仓库名保持原样）同样使用 `package://tiangong3_urdf/...`）。
> - **模型数据**：当前内嵌的 URDF 结构、惯量与网格几何来自上游
>   [`Open-X-Humanoid/TienKung_URDF`](https://github.com/Open-X-Humanoid/TienKung_URDF)
>   的 `tiangong2dex_urdf` 目录，对应 **天工 2 Dex EVT2**。
> - 即：**包名已统一，模型几何仍为 EVT2 数据**。若需接入真正的天工 3 Dex 模型，
>   请参见 [`docs/model.md`](docs/model.md#命名与模型数据来源) —— 由于两代机型的
>   link/joint 命名集合完全相同（39 links / 38 joints），**替换 URDF 与 meshes 即可，
>   本仓库的 launch / GUI / 桥接代码无需修改**。
> - 重命名的完整记录见 [`CHANGELOG.md`](CHANGELOG.md)。

> 📖 英文说明见 [`README.en.md`](README.en.md)。完整文档索引见 [`docs/`](docs/)。

---

## 目录

- [Walker Tienkung Dex ROS 2 工具链](#walker-tienkung-dex-ros-2-工具链)
  - [目录](#目录)
  - [1. 项目简介](#1-项目简介)
  - [2. 演示效果](#2-演示效果)
  - [3. 功能特性](#3-功能特性)
  - [4. 机器人规格](#4-机器人规格)
  - [5. 仓库结构](#5-仓库结构)
  - [6. 系统要求](#6-系统要求)
  - [7. 安装与编译](#7-安装与编译)
    - [7.1 安装 ROS 2 Humble](#71-安装-ros-2-humble)
    - [7.2 安装本仓库依赖](#72-安装本仓库依赖)
    - [7.3 编译工作空间](#73-编译工作空间)
    - [7.4 发布包完整性校验（可选）](#74-发布包完整性校验可选)
  - [8. 快速开始](#8-快速开始)
  - [9. 三个 Launch 详解](#9-三个-launch-详解)
    - [9.1 `display.launch.py` — 离线模型查看](#91-displaylaunchpy--离线模型查看)
    - [9.2 `display_with_status.launch.py` — 真机状态回显（只读）](#92-display_with_statuslaunchpy--真机状态回显只读)
    - [9.3 `interactive_control.launch.py` — 交互式控制（⚠️ 会动真机）](#93-interactive_controllaunchpy--交互式控制️-会动真机)
  - [10. 通信协议概览](#10-通信协议概览)
    - [状态订阅（机器人 → 控制端）](#状态订阅机器人--控制端)
    - [控制指令（控制端 → 机器人）](#控制指令控制端--机器人)
    - [本仓库额外发布的话题](#本仓库额外发布的话题)
  - [11. 电机 ID 与关节映射](#11-电机-id-与关节映射)
  - [12. 模型与网格资产](#12-模型与网格资产)
  - [13. 常见问题（FAQ）](#13-常见问题faq)
  - [14. 已知限制](#14-已知限制)
  - [15. 版本与修订记录](#15-版本与修订记录)
  - [16. 路线图](#16-路线图)
  - [17. 贡献指南](#17-贡献指南)
  - [18. 许可证](#18-许可证)

---

## 1. 项目简介

本仓库是一个标准的 **ROS 2（colcon）工作空间**，包含两个功能包：

| 包名 | 类型 | 作用 |
|------|------|------|
| [`tiangong3_urdf`](src/tiangong3_urdf) | `ament_cmake`（数据包） | 机器人 URDF/Xacro 模型、RViz 配置、Launch 文件、可视化桥接与交互控制 GUI |
| [`bodyctrl_msgs`](src/bodyctrl_msgs) | `rosidl` 接口包 | 机体控制通信协议：电机状态反馈、位置/速度/电流控制指令、标定与升级服务 |

配套形成完整链路：

```
真实机器人本体 ──(bodyctrl_msgs 话题)──> 桥接节点 ──(JointState)──> robot_state_publisher ──> TF / RViz
     ▲                                                                                             │
     └──────────────────(CmdSetMotorPosition 位置指令)────── 交互控制 GUI ◄──── 滑块拖拽 + Ghost 预览 ◄┘
```

## 2. 演示效果

拖动 GUI 滑块 → RViz 中青色半透明 Ghost 机器人实时预览目标姿态 →
点击 Execute → 真实机器人同步运动到位。

▶️ **演示视频**：[`docs/assets/tiangong3_joint_control_demo.mp4`](docs/assets/tiangong3_joint_control_demo.mp4)（约 6 MB，点击下载观看）

```text
┌─────────────────────────┬───────────────────────────────┐
│  Qt 控制面板             │  RViz                         │
│  ─────────────────────  │  ───────────────────────────  │
│  Head        [====o==]  │        ▓▓▓  Ghost (青色半透明)  │
│  Waist       [==o====]  │        ░░░  Real  (灰色实体)    │
│  Left Arm    [===o===]  │                               │
│  Right Arm   [=o=====]  │   Fixed Frame: pelvis         │
│  Left Leg    [====o==]  │   Displays: RobotModel / TF /  │
│  Right Leg   [==o====]  │             MarkerArray        │
│  ─────────────────────  │                               │
│ [Sync to Real] [Execute]│                               │
└─────────────────────────┴───────────────────────────────┘
```

## 3. 功能特性

| 特性 | 说明 | 实现位置 |
|------|------|----------|
| **完整机器人描述** | 39 个 link、38 个 joint（31 个 revolute + 7 个 fixed），含惯量参数 | `urdf/tiangong3.urdf(.xacro)` |
| **TF 树发布** | 集成 `robot_state_publisher`，实时发布全机坐标变换 | `launch/*.launch.py` |
| **RViz 可视化** | 预置两套 RViz 配置（基础显示 / 交互调试） | `config/display.rviz`、`config/interactive.rviz` |
| **真机状态桥接** | 订阅 4 路 `MotorStatusMsg` + 2 路灵巧手状态，聚合为 `/joint_states` | `scripts/joint_state_publisher.py` |
| **Ghost Robot 预览** | 拖动滑块时以 `MarkerArray` 绘制青色半透明机器人，**不污染 TF 树** | `scripts/interactive_gui.py` |
| **离线红色告警** | 1 秒无数据即判定离线，在所有 link 上叠加红色半透明网格 | `scripts/joint_state_publisher.py` |
| **一键同步真机** | "Sync to Real" 将滑块与真实关节位置对齐 | `scripts/interactive_gui.py` |
| **安全确认执行** | Execute 前弹出碰撞风险确认框，未连接真机时按钮禁用 | `scripts/interactive_gui.py` |
| **自实现前向运动学** | 不依赖 KDL，直接从 URDF 解析关节链做 FK，用于 Ghost 定位 | `scripts/interactive_gui.py` |
| **灵巧手接口预留** | 手部网格与 6 自由度映射已就绪（当前模型未挂载手部 link） | `meshes_hand/`、`docs/joints.md` |

## 4. 机器人规格

| 项目 | 参数 |
|------|------|
| 自由度 | **31 个 revolute 关节**（7 轴臂 ×2 + 6 轴腿 ×2 + 3 轴腰 + 2 轴头） |
| 固定坐标系 | 7 个（头部相机、雷达、2 个 IMU、胸前相机、左右 TCP） |
| 模型总质量 | ≈ **63.27 kg**（不含手部） |
| 关节顺序 | 腰 → 头 → 臂 → 腿（URDF 中 `pelvis` 为根 link） |
| 单位 | 长度 m，角度 rad，质量 kg |
| 关节限位 | 见 [`docs/joints.md`](docs/joints.md) 完整表格 |

<details>
<summary>关节总览（点击展开）</summary>

| 部位 | 关节 | 数量 |
|------|------|------|
| 头部 | `head_yaw`, `head_pitch` | 2 |
| 腰部 | `waist_yaw`, `waist_roll`, `waist_pitch` | 3 |
| 左臂 | `shoulder_pitch`, `shoulder_roll`, `shoulder_yaw`, `elbow_pitch`, `elbow_yaw`, `wrist_pitch`, `wrist_roll` | 7 |
| 右臂 | 同上（`_r` 后缀镜像） | 7 |
| 左腿 | `hip_pitch`, `hip_roll`, `hip_yaw`, `knee_pitch`, `ankle_pitch`, `ankle_roll` | 6 |
| 右腿 | 同上（`_r` 后缀镜像） | 6 |

</details>

## 5. 仓库结构

```text
Dex-TF/
├── README.md                    # 本文件（中文）
├── README.en.md                 # English README
├── LICENSE                      # Apache-2.0（仅覆盖软件代码）
├── NOTICE                       # 模型资产与第三方依赖授权声明
├── SECURITY.md                  # 真机操作安全与网络安全要求
├── CHANGELOG.md                 # 版本与修订记录
├── CONTRIBUTING.md              # 贡献指南
├── run.sh                       # 一键编译 + 启动脚本
├── .gitignore / .gitattributes
├── .github/workflows/ci.yml     # GitHub Actions：colcon build 校验
├── docs/
│   ├── architecture.md          # 系统架构与数据流
│   ├── usage.md                 # 详细使用说明与故障排查
│   ├── protocol.md              # bodyctrl_msgs 通信协议详解
│   ├── joints.md                # 关节 / 电机 ID / 限位全表（自动生成）
│   ├── model.md                 # URDF 模型与网格资产说明
│   └── assets/                  # 演示视频等媒体资源
├── scripts/
│   ├── build.sh                 # 编译封装（含完整性校验）
│   ├── validate.py              # 发布包完整性校验（27 项，无需 ROS 环境）
│   ├── gen_joint_docs.py        # 由 URDF 自动生成 docs/joints.md
│   └── release.sh               # 打包 GitHub Release 附件
└── src/
    ├── bodyctrl_msgs/           # 通信协议接口包
    │   ├── msg/  (42 个)
    │   ├── srv/  (22 个)
    │   └── doc/BodyControlNode.md
    └── tiangong3_urdf/       # 机器人描述与工具包
        ├── urdf/                # tiangong3.urdf / .urdf.xacro
        ├── meshes/              # 本体 39 个 STL（简化网格，26 MB）
        ├── meshes_hand/         # 灵巧手 26 个 STL（预留，14 MB）
        ├── launch/              # display / display_with_status / interactive_control
        ├── config/              # RViz 配置
        └── scripts/             # joint_state_publisher.py / interactive_gui.py
```

## 6. 系统要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Ubuntu 22.04 LTS（x86_64 / arm64） |
| ROS 版本 | **ROS 2 Humble Hawksbill** |
| Python | 3.10 |
| 网络 | 与机器人本体处于**同一 DDS 域（同一网段/域 ID）** |
| 显卡 | 建议支持 OpenGL 3.3+（RViz 与 Qt GUI 需要） |
| 磁盘 | 源码约 46 MB（其中网格 40 MB），编译后约 150 MB |

> Windows / macOS 理论上可编译模型显示部分，但真机通信与 Qt GUI 未做验证。

## 7. 安装与编译

先获取代码：

```bash
git clone https://github.com/luckylhf/Dex-TF.git
cd Dex-TF
```

### 7.1 安装 ROS 2 Humble

```bash
# 参考官方文档，此处为 Ubuntu 22.04 的常规步骤
sudo apt update && sudo apt install -y curl gnupg lsb-release
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
sudo apt update && sudo apt install -y ros-humble-desktop
```

### 7.2 安装本仓库依赖

推荐使用 `rosdep` 自动解析（会读取两个包的 `package.xml`）：

```bash
cd /path/to/Dex-TF
source /opt/ros/humble/setup.bash
sudo rosdep init 2>/dev/null || true
rosdep update
rosdep install --from-paths src --ignore-src -r -y
```

或手动安装：

```bash
sudo apt install -y \
  ros-humble-joint-state-publisher \
  ros-humble-joint-state-publisher-gui \
  ros-humble-robot-state-publisher \
  ros-humble-rviz2 \
  ros-humble-xacro \
  ros-humble-sensor-msgs \
  ros-humble-visualization-msgs \
  ros-humble-geometry-msgs \
  ros-humble-std-msgs \
  ros-humble-rclpy \
  ros-humble-ament-index-python \
  ros-humble-rosidl-default-runtime \
  ros-humble-python-qt-binding \
  python3-numpy
```

> ⚠️ **`ros-humble-python-qt-binding` 不能省**：`interactive_gui.py` 里
> `from python_qt_binding.QtWidgets import ...` 所需的 **`python_qt_binding`
> 模块由该 ROS 包提供**，仅安装 `python3-pyqt5` 是不够的（后者只是它的依赖之一），
> 否则启动 GUI 会报
> `ModuleNotFoundError: No module named 'python_qt_binding'`。
>
> 以上是本仓库声明的**最小依赖集**；`ros-humble-desktop` 已包含其中大部分，
> 用 §7.1 的方式安装通常无需再逐条装。优先使用上面的 `rosdep` 方式，
> 它会自动按 `package.xml` 解析出完整依赖。

### 7.3 编译工作空间

```bash
cd /path/to/Dex-TF
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

`--symlink-install` 让 `launch/`、`urdf/`、`meshes/`、`scripts/` 以软链接方式安装，
**修改后无需重新编译**，非常适合调试阶段。

也可使用封装脚本：

```bash
bash scripts/build.sh            # 等价于 colcon build --symlink-install（编译后自动校验）
bash scripts/build.sh --clean    # 清理 build/install/log 后重新编译
```

### 7.4 发布包完整性校验（可选）

`scripts/validate.py` **不需要 ROS 2 环境**，可在任意 Python ≥ 3.8 下运行，
用于校验模型、网格、文档与代码的一致性：

```bash
pip install trimesh numpy lxml xmlschema pyyaml     # 可选，缺失时自动降级为告警
python3 scripts/validate.py -v
```

它覆盖 **12 类共 27 项**检查（安装不同的可选依赖时条目数略有增减）：

| 类别 | 检查内容 |
|------|----------|
| URDF 结构 | link/joint 数量、单根、无多父、引用完整性、限位有效性、质量总和 |
| STL 网格 | 二进制格式、面片数、NaN/Inf 面片、trimesh 可加载性、封闭性 |
| 引用一致性 | URDF 引用的 mesh 是否存在、`meshes/` 是否有孤儿文件 |
| package.xml | XML 语法、`<name>` 与目录名一致、必填字段、官方 `package_format3.xsd` 校验 |
| Launch | Python 语法、`CMakeLists.txt` 声明的脚本、引用的 rviz/urdf 资源 |
| 电机映射 | 三个脚本中的映射表是否一致、映射关节是否都存在于 URDF |
| 两模型差异 | `.urdf` 与 `.xacro` 结构与几何是否完全一致、限位是否只收紧不放宽 |
| 文档一致性 | `docs/joints.md`、`docs/model.md` 的数值与实测是否吻合（独立复核） |
| Markdown | 全部内部链接是否有效 |
| 发布元信息 | 版权主体统一且无占位残留、`package.xml` 的 `<url>` 指向真实仓库 |
| 发布前占位符 | 全文扫描未填写的尖括号占位符（仓库地址 / fork 地址 / 维护者邮箱）与 `package.xml` 中的模板描述字段 |
| 发布卫生 | 无缓存/临时/内部文件、脚本可执行权限 |

退出码非 0 表示存在 FAIL 项，可直接用于 CI 门禁。

> 这个脚本是**面向所有使用者的自检工具**（不是内部维护脚本）：克隆仓库后即可离线
> 验证模型、网格、文档与代码是否自洽；CI 的 `lint` 作业与 `scripts/build.sh`
> 都依赖它，因此**必须随仓库一同发布**。

## 8. 快速开始

```bash
cd /path/to/Dex-TF

bash run.sh              # 编译并启动【交互控制】（默认，会连接真机！）
bash run.sh display      # 编译并查看基础模型（纯离线，安全）
bash run.sh status       # 编译并查看【带真机状态桥接】的模型
bash run.sh interactive  # 编译并启动交互控制
```

第一次接触请从 `display` 开始，它完全离线、不会向机器人发送任何指令。

## 9. 三个 Launch 详解

### 9.1 `display.launch.py` — 离线模型查看

```bash
ros2 launch tiangong3_urdf display.launch.py
```

启动节点：`robot_state_publisher` + `joint_state_publisher_gui` + `rviz2`。

- 使用 `joint_state_publisher_gui` 手动拖动关节，**不连接机器人，零风险**；
- 适合核对模型外观、坐标系朝向、关节方向。

参数：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `model` | `share/tiangong3_urdf/urdf/tiangong3.urdf.xacro` | 模型文件绝对路径 |
| `rvizconfig` | `share/tiangong3_urdf/config/display.rviz` | RViz 配置路径 |

### 9.2 `display_with_status.launch.py` — 真机状态回显（只读）

```bash
ros2 launch tiangong3_urdf display_with_status.launch.py
```

启动节点：`robot_state_publisher` + `joint_state_publisher.py` + `rviz2`。

- 桥接节点订阅 `/head/status`、`/waist/status`、`/arm/status`、`/leg/status`
  与两路灵巧手状态，聚合发布 `/joint_states`；
- **只读模式**：不会向机器人发送任何控制指令，可安全用于观察；
- 超过 1 秒无数据时，机器人模型被红色半透明网格覆盖，提示离线。

### 9.3 `interactive_control.launch.py` — 交互式控制（⚠️ 会动真机）

```bash
ros2 launch tiangong3_urdf interactive_control.launch.py
```

启动节点：`robot_state_publisher` + `joint_state_publisher.py` +
`interactive_gui.py` + `rviz2`。

GUI 功能：

| 按钮 / 控件 | 行为 |
|-------------|------|
| 分组滑块（**6 组**） | 拖动即更新 Ghost 机器人预览，**不下发指令**。手部 2 组因 URDF 未接入手部 link 而**不显示**（详见[已知限制](#14-已知限制)） |
| `Sync to Real` | 将滑块与当前真实关节位置对齐；未连接时禁用 |
| `Execute` | 二次确认后下发位置指令到 4 路 `/xxx/cmd_pos`。**手部指令默认不下发**（`SEND_HAND_COMMANDS = False`，见下） |
| `Print Joint Values` | 在终端打印当前全部关节值，便于记录/复现 |

- 启动时自动执行一次 `Sync to Real`；
- 窗口标题显示 `[CONNECTED]` / `[DISCONNECTED]` 连接状态；
- 默认指令参数：`spd = 0.2`、`cur = 8.0`（相对保守，勿随意调大）；
- ⚠️ `spd` 的**单位以 `SetMotorPosition.msg` 的协议定义为准**（该文件标注为 `rpm`）。
  代码中不再断言为 rad/s；若固件按 rpm 解释，则 `0.2` 约为 `0.021 rad/s`（极慢），
  首次真机调试请与固件确认后再调整。
- ⚠️ 手部指令**默认关闭**：当前 URDF 未接入手部 link，GUI 中也没有手部滑条，
  手部关节目标值只是初始值；若无条件下发，在未收到手部状态时会把
  「归一化 1.0 = 双手完全张开」发给真机。接入手部模型后（见
  [`docs/model.md`](docs/model.md#手部模型接入预留)）再将源码中的
  `SEND_HAND_COMMANDS` 改为 `True`。

详细操作流程与排错见 [`docs/usage.md`](docs/usage.md)。

## 10. 通信协议概览

完整字段定义见 [`docs/protocol.md`](docs/protocol.md) 与
[`src/bodyctrl_msgs/README.md`](src/bodyctrl_msgs/README.md)。

### 状态订阅（机器人 → 控制端）

| 话题 | 消息类型 | 说明 |
|------|----------|------|
| `/head/status` | `bodyctrl_msgs/MotorStatusMsg` | 头部 2 关节（电机 ID 1–2） |
| `/waist/status` | `bodyctrl_msgs/MotorStatusMsg` | 腰部 3 关节（ID 31–33） |
| `/arm/status` | `bodyctrl_msgs/MotorStatusMsg` | 双臂 14 关节（ID 11–17、21–27） |
| `/leg/status` | `bodyctrl_msgs/MotorStatusMsg` | 双腿 12 关节（ID 51–56、61–66） |
| `/inspire_hand/state/left_hand` | `sensor_msgs/JointState` | 左手 6 自由度（归一化 0–1） |
| `/inspire_hand/state/right_hand` | `sensor_msgs/JointState` | 右手 6 自由度 |

### 控制指令（控制端 → 机器人）

| 话题 | 消息类型 | 说明 |
|------|----------|------|
| `/head/cmd_pos` | `bodyctrl_msgs/CmdSetMotorPosition` | 头部位置控制 |
| `/waist/cmd_pos` | `bodyctrl_msgs/CmdSetMotorPosition` | 腰部位置控制 |
| `/arm/cmd_pos` | `bodyctrl_msgs/CmdSetMotorPosition` | 双臂位置控制 |
| `/leg/cmd_pos` | `bodyctrl_msgs/CmdSetMotorPosition` | 双腿位置控制 |
| `/inspire_hand/ctrl/left_hand` | `sensor_msgs/JointState` | 左手抓握（归一化 0–1） |
| `/inspire_hand/ctrl/right_hand` | `sensor_msgs/JointState` | 右手抓握 |

`SetMotorPosition` 字段：

| 字段 | 类型 | 说明 | 本仓库默认 |
|------|------|------|-----------|
| `name` | `uint16` | 电机 ID | 由关节名映射 |
| `pos` | `float32` | 绝对目标位置 (rad) | 滑块值 |
| `spd` | `float32` | 期望速度 (rpm) | `0.2` |
| `cur` | `float32` | 最大电流 (A) | `8.0` |

### 本仓库额外发布的话题

| 话题 | 类型 | 说明 |
|------|------|------|
| `/joint_states` | `sensor_msgs/JointState` | 全机 31 关节（+ 手部预留）聚合状态 |
| `/robot_online_status` | `std_msgs/Bool` | 真机连接状态（1 s 超时判定） |
| `/ghost/markers` | `visualization_msgs/MarkerArray` | Ghost 机器人预览（青色半透明） |
| `/ghost/joint_states` | `sensor_msgs/JointState` | Ghost 关节状态（调试用） |
| `/offline_robot_markers` | `visualization_msgs/MarkerArray` | 离线红色覆盖网格 |

## 11. 电机 ID 与关节映射

```text
Head:     1 = head_yaw_joint,       2 = head_pitch_joint
Waist:   31 = waist_pitch_joint,   32 = waist_roll_joint,  33 = waist_yaw_joint
L Arm:   11 = shoulder_pitch_l, 12 = shoulder_roll_l, 13 = shoulder_yaw_l,
         14 = elbow_pitch_l,    15 = elbow_yaw_l,    16 = wrist_pitch_l, 17 = wrist_roll_l
R Arm:   21 ~ 27（与左臂同序）
L Leg:   51 = hip_pitch_l, 52 = hip_roll_l, 53 = hip_yaw_l,
         54 = knee_pitch_l, 55 = ankle_pitch_l, 56 = ankle_roll_l
R Leg:   61 ~ 66（与左腿同序）
Hand L:   1 = left_little_1, 2 = left_ring_1, 3 = left_middle_1,
          4 = left_index_1,  5 = left_thumb_2, 6 = left_thumb_1
Hand R:   1 ~ 6（与左手同序，right_*）
```

> 完整表格（含关节限位、力矩、速度上限、父子 link、轴向）见
> [`docs/joints.md`](docs/joints.md)。

## 12. 模型与网格资产

| 资产 | 路径 | 规格 |
|------|------|------|
| URDF | `urdf/tiangong3.urdf` | 39 link / 38 joint，GUI 与桥接节点解析用 |
| Xacro | `urdf/tiangong3.urdf.xacro` | 同上，Launch 默认加载（当前**未使用任何 xacro 宏**） |
| 本体网格 | `meshes/*.STL` | 39 个二进制 STL，米制，**简化版**（约 26 MB） |
| 手部网格 | `meshes_hand/*.STL` | 26 个二进制 STL，**当前 URDF 未引用**（约 14 MB） |

**关于两套模型文件的差异**：`tiangong3.urdf` 与 `.xacro` 的几何完全一致，
但**部分关节限位不同**（`.urdf` 为略收紧的保守值）。
详见 [`docs/model.md`](docs/model.md)，使用前请与机器人固件参数核对。

**关于精度**：本仓库的 `meshes/` 是用于可视化与碰撞检测的**简化网格**，
而非原始 CAD 高精度网格。若需要高精度模型（整机 CAD 导出、面片数约为本仓库的
3–10 倍），请联系模型权利人获取，详见 [`NOTICE`](NOTICE)。

> ⚠️ 模型与网格资产**不在 Apache-2.0 授权范围内**，公开再发布前请确认已获授权。

## 13. 常见问题（FAQ）

<details>
<summary><b>Q1: 为什么启动后机器人是"红色"的？</b></summary>

说明桥接节点超过 1 秒没有收到任何 `MotorStatusMsg`，即判定为离线。
请检查：是否与机器人处于同一 DDS 域、`ROS_DOMAIN_ID` 是否一致、
`ros2 topic list` 能否看到 `/arm/status` 等话题。
</details>

<details>
<summary><b>Q2: Execute 按钮是灰的，点不动？</b></summary>

未检测到真机在线（`/robot_online_status = false`）时按钮会被禁用。
先确保能看到真机状态话题，再点击 `Sync to Real`。
</details>

<details>
<summary><b>Q3: Ghost 机器人位置明显偏移/不对？</b></summary>

Ghost 由 `interactive_gui.py` 内的自实现 FK 计算，依赖 URDF 中的
关节父子关系、`origin` 与 `axis`。若模型被替换，请确认这些字段完整；
另外启动瞬间使用零位姿态可能出现偏差，执行一次 `Sync to Real` 即可。
</details>

<details>
<summary><b>Q4: 报错 <code>Package 'tiangong3_urdf' not found</code>？</b></summary>

没有 source 工作空间：

```bash
cd /path/to/Dex-TF && source install/setup.bash
```
</details>

<details>
<summary><b>Q5: 为什么 GUI 里没有手部滑块？</b></summary>

当前 URDF **未包含手部 link**（`meshes_hand/` 为预留资产，尚未接入）。
GUI 的滑条由 URDF 的关节限位生成，手部关节不在其中，因此
**Left/Right Hand 两个分组不会显示**（而不是显示为空的框）。

同时，为避免"未收到手部状态时把归一化 1.0（完全张开）发给真机"，
源码中 `SEND_HAND_COMMANDS` 默认 `False` —— 点击 `Execute` **不会**下发手部指令。
接入手部模型后见 [`docs/model.md`](docs/model.md#手部模型接入预留)。
</details>

<details>
<summary><b>Q6: <code>colcon build</code> 时 ament_lint 报版权/许可证错误？</b></summary>

本仓库各 `package.xml` 已填写 `Apache-2.0`，并保留了模板中
`ament_cmake_copyright_FOUND` / `cpplint` 的跳过设置。
若你自己新增源码文件，请补充对应版权头。
</details>

更多排错见 [`docs/usage.md`](docs/usage.md#故障排查)。

## 14. 已知限制

| # | 限制 | 影响 | 备注 |
|---|------|------|------|
| 1 | 模型未挂载手部 link | 手部姿态无法可视化；GUI 中**无手部滑条**（Left/Right Hand 分组不显示） | 网格资产已就绪，缺关节 origin/limit 数据，等待接入 |
| 2 | 两份模型文件关节限位不一致 | 以哪份为准会得到不同的软限位 | 见 [`docs/model.md`](docs/model.md) |
| 3 | `.xacro` 未参数化（无宏/无 `<xacro:arg>`） | 无法通过 launch 参数配置硬件版本 | 后续可改造 |
| 4 | 桥接节点超时判定为固定 1 s | 网络抖动可能误报离线 | 可提为 ROS 参数 |
| 5 | `/joint_states` 含 12 个手部关节名但 URDF 无对应 link | `robot_state_publisher` 会忽略这些关节；部分版本会打印节流告警 | 不影响 TF 树；接入手部模型后消除 |
| 6 | 手部指令默认不下发（`SEND_HAND_COMMANDS = False`） | 无法从 GUI 控制手部 | 有意为之的安全默认值；接入手部模型后改为 `True` |
| 7 | `spd` 字段单位存在协议/代码歧义（`rpm` vs `rad/s`） | `0.2` 的实际运动速度不确定 | 以固件为准，见 [`docs/protocol.md`](docs/protocol.md#3-控制指令) |
| 8 | 无仿真（Gazebo/MuJoCo）支持 | 只能看模型或动真机 | 见路线图 |
| 9 | 指令为一次性位置下发，无轨迹插值 | 关节间运动不同步 | 需上层规划器配合 |

## 15. 版本与修订记录

当前状态：**EVT2**。完整记录见 [`CHANGELOG.md`](CHANGELOG.md)，模型侧摘要：

| 日期 | 内容 |
|------|------|
| 2025-11-13 | 天工 2 Dex 1.25 版本 |
| 2025-11-26 | EVT 版本（无末端法兰盘、无手） |
| 2025-12-02 | EVT 版本修订关键参数表（有手） |
| 2025-12-08 | EVT 版本，带假手 |
| 2026-02-02 | EVT2 版本 |
| 2026-02-26 | EVT2 更新关节参数 |
| 2026-03-21 | EVT2 更新雷达坐标系方向 |
| 2026-09 | 整理为公开发布版本（v0.1.0） |

## 16. 路线图

- [ ] 接入灵巧手 URDF link（使用已就绪的 `meshes_hand/`）
- [ ] 将关节限位、超时阈值、速度/电流上限提为 ROS 参数
- [ ] 用 xacro 宏参数化机型差异，消除两份模型文件的不一致
- [ ] 增加 RViz 交互式 Marker（拖拽末端目标点）
- [ ] 增加轨迹插值与关节同步下发
- [ ] Gazebo / MuJoCo 仿真描述支持
- [ ] 单元测试：URDF 完整性校验、ID 映射一致性校验

## 17. 贡献指南

欢迎提交 Issue 与 Pull Request。请先阅读 [`CONTRIBUTING.md`](CONTRIBUTING.md)，
其中包含分支规范、提交信息格式、代码风格与自检清单。

## 18. 许可证

| 范围 | 许可证 |
|------|--------|
| 软件代码（`src/` 下 ROS 2 包、脚本、Launch、配置、文档） | [Apache-2.0](LICENSE) |
| 机器人模型与 3D 网格（`urdf/`、`meshes/`、`meshes_hand/`） | **专有资产，不适用开源许可**，见 [`NOTICE`](NOTICE) |
| 第三方依赖 | 各自原始许可证，见 [`NOTICE`](NOTICE#4-第三方依赖) |

```
Copyright 2026 Walker Tienkung Dex Project Contributors
```

> 版权主体已填写为 `Walker Tienkung Dex Project Contributors`；如需变更，
> 请按 [`NOTICE`](NOTICE) 的「版权主体」一节同步修改全部位置
> （`scripts/validate.py` 会校验一致性）。
>
> 公开发布前请确认已获得**模型与网格资产的公开传播授权**。

---

<sub>本项目与机器人整机厂商之间不存在官方从属关系；相关商标归其各自所有者。</sub>
