#!/usr/bin/env bash
# Copyright 2026 Walker Tienkung Dex Project Contributors
# SPDX-License-Identifier: Apache-2.0
#
# 编译 Tiangong Dex 工作空间（带依赖检查与文档一致性校验）
#
# 用法:
#   ./scripts/build.sh              # 正常编译
#   ./scripts/build.sh --clean      # 清理 build/install/log 后重新编译
#   ./scripts/build.sh --no-check   # 跳过 joints.md 一致性校验

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_DIR="$(dirname "${SCRIPT_DIR}")"
DISTRO="${ROS_DISTRO:-humble}"
SETUP_ROS="/opt/ros/${DISTRO}/setup.bash"

CLEAN=0
CHECK=1
for arg in "$@"; do
  case "${arg}" in
    --clean)    CLEAN=1 ;;
    --no-check) CHECK=0 ;;
    -h|--help)
      sed -n '2,12p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      echo "错误: 未知参数 '${arg}'" >&2
      exit 2
      ;;
  esac
done

cd "${WS_DIR}"

if [[ ! -f "${SETUP_ROS}" ]]; then
  echo "错误: 找不到 ${SETUP_ROS}（可通过 ROS_DISTRO 指定发行版）" >&2
  exit 1
fi

# shellcheck disable=SC1090
set +u
source "${SETUP_ROS}"
set -u

if [[ "${CLEAN}" == "1" ]]; then
  echo "=== 清理构建产物 ==="
  rm -rf build install log
fi

echo "=== colcon build --symlink-install ==="
colcon build --symlink-install

# ---- 可选校验 ------------------------------------------------------------
# 校验器只依赖标准库 + 可选第三方库（trimesh/xmlschema/pyyaml/lxml），
# 缺失时自动降级为告警，不会阻塞编译。
if [[ "${CHECK}" == "1" ]] && command -v python3 >/dev/null 2>&1; then
  echo "=== 校验发布包完整性（scripts/validate.py）==="
  if python3 "${SCRIPT_DIR}/validate.py"; then
    :
  else
    echo "提示: 校验未通过，请先修复上述 FAIL 项。" >&2
    echo "      若 docs/joints.md 过期，运行: python3 scripts/gen_joint_docs.py" >&2
    exit 1
  fi
fi

echo
echo "=== 编译完成 ==="
echo "请执行: source ${WS_DIR}/install/setup.bash"
