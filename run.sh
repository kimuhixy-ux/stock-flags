#!/bin/zsh
# 売買フラグを計算し、変化があれば GitHub に反映する
# __PYTHON__ を python3 のフルパスに書き換えてください(which python3 で確認)
cd "$(dirname "$0")" || exit 1

/usr/bin/python3 update_flags.py

# flags.json に変化があった時だけ commit & push(無駄なコミットを防ぐ)
if ! git diff --quiet flags.json 2>/dev/null; then
  git add flags.json
  git commit -m "update flags $(date '+%Y-%m-%d %H:%M')" >/dev/null 2>&1
  git push >/dev/null 2>&1
  echo "pushed."
fi
