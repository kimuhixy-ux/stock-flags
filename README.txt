売買フラグ(外出先からiPhoneで確認)セットアップ手順
=====================================================

仕組み
------
  Mac が30分ごとに計算 → flags.json を更新 → GitHub に push
  → GitHub Pages が HTTPS で公開 → iPhone はそのURLを開くだけ
  (Mac は自宅Wi-Fi内のままでよい。外に出るのは結果データだけ)

フォルダ構成
------------
  update_flags.py          計算スクリプト(stock_flag.py の判定を再利用)
  stock_flag.py            判定ロジック(あなたの編集版に差し替え可)
  index.html               iPhoneで開く画面
  manifest.json            ホーム画面追加の設定
  icon-180.png / 512.png   アプリアイコン
  flags.json               計算結果(最初はサンプル。実行で上書きされる)
  run.sh                   計算 + GitHub反映をまとめたスクリプト
  com.user.stockflags.plist  30分ごとの定期実行設定(launchd)


■ 手順1: 計算が動くか単体で確認
  pip install yfinance pandas
  python update_flags.py
  → flags.json が更新されればOK(市場時間外なら「更新しません」と出る。
     その場合は確認のため update_flags.py の market_status を一時的に
     "暫定" 固定にして試す、などでも可)

■ 手順2: GitHubに公開(無料)
  1) github.com でアカウントを作成(未作成の場合)
  2) 新しいリポジトリを作成(例: stock-flags)
  3) このフォルダを git で push
  4) リポジトリの Settings > Pages で、公開ブランチを main に設定
  5) 数分後 https://<ユーザー名>.github.io/stock-flags/ で表示される
  ※ この手順は Claude Code に任せると対話的に進めてくれます。

■ 手順3: iPhoneでホーム画面に追加
  1) 上記URLを iPhone の Safari で開く
  2) 共有ボタン >「ホーム画面に追加」
  3) アイコンが並び、タップで全画面表示される

■ 手順4: 30分ごとの自動実行(launchd)
  1) run.sh と com.user.stockflags.plist の中の
     __PYTHON__       を `which python3` の結果に
     __PROJECT_DIR__  をこのフォルダのフルパスに 置換
  2) chmod +x run.sh
  3) plist を ~/Library/LaunchAgents/ にコピー
  4) launchctl load ~/Library/LaunchAgents/com.user.stockflags.plist
  ※ これも Claude Code に任せられます。


【重要な注意点】
----------------
・公開範囲:GitHub Pages(無料)は誰でもURLを開けば見られます。
  flags.json には銘柄名と売買フラグが載るため、保有株数・取得単価・口座情報
  などの個人情報は絶対に入れないでください(現状の設計にも入れていません)。
  完全に非公開にしたい場合は、有料プランや別のホスティングが必要です。

・「暫定」と「確定」:立会時間中(9:00-11:30, 12:30-15:30)の値は確定前の
  「暫定」です。最終的な判定は15:30の終値で「確定」します。

・データ遅延:無料データは15〜20分ほど遅れることがあります。

・祝日:現在は土日のみ自動でスキップします。祝日も止めたい場合は
  jpholiday ライブラリの追加が簡単です(必要になったら相談を)。

・判定は過去パターンの要約であり、将来を予測するものではありません。
  投資判断はご自身の責任で行ってください。
