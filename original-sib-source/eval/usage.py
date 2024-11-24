#!/usr/bin/env python3

import os
import sys
import json

repo = sys.argv[1]
dump = sys.argv[2]

with open(dump, 'r', encoding='utf8') as f:
    js = json.load(f)

file_intervals = js['used_lines']
internal_used_lines = 0
internal_total_lines = 0
internal_files = 0
external_used_lines = 0
external_total_lines = 0
external_files = 0


for file, intervals in file_intervals.items():
    if not os.path.exists(file):
        print(f'File not found: {file}')
        continue

    with open(file, 'r', encoding='utf8') as f:
        total_lines = sum(1 for _ in f)

    used_lines = 0
    for interval in intervals['intervals']:
        used_lines += interval['stop'] - interval['start']

    if file.startswith(repo):
        internal_used_lines += used_lines
        internal_total_lines += total_lines
        internal_files += 1
    else:
        external_used_lines += used_lines
        external_total_lines += total_lines
        external_files += 1


print('internal used files:', internal_files)
print('internal used lines:', internal_used_lines)
print('internal total lines:', internal_total_lines)
print('external used files:', external_files)
print('external used lines:', external_used_lines)
print('external total lines:', external_total_lines)
print('total used files:', internal_files + external_files)
print('total used lines:', internal_used_lines + external_used_lines)
print('total total lines:', internal_total_lines + external_total_lines)
