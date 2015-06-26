#!/usr/bin/env python
from __future__ import absolute_import, division, print_function, unicode_literals

rows = [['a'] + ['-' for i in range(512)] + ['a'] for j in range(512)]
rows.insert(0, ['a' for i in range(514)])
rows.append(['a' for i in range(514)])

for row in rows:
    for c in row:
        print(c, end='')
    print()
