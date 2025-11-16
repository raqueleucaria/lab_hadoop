#!/usr/bin/env python3
import sys
import io
import re

input_stream = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors='replace')

word_regex = re.compile(r'\S+')

for line in input_stream:
    for match in word_regex.finditer(line):
        print(f'{match.group()}\t1')
