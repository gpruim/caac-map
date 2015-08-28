#!/usr/bin/env python
"""Fetch data for the CaaC map from a Google Sheet.

https://developers.google.com/google-apps/spreadsheets/

The result of this script is a JSON file at ./output/resources.json.

"""
from __future__ import absolute_import, division, print_function, unicode_literals

import csv
import json
import os
import re
import shutil
from StringIO import StringIO
import xml.etree.ElementTree as ET

import requests


def _get(url):
    response = requests.get(url)
    if not response.status_code == 200:
        print(response.status_code)
        print(response.text)
        raise SystemExit
    if 'Sign in to continue to Sheets' in response.text:
        #open('bad.html', 'w+').write(response.content)
        print("They're asking us to sign in. Try 'File > Publish to the web ...'.")
        raise SystemExit
    return response.text


def fetch_worksheets(sheet_key):
    url = "https://spreadsheets.google.com/feeds/worksheets/{}/public/basic"
    url = url.format(sheet_key)
    raw = _get(url)
    tree = ET.fromstring(raw)
    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    entries = tree.findall('./atom:entry', ns)
    xtitle = lambda entry: entry.find('./atom:title', ns).text
    xcsvurl = lambda entry: entry.find("./atom:link[@type='text/csv']", ns).attrib['href']
    return [(xtitle(e), xcsvurl(e)) for e in entries]


def fetch_resources_by_topic(worksheets):
    topics = {}
    for topic, csvurl in worksheets:
        raw = _get(csvurl)
        raw = raw.encode('utf8')  # csv can only use str
        reader = csv.reader(StringIO(raw))
        headers = reader.next()
        UID = 1
        resources = {row[UID]: dict(zip(headers, row)) for row in reader}
        topics[topic] = resources
    return topics


def validate_uids(topics):
    bad = set()
    for name, topic in topics.items():
        for resource in topic.values():
            for field in ('uid', 'comes_before', 'comes_after'):
                if not re.match(r'^[a-z-]+$', resource[field]):
                    bad.add((name, field, resource[field].encode('ascii', errors='replace')))
    if bad:
        print("{} bad uid(s)!".format(len(bad)))
        for sheet, field, value in sorted(bad):
            print(sheet, field, value)
        raise SystemExit


def dump_topics(topics, fspath):
    fp = open(fspath, 'w+')
    json.dump(topics, fp, sort_keys=True, indent=4, separators=(',', ': '))


def main(sheets_key, staging_filepath, final_filepath):
    worksheets = fetch_worksheets(sheets_key)
    topics = fetch_resources_by_topic(worksheets)
    validate_uids(topics)
    dump_topics(topics, staging_filepath)
    shutil.move(staging_filepath, final_filepath)


if __name__ == '__main__':

    sheets_key = '10PurQxMbALCYNu7I3KfgUb2oMz4Uk5dLPZbTkdNb0ZM'
    staging = os.path.join('output', '.resources.json')
    final = os.path.join('output', 'resources.json')

    main(sheets_key, staging, final)
