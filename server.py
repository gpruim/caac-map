#!/usr/bin/env python
import os
import io
import genmap
import threading

import requests
import flask

DEV = bool(os.environ.get('FLASK_DEBUG', False))


# Job Class
# =========

class Job(threading.Thread):

    is_daemon = True

    def run(self):
        callback_url, topics = self._args
        fp = io.StringIO()
        big, blocks = genmap.generate_map(topics, **self._kwargs)
        genmap.output_svg(topics, fp, big, blocks)

        fp.seek(0)
        requests.post(callback_url, data=fp.read(), headers={'Content-Type': 'image/svg+xml'})


# Flask App
# =========

app = flask.Flask(__name__)

@app.route('/')
def redirect_to_v1():
    return flask.redirect('/v1')

_documentation = open('documentation.html').read()
@app.route('/v1', methods=['GET'])
def documentation():
    return _documentation

@app.route('/v1', methods=['POST'])
def v1():
    kw = flask.request.get_json()
    callback_url = kw.pop('callback_url')
    topics = kw.pop('topics')
    Job(args=(callback_url, topics), kwargs=kw).start()
    return ''


if DEV:
    @app.route('/v1/callback-test/<filename>', methods=['POST'])
    def callback_test(filename):
        open(filename, 'wb+').write(flask.request.get_data())
        return ''


if __name__ == '__main__':
    app.debug = DEV
    kw = dict()
    if app.debug:
        kw['extra_files'] = ['documentation.html']
    app.run(**kw)
