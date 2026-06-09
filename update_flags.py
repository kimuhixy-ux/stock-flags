"""
売買フラグ計算スクリプト(Macで30分ごとに定期実行する想定)
------------------------------------------------------------
- 既存の stock_flag.py の判定ロジックを再利用
- 市場が開いている時間帯は「暫定」、引け後は「確定」として flags.json を出力
- 市場と無関係な時間帯(夜間・週末)は何もせず終了する

出力された flags.json を GitHub Pages に push すると、
外出先の iPhone からインターネット経由で確認できる。

※ 判定は過去パターンの要約であり将来を予測するものではありません。
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, time
from zoneinfo import ZoneInfo

import stock_flag as sf

OUTPUT = "flags.json"

# 判定したい銘柄(コード: 表示名)
TICKERS = {
    # --- 保有銘柄 ---
    "2914.T": "日本たばこ産業（JT）",
    "7751.T": "キヤノン",
    "2593.T": "伊藤園",
    "9984.T": "ソフトバンクグループ",
    # --- ウォッチ銘柄 ---
    "7974.T": "任天堂",
    "6954.T": "ファナック",
    "6506.T": "安川電機",
    "5802.T": "住友電工",
    "5803.T": "フジクラ",
    "6098.T": "リクルートHD",
    "4063.T": "信越化学工業",
    "6981.T": "村田製作所",
}

# 東証の立会時間(2024/11/5 以降。後場の引けは 15:30)
MORNING_OPEN = time(9, 0)
MORNING_CLOSE = time(11, 30)
AFTERNOON_OPEN = time(12, 30)
AFTERNOON_CLOSE = time(15, 30)
POST_CLOSE_UNTIL = time(16, 30)   # 引け後にこの時刻までに走れば「確定」とみなす


def market_status(now: datetime) -> str | None:
    """
    現在時刻(JST)から状態を返す。
    "暫定" = 立会時間中 / "確定" = 引け後の確定枠 / None = 更新不要な時間帯
    """
    if now.weekday() >= 5:          # 土日
        return None
    t = now.time()
    in_session = (MORNING_OPEN <= t <= MORNING_CLOSE) or (AFTERNOON_OPEN <= t <= AFTERNOON_CLOSE)
    if in_session:
        return "暫定"
    if AFTERNOON_CLOSE < t <= POST_CLOSE_UNTIL:
        return "確定"
    return None


def judge_one(ticker: str) -> dict:
    df = sf.fetch_data(ticker, sf.PERIOD)
    df = sf.add_indicators(df)
    r = sf.judge_flag(df)
    return {
        "flag": r["flag"],
        "date": str(r["date"]),
        "close": round(float(r["close"]), 1),
        "sma_short": round(float(r["sma_short"]), 1),
        "sma_long": round(float(r["sma_long"]), 1),
        "macd_above": bool(r["macd_above"]),
        "cross": r["cross"],
    }


def build_payload(now: datetime, status: str) -> dict:
    results = []
    for code, name in TICKERS.items():
        try:
            data = judge_one(code)
        except Exception as e:
            data = {"flag": "取得失敗", "error": str(e)}
        data.update({"code": code, "name": name})
        results.append(data)
    return {
        "generated_at": now.strftime("%Y-%m-%d %H:%M"),
        "status": status,
        "short": sf.SHORT_MA,
        "long": sf.LONG_MA,
        "results": results,
    }


def main():
    now = datetime.now(ZoneInfo("Asia/Tokyo"))
    status = market_status(now)
    if status is None:
        print(f"[{now:%H:%M}] 市場時間外のため更新しません。")
        return
    payload = build_payload(now, status)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"[{now:%H:%M}] {status} で {OUTPUT} を更新しました。")


if __name__ == "__main__":
    main()
