#!/usr/bin/env bash
# Copyright 2026 Walker Tienkung Dex Project Contributors
# SPDX-License-Identifier: Apache-2.0
#
# 生成 GitHub Release 用的源码压缩包（不含构建产物与内部文件）
#
# 用法:
#   ./scripts/release.sh                    # 版本号取自 git describe
#   ./scripts/release.sh v0.1.0             # 指定版本号
#   ./scripts/release.sh v0.1.0 --no-meshes # 额外产出不含 3D 网格的精简包
#
# 产物:
#   dist/tiangong3_tf-<version>.tar.gz          完整源码包（含网格与视频，约 22 MB）
#   dist/tiangong3_tf-<version>-slim.tar.gz     精简包（仅代码与文档，约 100 KB）

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_DIR="$(dirname "${SCRIPT_DIR}")"
DIST_DIR="${WS_DIR}/dist"
PKG_NAME="tiangong3_tf"

VERSION=""
SLIM=0
for arg in "$@"; do
  case "${arg}" in
    --no-meshes) SLIM=1 ;;
    -h|--help)
      sed -n '2,14p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    -*)
      echo "错误: 未知选项 '${arg}'" >&2
      exit 2
      ;;
    *)
      VERSION="${arg}"
      ;;
  esac
done

if [[ -z "${VERSION}" ]]; then
  if command -v git >/dev/null 2>&1 && git -C "${WS_DIR}" rev-parse --git-dir >/dev/null 2>&1; then
    VERSION="$(git -C "${WS_DIR}" describe --tags --always --dirty 2>/dev/null || echo v0.0.0)"
  else
    VERSION="v0.0.0"
  fi
fi

mkdir -p "${DIST_DIR}"

# 排除清单（相对工作空间根）：构建产物、缓存、内部配置、发布包自身
RSYNC_EXCLUDES=(
  --exclude 'build/'
  --exclude 'install/'
  --exclude 'log/'
  --exclude 'dist/'
  --exclude '.git/'
  --exclude '.claude/'
  --exclude '.cursor/'
  --exclude '__pycache__/'
  --exclude '*.pyc'
  --exclude '.DS_Store'
  --exclude '.vscode/'
  --exclude '.idea/'
  --exclude '*.zip'
)

command -v rsync >/dev/null 2>&1 || {
  echo "错误: 需要 rsync（sudo apt install rsync / macOS 自带）" >&2
  exit 1
}

pack() {  # pack <输出名> [额外 rsync -exclude 参数...]
  local out="$1"; shift
  local stage
  stage="$(mktemp -d)"
  local target="${stage}/${PKG_NAME}-${VERSION}"

  echo "=== 打包 ${out} ==="
  mkdir -p "${target}"
  # 尾随 '/' 保证复制“内容”而非“目录本身”，以便 tar 内层目录名可控
  rsync -a "${RSYNC_EXCLUDES[@]}" "$@" "${WS_DIR}/" "${target}/"
  tar -czf "${DIST_DIR}/${out}" -C "${stage}" "${PKG_NAME}-${VERSION}"
  rm -rf "${stage}"
}

# 1) 完整源码包（默认，含 3D 网格，解压即可编译运行）
pack "${PKG_NAME}-${VERSION}.tar.gz"

# 2) 精简包（可选，仅代码与文档，便于代码审查 / 小带宽分发）
if [[ "${SLIM}" == "1" ]]; then
  pack "${PKG_NAME}-${VERSION}-slim.tar.gz" \
    --exclude 'src/tiangong3_urdf/meshes/' \
    --exclude 'src/tiangong3_urdf/meshes_hand/' \
    --exclude 'docs/assets/'
fi

echo
echo "=== 完成 ==="
ls -lh "${DIST_DIR}"
echo
echo "上传到 GitHub Release:"
echo "  gh release create ${VERSION} ${DIST_DIR}/*.tar.gz --title \"${VERSION}\" --notes-file CHANGELOG.md"
