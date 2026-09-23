# 更新日志 / Changelog

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)，
日期格式为 `YYYY-MM-DD`。

## [未发布]

### 计划中
- 接入灵巧手 URDF link（启用 `meshes_hand/`）
- 关节限位、超时阈值、速度/电流上限改为 ROS 参数
- xacro 宏参数化，消除两份模型文件的不一致
- Gazebo / MuJoCo 仿真描述
- 单元测试（URDF 完整性、ID 映射一致性）

---

## [v0.1.0] - 2026-09-23

首个对外发布版本。在原始工作空间基础上完成发布整理与包名统一。

### 新增

- **仓库工程化**
  - `README.md`（详细中文文档）与 `README.en.md`（英文）
  - `LICENSE`（Apache-2.0，覆盖软件代码）
  - `NOTICE`（明确区分开源代码与专有模型资产）
  - `SECURITY.md`（真机操作与网络安全要求）
  - `CONTRIBUTING.md`、`CHANGELOG.md`
  - `.gitignore`、`.gitattributes`
  - `.github/workflows/ci.yml`（ROS 2 Humble 下的 `colcon build` 校验）
  - `scripts/build.sh`、`scripts/release.sh`
  - `scripts/validate.py`：发布包完整性校验（12 类 27 项：URDF 结构、
    网格格式与可加载性、mesh 引用一致性、package.xml XSD 与目录名一致、
    launch 资源引用、电机映射三处一致性、两模型差异与文档吻合、
    文档数值独立复核、Markdown 链接、发布元信息（版权主体/仓库 URL）、
    发布前占位符扫描、发布卫生）
- **文档目录 `docs/`**
  - `architecture.md` 系统架构与数据流
  - `usage.md` 使用说明与故障排查
  - `protocol.md` `bodyctrl_msgs` 协议详解
  - `joints.md` 关节 / 电机 ID / 限位全表
  - `model.md` URDF 与网格资产说明
  - `assets/tiangong3_joint_control_demo.mp4` 演示视频

### 修复

- `bodyctrl_msgs/package.xml`：`<member_of_group>` 原先位于 `<test_depend>`
  之前，不符合 REP-149 / `package_format3.xsd` 的元素顺序要求
  （所有 `*_depend` 必须在前），会导致 `ament_xmllint` 报错；已调整顺序
  并通过官方 XSD 校验
- **`bodyctrl_msgs` 移除 4 个未使用的构建依赖**（自洽性审查发现）：
  - `find_package(sensor_msgs REQUIRED)` — 42 个 `.msg` / 22 个 `.srv`
    **均未引用** `sensor_msgs` 类型，且 `package.xml` 未声明 →
    在 `ros-base` 等最小环境会导致 CMake 配置失败
  - `find_package(yaml-cpp REQUIRED)` + `<depend>yaml_cpp_vendor</depend>`
    — 纯接口包无任何 C++ 代码使用 yaml-cpp；`yaml_cpp_vendor` 还是
    从源码编译的重依赖
  - `find_package(rclcpp REQUIRED)` / `find_package(rclcpp_components
    REQUIRED)` + `<depend>` — 包内无 C++ 源码、无组件注册
  - 顺带移除从未被使用的 `rosidl_get_typesupport_target()` 调用
  - 保留的依赖：`ament_cmake`、`rosidl_default_generators`、
    `std_msgs` / `geometry_msgs` / `builtin_interfaces`、
    `rosidl_default_runtime`、`member_of_group`
- **统一 `.msg` 单位注释**：
  - `MotorStatus.msg` 的 `speed`：`# rad` → `# rad/s`
  - `MotorStatusMsgPlate.msg` 的 `speed1`–`speed12`：共 12 处 `# rad` →
    `# rad/s`
  - `WaistMotorStatus.msg` 的 `pos`：`# rad/s` → `# rad`（原注释把位置
    误写成速度单位）
  - `MotorStatusMsg2.msg` 的 `pos` / `speed` / `current` 补上单位注释
  - `SetMotorPosition.msg` 的 `spd`：保留协议定义的 `rpm`，并注明与示例
    代码曾用的 `rad/s` 之间的歧义，指明**以固件为准**
- **交互 GUI 手部行为修复**（自洽性审查发现）：
  - docstring 不再宣称"31 revolute joints + 12 hand joints"，改为说明手部
    未接入 URDF、不显示滑条
  - 修复"分组内无可用关节仍渲染空分组框"：`n_sliders == 0` 时跳过该组，
    Left/Right Hand 两个空框不再出现
  - 新增 `SEND_HAND_COMMANDS = False`：**默认不再下发手部指令**。原先
    `execute_commands()` 无条件下发，在未收到手部状态时会把初始值
    `0.0 rad` 换算成**归一化 1.0（双手完全张开）**发给真机，属非预期指令
  - 移除 `cmd.spd = 0.2  # 0.2 rad/s` 的单位断言（与协议注释矛盾），
    改为指向 `.msg` 的协议定义
