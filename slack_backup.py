import os
import sys
import json
import time
import requests
from datetime import datetime
import calendar
from dateutil.relativedelta import relativedelta

from argparse import ArgumentParser


# --------------------------------------------------------------------------------------
SLACK_API_TOKEN = "your-slack-api-token"  # Slack APIトークン

HIST_DIR = "histories"  # このディレクトリの下に、チャンネルごとにディレクトリを作成し、チャット履歴を保存
TARGET_CHANNEL_FILE = "_target_channels.json"

START_YEAR = 2017
START_MONTH = 5
# --------------------------------------------------------------------------------------


def _parser():
    usage = "python {} [-t token_file] [-d history_directory] [-t target_channels json] [--help]".format(os.path.basename(__file__))
    argparser = ArgumentParser(usage=usage)
    argparser.add_argument("-t", "--token", type=str, default="./.token", help="target directory")
    argparser.add_argument("-d", "--directory", type=str, default="./histories", help="target directory")
    argparser.add_argument("-c", "--channel", type=str, default="./_target_channels.json", help="question number")
    return argparser.parse_args()


def unix_to_yyyymmdd_hhmm(unix_time):
    dt = datetime.fromtimestamp(unix_time)
    return dt.strftime('%Y%m%d-%H%M')


def unix_to_yyyymmdd(unix_time):
    dt = datetime.fromtimestamp(unix_time)
    return dt.strftime('%Y%m%d')


# メッセージを取得する関数
def fetch_channel_messages(channel_id: str, oldest: int, latest: int):
    url = "https://slack.com/api/conversations.history"
    messages = []
    has_more = True
    next_cursor = None

    while has_more:
        params = {
            "channel": channel_id,
            "limit": 1000,
            "oldest": oldest,
            "latest": latest
        }
        if next_cursor:
            params["cursor"] = next_cursor

        HEADERS = {"Authorization": f"Bearer {SLACK_API_TOKEN}"}
        response = requests.get(url, headers=HEADERS, params=params)
        data = response.json()

        if not data.get("ok"):
            print(f"Error fetching messages for channel {channel_id}: {data.get('error')}")
            break

        messages.extend(data.get("messages", []))
        has_more = data.get("has_more", False)
        next_cursor = data.get("response_metadata", {}).get("next_cursor")

        time.sleep(1)  # Rate limiting

    return messages


# チャンネルリストを取得する関数
def fetch_all_channels():
    url = "https://slack.com/api/conversations.list"
    channels = []
    has_more = True
    next_cursor = None

    while has_more:
        params = {
            "limit": 1000,
            "types": "public_channel,private_channel"
        }
        if next_cursor:
            params["cursor"] = next_cursor

        HEADERS = {"Authorization": f"Bearer {SLACK_API_TOKEN}"}
        response = requests.get(url, headers=HEADERS, params=params)
        data = response.json()

        if not data.get("ok"):
            print(f"Error fetching channels: {data.get('error')}")
            break

        channels.extend(data.get("channels", []))
        has_more = data.get("has_more", False)
        next_cursor = data.get("response_metadata", {}).get("next_cursor")

    return channels


# ファイルリストを取得する関数
def fetch_files(channel_id, oldest: int, latest: int):
    url = "https://slack.com/api/files.list"
    files = []
    has_more = True
    next_cursor = None

    while has_more:
        params = {
            "channel": channel_id,
            "limit": 1000,  # 一度に取得するファイル数
            "ts_from": oldest,
            "ts_to": latest
        }
        if next_cursor:
            params["cursor"] = next_cursor

        HEADERS = {"Authorization": f"Bearer {SLACK_API_TOKEN}"}
        response = requests.get(url, headers=HEADERS, params=params)
        data = response.json()

        if not data.get("ok"):
            print(f"Error fetching files: {data.get('error')}")
            break

        files.extend(data.get("files", []))
        has_more = data.get("has_more", False)
        next_cursor = data.get("paging", {}).get("next_cursor")

        time.sleep(1)  # Rate limiting

    return files


def fetch_thread_messages(channel_id: str, parent_ts: str):
    url = "https://slack.com/api/conversations.replies"
    messages = []
    has_more = True
    next_cursor = None

    while has_more:
        params = {
            "channel": channel_id,
            "ts": parent_ts,
            "limit": 1000
        }
        if next_cursor:
            params["cursor"] = next_cursor

        HEADERS = {"Authorization": f"Bearer {SLACK_API_TOKEN}"}
        response = requests.get(url, headers=HEADERS, params=params)
        data = response.json()

        if not data.get("ok"):
            print(f"Error fetching thread messages for channel {channel_id}: {data.get('error')}")
            break

        messages.extend(data.get("messages", []))
        has_more = data.get("has_more", False)
        next_cursor = data.get("response_metadata", {}).get("next_cursor")
        time.sleep(0.1)  # Rate limiting

    return messages


