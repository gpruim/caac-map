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
        postback_url, topics = self._args
        fp = io.StringIO()
        big, blocks = genmap.generate_map(topics, **self._kwargs)
        genmap.output_svg(topics, fp, big, blocks)

        fp.seek(0)
        requests.post(postback_url, data=fp.read(), headers={'Content-Type': 'image/svg+xml'})


# Flask App
# =========

app = flask.Flask(__name__)

_favicon = open('favicon.ico', 'rb').read()
@app.route('/favicon.ico')
def favicon():
    response = flask.Response(_favicon)
    response.headers['Content-Type'] = 'image/x-icon'
    return response

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
    postback_url = kw.pop('postback_url')
    topics = kw.pop('topics')
    Job(args=(postback_url, topics), kwargs=kw).start()
    return ''


if DEV:
    @app.route('/v1/postback-test/<filename>', methods=['POST'])
    def postback_test(filename):
        open(filename, 'wb+').write(flask.request.get_data())
        return ''


if __name__ == '__main__':
    app.debug = DEV
    kw = dict()
    if app.debug:
        kw['extra_files'] = ['documentation.html']
    app.run(**kw)