- 文档同步：`README.md`（GUI 功能表、演示示意图、FAQ Q5、已知限制表）、
  `docs/usage.md`（分组表 §5.2、手部章节 §5.3、排错 §9.3/§9.4）、
  `docs/protocol.md`（§2 `spd` 单位、§3.2 特点表、§4 手部、§5 话题表）、
  `docs/architecture.md`（手部映射说明）、`NOTICE`（maintainer 说明）

### 变更

- **包名统一（重要）**：`tiangong2dex_urdf` → **`tiangong3_urdf`**，对齐天工 Dex
  生态命名（同目录 `Dex-URDF/Tienkung_Dex_Model_All`（天工 3.0 Dex V3 资源包）
  同样使用 `package://tiangong3_urdf/...`）。共修改 **298 处 / 26 个文件**：
  - 目录 `src/tiangong2dex_urdf/` → `src/tiangong3_urdf/`
  - URDF 文件 `tiangong2dex.urdf(.xacro)` → `tiangong3.urdf(.xacro)`
  - `package.xml` 的 `<name>`、`CMakeLists.txt` 的 `project()`
  - URDF 中 78 处 `package://` mesh URI 与 `<robot name>`
  - 3 个 launch、2 个 Python 节点、`run.sh`、CI、5 份文档与全部脚本
  - 演示视频 `tiangong2dex_joint_control_demo.mp4` → `tiangong3_joint_control_demo.mp4`
- 品牌文案去掉版本号：`Tiangong 2 Dex` → `Tiangong Dex`
- `README.md` 新增「称谓对照」表：`Tiangong Dex`、`Tienkung Dex`、`天工 Dex`、
  `天工 2 Dex` 等为**同一对象的不同写法**，统一称谓为 **Walker Tienkung Dex**。
  仓库内文案**未做改写**（避免与上游仓库名、溯源记录、技术标识符混淆），
  以该对照表为准
- **模型数据未做任何改动**：仍为天工 2 Dex EVT2；命名与溯源记录见
  [`NOTICE`](NOTICE) §5，接入天工 3 Dex 模型的替换步骤见
  [`docs/model.md`](docs/model.md#命名与模型数据来源)
- 修正 `docs/model.md` 对两份模型文件限位差异的解释：不是人为的「保守裕量」，
  而是**两代机型参数**——`tiangong3.urdf`（无宏）限位与天工 3.0 Dex V3 有
  **28/31 一致**，`tiangong3.urdf.xacro` 仅 8/31 一致（2 Dex 参数）

- `package.xml`（两个包）：补齐 `description`、`license`（`Apache-2.0`）、
  版本号统一为 `0.1.0`；`tiangong3_urdf` 补充 `geometry_msgs` 依赖
- `run.sh`：增加工作空间自动定位、`set -euo pipefail`、ROS 环境检查、
  未知参数提示与帮助信息
- `tiangong3_urdf/README.md`：由简略修订记录扩充为包级说明

### 移除

- `.claude/settings.local.json`（本地 AI 工具会话配置）
- `src/bodyctrl_msgs/.gitlab-ci.yml`（内部 GitLab CI 配置，含内网镜像地址）
- `__pycache__/`、`.DS_Store` 等非源码文件
- 打包快照 `ros_dex_tf.v0.1.zip` 移出版本控制（改用 Release 附件）

---

## 模型侧修订记录（上游）

以下记录来自 `src/tiangong3_urdf/README.md`，为机器人模型的版本演进历史：

| 日期 | 内容 |
|------|------|
| 2025-11-13 | 天工 2 Dex **1.25 版本** |
| 2025-11-26 | 天工 2 Dex **EVT 版本**（无末端法兰盘、无手） |
| 2025-12-02 | EVT 版本，修订关键参数表（有手） |
| 2025-12-08 | EVT 版本，带假手 |
| 2026-02-02 | **EVT2 版本** |
| 2026-02-26 | EVT2 更新关节参数 |
| 2026-03-21 | EVT2 更新雷达坐标系方向 |

当前仓库模型对应 **EVT2**（2026-03-21 更新雷达坐标系方向之后）。

---

## 版本号约定

| 变更类型 | 版本递增 | 示例 |
|----------|----------|------|
| 破坏性变更（话题名、消息字段、launch 参数不兼容） | MAJOR | `1.0.0 → 2.0.0` |
| 新增功能（新 launch、新话题、新文档章节） | MINOR | `0.1.0 → 0.2.0` |
| 修复 / 文档 / 模型参数微调 | PATCH | `0.1.0 → 0.1.1` |