# ファイルをダウンロードする関数
def download_file(file_info, download_dir="downloads"):
    url = file_info["url_private"]
    file_name = file_info["name"]
    headers = {"Authorization": f"Bearer {SLACK_API_TOKEN}"}

    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    response = requests.get(url, headers=headers, stream=True)
    if response.status_code == 200:
        tm = file_info["timestamp"]
        file_path = os.path.join(download_dir, f"{tm}_{file_name}")
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded: {file_name}")
    else:
        print(f"Failed to download file {file_name}: {response.status_code}")


def get_channel_info(channel_name: str):
    """_info.jsonには、次の時に取得を再開すべき日付（月の初日の0時）を記録する"""
    try:
        with open(f"{HIST_DIR}/{channel_name}/_info.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        next_start_date = datetime(START_YEAR, START_MONTH, 1)
        return {"latest": int(next_start_date.timestamp())}


def read_token(path: str):
    if not os.path.exists(path):
        print(f"XXXX No such token file ({path})")
        sys.exit(1)
        return
    global SLACK_API_TOKEN
    with open(path, "r") as f:
        SLACK_API_TOKEN = f.read().strip()


# メイン処理
def main(token: str, directory: str, target: str):
    read_token(token)

    global HIST_DIR, TARGET_CHANNEL_FILE

    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    HIST_DIR = directory

    if not os.path.exists(target):
        print(f"XXXX No such target channel file ({target})")
        print(f"XXXX Please create {target} file with the list of channels. Run 'make channel-list' and edit _channels.json.")
        sys.exit(1)
        return
    TARGET_CHANNEL_FILE = target

    # 全てのチャンネルを取得
    with open(TARGET_CHANNEL_FILE, "r") as f:
        channels = json.load(f)
    print(f"Num of the target channel is {len(channels)}.")

    for channel in channels:
        channel_id = channel["id"]
        channel_name = channel.get("name", "unknown")
        print(f"=============== {channel_name} ({channel_id}) ============")
        os.makedirs(f"{HIST_DIR}/{channel_name}/files", exist_ok=True)

        # チャンネル情報を保存
        info = get_channel_info(channel_name)
        now = datetime.now().timestamp()
        start_date = datetime.fromtimestamp(info["latest"])  # info["latest"]は次に取得を開始すべき日付（月の初日の0時）が記録されている
        end_date = datetime.fromtimestamp(info["latest"]-1)
        while start_date.timestamp() < now:
            all_messages = list()
            # メッセージを月毎に取得する
            prev_month_date = start_date
            start_date = end_date+relativedelta(seconds=1)
            last_day = calendar.monthrange(start_date.year, start_date.month)[1]  # start_dateの月の月末
            end_date = start_date.replace(day=last_day, hour=23, minute=59, second=59)
            messages = fetch_channel_messages(channel_id, int(start_date.timestamp()), int(end_date.timestamp()))
            print(f"*** chat messages in {channel_name}: {unix_to_yyyymmdd(int(start_date.timestamp()))} - {unix_to_yyyymmdd(int(end_date.timestamp()))}: Num of messages: {len(messages)}")
            if len(messages) == 0:
                # 何もメッセージがないならファイルも作らない
                info["latest"] = int(prev_month_date.timestamp())
                with open(f"{HIST_DIR}/{channel_name}/_info.json", "w", encoding="utf-8") as f:
                    json.dump(info, f, ensure_ascii=False, indent=4)
                continue

            # スレッドがあればそれも取得する
            for message in messages:
                all_messages.append(message)
                if "thread_ts" in message and message["ts"] == message["thread_ts"]:
                    thread_messages = fetch_thread_messages(channel_id, message["thread_ts"])
                    print(f"Thread messages for {message['ts']}: {len(thread_messages)}")
                    all_messages.extend(thread_messages)

            # チャット履歴を保存
            mon = start_date.strftime('%Y%m')
            filename = f"{HIST_DIR}/{channel_name}/chat_{mon}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(all_messages, f, ensure_ascii=False, indent=4)
            print(f"Saved chat history for {channel_name} in {mon}")

            # ファイルを取得
            print(f"Fetching files for channel: {channel_name} ({channel_id})")
            files = fetch_files(channel_id, int(start_date.timestamp()), int(end_date.timestamp()))
            print(f"  -> {unix_to_yyyymmdd(int(start_date.timestamp()))} - {unix_to_yyyymmdd(int(end_date.timestamp()))}: Num of files: {len(files)}")
            for file_info in files:
                download_file(file_info, f"{HIST_DIR}/{channel_name}/files")

            # その月の最初の日付を記録（必ず月の初日から取得を再開するため）
            info["latest"] = int(start_date.timestamp())
            with open(f"{HIST_DIR}/{channel_name}/_info.json", "w", encoding="utf-8") as f:
                json.dump(info, f, ensure_ascii=False, indent=4)

    print("All chat history has been saved to slack_chat_history.json")


if __name__ == "__main__":
    args = _parser()
    main(args.token, args.directory, args.channel)
