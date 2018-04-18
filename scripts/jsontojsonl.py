#!/usr/bin/python3

import sys

for line in sys.stdin:
    line = line.strip()
    if line[-1] == ',':
        line = line[:-1]
    if line[0] == '{' and line[-1] == '}':
        print(line)
