#!/usr/bin/env python
from __future__ import absolute_import, division, print_function, unicode_literals

import os
from subprocess import PIPE, Popen

ntries = 10000
outputs = set()
for i in range(ntries):
    print("\rTries: {:,} / {:,} ({:.1f}%)".format(i, ntries, i / ntries), end='')
    p = Popen( 'python genmap.py 62 -W256 -H512 -a4 --charset=svg'.split()
             , stdout=open('map.svg', 'w+')
             , stderr=PIPE
              )
    err = p.stderr.read()

    if i < 10:
        outputs.add(err)
    elif len(outputs) == 1:
        print("\n\nThey're all failing the same way.\n")
        print(err)
        break

    if 'Traceback' not in err:
        if 'Remaining area: 0' in err:
            print("\nFound one!")
            print(err)
            os.system('mv map.svg www/map.svg')
            break
