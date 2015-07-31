#!/usr/bin/env python
"""Fetch data for the CaaC map from a Google Sheet.

https://developers.google.com/google-apps/spreadsheets/

The result of this script is a set of JSON files in ./data/, one per sheet.

"""
from __future__ import absolute_import, division, print_function, unicode_literals

import csv
import json
import os
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
        resources = [dict(zip(headers, row)) for row in reader]
        topics[topic] = resources
    return topics


def dump_topics(topics, fspath):
    fp = open(fspath, 'w+')
    json.dump(topics, fp, sort_keys=True, indent=4, separators=(',', ': '))


def main(sheets_key, staging_filename, final_filename):
    worksheets = fetch_worksheets(sheets_key)
    topics = fetch_resources_by_topic(worksheets)
    dump_topics(topics, staging_filename)
    shutil.move(staging_filename, final_filename)


if __name__ == '__main__':

    sheets_key = '1wZ2uz0KTkylLgo46fJ7gYYpNEKjVljoGTCjFecjZQ9c'
    staging_dir = '.resources.json'
    final_dir = 'resources.json'

    main(sheets_key, staging_dir, final_dir)
