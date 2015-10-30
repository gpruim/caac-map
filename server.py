#!/usr/bin/env python
import os
import io
import genmap
import threading

import requests
from flask import Flask, request


DEV = bool(os.environ.get('FLASK_DEBUG', False))


# Job Class
# =========

class Job(threading.Thread):

    is_daemon = True

    def run(self):
        postback_url, topics = self._args
        fp = io.StringIO()
        big, blocks = genmap.generate_map(topics, **self._kwargs)
        genmap.output_svg(topics, fp, big, blocks)

        fp.seek(0)
        requests.post(postback_url, data=fp.read(), headers={'Content-Type': 'image/svg+xml'})


# Flask App
# =========

app = Flask(__name__)

@app.route('/v1', methods=['POST'])
def v1():
    kw = request.get_json()
    postback_url = kw.pop('postback_url')
    topics = kw.pop('topics')
    Job(args=(postback_url, topics), kwargs=kw).start()
    return ''


if DEV:
    @app.route('/v1/postback-test/<filename>', methods=['POST'])
    def postback_test(filename):
        open(filename, 'wb+').write(request.get_data())
        return ''


if __name__ == '__main__':
    app.debug = DEV
    app.run()
