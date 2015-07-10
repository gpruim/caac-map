#!/usr/bin/env python
"""Convert CSV to JSON, while sneaking in an immutable id.
"""
import csv, json, sys

incoming = csv.reader(sys.stdin)
headers = incoming.next()
outgoing = [dict(zip(headers, row), id=i) for i, row in enumerate(incoming)]
json.dump(outgoing, sys.stdout)
