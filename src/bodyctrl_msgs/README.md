# bodyctrl_msgs

天工机器人**机体控制通信协议**接口包
（Base Plugins：包含与机体控制等相关的基础功能节点，为算法和应用节点提供数据和服务）。

> 📖 本工具链实际使用的接口、话题与换算关系见
> [`docs/protocol.md`](../../docs/protocol.md)；
> 关节与电机 ID 映射见 [`docs/joints.md`](../../docs/joints.md)。

## 包内容

| 目录 | 内容 |
|------|------|
| `msg/` | 42 个消息定义：电机控制、电机状态、机体状态、电源、告警、灵巧手等 |
| `srv/` | 22 个服务定义：电机标定与启停、零位设置、运动规划等 |
| `doc/` | 节点级说明文档 |

## 按功能分类

| 分类 | 消息 |
|------|------|
| 电机控制 | `CmdMotorCtrl`、`CmdSetMotorPosition`、`CmdSetMotorSpeed`、`CmdSetMotorCurTor`、`CmdSetMotorDistance`、`SetMotorPosition`、`SetMotorSpeed`、`SetMotorCurTor`、`SetMotorDistance`、`MotorCtrl`、`MotorName` |
| 电机状态 | `MotorStatus`、`MotorStatus1`、`MotorStatusMsg`、`MotorStatusMsg1`、`MotorStatusMsg2`、`MotorStatusMsgPlate`、`WaistMotorStatus` |
| 腰部与灵巧手 | `CmdSetWaistMotorPos`、`CmdSetTsHandCtrl`、`CmdSetTsHandPosition`、`SetTsHandCtrl`、`SetTsHandCtrlItem`、`SetTsHandPosition`、`TsHandName`、`TsHandStatus`、`TsHandStatusMsg` |
| 机体状态 | `Imu`、`Euler`、`NodeState`、`Sri`、`SriName`、`SbusData` |
| 电源 | `PowerStatus`、`PowerBatteryStatus`、`PowerBoardCtrl`、`PowerBoardKeyStatus`、`PowerLightCtrl` |
| 告警与异常 | `Alarm`、`AlarmArray`、`Exception`、`ExceptionArray` |

| 分类 | 服务 |
|------|------|
| 电机控制与标定 | `MotorInit`、`MotorStart`、`MotorStop`、`MotorResetPosition`、`SetAngle`、`SetAngleFlexible`、`SetSpeed`、`SetForce`、`GetAngleAct`、`GetForceAct`、`JointSetZero`、`SetMotorZeroOffset`、`ResetMotorZeroOffset`、`SetClearError`、`GetError`、`GetStatus`、`XSensImuInit`、`VersionUpgrade` |
| 运动规划 | `Movement`、`PlanEefLine`、`PlanEefRelLine`、`PlanJointTraj` |

## 节点

| 节点 | 说明 |
|------|------|
| [Body Control Node](./doc/BodyControlNode.md) | 机体信息上报及机体基础控制功能 |

## 核心消息速览

```text
MotorStatusMsg          # 机器人 → 控制端（按部位发布）
├── std_msgs/Header header
└── MotorStatus[] status
    ├── uint16  name          # 电机 ID
    ├── float32 pos           # rad
    ├── float32 speed         # rad
    ├── float32 current       # A
    ├── float32 temperature
    └── uint32  error

CmdSetMotorPosition     # 控制端 → 机器人（位置控制）
├── std_msgs/Header header
└── SetMotorPosition[] cmds
    ├── uint16  name          # 电机 ID
    ├── float32 pos           # rad（绝对目标位置）
    ├── float32 spd           # rpm（期望速度）
    └── float32 cur           # A（最大电流）
```

## 编译

```bash
colcon build --packages-select bodyctrl_msgs
source install/setup.bash
ros2 interface show bodyctrl_msgs/msg/MotorStatusMsg
```

## 许可与授权

接口定义代码采用 **Apache-2.0**。本包描述的通信协议规格属于机器人厂商，
再发布或商用前请确认已获得相应授权，详见仓库根目录 [`NOTICE`](../../NOTICE)。
