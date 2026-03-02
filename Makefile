SHELL:=/bin/bash


get-all:
	mkdir -p histories
	. venv/bin/activate && python ./slack_backup.py

channel-list:
	. venv/bin/activate && python ./list_channels.py

copy-new-files:
	. venv/bin/activate && python ./copy_new_files.py -s ./histories -t /Users/t-kubo/Library/CloudStorage/GoogleDrive-takeshi.kubo@zettant.com/共有ドライブ/情シスG/service_backup/slack

prepare:
	python3 -mvenv venv && . venv/bin/activate && pip install -r requirements.txt
