# 关节规格与电机 ID 映射表

> 本文件由 [`scripts/gen_joint_docs.py`](../scripts/gen_joint_docs.py) 从
> `src/tiangong3_urdf/urdf/tiangong3.urdf` 自动生成，**请勿手工编辑**。

## 0. 模型概要

| 项目 | 数值 |
|------|------|
| robot 名称 | `tiangong3_urdf` |
| 根 link | `pelvis` |
| link 总数 | 39 |
| joint 总数 | 38 （revolute 31 + fixed 7） |
| 模型总质量 | 65.818 kg |
| 长度单位 | m |
| 角度单位 | rad |

模型文件：`src/tiangong3_urdf/urdf/tiangong3.urdf`（GUI / 桥接节点解析用）、`src/tiangong3_urdf/urdf/tiangong3.urdf.xacro`（launch 默认加载）。
两份文件的几何完全一致，部分关节限位不同，见 [`model.md`](model.md#两套模型文件的差异)。

## 1. 电机 ID ↔ 关节名映射

| 部位 | 电机 ID | 关节名 |
|------|---------|--------|
| 头部 | 1 | `head_yaw_joint` |
|  | 2 | `head_pitch_joint` |
| 腰部 | 31 | `waist_pitch_joint` |
|  | 32 | `waist_roll_joint` |
|  | 33 | `waist_yaw_joint` |
| 左臂 | 11 | `shoulder_pitch_l_joint` |
|  | 12 | `shoulder_roll_l_joint` |
|  | 13 | `shoulder_yaw_l_joint` |
|  | 14 | `elbow_pitch_l_joint` |
|  | 15 | `elbow_yaw_l_joint` |
|  | 16 | `wrist_pitch_l_joint` |
|  | 17 | `wrist_roll_l_joint` |
| 右臂 | 21 | `shoulder_pitch_r_joint` |
|  | 22 | `shoulder_roll_r_joint` |
|  | 23 | `shoulder_yaw_r_joint` |
|  | 24 | `elbow_pitch_r_joint` |
|  | 25 | `elbow_yaw_r_joint` |
|  | 26 | `wrist_pitch_r_joint` |
|  | 27 | `wrist_roll_r_joint` |
| 左腿 | 51 | `hip_pitch_l_joint` |
|  | 52 | `hip_roll_l_joint` |
|  | 53 | `hip_yaw_l_joint` |
|  | 54 | `knee_pitch_l_joint` |
|  | 55 | `ankle_pitch_l_joint` |
|  | 56 | `ankle_roll_l_joint` |
| 右腿 | 61 | `hip_pitch_r_joint` |
|  | 62 | `hip_roll_r_joint` |
|  | 63 | `hip_yaw_r_joint` |
|  | 64 | `knee_pitch_r_joint` |
|  | 65 | `ankle_pitch_r_joint` |
|  | 66 | `ankle_roll_r_joint` |

> 灵巧手为独立控制器，ID 与关节名映射如下（归一化角度 0–1，`1.0` 为完全张开）：

| 手 | 电机 ID | 关节名 | 角度上限 (rad) |
|----|---------|--------|----------------|
| 左手 | 1 | `left_little_1_joint` | 1.333 |
| 左手 | 2 | `left_ring_1_joint` | 1.333 |
| 左手 | 3 | `left_middle_1_joint` | 1.333 |
| 左手 | 4 | `left_index_1_joint` | 1.333 |
| 左手 | 5 | `left_thumb_2_joint` | 0.48 |
| 左手 | 6 | `left_thumb_1_joint` | 1.246165 |
| 右手 | 1 | `right_little_1_joint` | 1.333 |
| 右手 | 2 | `right_ring_1_joint` | 1.333 |
| 右手 | 3 | `right_middle_1_joint` | 1.333 |
| 右手 | 4 | `right_index_1_joint` | 1.333 |
| 右手 | 5 | `right_thumb_2_joint` | 0.48 |
| 右手 | 6 | `right_thumb_1_joint` | 1.246165 |

## 2. revolute 关节限位表

> 数据来源：`src/tiangong3_urdf/urdf/tiangong3.urdf`。`下限 / 上限` 同时给出弧度与角度制值。

### 左腿

| 关节 | 电机 ID | 父 link | 子 link | 轴向 | 下限 (rad) | 上限 (rad) | 下限 (°) | 上限 (°) | 力矩 (N·m) | 速度 (rad/s) |
|------|---------|---------|---------|------|-----------|-----------|----------|----------|------------|--------------|
| `hip_pitch_l_joint` | 51 | `pelvis` | `hip_pitch_l_link` | `0 1 0` | -3.054326 | 2.792527 | -175 | 160 | 235 | 16.755161 |
| `hip_roll_l_joint` | 52 | `hip_pitch_l_link` | `hip_roll_l_link` | `1 0 0` | -0.418879 | 2.617994 | -24 | 150 | 235 | 16.755161 |
| `hip_yaw_l_joint` | 53 | `hip_roll_l_link` | `hip_yaw_l_link` | `0 0 1` | -1.396263 | 4.45059 | -80 | 255 | 150 | 13.823008 |
| `knee_pitch_l_joint` | 54 | `hip_yaw_l_link` | `knee_pitch_l_link` | `0 1 0` | -0.087266 | 2.530727 | -5 | 145 | 400 | 11.100294 |
| `ankle_pitch_l_joint` | 55 | `knee_pitch_l_link` | `ankle_pitch_l_link` | `0 1 0` | -1.186824 | 0.523599 | -68 | 30 | 55 | 14.137167 |
| `ankle_roll_l_joint` | 56 | `ankle_pitch_l_link` | `ankle_roll_l_link` | `1 0 0` | -0.523599 | 0.523599 | -30 | 30 | 55 | 14.137167 |

### 右腿

| 关节 | 电机 ID | 父 link | 子 link | 轴向 | 下限 (rad) | 上限 (rad) | 下限 (°) | 上限 (°) | 力矩 (N·m) | 速度 (rad/s) |
|------|---------|---------|---------|------|-----------|-----------|----------|----------|------------|--------------|
| `hip_pitch_r_joint` | 61 | `pelvis` | `hip_pitch_r_link` | `0 1 0` | -3.054326 | 2.792527 | -175 | 160 | 235 | 16.755161 |
| `hip_roll_r_joint` | 62 | `hip_pitch_r_link` | `hip_roll_r_link` | `1 0 0` | -2.617994 | 0.418879 | -150 | 24 | 235 | 16.755161 |
| `hip_yaw_r_joint` | 63 | `hip_roll_r_link` | `hip_yaw_r_link` | `0 0 1` | -4.45059 | 1.396263 | -255 | 80 | 150 | 13.823008 |
| `knee_pitch_r_joint` | 64 | `hip_yaw_r_link` | `knee_pitch_r_link` | `0 1 0` | -0.087266 | 2.530727 | -5 | 145 | 400 | 11.100294 |
| `ankle_pitch_r_joint` | 65 | `knee_pitch_r_link` | `ankle_pitch_r_link` | `0 1 0` | -1.186824 | 0.523599 | -68 | 30 | 55 | 14.137167 |
| `ankle_roll_r_joint` | 66 | `ankle_pitch_r_link` | `ankle_roll_r_link` | `1 0 0` | -0.523599 | 0.523599 | -30 | 30 | 55 | 14.137167 |

### 腰部

| 关节 | 电机 ID | 父 link | 子 link | 轴向 | 下限 (rad) | 上限 (rad) | 下限 (°) | 上限 (°) | 力矩 (N·m) | 速度 (rad/s) |
|------|---------|---------|---------|------|-----------|-----------|----------|----------|------------|--------------|
| `waist_yaw_joint` | 33 | `pelvis` | `waist_yaw_link` | `0 0 1` | -2.617994 | 3.228859 | -150 | 185 | 200 | 10.053096 |
| `waist_roll_joint` | 32 | `waist_yaw_link` | `waist_roll_link` | `1 0 0` | -0.436332 | 0.436332 | -25 | 25 | 150 | 13.823008 |
| `waist_pitch_joint` | 31 | `waist_roll_link` | `waist_pitch_link` | `0 1 0` | -0.523599 | 0.872665 | -30 | 50 | 150 | 13.823008 |

### 头部

| 关节 | 电机 ID | 父 link | 子 link | 轴向 | 下限 (rad) | 上限 (rad) | 下限 (°) | 上限 (°) | 力矩 (N·m) | 速度 (rad/s) |
|------|---------|---------|---------|------|-----------|-----------|----------|----------|------------|--------------|
| `head_yaw_joint` | 1 | `waist_pitch_link` | `head_yaw_link` | `0 0 1` | -1.047198 | 1.047198 | -60 | 60 | 6.3 | 7.644542 |
| `head_pitch_joint` | 2 | `head_yaw_link` | `head_pitch_link` | `0 1 0` | -0.872665 | 0.261799 | -50 | 15 | 6.3 | 7.644542 |

### 左臂

| 关节 | 电机 ID | 父 link | 子 link | 轴向 | 下限 (rad) | 上限 (rad) | 下限 (°) | 上限 (°) | 力矩 (N·m) | 速度 (rad/s) |
|------|---------|---------|---------|------|-----------|-----------|----------|----------|------------|--------------|
| `shoulder_pitch_l_joint` | 11 | `waist_pitch_link` | `shoulder_pitch_l_link` | `0 1 0` | -2.844887 | 2.844887 | -163 | 163 | 90 | 7.218333 |
| `shoulder_roll_l_joint` | 12 | `shoulder_pitch_l_link` | `shoulder_roll_l_link` | `1 0 0` | -0.191986 | 3.333579 | -11 | 191 | 90 | 7.218333 |
| `shoulder_yaw_l_joint` | 13 | `shoulder_roll_l_link` | `shoulder_yaw_l_link` | `0 0 1` | -2.844887 | 2.844887 | -163 | 163 | 50 | 11.455294 |
| `elbow_pitch_l_joint` | 14 | `shoulder_yaw_l_link` | `elbow_pitch_l_link` | `0 1 0` | -2.548181 | 0.191986 | -146 | 11 | 50 | 11.455294 |
| `elbow_yaw_l_joint` | 15 | `elbow_pitch_l_link` | `elbow_yaw_l_link` | `0 0 1` | -2.844887 | 2.844887 | -163 | 163 | 40 | 18.325957 |
| `wrist_pitch_l_joint` | 16 | `elbow_yaw_l_link` | `wrist_pitch_l_link` | `0 1 0` | -1.32645 | 1.32645 | -76 | 76 | 40 | 18.325957 |
| `wrist_roll_l_joint` | 17 | `wrist_pitch_l_link` | `wrist_roll_l_link` | `1 0 0` | -1.32645 | 1.32645 | -76 | 76 | 40 | 18.325957 |

### 右臂

| 关节 | 电机 ID | 父 link | 子 link | 轴向 | 下限 (rad) | 上限 (rad) | 下限 (°) | 上限 (°) | 力矩 (N·m) | 速度 (rad/s) |
|------|---------|---------|---------|------|-----------|-----------|----------|----------|------------|--------------|
| `shoulder_pitch_r_joint` | 21 | `waist_pitch_link` | `shoulder_pitch_r_link` | `0 1 0` | -2.844887 | 2.844887 | -163 | 163 | 90 | 7.218333 |
| `shoulder_roll_r_joint` | 22 | `shoulder_pitch_r_link` | `shoulder_roll_r_link` | `1 0 0` | -3.333579 | 0.191986 | -191 | 11 | 90 | 7.218333 |
| `shoulder_yaw_r_joint` | 23 | `shoulder_roll_r_link` | `shoulder_yaw_r_link` | `0 0 1` | -2.844887 | 2.844887 | -163 | 163 | 50 | 11.455294 |
| `elbow_pitch_r_joint` | 24 | `shoulder_yaw_r_link` | `elbow_pitch_r_link` | `0 1 0` | -2.548181 | 0.191986 | -146 | 11 | 50 | 11.455294 |
| `elbow_yaw_r_joint` | 25 | `elbow_pitch_r_link` | `elbow_yaw_r_link` | `0 0 1` | -2.844887 | 2.844887 | -163 | 163 | 40 | 18.325957 |
| `wrist_pitch_r_joint` | 26 | `elbow_yaw_r_link` | `wrist_pitch_r_link` | `0 1 0` | -1.32645 | 1.32645 | -76 | 76 | 40 | 18.325957 |
| `wrist_roll_r_joint` | 27 | `wrist_pitch_r_link` | `wrist_roll_r_link` | `1 0 0` | -1.32645 | 1.32645 | -76 | 76 | 40 | 18.325957 |

## 3. fixed（固定）关节表

| 关节 | 父 link | 子 link | origin xyz (m) | origin rpy (rad) |
|------|---------|---------|----------------|------------------|
| `camera_head_joint` | `head_pitch_link` | `camera_head_link` | `0.01555 0.011209 -0.00012387` | `-1.5659 0 -1.5708` |
| `radar_head_joint` | `waist_pitch_link` | `radar_head_link` | `0 0 0.38177` | `3.1416 0 1.5708` |
| `imu_head_joint` | `waist_pitch_link` | `imu_head_link` | `-0.057774 0 0.42677` | `-3.1416 0 -1.5708` |
| `left_tcp_joint` | `wrist_roll_l_link` | `left_tcp_link` | `0 0 -0.045` | `0 0 0` |
| `right_tcp_joint` | `wrist_roll_r_link` | `right_tcp_link` | `0 0 -0.045` | `0 0 0` |
| `camera_body_front_joint` | `waist_pitch_link` | `camera_body_front_link` | `0.092709 -0.02375 0.039976` | `2.5307 0 1.5708` |
| `imu_waist_joint` | `pelvis` | `imu_waist_link` | `-0.081641 -0.00010952 -0.063057` | `-3.1416 0 -1.5695` |

## 4. TF 树结构

```text
pelvis
  └─[R] hip_pitch_l_joint
    hip_pitch_l_link
      └─[R] hip_roll_l_joint
        hip_roll_l_link
          └─[R] hip_yaw_l_joint
            hip_yaw_l_link
              └─[R] knee_pitch_l_joint
                knee_pitch_l_link
                  └─[R] ankle_pitch_l_joint
                    ankle_pitch_l_link
                      └─[R] ankle_roll_l_joint
                        ankle_roll_l_link
  └─[R] hip_pitch_r_joint
    hip_pitch_r_link
      └─[R] hip_roll_r_joint
        hip_roll_r_link
          └─[R] hip_yaw_r_joint
            hip_yaw_r_link
              └─[R] knee_pitch_r_joint
                knee_pitch_r_link
                  └─[R] ankle_pitch_r_joint
                    ankle_pitch_r_link
                      └─[R] ankle_roll_r_joint
                        ankle_roll_r_link
  └─[R] waist_yaw_joint
    waist_yaw_link
      └─[R] waist_roll_joint
        waist_roll_link
          └─[R] waist_pitch_joint
            waist_pitch_link
              └─[R] head_yaw_joint
                head_yaw_link
                  └─[R] head_pitch_joint
                    head_pitch_link
                      └─[F] camera_head_joint
                        camera_head_link
              └─[F] radar_head_joint
                radar_head_link
              └─[F] imu_head_joint
                imu_head_link
              └─[R] shoulder_pitch_l_joint
                shoulder_pitch_l_link
                  └─[R] shoulder_roll_l_joint
                    shoulder_roll_l_link
                      └─[R] shoulder_yaw_l_joint
                        shoulder_yaw_l_link
                          └─[R] elbow_pitch_l_joint
                            elbow_pitch_l_link
                              └─[R] elbow_yaw_l_joint
                                elbow_yaw_l_link
                                  └─[R] wrist_pitch_l_joint
                                    wrist_pitch_l_link
                                      └─[R] wrist_roll_l_joint
                                        wrist_roll_l_link
                                          └─[F] left_tcp_joint
                                            left_tcp_link
              └─[R] shoulder_pitch_r_joint
                shoulder_pitch_r_link
                  └─[R] shoulder_roll_r_joint
                    shoulder_roll_r_link
                      └─[R] shoulder_yaw_r_joint
                        shoulder_yaw_r_link
                          └─[R] elbow_pitch_r_joint
                            elbow_pitch_r_link
                              └─[R] elbow_yaw_r_joint
                                elbow_yaw_r_link
                                  └─[R] wrist_pitch_r_joint
                                    wrist_pitch_r_link
                                      └─[R] wrist_roll_r_joint
                                        wrist_roll_r_link
                                          └─[F] right_tcp_joint
                                            right_tcp_link
              └─[F] camera_body_front_joint
                camera_body_front_link
  └─[F] imu_waist_joint
    imu_waist_link
```

> `[R]` = revolute（31 个，会随 `/joint_states` 变化），`[F]` = fixed（7 个，静态变换）。
