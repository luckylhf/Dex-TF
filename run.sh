#!/usr/bin/env bash
# Copyright 2026 Walker Tienkung Dex Project Contributors
# SPDX-License-Identifier: Apache-2.0
#
# Tiangong Dex 工作空间：一键编译 + 启动
#
# 用法:
#   ./run.sh                  # 编译并启动【交互控制】（默认，会控制真机！）
#   ./run.sh display          # 编译并查看基础模型（纯离线）
#   ./run.sh status           # 编译并查看带状态桥接的模型（只读）
#   ./run.sh interactive      # 编译并启动交互控制
#   ./run.sh build            # 仅编译，不启动
#   ./run.sh -h | --help      # 显示帮助
#
# 环境变量:
#   ROS_DISTRO   ROS 2 发行版名（默认从环境读取，未设置时使用 humble）
#   SKIP_BUILD   设为 1 跳过编译（仅启动）

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

DISTRO="${ROS_DISTRO:-humble}"
SETUP_ROS="/opt/ros/${DISTRO}/setup.bash"
MODE="${1:-interactive}"

usage() {
  cat <<'EOF'
Tiangong Dex 工作空间启动脚本

用法:
  ./run.sh [模式]

模式:
  display       查看基础模型（joint_state_publisher_gui，纯离线，零风险）
  status        查看机器人状态驱动模型（只读，不会发送指令）
  interactive   交互控制（默认；会向真实机器人发送运动指令）
  build         仅编译工作空间，不启动任何节点

选项:
  -h, --help    显示本帮助

示例:
  ./run.sh display
  SKIP_BUILD=1 ./run.sh status

⚠️  安全提示: interactive 模式会真实移动机器人。请在急停可达、
    执行区域无人的条件下使用。详见 SECURITY.md。
EOF
}

case "${MODE}" in
  -h|--help|help)
    usage
    exit 0
    ;;
  display|status|interactive|build)
    ;;
  *)
    echo "错误: 未知模式 '${MODE}'" >&2
    echo
    usage >&2
    exit 2
    ;;
esac

# ---- 环境检查 ------------------------------------------------------------
if [[ ! -f "${SETUP_ROS}" ]]; then
  echo "错误: 找不到 ${SETUP_ROS}" >&2
  echo "      请确认已安装 ROS 2 ${DISTRO}，或设置 ROS_DISTRO 环境变量。" >&2
  exit 1
fi

# shellcheck disable=SC1090
set +u
source "${SETUP_ROS}"
set -u

# ---- 编译 ----------------------------------------------------------------
if [[ "${SKIP_BUILD:-0}" != "1" ]]; then
  echo "=== 编译工作空间 (colcon build --symlink-install) ==="
  if ! command -v colcon >/dev/null 2>&1; then
    echo "错误: 未找到 colcon，请执行: sudo apt install python3-colcon-common-extensions" >&2
    exit 1
  fi
  colcon build --symlink-install
else
  echo "=== 跳过编译 (SKIP_BUILD=1) ==="
fi

if [[ ! -f "${SCRIPT_DIR}/install/setup.bash" ]]; then
  echo "错误: 编译产物缺失，${SCRIPT_DIR}/install/setup.bash 不存在。" >&2
  exit 1
fi

if [[ "${MODE}" == "build" ]]; then
  echo "=== 编译完成，未启动任何节点 ==="
  echo "请执行: source install/setup.bash"
  exit 0
fi

# shellcheck disable=SC1091
set +u
source "${SCRIPT_DIR}/install/setup.bash"
set -u

# ---- 启动 ----------------------------------------------------------------
case "${MODE}" in
  display)
    echo "=== 启动 Tiangong Dex 基础显示（离线，不会控制机器人）==="
    exec ros2 launch tiangong3_urdf display.launch.py
    ;;
  status)
    echo "=== 启动 Tiangong Dex 状态桥接显示（只读，不会发送指令）==="
    exec ros2 launch tiangong3_urdf display_with_status.launch.py
    ;;
  interactive)
    echo "=============================================================="
    echo "  警告: 即将启动【交互控制】，可以真实移动机器人！"
    echo "  请确认: 急停可达 / 执行区域无人 / 已阅读 SECURITY.md"
    echo "=============================================================="
    exec ros2 launch tiangong3_urdf interactive_control.launch.py
    ;;
esac
