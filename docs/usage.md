# 使用说明与故障排查

本文档面向实际使用者，给出从零到操作的完整流程。
**操作真机前请先阅读 [`SECURITY.md`](../SECURITY.md)。**

## 目录

- [1. 环境准备](#1-环境准备)
- [2. 网络与 DDS 连通性](#2-网络与-dds-连通性)
- [3. 场景一：只看模型（离线）](#3-场景一只看模型离线)
- [4. 场景二：观察真机状态（只读）](#4-场景二观察真机状态只读)
- [5. 场景三：交互控制真机（危险）](#5-场景三交互控制真机危险)
- [6. 关闭与清理](#6-关闭与清理)
- [7. Launch 参数与配置](#7-launch-参数与配置)
- [8. 数据记录与回放](#8-数据记录与回放)
- [9. 故障排查](#9-故障排查)
- [10. 维护与升级](#10-维护与升级)

---

## 1. 环境准备

```bash
# 1) 检查 ROS 版本
echo $ROS_DISTRO          # 期望输出 humble

# 2) 进入工作空间并编译
cd /path/to/Dex-TF
source /opt/ros/humble/setup.bash
colcon build --symlink-install

# 3) 载入工作空间
source install/setup.bash

# 4) 确认两个包都在
ros2 pkg list | grep -E "tiangong3_urdf|bodyctrl_msgs"
```

> 💡 建议把 `source /opt/ros/humble/setup.bash` 与
> `source <workspace>/install/setup.bash` 写入 `~/.bashrc`，
> 避免每次开新终端都忘记。
>
> 注意：**`--symlink-install` 下 `scripts/` 中新增的 Python 文件仍需重新
> `colcon build`**（因为安装的是软链接列表，列表本身在编译时生成）。

## 2. 网络与 DDS 连通性

真机相关功能（场景二、三）要求控制端与机器人处于**同一 DDS 域**。

### 2.1 检查项

| 检查项 | 命令 / 方法 | 期望 |
|--------|-------------|------|
| 域 ID 一致 | `echo $ROS_DOMAIN_ID`（两端对比） | 相同（机器人通常为 `0`） |
| 中间件一致 | `echo $RMW_IMPLEMENTATION` | 与机器人一致（如 `rmw_fastrtps_cpp`） |
| 网段互通 | `ping <robot-ip>` | 通 |
| DDS 发现正常 | `ros2 topic list` | 能看到 `/arm/status` 等话题 |
| 数据在流动 | `ros2 topic hz /arm/status` | 有稳定频率输出 |

### 2.2 常见网络问题

- **只能看到自己的话题**：域 ID 或中间件不一致；或处于不同网段，
  组播发现被阻断。可尝试 `ros2 daemon stop && ros2 daemon start` 后重试。
- **能 ping 通但发现不了**：常见于跨网段/VPN 环境，组播不转发。
  可改用 Zenoh（`rmw_zenoh_cpp`）或配置 DDS 单播 peer 列表。
- **多网卡导致发现异常**：通过 `ROS_STATIC_PEERS` 或 DDS XML profile
  限定网卡。

## 3. 场景一：只看模型（离线）

**零风险，不需要机器人。**

```bash
ros2 launch tiangong3_urdf display.launch.py
```

或：

```bash
bash run.sh display
```

预期结果：

1. 弹出 RViz 窗口，`Fixed Frame = pelvis`；
2. 中央显示浅灰色人形机器人；
3. `joint_state_publisher_gui` 窗口中拖动任意滑块，对应部位实时变化；
4. 左侧 `Displays` 面板中 `RobotModel` 无红色报错。

**检查点**：

- 机器人为**灰色**（不是红色）——红色说明启动的是另外两个 launch；
- TF 面板中 `pelvis` 为根，所有 link 都有变换；
- 若模型显示为白色线框/缺件，检查是否所有 STL 都已安装
  （`--symlink-install` 下修改网格无需重编译）。

## 4. 场景二：观察真机状态（只读）

**不会向机器人发送任何指令。**

```bash
ros2 launch tiangong3_urdf display_with_status.launch.py
```

或：

```bash
bash run.sh status
```

预期结果：

| 现象 | 含义 |
|------|------|
| 机器人模型跟随真机姿态实时变化 | 桥接正常 |
| 模型整体被**红色半透明**覆盖 | 机器人离线（>1 s 无数据） |
| 终端出现 `无法连接到真实机器人...` 警告 | 同上（GUI 场景下会周期打印） |

辅助命令：

```bash
ros2 topic echo /robot_online_status      # true / false
ros2 topic hz /joint_states               # 应为 ~20 Hz
ros2 topic echo /joint_states --once      # 查看关节名与数值
```

## 5. 场景三：交互控制真机（危险）

> ⚠️ **执行前必须确认**：机器人已固定/吊装、执行区域无人、
> 急停按钮就在手边。

```bash
ros2 launch tiangong3_urdf interactive_control.launch.py
```

或：

```bash
bash run.sh interactive      # 与 run.sh（无参数）等价
```

### 5.1 标准操作流程

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | 启动后确认窗口标题为 `[CONNECTED]` | 若为 `[DISCONNECTED]`，先解决连接问题 |
| 2 | 观察 Ghost 与真机是否重合 | 启动时已自动执行一次 `Sync to Real` |
| 3 | 拖动**单个**滑块做小幅测试（如 5°） | Ghost（青色）立即跟随，真机**不动** |
| 4 | 点击 `Execute`，在确认框中确认 | 真机以 `spd=0.2`、`cur=8.0` 运动到目标 |
| 5 | 观察真机到位后，重复第 3–4 步扩大范围 | 每次只改一个部位，逐步验证 |
| 6 | 需要回到真机当前姿态时点 `Sync to Real` | 滑块与 Ghost 重新对齐到真机 |
| 7 | 需要记录数据时点 `Print Joint Values` | 终端输出全部关节值（保留 4 位小数） |

### 5.2 分组说明

GUI 中有 6 个**会显示**的分组，每个分组对应一个或两个下发话题：

| 分组 | 关节数 | 下发话题 |
|------|--------|----------|
| Head | 2 | `/head/cmd_pos` |
| Waist | 3 | `/waist/cmd_pos` |
| Left Arm / Right Arm | 7 + 7 | 合并为 `/arm/cmd_pos` |
| Left Leg / Right Leg | 6 + 6 | 合并为 `/leg/cmd_pos` |
| ~~Left Hand / Right Hand~~ | ~~6 + 6~~ | **当前不显示**（URDF 无手部 link；见下节） |

> 点击 `Execute` 会**同时下发全部 6 个已显示分组**（即使你只改了其中一个滑块）。
> 这意味着未被修改的关节也会收到一条等于**当前滑块值**的指令。
> 因此**执行前务必先 `Sync to Real`**，否则滑块中的旧值会被当作目标下发。

### 5.3 手部：当前状态（重要）

> ⚠️ **当前版本无法从 GUI 控制手部**，两点原因：

| 事项 | 说明 |
|------|------|
| **没有手部滑条** | 滑条由 URDF 的 `<limit>` 生成，而手部关节**不在 URDF 中** → Left/Right Hand 分组整组不显示 |
| **指令默认不下发** | 源码中 `SEND_HAND_COMMANDS = False`。因为手部目标值只是初始值（`0.0 rad`），若无条件下发会换算成**归一化 1.0 = 双手完全张开**，属于非预期指令 |

接入手部模型后（见 [`model.md`](model.md#手部模型接入预留)）：

- 手部滑条会自动出现，方向与其他关节**相反**：**右端 = 1.00（张开）**，左端 = 0.00（闭合）；
- 把源码中的 `SEND_HAND_COMMANDS` 改为 `True` 才会真正下发；
- 手部为**归一化**下发（见 [`protocol.md`](protocol.md#4-灵巧手协议)）；
- 手部**不会**在 RViz 中显示（URDF 无手部 link），只能通过真机观察；
- 手指远端关节由机械耦合驱动，无需单独控制。

### 5.4 安全边界（务必理解）

| 边界 | 说明 |
|------|------|
| **无碰撞检测** | 本工具链不检查自碰撞与环境碰撞，完全依赖使用者的判断 |
| **无轨迹规划** | 直接位置下发，机器人按自身速度规划运动；大角度跳变会快速运动 |
| **无看门狗** | 指令一旦发出，本工具不会撤销；只能靠急停或再次下发新目标 |
| **状态非实时** | GUI 中的真机位姿来自桥接节点 20 Hz 的聚合值，存在延迟 |
| **在线判定简化** | `/robot_online_status` 为 1 s 超时判定，网络抖动会误报 |

## 6. 关闭与清理

- **正常关闭**：直接关闭 RViz 与 GUI 窗口，再在终端 `Ctrl+C`。
  只关窗口不关终端会导致节点残留；
- **检查残留节点**：

```bash
ros2 node list
# 如有残留
pkill -f interactive_gui.py
pkill -f joint_state_publisher.py
```

> ⚠️ **机器人不会因关闭 GUI 而停止**——若正在运动中，它会继续运动到
> 上一次指令的目标位置。需要立即停止请使用急停。

## 7. Launch 参数与配置

### 7.1 可用参数

| Launch | 参数 | 默认值 |
|--------|------|--------|
| `display.launch.py` | `model` | `share/tiangong3_urdf/urdf/tiangong3.urdf.xacro` |
| | `rvizconfig` | `share/tiangong3_urdf/config/display.rviz` |
| `display_with_status.launch.py` | `model` | 同上 |
| | `rvizconfig` | 同上 |
| `interactive_control.launch.py` | `model` | 同上 |

用法示例（加载自定义模型）：

```bash
ros2 launch tiangong3_urdf display.launch.py \
  model:=$HOME/my_models/tiangong3.urdf \
  rvizconfig:=$(ros2 pkg prefix tiangong3_urdf)/share/tiangong3_urdf/config/display.rviz
```

> ⚠️ `interactive_control.launch.py` 中的 `model` 参数**只影响 TF 显示**；
> GUI 与桥接节点内部固定读取 `share/tiangong3_urdf/urdf/tiangong3.urdf`
> （硬编码路径，见 `interactive_gui.py::_load_urdf`）。
> 若替换了模型文件，请直接覆盖该路径下的文件。

### 7.2 自定义 RViz 布局

RViz 中调整布局后，`File → Save Config As` 覆盖到
`src/tiangong3_urdf/config/interactive.rviz` 即可
（`--symlink-install` 下立即生效）。

## 8. 数据记录与回放

```bash
# 记录关节状态与连接状态
ros2 bag record -o my_run /joint_states /robot_online_status

# 回放（不会控制机器人）
ros2 bag play my_run

# 查看内容
ros2 bag info my_run
```

> 记录到的 `/joint_states` 可通过 `ros2 bag play` + `robot_state_publisher`
> 离线重现整段运动，适合复盘与撰写报告。

## 9. 故障排查

### 9.1 启动类

| 现象 | 原因 | 解决 |
|------|------|------|
| `Package 'tiangong3_urdf' not found` | 未 source 工作空间 | `source install/setup.bash` |
| `executable 'joint_state_publisher.py' not found` | 未编译或未安装脚本 | `colcon build --symlink-install` |
| `ModuleNotFoundError: bodyctrl_msgs` | `bodyctrl_msgs` 未编译成功 | 查看 `log/latest_build/bodyctrl_msgs` |
| `ModuleNotFoundError: No module named 'python_qt_binding'` | 只装了 `python3-pyqt5`；`python_qt_binding` 模块由 ROS 包提供 | `sudo apt install ros-humble-python-qt-binding` |
| `ModuleNotFoundError: PyQt5` | 缺少底层 Qt 绑定（`ros-humble-python-qt-binding` 会自动带上） | `sudo apt install python3-pyqt5` |
| `ModuleNotFoundError: No module named 'ament_index_python'` / `'rclpy'` | ROS 环境未 source 或依赖不全 | `source /opt/ros/humble/setup.bash`；必要时 `sudo apt install ros-humble-ament-index-python ros-humble-rclpy` |
| `xacro: command not found` | 缺少 xacro | `sudo apt install ros-humble-xacro` |

### 9.2 显示类

| 现象 | 原因 | 解决 |
|------|------|------|
| 模型为**红色** | 机器人离线（>1 s 无状态数据） | 检查 DDS 连通性与状态话题 |
| 模型只显示部分 link | 部分 STL 未安装 | 检查 `install/.../share/tiangong3_urdf/meshes/` |
| 模型全白/无线框但无报错 | RViz 材质设置 | `RobotModel → Visual Enabled` 勾选，检查 `Alpha` |
| Ghost 机器人位置偏移 | 未 `Sync to Real` 或模型 origin 异常 | 先 `Sync to Real`；确认 URDF 的 `origin`/`axis` 完整 |
| RViz 启动很慢 | 首次加载 39 个 STL | 正常现象（约 26 MB 网格） |
| 拖滑块卡顿 | 每帧全量发布 39 个 marker | 见 [`architecture.md`](architecture.md#52-设计权衡) |

### 9.3 真机通信类

| 现象 | 原因 | 解决 |
|------|------|------|
| `Execute` 按钮灰色不可点 | `/robot_online_status` 为 false | 检查状态话题与 DDS 域 |
| 模型一直红色但话题有数据 | 话题名/类型不匹配 | `ros2 topic info /arm/status` 核对类型 |
| 状态数值全为 0 | 未收到任何 `MotorStatusMsg` | 检查机器人是否上电并使能 |
| 有状态但真机不动 | 指令话题名或电机 ID 不匹配 | 用 `ros2 topic info` 核对；确认电机 ID 映射 |
| 偶发误报离线 | 1 s 超时在网络抖动下过紧 | 见 [`architecture.md`](architecture.md#43-时序约束)，需改源码 |
| `robot_state_publisher` 警告未知关节 | `/joint_states` 含 12 个手部关节名而 URDF 无对应 link | 不影响 TF 树（RSP 忽略它们）；接入手部模型可消除 |

### 9.4 手部类

| 现象 | 原因 | 解决 |
|------|------|------|
| **GUI 里没有手部滑条** | URDF 未包含手部 link，滑条由 URDF 限位生成 | **正常现象**，见 [`model.md`](model.md#手部模型接入预留) |
| 点 `Execute` 后真机手部没动 | `SEND_HAND_COMMANDS = False`（安全默认） | 有意为之；接入手部模型后改为 `True` |
| 手部方向与直觉相反 | 归一化语义：1.0 = 张开 | 见 [`protocol.md`](protocol.md#4-灵巧手协议) |
| 手部话题无数据 | 手部控制器未上电或话题名不一致 | `ros2 topic list \| grep inspire` 核对 |

## 10. 维护与升级

```bash
# 拉取更新后重新编译
git pull
source /opt/ros/humble/setup.bash
colcon build --symlink-install

# 彻底清理重编（当出现奇怪的编译缓存问题时）
rm -rf build install log
colcon build --symlink-install
```

模型参数更新后，建议同步刷新自动生成的关节文档：

```bash
python3 scripts/gen_joint_docs.py          # 重新生成 docs/joints.md
python3 scripts/gen_joint_docs.py --check  # 校验是否与模型一致
```
