# 贡献指南

感谢你愿意为本项目做出贡献。本文档说明参与开发的流程与规范。

## 目录

- [1. 行为准则](#1-行为准则)
- [2. 开发环境](#2-开发环境)
- [3. 分支与提交规范](#3-分支与提交规范)
- [4. 代码风格](#4-代码风格)
- [5. 提交前自检清单](#5-提交前自检清单)
- [6. 文档与模型变更](#6-文档与模型变更)
- [7. 与真机相关的贡献（重要）](#7-与真机相关的贡献重要)
- [8. 提交 Issue](#8-提交-issue)
- [9. 开源许可与版权](#9-开源许可与版权)

---

## 1. 行为准则

- 尊重所有参与者，讨论对事不对人；
- 不发布他人隐私信息、内部资料与未授权内容；
- 涉及真机安全的问题优先私下沟通（见 [`SECURITY.md`](SECURITY.md)）。

## 2. 开发环境

| 项目 | 版本 |
|------|------|
| Ubuntu | 22.04 LTS |
| ROS 2 | Humble |
| Python | 3.10 |
| 构建 | `colcon` + `ament_cmake` |

```bash
# 主仓库: https://github.com/luckylhf/Dex-TF
git clone https://github.com/luckylhf/Dex-TF.git      # 或你的 fork 地址
cd Dex-TF
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

> `--symlink-install` 下修改 `launch/`、`urdf/`、`config/`、`scripts/` 无需重新编译。
> 但 **`scripts/` 中新添加的 Python 文件**（或 `CMakeLists.txt` 中
> `install(PROGRAMS ...)` 列表变化）仍需重新执行 `colcon build`。

## 3. 分支与提交规范

### 分支命名

```
feat/<简短描述>     新功能       例：feat/hand-urdf-integration
fix/<简短描述>      缺陷修复     例：fix/ghost-fk-offset
docs/<简短描述>     文档         例：docs/protocol-details
model/<简短描述>    模型参数调整  例：model/evt2-ankle-limits
chore/<简短描述>    杂项         例：chore/cleanup-scripts
```

### 提交流息（Conventional Commits）

```
<type>(<scope>): <简述>

<可选的详细说明>

<可选的关联 Issue：Closes #12>
```

`type` 取值：`feat` | `fix` | `docs` | `model` | `refactor` | `test` | `chore` | `perf`

`scope` 建议：`urdf` | `gui` | `bridge` | `msgs` | `launch` | `docs` | `ci`

示例：

```
feat(gui): 支持通过 ROS 参数配置速度与电流上限

fix(bridge): 修正灵巧手归一化角度换算的边界溢出

model(urdf): 同步 EVT2 踝关节俯仰限位
```

## 4. 代码风格

### Python

- 遵循 [PEP 8](https://peps.python.org/pep-0008/)，缩进 4 空格，行宽 ≤ 100；
- 使用类型注解标注公开函数签名；
- ROS 节点内部日志使用 `self.get_logger()`，不要用裸 `print()`
  （`Print Joint Values` 这类**面向用户输出**的功能除外）；
- 不要在导入阶段执行有副作用的操作（如 `rclpy.init()`），统一放在 `main()`；
- 中文注释可以接受，但**日志与异常信息建议中英一致**，便于检索。

### Launch / URDF / Xacro

- launch 文件内的路径一律通过 `FindPackageShare` / `PathJoinSubstitution` 构造，
  **禁止硬编码绝对路径**；
- 新增可调项请用 `DeclareLaunchArgument` 暴露，并给出 `description`；
- URDF 修改请保持 `link` / `joint` 命名规范：`<部位>_<动作>_<l|r>_link|joint`。

### 消息 / 服务

- 新增 `.msg` / `.srv` 时不要修改已有字段的**顺序与类型**（会破坏二进制兼容）；
- 需要破坏性变更时，新建 `XxxV2.msg` 而非原地修改，并在 PR 中说明迁移方案。

## 5. 提交前自检清单

```bash
# 1. 发布包完整性校验（不需要 ROS 环境，建议先跑这一条）
pip install trimesh numpy lxml xmlschema pyyaml     # 可选
python3 scripts/validate.py -v

# 2. 编译通过（已内置上面的校验）
bash scripts/build.sh

# 3. 模型可被 xacro 解析
xacro src/tiangong3_urdf/urdf/tiangong3.urdf.xacro > /dev/null

# 4. 离线启动自测（不需要真机）
ros2 launch tiangong3_urdf display.launch.py
```

- [ ] `python3 scripts/validate.py` 无 FAIL 项
- [ ] `colcon build` 无新增错误与警告
- [ ] `display.launch.py` 可正常打开 RViz 且模型无错位、无缺失网格
- [ ] 若改动 URDF，已运行 `python3 scripts/gen_joint_docs.py` 重新生成 `docs/joints.md`
- [ ] 若改动关节限位，已同步 `docs/model.md` 的差异表（`validate.py` 会校验）
- [ ] 新增文件已加入 `CMakeLists.txt` 的 `install(...)` 规则（否则不会被安装）
- [ ] 未提交构建产物、`__pycache__`、`.DS_Store`、内部配置文件
- [ ] 文档已同步更新（README / `docs/` / `CHANGELOG.md`）
- [ ] 提交信息符合规范

## 6. 文档与模型变更

- **文档**：中文文档为主（`README.md`、`docs/*.md`）；修改对外行为时，
  请同步更新 `README.en.md` 中的对应章节；
- **模型**：任何 URDF / 网格变更**必须**在 [`CHANGELOG.md`](CHANGELOG.md)
  与 [`docs/model.md`](docs/model.md) 中记录：变更日期、对应硬件版本（EVT/EVT2…）、
  变更内容与影响；
- **网格**：请勿提交未经优化的高精度 CAD 网格（单文件建议 < 10 MB），
  提交前请说明来源与授权情况（见 [`NOTICE`](NOTICE)）。

## 7. 与真机相关的贡献（重要）

任何会**向真实机器人发送指令**的改动，PR 描述中必须包含：

1. 改动影响的关节 / 话题清单；
2. 默认 `spd` / `cur` 取值及其安全性论证；
3. 已在何种条件下验证（真机 / 仿真 / 仅静态检查）；
4. 失效模式分析：通信中断、超时、异常关节值时的行为；
5. 若涉及关节限位、零位、方向符号变更，请附上厂商参数依据。

未提供上述信息的真机相关 PR 将被要求补充后再评审。

## 8. 提交 Issue

请使用以下模板组织信息：

```markdown
### 环境
- Ubuntu / ROS 2 版本：
- 机器人整机固件版本（如相关）：
- 本仓库版本 / commit：

### 复现步骤
1.
2.

### 期望行为

### 实际行为
（附完整终端日志、`ros2 topic list`、`ros2 topic echo <topic> --once` 输出）

### 附加信息
（截图、RViz 配置、是否真机在线等）
```

> 安全类问题请勿公开提交，见 [`SECURITY.md`](SECURITY.md#3-报告安全问题)。

## 9. 开源许可与版权

- 提交即表示你同意以 [Apache-2.0](LICENSE) 授权你的**代码**贡献；
- **模型与网格资产不适用该许可**，若你的贡献包含此类资产，
  必须在 PR 中声明其来源与授权依据（见 [`NOTICE`](NOTICE)）；
- 新增源码文件请在文件头添加版权与许可声明：

```python
# Copyright 2026 Walker Tienkung Dex Project Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
```
