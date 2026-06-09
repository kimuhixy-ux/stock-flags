"""
株価トレンド分析 & 売買フラグ判定スクリプト
----------------------------------------
- 日足データを yfinance で取得
- 25日 / 75日 移動平均線のクロスを判定
- MACD(12, 26, 9)で勢いを裏取り
- 買い / 売り / 中立 の3フラグを出力

【使い方】
    pip install yfinance pandas
    python stock_flag.py

※ これは過去の値動きパターンの要約であり、将来を予測するものではありません。
"""

import yfinance as yf
import pandas as pd


# ============================================================
# 設定(ここを書き換えるだけで挙動を調整できます)
# ============================================================
TICKER = "7203.T"       # 銘柄コード。日本株は末尾に .T を付ける(例: トヨタ = 7203.T)
PERIOD = "1y"           # 取得期間(75日線の計算には最低でも半年以上を推奨)
SHORT_MA = 25           # 短期移動平均の日数
LONG_MA = 75            # 長期移動平均の日数
CROSS_LOOKBACK = 5      # クロスが「直近何営業日以内」に起きたかを見る範囲

# MACD のパラメータ(標準値)
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9


def fetch_data(ticker: str, period: str) -> pd.DataFrame:
    """yfinance で日足データを取得する。"""
    df = yf.Ticker(ticker).history(period=period, interval="1d")
    if df.empty:
        raise ValueError(f"データを取得できませんでした: {ticker}")
    return df


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """移動平均線と MACD を計算して列を追加する。"""
    close = df["Close"]

    # --- 移動平均線(SMA) ---
    df["SMA_short"] = close.rolling(SHORT_MA).mean()
    df["SMA_long"] = close.rolling(LONG_MA).mean()

    # --- MACD ---
    # 短期EMAと長期EMAの差が MACD 線、それをさらに平滑化したものがシグナル線
    ema_fast = close.ewm(span=MACD_FAST, adjust=False).mean()
    ema_slow = close.ewm(span=MACD_SLOW, adjust=False).mean()
    df["MACD"] = ema_fast - ema_slow
    df["MACD_signal"] = df["MACD"].ewm(span=MACD_SIGNAL, adjust=False).mean()

    return df


def detect_recent_cross(df: pd.DataFrame, lookback: int) -> str:
    """
    直近 lookback 営業日以内に発生した移動平均クロスを判定する。
    戻り値: "golden"(上抜け) / "dead"(下抜け) / "none"(なし)
    """
    # 短期線が長期線より上にあれば True になる真偽値の列
    short_above = df["SMA_short"] > df["SMA_long"]

    # 移動平均が計算できている部分だけを取り出し、直近 (lookback+1) 日分を見る
    recent = short_above[df["SMA_long"].notna()].iloc[-(lookback + 1):]
    if len(recent) < 2:
        return "none"

    started_below = not bool(recent.iloc[0])   # 期間の最初は短期線が下だったか
    ended_above = bool(recent.iloc[-1])        # 期間の最後は短期線が上か

    if started_below and ended_above:
        return "golden"   # 下 → 上 = ゴールデンクロス
    if (not started_below) and (not ended_above):
        return "dead"     # 上 → 下 = デッドクロス
    return "none"


def judge_flag(df: pd.DataFrame) -> dict:
    """売買フラグを判定する。"""
    latest = df.iloc[-1]

    # MACD 線がシグナル線より上にあるか(勢いが上向きか)
    macd_above = bool(latest["MACD"] > latest["MACD_signal"])

    # 直近のクロスを確認
    cross = detect_recent_cross(df, CROSS_LOOKBACK)

    # --- フラグ判定 ---
    # 買い : ゴールデンクロス かつ MACD が上向き
    # 売り : デッドクロス かつ MACD が下向き
    # 中立 : それ以外すべて
    if cross == "golden" and macd_above:
        flag = "買い"
    elif cross == "dead" and (not macd_above):
        flag = "売り"
    else:
        flag = "中立"

    return {
        "flag": flag,
        "date": df.index[-1].date(),
        "close": latest["Close"],
        "sma_short": latest["SMA_short"],
        "sma_long": latest["SMA_long"],
        "macd": latest["MACD"],
        "macd_signal": latest["MACD_signal"],
        "cross": cross,
        "macd_above": macd_above,
    }


def main():
    print(f"=== {TICKER} のトレンド分析 ===\n")

    df = fetch_data(TICKER, PERIOD)
    df = add_indicators(df)

    # 75日線が計算できる十分なデータがあるか確認
    if df["SMA_long"].dropna().empty:
        print("データが不足しています。PERIOD を長くしてください。")
        return

    result = judge_flag(df)
    cross_label = {"golden": "ゴールデンクロス", "dead": "デッドクロス", "none": "なし"}

    print(f"判定日       : {result['date']}")
    print(f"終値         : {result['close']:.1f}")
    print(f"{SHORT_MA}日線       : {result['sma_short']:.1f}")
    print(f"{LONG_MA}日線       : {result['sma_long']:.1f}")
    print(f"直近のクロス : {cross_label[result['cross']]}")
    print(f"MACD         : {result['macd']:.2f}(シグナル {result['macd_signal']:.2f})")
    print(f"MACDの勢い   : {'上向き' if result['macd_above'] else '下向き'}")
    print()
    print(f">>> 売買フラグ: 【{result['flag']}】")
    print()
    print("※ これは過去の値動きパターンの要約であり、将来を予測するものではありません。")
    print("※ 投資判断はご自身の責任で行ってください。")


if __name__ == "__main__":
    main()
