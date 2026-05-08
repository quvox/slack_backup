import os
import json
import sys
from argparse import ArgumentParser

CHANNELS_FILE = "_channels.json"
TARGET_FILE = "_target_channels.json"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def print_table(channels, target_ids):
    print(f"\n{'No':>3}  {'ID':<13} {'Name':<35} {'Archived':>8}  In target")
    print("-" * 72)
    for i, ch in enumerate(channels, 1):
        mark = "*" if ch["id"] in target_ids else " "
        archived = "yes" if ch.get("is_archived") else ""
        print(f"{i:>3}  {ch['id']:<13} {ch['name']:<35} {archived:>8}  [{mark}]")


def find_channel(channels, name_or_id):
    for ch in channels:
        if ch["id"] == name_or_id or ch["name"] == name_or_id:
            return ch
    return None


def cmd_list(channels, targets):
    target_ids = {c["id"] for c in targets}
    print_table(channels, target_ids)
    print(f"\n  * = already in {TARGET_FILE}  ({len(targets)} targeted / {len(channels)} total)")


def cmd_add(channels, targets, names):
    target_ids = {c["id"] for c in targets}
    changed = False
    for name in names:
        ch = find_channel(channels, name)
        if ch is None:
            print(f"  !! Not found: {name}", file=sys.stderr)
            continue
        if ch["id"] in target_ids:
            print(f"  -- Already targeted: {ch['name']}")
            continue
        targets.append(ch)
        target_ids.add(ch["id"])
        changed = True
        print(f"  ++ Added: {ch['name']}")
    return changed


def cmd_remove(targets, names):
    changed = False
    for name in names:
        before = len(targets)
        targets[:] = [c for c in targets if c["id"] != name and c["name"] != name]
        if len(targets) < before:
            changed = True
            print(f"  -- Removed: {name}")
        else:
            print(f"  !! Not in targets: {name}", file=sys.stderr)
    return changed


def cmd_interactive(channels, targets):
    target_ids = {c["id"] for c in targets}
    print_table(channels, target_ids)
    print(f"\n  * = already in {TARGET_FILE}  ({len(targets)} targeted / {len(channels)} total)")
    print("番号を入力してトグル（複数はカンマ/スペース区切り）。空Enter で保存終了。Ctrl+C でキャンセル。\n")

    changed = False
    try:
        while True:
            line = input("> ").strip()
            if not line:
                break
            tokens = line.replace(",", " ").split()
            for token in tokens:
                try:
                    idx = int(token) - 1
                except ValueError:
                    print(f"  !! 無効な入力: {token}")
                    continue
                if not (0 <= idx < len(channels)):
                    print(f"  !! 範囲外: {token}")
                    continue
                ch = channels[idx]
                if ch["id"] in target_ids:
                    targets[:] = [c for c in targets if c["id"] != ch["id"]]
                    target_ids.discard(ch["id"])
                    print(f"  -- Removed: {ch['name']}")
                else:
                    targets.append(ch)
                    target_ids.add(ch["id"])
                    print(f"  ++ Added: {ch['name']}")
                changed = True
    except KeyboardInterrupt:
        print("\nキャンセルしました。変更は保存されません。")
        return False

    return changed


def main():
    parser = ArgumentParser(description="_channels.json から _target_channels.json を更新する")
    parser.add_argument("-l", "--list", action="store_true", help="チャンネル一覧を表示して終了")
    parser.add_argument("-a", "--add", nargs="+", metavar="NAME_OR_ID", help="チャンネルを追加（名前またはID）")
    parser.add_argument("-r", "--remove", nargs="+", metavar="NAME_OR_ID", help="チャンネルを削除（名前またはID）")
    parser.add_argument("--channels", default=CHANNELS_FILE, help=f"チャンネルリストファイル（デフォルト: {CHANNELS_FILE}）")
    parser.add_argument("--target", default=TARGET_FILE, help=f"ターゲットファイル（デフォルト: {TARGET_FILE}）")
    args = parser.parse_args()

    if not os.path.exists(args.channels):
        print(f"Error: {args.channels} が見つかりません。先に 'make channel-list' を実行してください。", file=sys.stderr)
        sys.exit(1)

    channels = load_json(args.channels)
    targets = load_json(args.target) if os.path.exists(args.target) else []

    if args.list:
        cmd_list(channels, targets)
        return

    if args.add and args.remove:
        print("Error: -a と -r は同時に指定できません。", file=sys.stderr)
        sys.exit(1)

    if args.add:
        changed = cmd_add(channels, targets, args.add)
    elif args.remove:
        changed = cmd_remove(targets, args.remove)
    else:
        changed = cmd_interactive(channels, targets)

    if changed:
        save_json(args.target, targets)
        print(f"\nSaved: {len(targets)} channels → {args.target}")
    else:
        print("変更なし。")


if __name__ == "__main__":
    main()
