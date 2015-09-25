#!/usr/bin/env python
"""Fetch data for the CaaC map from a Google Sheet.

https://developers.google.com/google-apps/spreadsheets/

The result of this script is a JSON file at ./output/topics.json.

"""
from __future__ import absolute_import, division, print_function, unicode_literals

import csv
import json
import os
import re
import shutil
from collections import defaultdict
from StringIO import StringIO
from dag import DAG
import xml.etree.ElementTree as ET

import requests


def _get(url):
    print("Getting {} ...".format(url))
    response = requests.get(url, headers={'If-Modified-Since': 'Wed, 16 Feb 2011 13:52:26 GMT'})
    if not response.status_code == 200:
        print("Problem downloading {} ...".format(url))
        print(response.status_code)
        print(response.text)
        raise SystemExit
    if 'Sign in to continue to Sheets' in response.text:
        print("Problem downloading {} ...".format(url))
        print("They're asking us to sign in. Try 'File > Publish to the web ...'.")
        raise SystemExit
    return response.text


def fetch_worksheets(sheet_key):
    csv_url = "https://docs.google.com/spreadsheets/d/{}/pub?gid={}&single=true&output=csv"
    listing_url = "https://spreadsheets.google.com/feeds/worksheets/{}/public/basic"
    listing_url = listing_url.format(sheet_key)
    raw = _get(listing_url)
    tree = ET.fromstring(raw)
    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    entries = tree.findall('./atom:entry', ns)
    xtitle = lambda entry: entry.find('./atom:title', ns).text
    xcsvurl = lambda entry: entry.find("./atom:link[@type='text/csv']", ns).attrib['href']
    xgid = lambda csvurl: re.findall('gid=(\d+)', csvurl)[0]
    puburl = lambda gid: csv_url.format(sheet_key, gid)
    return [(xtitle(e), puburl(xgid(xcsvurl(e)))) for e in entries]


def fetch_resources_by_topic(worksheets):
    """Smooth out into a nice JSON-able data structure.

    { "deadbeef": { "id": "deadbeef"
                  , "subtopics": { "fa1afe1": { "id": "fa1afe1"
                                              , "topic_id": "deadbeef"
                                              , "dag": { "names": ["fadedfad"]
                                                       , "vertices": [{"incomingNames": "feeddeaf"}]
                                                        }
                                              , "resources": { "fadedfad": { "id": "fadedfad"
                                                                           , "topic_id": "deadbeef"
                                                                           , "subtopic_id": "fa1afe1"
                                                                           , "etc": "stuff"
                                                                            }
                                                              }
                                               }
                   }
    """
    topics = {}
    for topic_id, csvurl in worksheets:
        topic = {}
        topic['id'] = topic_id
        topic['subtopics'] = subtopics = defaultdict(lambda: defaultdict(dict))

        raw = _get(csvurl)
        raw = raw.encode('utf8')  # the csv module can only use str
        reader = csv.reader(StringIO(raw))
        headers = reader.next()

        for row in reader:
            resource = dict(zip(headers, row))
            resource['id'] = resource['uid']
            resource['topic_id'] = topic_id

            subtopic = subtopics[resource['subtopic_id']]
            subtopic['resources'][resource['id']] = resource

            if 'dag' not in subtopic:
                # First time seeing it. Populate!
                subtopic['dag'] = DAG()
                subtopic['id'] = resource['subtopic_id']
                subtopic['topic_id'] = topic_id


        # Populate DAGs.
        # ==============
        # We have to do this in a second loop so that we can tell whether
        # before_this and after_this are in fact in the same subtopic as a
        # given resource. The base data is not clean on this point.

        for subtopic in subtopics.values():
            for resource in subtopic['resources'].values():

                # Relax the py-dag API to be more like the js DAG we had.
                d = subtopic['dag']
                add_node = lambda node: d.add_node(node) if node and node not in d.graph else None
                add_edge = lambda a,b: d.add_edge(a,b) if a and b and a != b else None

                add_node(resource['id'])
                if resource['before_this'] in subtopic['resources']:
                    add_node(resource['before_this'])
                    add_edge(resource['before_this'], resource['id'])
                if resource['after_this'] in subtopic['resources']:
                    add_node(resource['after_this'])
                    add_edge(resource['id'], resource['after_this'])

        # Convert DAGs to the format that the JavaScript expects.
        for subtopic in subtopics.values():
            dag = subtopic['dag']
            subtopic['dag'] = { "names": dag.topological_sort()
                              , "vertices": \
                                      {k: {"incomingNames": list(dag.graph[k])} for k in dag.graph}
                               }

        topics[topic_id] = topic
    return topics


def validate_uids(topics):
    bad = set()
    for name, topic in topics.items():
        for subtopic in topic['subtopics'].values():
            for resource in subtopic['resources'].values():
                for field in ('uid', 'before_this', 'after_this'):
                    if '\n' in resource[field] or not re.match(r'^[a-z0-9-]*$', resource[field]):
                        bad.add((name, field, resource[field].encode('ascii', errors='replace')))
    if bad:
        print("{} bad uid(s)!".format(len(bad)))
        print("{:24} {:24} {:24}".format("sheet", "field", "value"))
        print("{:-<24} {:-<24} {:-<24}".format("", "", ""))
        for sheet, field, value in sorted(bad):
            print("{:24} {:24} {:24}".format(sheet, field, repr(value)))
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
    staging = os.path.join('output', '.topics.json')
    final = os.path.join('output', 'topics.json')

    main(sheets_key, staging, final)
