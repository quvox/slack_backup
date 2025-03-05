import os
import json
import time
import requests

from argparse import ArgumentParser


# Slack APIトークン
# -------- この下のパラメータを必要に応じて変更する（本来は起動引数で与えられるようにすべき） --------
SLACK_API_TOKEN = "your-slack-api-token"  # Slack APIトークン
# --------------------------------------------------------------------------------------

def _parser():
    usage = "python {} [-t token_file] [--help]".format(os.path.basename(__file__))
    argparser = ArgumentParser(usage=usage)
    argparser.add_argument("-t", "--token", type=str, default=".token", help="target directory")
    return argparser.parse_args()


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

        time.sleep(1)  # Rate limiting

    return channels


def read_token(path: str):
    if not os.path.exists(path):
        print(f"XXXX No such token file ({path})")
        sys.exit(1)
        return
    global SLACK_API_TOKEN
    with open(path, "r") as f:
        SLACK_API_TOKEN = f.read().strip()


# メイン処理
def main():
    args = _parser()
    read_token(args.token)


    # 全てのチャンネルを取得
    channels = fetch_all_channels()
    print(f"Found {len(channels)} channels.")
    with open("_channels.json", "w") as f:
        json.dump(channels, f, indent=4)


if __name__ == "__main__":
    main()

