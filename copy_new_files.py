import os
import shutil
import datetime
import sys
from pathlib import Path
from argparse import ArgumentParser


def _parser():
    usage = "python {} [-d YYYYMMDD] [-s source_directory] [-t target_directory] [--help]".format(os.path.basename(__file__))
    argparser = ArgumentParser(usage=usage)
    argparser.add_argument("-d", "--date", type=str, help="date from (YYYYMMDD)")
    argparser.add_argument("-s", "--source", type=str, default="./histories", help="source directory")
    argparser.add_argument("-t", "--target", type=str, required=True, help="target directory")
    return argparser.parse_args()


def get_previous_month_first_day():
    today = datetime.date.today()
    first_day_this_month = today.replace(day=1)
    previous_month_last_day = first_day_this_month - datetime.timedelta(days=1)
    previous_month_first_day = previous_month_last_day.replace(day=1)
    return previous_month_first_day.strftime("%Y%m%d")


def get_this_month_first_day():
    today = datetime.date.today()
    first_day_this_month = today.replace(day=1)
    return first_day_this_month.strftime("%Y%m%d")


def copy_new_files(source_dir, dest_dir, timestamp):
    source_path = Path(source_dir)
    dest_path = Path(dest_dir)
    
    if not dest_path.exists():
        dest_path.mkdir(parents=True)

    count = 0
    for item in source_path.rglob("*"):
        if item.is_file() or item.is_dir():
            modified_time = datetime.datetime.fromtimestamp(item.stat().st_mtime)
            created_time = datetime.datetime.fromtimestamp(item.stat().st_ctime)
            
            if modified_time > timestamp or created_time > timestamp:
                relative_path = item.relative_to(source_path)
                target_path = dest_path / relative_path

                if item.is_dir():
                    if not target_path.exists():
                        print(f"Creating directory: {target_path}")
                        target_path.mkdir(parents=True)
                    pass
                else:
                    print(f"Copying {item.relative_to(source_path)} to {target_path}")
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, target_path)
                    count += 1
    return count

def main():
    args = _parser()

    if not os.path.exists(args.source):
        print("XXXXXX source directory not found")
        sys.exit(1)

    if not os.path.exists(args.target):
        print("XXXXXX target directory not found")
        sys.exit(1)

    source_directory = args.source
    destination_directory = args.target
    if args.date is None:
        time_threshold = get_this_month_first_day()
    else:
        time_threshold = args.date
    
    timestamp = datetime.datetime.strptime(time_threshold, "%Y%m%d")
    cnt = copy_new_files(source_directory, destination_directory, timestamp)
    print("コピー完了: {} ファイル".format(cnt))

if __name__ == "__main__":
    main()

