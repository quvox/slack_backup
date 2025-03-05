Slackバックアップツール
=====

Slackのワークスペース内の対象チャンネルに対して、全チャット履歴およびファイルをダウンロードして保存する。

使いやすさを考慮していないし、引数もない。とりあえず使えるようにしただけなので、アプリケーションとして体裁を整える必要がある。


## 準備

1. Slack APIトークン（ユーザートークンまたはボットトークン）を取得する。
2. Slackアプリの"Bot Token Scopes"から、"Add an Oauth Scope"、スコープ（channels:history, groups:history, im:history, mpim:history, channels:read, groups:read）を設定する。
3. ボットアプリをワークスペースにインストールし、バックアップを取りたいチャンネルに参加させる（integrateする）。
3. list_channels.pyおよびslack_backup.pyの *SLACK_API_TOKEN*にトークン文字列を書く


## 使い方
* ```make channel-list```で、ワークスペースのすべてのチャンネルのリストを取得し、_channels.json_に出力する。
* ```cp _channels.json_ _target_channels.json```して、target_channels.jsonの中から、バックアップする必要のないチャンネルを削除する。
* ```make```を実行する。
  - histories/の下に、チャンネルごとにディレクトリが作られ、チャットメッセージが月毎にjsonにまとめられる
  - 添付ファイルは、さらに、files/の下に置かれる。
  - 各チャンネルディレクトリに置かれる_info.jsonには、どこまで読み込んだかが記録される。これを消すと最初からまた取り直す羽目になる。
  - 途中でCtrl-Cで中断しても、再開すると、前回の中断した月の初めから取得を再開する


