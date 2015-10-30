#!/usr/bin/env python
from flask import Flask, request, Response
app = Flask(__name__)


import os
import io
import genmap


@app.route('/v1', methods=['POST'])
def v1():
    topics = request.get_json()
    fp = io.StringIO()
    w, h = map(int, [request.args.get('w', 2048), request.args.get('h', 2048)])
    kw = dict(charset='utf8', alley_width=6, building_min=10)
    big, blocks = genmap.generate_map(topics, width=w, height=h, **kw)
    genmap.output_svg(topics, fp, big, blocks)
    fp.seek(0)
    return Response(fp, mimetype='image/svg+xml')

if __name__ == '__main__':
    app.debug = bool(os.environ.get('FLASK_DEBUG', False))
    app.run()
