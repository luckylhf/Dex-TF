# 通信协议详解（bodyctrl_msgs）

本仓库的 `bodyctrl_msgs` 包定义了与控制端交互的全部话题与服务。
本文档汇总本工具链**实际使用**的接口，完整消息清单见
[`msg/`](../src/bodyctrl_msgs/msg) 与 [`srv/`](../src/bodyctrl_msgs/srv)。

## 目录

- [1. 话题总览](#1-话题总览)
- [2. 使用的消息结构](#2-使用的消息结构)
- [3. 控制指令](#3-控制指令)
- [4. 灵巧手协议](#4-灵巧手协议)
- [5. 本仓库发布的话题](#5-本仓库发布的话题)
- [6. 完整消息与服务清单](#6-完整消息与服务清单)
- [7. 调试命令速查](#7-调试命令速查)

---

## 1. 话题总览

### 1.1 状态反馈（机器人 → 控制端）

| 话题 | 类型 | 频率（实测/预期） | 内容 |
|------|------|-------------------|------|
| `/head/status` | `MotorStatusMsg` | ~100 Hz | 头部 2 关节（电机 ID 1–2） |
| `/waist/status` | `MotorStatusMsg` | ~100 Hz | 腰部 3 关节（ID 31–33） |
| `/arm/status` | `MotorStatusMsg` | ~100 Hz | 双臂 14 关节（ID 11–17、21–27） |
| `/leg/status` | `MotorStatusMsg` | ~100 Hz | 双腿 12 关节（ID 51–56、61–66） |
| `/inspire_hand/state/left_hand` | `sensor_msgs/JointState` | — | 左手 6 自由度（归一化 0–1） |
| `/inspire_hand/state/right_hand` | `sensor_msgs/JointState` | — | 右手 6 自由度（归一化 0–1） |

> 频率为经验值，实际以机器人固件配置为准。本仓库桥接节点不依赖具体频率
> （使用覆盖式更新 + 固定 20 Hz 发布）。

### 1.2 控制指令（控制端 → 机器人）

| 话题 | 类型 | 说明 |
|------|------|------|
| `/head/cmd_pos` | `CmdSetMotorPosition` | 头部位置控制 |
| `/waist/cmd_pos` | `CmdSetMotorPosition` | 腰部位置控制 |
| `/arm/cmd_pos` | `CmdSetMotorPosition` | 双臂位置控制（左右臂合并在一帧内） |
| `/leg/cmd_pos` | `CmdSetMotorPosition` | 双腿位置控制（左右腿合并在一帧内） |
| `/inspire_hand/ctrl/left_hand` | `sensor_msgs/JointState` | 左手抓握指令（归一化 0–1） |
| `/inspire_hand/ctrl/right_hand` | `sensor_msgs/JointState` | 右手抓握指令（归一化 0–1） |

### 1.3 本仓库内部话题

| 话题 | 类型 | 发布者 |
|------|------|--------|
| `/joint_states` | `sensor_msgs/JointState` | 桥接节点 |
| `/robot_online_status` | `std_msgs/Bool` | 桥接节点 |
| `/robot_status_marker` | `visualization_msgs/Marker` | 桥接节点（当前用于 DELETE，保留扩展） |
| `/offline_robot_markers` | `visualization_msgs/MarkerArray` | 桥接节点 |
| `/ghost/markers` | `visualization_msgs/MarkerArray` | 交互 GUI |
| `/ghost/joint_states` | `sensor_msgs/JointState` | 交互 GUI |

## 2. 使用的消息结构

### `bodyctrl_msgs/MotorStatusMsg`

```text
std_msgs/Header header
MotorStatus[] status
```

### `bodyctrl_msgs/MotorStatus`

```text
uint16 name          # 电机 ID（见 joints.md 映射表）
float32 pos          # 当前位置 (rad)          ← 本工具链使用
float32 speed        # 当前速度 (rad)
float32 current      # 当前电流 (A)
float32 temperature  # 温度
uint32 error         # 错误码
```

> 桥接节点目前**只使用 `name` 与 `pos`**；`speed` / `current` / `temperature` /
> `error` 未接入可视化，可作为后续扩展点（例如在 RViz 中以文字 marker 显示）。

### `bodyctrl_msgs/CmdSetMotorPosition`

```text
std_msgs/Header header
SetMotorPosition[] cmds
```

### `bodyctrl_msgs/SetMotorPosition`

```text
uint16 name   # 电机 ID
float32 pos   # 绝对目标位置 (rad)
float32 spd   # 期望速度（协议标注 rpm）
float32 cur   # 最大电流 (A)
```

> ⚠️ **`spd` 的单位存在歧义，必须以固件为准。**
>
> | 来源 | 说法 |
> |------|------|
> | 本 `.msg` 文件（协议定义） | `rpm` |
> | `interactive_gui.py` 原注释 | 曾写作 `# 0.2 rad/s`（**已删除该断言**） |
>
> 现在的处理方式：**代码与文档统一以 `.msg` 的协议定义为准（`rpm`）**，
> 不再由代码注释另行断言单位。若固件实际按 `rad/s` 解释，请以固件为准
> 并同步修改 `.msg` 注释。
>
> 实践影响：若确为 `rpm`，则 `0.2 rpm ≈ 0.021 rad/s`，属于**极慢**；
> 首次真机调试请从极小值开始，并在空载、有监护的条件下验证。

## 3. 控制指令

### 3.1 交互 GUI 的下发行为

点击 `Execute` 后，`interactive_gui.py::execute_commands()` 按部位构建 4 帧指令：

```python
msg = CmdSetMotorPosition()
msg.header.stamp = now
for jn in joint_list:                  # 该部位的关节列表
    if jn in JOINT_TO_MOTOR_ID:
        cmd = SetMotorPosition()
        cmd.name = JOINT_TO_MOTOR_ID[jn]   # 关节名 → 电机 ID
        cmd.pos  = joint_positions[jn]     # 滑块对应的目标角 (rad)
        cmd.spd  = 0.2                     # 速度
        cmd.cur  = 8.0                     # 电流上限 (A)
        msg.cmds.append(cmd)
pub.publish(msg)
```

| 部位话题 | 包含的关节 |
|----------|-----------|
| `/head/cmd_pos` | `head_yaw`, `head_pitch` |
| `/waist/cmd_pos` | `waist_pitch`, `waist_roll`, `waist_yaw` |
| `/arm/cmd_pos` | 左臂 7 + 右臂 7 = 14 个 |
| `/leg/cmd_pos` | 左腿 6 + 右腿 6 = 12 个 |

### 3.2 下发特性与注意事项

| 特性 | 说明 |
|------|------|
| **一次性位置下发** | 不做轨迹插值，机器人自身按 `spd` 运动到目标；多个关节同时收到指令但**不保证同步到达** |
| **绝对位置** | `pos` 为绝对角度（rad），不是增量 |
| **未包含的关节保持不动** | 只发送出现在列表中的电机；未连接的关节不会收到指令 |
| **无心跳 / 无确认** | 协议中没有应答机制，GUI 无法感知指令是否被接受，只能通过状态反馈间接观察 |
| **手部为归一化量** | 与本体不同，手部使用 0–1 归一化值，见下节 |
| **手部指令默认不下发** | 源码常量 `SEND_HAND_COMMANDS = False`，`Execute` 只下发 4 路本体话题；原因见 §4 |

## 4. 灵巧手协议

灵巧手（Inspire Hand）使用标准 `sensor_msgs/JointState` 传输**归一化开合度**，
而非弧度：

| 方向 | 话题 | 语义 |
|------|------|------|
| 状态 | `/inspire_hand/state/{left,right}_hand` | `position[i]` ∈ [0,1]，**1.0 = 完全张开**，0.0 = 完全闭合 |
| 控制 | `/inspire_hand/ctrl/{left,right}_hand` | 同上；`name` 字段固定为 `['1'..'6']` |

### 4.1 手部电机 ID ↔ 关节名 ↔ 角度上限

| 电机 ID | 关节名 | 角度上限 (rad) |
|---------|--------|----------------|
| 1 | `{side}_little_1_joint` | 1.333 |
| 2 | `{side}_ring_1_joint` | 1.333 |
| 3 | `{side}_middle_1_joint` | 1.333 |
| 4 | `{side}_index_1_joint` | 1.333 |
| 5 | `{side}_thumb_2_joint` | 0.48 |
| 6 | `{side}_thumb_1_joint` | 1.246165 |

### 4.2 换算关系

```text
状态方向（读）:  rad = (1.0 - normalized_value) * limit
控制方向（写）:  normalized_value = 1.0 - (rad / limit)
```

即：**归一化 1.0 对应 rad = 0（完全张开）**，
归一化 0.0 对应 `rad = limit`（完全闭合/收拢）。

> ⚠️ 手指的远端关节（`*_2_joint`、`thumb_3/4`）由近端关节**机械耦合**驱动，
> 不需要单独下发。GUI 中的耦合关系定义在 `FINGER_COUPLING`，仅用于 Ghost 预览联动。
>
> ⚠️ **当前版本 GUI 不会下发手部指令**：手部关节不在 URDF 中（无滑条、无
> `joint_limits`），且源码中 `SEND_HAND_COMMANDS = False`。因为手部目标值
> 只是初始值 `0.0 rad`，若无条件下发会换算成**归一化 1.0（完全张开）**，
> 属于非预期指令。接入手部模型后再将该常量改为 `True`。

## 5. 本仓库发布的话题

| 话题 | 类型 | 说明 |
|------|------|------|
| `/joint_states` | `sensor_msgs/JointState` | 31 个本体关节 + **12 个手部关节名**（手部在 URDF 中无对应 link，`robot_state_publisher` 会忽略它们）。仅 `name` 与 `position` 填充，`velocity` / `effort` 为空 |
| `/robot_online_status` | `std_msgs/Bool` | `true` = 最近 1 s 内收到过状态数据 |
| `/offline_robot_markers` | `visualization_msgs/MarkerArray` | 离线时为红色覆盖网格；在线时发送 `DELETEALL` |
| `/ghost/markers` | `visualization_msgs/MarkerArray` | Ghost 机器人（青色半透明，`frame_id = pelvis`） |
| `/ghost/joint_states` | `sensor_msgs/JointState` | Ghost 关节状态（调试/二次开发用） |

> `/robot_status_marker` 目前仅用于周期发送 `TEXT_VIEW_FACING` 的 `DELETE` 动作
> （清除历史 marker），属于兼容性保留，未实际显示文本。

## 6. 完整消息与服务清单

### 6.1 消息（42 个）

<details>
<summary>点击展开</summary>

**电机控制**

`CmdMotorCtrl` · `CmdSetMotorCurTor` · `CmdSetMotorDistance` ·
`CmdSetMotorPosition` · `CmdSetMotorSpeed` · `MotorCtrl` · `MotorName` ·
`SetMotorCurTor` · `SetMotorDistance` · `SetMotorPosition` · `SetMotorSpeed`

**电机状态**

`MotorStatus` · `MotorStatus1` · `MotorStatusMsg` · `MotorStatusMsg1` ·
`MotorStatusMsg2` · `MotorStatusMsgPlate` · `WaistMotorStatus`

**腰部 / 灵巧手**

`CmdSetWaistMotorPos` · `CmdSetTsHandCtrl` · `CmdSetTsHandPosition` ·
`SetTsHandCtrl` · `SetTsHandCtrlItem` · `SetTsHandPosition` ·
`TsHandName` · `TsHandStatus` · `TsHandStatusMsg`

**机体状态**

`Imu` · `Euler` · `NodeState` · `Sri` · `SriName` · `SbusData`

**电源系统**

`PowerStatus` · `PowerBatteryStatus` · `PowerBoardCtrl` ·
`PowerBoardKeyStatus` · `PowerLightCtrl`

**告警 / 异常**

`Alarm` · `AlarmArray` · `Exception` · `ExceptionArray`

</details>

### 6.2 服务（22 个）

<details>
<summary>点击展开</summary>

**电机控制与标定**

`GetAngleAct` · `SetAngle` · `SetAngleFlexible` · `SetSpeed` · `SetForce` ·
`GetForceAct` · `MotorInit` · `MotorStart` · `MotorStop` ·
`MotorResetPosition` · `JointSetZero` · `SetMotorZeroOffset` ·
`ResetMotorZeroOffset` · `SetClearError` · `GetError` · `GetStatus` ·
`XSensImuInit` · `VersionUpgrade`

**运动规划**

`Movement` · `PlanEefLine` · `PlanEefRelLine` · `PlanJointTraj`

</details>

> 本工具链目前**未使用任何服务**，它们为上层运动规划与标定工具预留。

## 7. 调试命令速查

```bash
# 查看机器人是否在发布状态
ros2 topic list | grep status
ros2 topic hz /arm/status
ros2 topic echo /waist/status --once

# 查看桥接节点输出
ros2 topic echo /joint_states --once
ros2 topic echo /robot_online_status

# 手动下发一条位置指令（危险！仅在安全条件下使用）
# 注意：需要自行构造 CmdSetMotorPosition，建议用 GUI 或编写脚本

# 查看关节在 TF 中的实际位置
ros2 run tf2_ros tf2_echo pelvis wrist_roll_l_link

# 录包用于事后分析
ros2 bag record /joint_states /robot_online_status
```

> 手动发布控制话题会导致**机器人运动**，请务必遵守
> [`SECURITY.md`](../SECURITY.md) 中的安全要求。
