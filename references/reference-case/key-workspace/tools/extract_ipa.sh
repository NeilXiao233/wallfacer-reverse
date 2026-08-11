#!/bin/zsh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IPA="${GRIDDLE_IPA:-$ROOT/device/Griddle-256.ipa}"
OUT="${GRIDDLE_IPA_EXTRACTED:-$ROOT/device/ipa-extracted}"

if [ ! -f "$IPA" ]; then
  echo "缺少 IPA: $IPA"
  echo "请先运行 tools/download_from_app_store.sh。"
  exit 1
fi

mkdir -p "$OUT"
unzip -o "$IPA" -d "$OUT" >/dev/null

DATA="$(find "$OUT" -path '*/Payload/Griddle.app/Data/data.unity3d' -print -quit)"
if [ -n "$DATA" ]; then
  echo "data.unity3d: $DATA"
  echo "下一步可从此文件解析 Unity 资源（关卡、图集、配置等）。"
else
  echo "IPA 已解包，但没有找到 data.unity3d；文件清单："
  find "$OUT" -maxdepth 4 -type f | sed -n '1,60p'
fi
