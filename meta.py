#!/usr/bin/env python
from __future__ import absolute_import, division, print_function, unicode_literals

from cStringIO import StringIO
from subprocess import PIPE, Popen

ntries = 10000
for i in range(ntries):
    print("\rTries: {:,} / {:,} ({:.1f}%)".format(i, ntries, i / ntries), end='')
    stderr = StringIO()
    p = Popen('python genmap.py web'.split(), stdout=open('map.html', 'w+'), stderr=PIPE)
    if 'Traceback' not in p.stderr.read():
        print("\nFound one!")
        break
