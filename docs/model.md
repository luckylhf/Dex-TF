# 机器人模型与网格资产说明

本文档说明 `src/tiangong3_urdf/` 下的 URDF 模型与 STL 网格资产的构成、
差异、精度与使用注意事项。

## 目录

- [命名与模型数据来源](#命名与模型数据来源)
- [1. 资产清单](#1-资产清单)
- [2. 模型拓扑](#2-模型拓扑)
- [3. 两套模型文件的差异](#3-两套模型文件的差异)
- [4. 网格精度说明](#4-网格精度说明)
- [5. 材质与颜色](#5-材质与颜色)
- [6. 手部模型接入预留](#6-手部模型接入预留)
- [7. 使用模型资产时的注意事项](#7-使用模型资产时的注意事项)

---

## 命名与模型数据来源

### 包名 vs 模型数据

| 项目 | 说明 |
|------|------|
| 包名 | `tiangong3_urdf` —— **命名规范代次**，对齐天工 Dex 生态 |
| 模型数据 | **拓扑 / 网格来自天工 2 Dex EVT2**；**link 惯量与关节限位已按《天工行者 Dex V3 关键参数表》对齐** |
| 上游来源 | 结构：`Open-X-Humanoid/TienKung_URDF` 的 `tiangong2dex_urdf` 目录，commit `5c22178`；参数：`关键参数/URDF关键参数表 - 天工行者Dex(V3).csv` |

> ⚠️ 包名中的 "3" **不代表**模型数据已升级到天工 3 Dex。请勿据包名推断硬件版本。

### ⚠️ 与外部 `tiangong3_urdf` 包的命名冲突

同目录下的 `Dex-URDF/Tienkung_Dex_Model_All/`（天工 3.0 Dex V3 资源包）
**其 `package.xml` 的 `<name>` 也是 `tiangong3_urdf`**，且其
`urdf/tiangong3.urdf` 与本仓库的 `urdf/tiangong3.urdf` **同名但内容不同**。

如果两者被放入同一个 colcon 工作空间：

- colcon 会因**包名重复**报错或其中一个被遮蔽；
- `package://tiangong3_urdf/meshes/...` 的解析结果取决于 **source 顺序**，
  可能静默加载**错误的网格**（两套网格几何不同）。

**接入天工 3 Dex 时的正确做法**：不要保留两个同名包，而是用 3 Dex 的
URDF + meshes **替换**本仓库内的模型文件（见下方「替换步骤」），
或在你的工作空间里只保留其中一个。

### 替换为天工 3 Dex 模型的步骤

由于两代机型的 **link / joint 命名集合完全相同**（39 links / 38 joints），
替换后本仓库的 launch / GUI / 桥接代码**无需任何修改**：

```bash
# 1) 备份当前 2 Dex 模型（可选）
cp -r src/tiangong3_urdf/urdf  src/tiangong3_urdf/urdf.evt2.bak

# 2) 用 3 Dex 资源包的 URDF 覆盖（注意先确认 mesh URI 前缀为 tiangong3_urdf）
cp <3dex-repo>/urdf/tiangong3.urdf src/tiangong3_urdf/urdf/tiangong3.urdf

# 3) 替换网格（3 套可选：高精度 meshes / 可视化 meshes_simplify / 碰撞 meshes_convex）
cp <3dex-repo>/meshes/*.STL src/tiangong3_urdf/meshes/

# 4) 同步 xacro 与文档（两份模型文件必须保持一致）
cp src/tiangong3_urdf/urdf/tiangong3.urdf src/tiangong3_urdf/urdf/tiangong3.urdf.xacro
python3 scripts/gen_joint_docs.py      # 重新生成 docs/joints.md
python3 scripts/validate.py            # 校验（会检查网格引用与限位表一致性）
```

可选：3 Dex 资源包还提供挂灵巧手的整机 URDF
（`tiangong3_inspire.urdf` 101 links、`tiangong3_brainco.urdf` 83 links），
接入方法见[第 6 节](#6-手部模型接入预留)。

---

## 1. 资产清单

| 资产 | 路径 | 数量 | 大小 | 用途 |
|------|------|------|------|------|
| URDF（无宏） | `urdf/tiangong3.urdf` | 1 | ~44 KB | GUI 与桥接节点 `ET.parse()` 解析 |
| URDF（xacro 后缀） | `urdf/tiangong3.urdf.xacro` | 1 | ~44 KB | launch 文件默认加载 |
| 本体网格 | `meshes/*.STL` | 39 | ~26 MB | `visual` + `collision` |
| 手部网格 | `meshes_hand/*.STL` | 26 | ~14 MB | **当前未被引用** |
| RViz 配置 | `config/*.rviz` | 2 | ~32 KB | `display` / `interactive` |
| 关键参数表 | `关键参数/URDF关键参数表 - 天工行者Dex(V3).csv` | 1 | ~7 KB | 模型参数基准（link 惯量 + 关节限位） |

所有网格为**二进制 STL**，坐标单位为**米**，与 URDF 一致，无需额外缩放。

## 2. 模型拓扑

| 项目 | 数值 |
|------|------|
| robot 名称 | `tiangong3_urdf` |
| 根 link | `pelvis` |
| link 总数 | 39 |
| joint 总数 | 38（31 revolute + 7 fixed） |
| 模型总质量 | **65.818 kg**（不含手部） |

每个 link 均包含 `inertial`、`visual`、`collision` 三类标签，
`visual` 与 `collision` 使用**同一个 STL**（未生成简化碰撞体）。

> `collision` 直接复用可视化网格意味着：若将该模型用于物理仿真
> （Gazebo / MuJoCo / Pinocchio 等），碰撞检测的三角面片数偏高，
> 建议为仿真自行生成凸包或简化碰撞体。

完整的父子关系、轴向、限位、力矩与速度上限见 [`joints.md`](joints.md)。

## 3. 两套模型文件的差异

`tiangong3.urdf` 与 `tiangong3.urdf.xacro` **内容完全一致**
（所有 link、mesh 路径、origin、axis、惯量、限位均相同），差异只有一处：

### 3.1 根标签

```diff
- <robot name="tiangong3_urdf">
+ <robot name="tiangong3_urdf" xmlns:xacro="http://wiki.ros.org/xacro">
```

`.xacro` 文件仅声明了 xacro 命名空间，**并未使用任何 xacro 宏**
（无 `<xacro:property>`、无 `<xacro:macro>`、无 `<xacro:arg>`），
因此两个文件解析结果完全相同。

### 3.2 参数基准

两份文件的 link 惯量与关节限位均已统一，对齐
`关键参数/URDF关键参数表 - 天工行者Dex(V3).csv`（天工行者 Dex V3）：

- 39 个 link 的质量、质心、惯量与 CSV 逐条一致；
- 31 个 revolute 关节的下限 / 上限（度 → 弧度）、速度限制（RPM → rad/s）、
  力矩限制（N·m）与 CSV 逐条一致；
- 模型总质量 **65.818 kg**（不含手部）。

### 3.3 影响与建议

| 影响 | 说明 |
|------|------|
| **滑块范围 / RViz 显示范围** | 两份文件限位一致，GUI 滑块与 RViz 显示范围相同 |
| **TF / RViz 变换不受影响** | `robot_state_publisher` 只做正运动学，限位不参与计算 |
| **不影响真机** | 机器人固件使用自身的限位，URDF 限位**不会**被下发到真机 |

> 📌 **使用建议**：真机控制前请以**机器人固件实际参数**为准。
> 任何模型参数变更请同步更新 [`CHANGELOG.md`](../CHANGELOG.md) 并在 PR 中说明硬件版本。

## 4. 网格精度说明

### 4.1 当前网格是「简化网格」

`meshes/` 中的 STL 是面向**可视化与实时渲染**的**减面（decimation）版本**，
而非原始 CAD 高精度导出，文件体积较小、面片数较低。

以部分 link 为例（三角面片数）：

| link | 本仓库网格（简化） | 高精度原始模型 | 倍率 |
|------|--------------------|----------------|------|
| `pelvis` | 27,422 | 253,940 | ≈ 9.3× |
| `head_pitch_link` | 1,558 | 9,807 | ≈ 6.3× |
| `wrist_roll_l_link` | 3,166 | 11,322 | ≈ 3.6× |

- **包围盒基本一致**，模型**整体尺度与装配位置正确**；
- 简化过程中会丢失部分细节特征（小圆角、倒角、微小凸台），
  因此**极少数 link 的包围盒会有毫米级差异**；
- 单位均为**米**，无需缩放。

> 若你需要用于**高保真渲染、精细碰撞检测或学术论文配图**的高精度网格，
> 请联系模型权利人获取原始 CAD 导出模型（见 [`NOTICE`](../NOTICE)）。

### 4.2 检查网格信息

```bash
# 查看单个 STL 的面片数与包围盒（需要 numpy）
python3 - <<'PY'
import struct, sys
p = 'src/tiangong3_urdf/meshes/pelvis.STL'
with open(p, 'rb') as f:
    data = f.read()
n = struct.unpack('<I', data[80:84])[0]
print(f'{p}: {n} triangles, {len(data)} bytes')
PY

# 可视化单个网格（需要 MeshLab 或 Blender）
# meshlab src/tiangong3_urdf/meshes/pelvis.STL
```

## 5. 材质与颜色

模型的 `visual` 标签中材质统一为浅灰：

```xml
<material name="">
  <color rgba="0.752941176470588 0.752941176470588 0.752941176470588 1" />
</material>
```

即 RGB ≈ (192, 192, 192)，不透明（`alpha = 1`），**不随 link 变化**。
`pelvis` 使用了命名材质 `pelvis_color`，颜色值相同。

> 因此 RViz 中整机为统一的浅灰色，无法通过颜色区分部位。
> 如需分区着色，可在 RViz 中对不同 link 使用 `RobotModel` 的
> `Links` 覆盖，或修改 URDF 中的材质定义。
> Ghost 预览的青色（`0, 1, 1, 0.6`）与离线告警的红色（`1, 0, 0, 1`）
> 均在运行时生成，与 URDF 材质无关。

## 6. 手部模型接入预留

`meshes_hand/` 已包含 26 个手部网格（左手 12 + 右手 12 + 左右掌基座各 1），
但**当前 URDF 未引用**，因此：

- RViz 中**看不到手**；
- `robot_state_publisher` 不会发布手部 link 的 TF；
- 但手部**控制与状态话题仍然正常工作**（`/inspire_hand/*`）。

网格文件命名：

```text
L_base_link.STL                                  # 左掌基座
left_index_1.STL   left_index_2.STL
left_middle_1.STL  left_middle_2.STL
left_ring_1.STL    left_ring_2.STL
left_little_1.STL  left_little_2.STL
left_thumb_1.STL   left_thumb_2.STL  left_thumb_3.STL  left_thumb_4.STL
R_base_link.STL                                  # 右掌基座
right_*.STL                                      # 右手指，命名规则同上
```

### 接入手部模型的步骤（概要）

1. 在 URDF 中新增手部 link，`mesh filename` 指向
   `package://tiangong3_urdf/meshes_hand/...`；
2. 关节命名需与脚本中的映射**完全一致**
   （`{left,right}_{little,ring,middle,index,thumb}_1_joint`、
   `{left,right}_thumb_2_joint`，见 [`joints.md`](joints.md#1-电机-id--关节名映射)）；
3. 远端关节（`*_2_joint`、`thumb_3/4_joint`）由近端关节**机械耦合**驱动，
   可用 `<mimic>` 标签或保持 fixed；
4. 为每个手部 link 补充 `inertial`（否则部分仿真器会报错）；
5. 将手腕末端 `<wrist_roll_*_link>` 改为手部基座的父 link，
   并将原 `*_tcp_link` 作为手部基座的子 link 保留（坐标不变）。

> 接入后 `/joint_states` 中的手部关节名将与 URDF 匹配，
> `robot_state_publisher` 的相关警告会消失。

## 7. 使用模型资产时的注意事项

| # | 事项 |
|---|------|
| 1 | **授权**：模型与网格**不在 Apache-2.0 授权范围内**，公开再发布前请确认已获授权，见 [`NOTICE`](../NOTICE) |
| 2 | **精度**：当前为简化网格，不适合高精度量测；如需原始 CAD 请联系权利人 |
| 3 | **碰撞**：`collision` 复用 `visual` 网格，物理仿真前建议自行简化 |
| 4 | **限位**：两份模型文件的限位已统一（对齐天工行者 Dex V3 关键参数表），真机参数以固件为准（见 [3.3](#33-影响与建议)） |
| 5 | **坐标**：无 `world` / `base_footprint`，根为 `pelvis`；与地面/里程计对齐需自行添加静态变换 |
| 6 | **修改记录**：任何模型变更请同步更新 [`CHANGELOG.md`](../CHANGELOG.md) 并在 PR 中说明硬件版本（EVT/EVT2…） |
