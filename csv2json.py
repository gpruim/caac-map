#!/usr/bin/env python
"""Convert CSV to JSON, while sneaking in an immutable id and a duration.
"""
import csv, json, random, sys

incoming = csv.reader(sys.stdin)
headers = incoming.next()
duration = lambda: random.randint(1, 20)
outgoing = [dict(zip(headers, row), id=i, duration=duration()) for i, row in enumerate(incoming)]
json.dump(outgoing, sys.stdout, sort_keys=True, indent=4, separators=(',', ': '))
