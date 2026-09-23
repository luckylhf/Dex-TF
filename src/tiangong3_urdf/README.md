# tiangong3_urdf

Tiangong Dex 人形机器人的 **描述与可视化工具包**。

> 📖 完整文档请见[仓库根目录 README](../../README.md) 与 [`docs/`](../../docs)。
> 本文件仅说明包内的目录职责与模型版本历史。

> ⚠️ **命名说明**：本包名 `tiangong3_urdf` 为**统一命名规范代次**，
> 内嵌模型数据（URDF 结构 / 惯量 / 网格几何）仍为**天工 2 Dex EVT2**，
> 来源于上游 `Open-X-Humanoid/TienKung_URDF` 的 `tiangong2dex_urdf` 目录。
> 请勿据包名推断硬件版本。详见 [`NOTICE`](../../NOTICE#5-命名与溯源) 与
> [`docs/model.md`](../../docs/model.md#命名与模型数据来源)。

## 包内容

```text
tiangong3_urdf/
├── urdf/
│   ├── tiangong3.urdf          # GUI / 桥接节点解析用（保守限位）
│   └── tiangong3.urdf.xacro    # launch 默认加载（当前无 xacro 宏）
├── meshes/                        # 本体 39 个 STL（简化网格，26 MB）
├── meshes_hand/                   # 灵巧手 26 个 STL（预留，当前未被引用）
├── launch/
│   ├── display.launch.py               # 离线模型查看
│   ├── display_with_status.launch.py   # 真机状态回显（只读）
│   └── interactive_control.launch.py   # 交互控制（会下发指令）
├── config/
│   ├── display.rviz               # 基础显示
│   └── interactive.rviz           # 交互调试（MarkerArray + TF）
├── scripts/
│   ├── joint_state_publisher.py   # 真机状态 → /joint_states 桥接
│   └── interactive_gui.py         # Qt 控制面板 + Ghost 预览
├── CMakeLists.txt                 # 仅 install DIRECTORY / PROGRAMS，无 C++ 编译
└── package.xml
```

## 使用

```bash
ros2 launch tiangong3_urdf display.launch.py
ros2 launch tiangong3_urdf display_with_status.launch.py
ros2 launch tiangong3_urdf interactive_control.launch.py
```

> ⚠️ `interactive_control.launch.py` 会向真实机器人下发运动指令，
> 使用前请阅读 [`SECURITY.md`](../../SECURITY.md)。

## 模型规格

| 项目 | 数值 |
|------|------|
| 根 link | `pelvis` |
| link / joint | 39 / 38（31 revolute + 7 fixed） |
| 总质量 | 63.272 kg（不含手部） |

关节限位、电机 ID 映射、TF 树结构见
[`docs/joints.md`](../../docs/joints.md)（由 `scripts/gen_joint_docs.py` 自动生成）。
模型与网格的差异、精度说明见 [`docs/model.md`](../../docs/model.md)。

## 模型修订记录

| 日期 | 版本 / 内容 |
|------|-------------|
| 2025-11-13 | 天工 2 Dex 1.25 版本 |
| 2025-11-26 | EVT 版本（无末端法兰盘、无手） |
| 2025-12-02 | EVT 版本，修订关键参数表（有手） |
| 2025-12-08 | EVT 版本，带假手 |
| 2026-02-02 | **EVT2 版本** |
| 2026-02-26 | EVT2 更新关节参数 |
| 2026-03-21 | EVT2 更新雷达坐标系方向 |

当前对应 **EVT2**（2026-03-21 之后）。

## 许可

代码采用 Apache-2.0；`urdf/`、`meshes/`、`meshes_hand/` 中的模型与网格资产
**不在该许可范围内**，详见 [`NOTICE`](../../NOTICE)。
