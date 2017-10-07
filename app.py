#!/usr/bin/env python3
from flask import Flask, jsonify, request
import psycopg2, itertools, glob, os

app = Flask(__name__)
MUSIC_DIR = os.getenv('MUSIC_DIR', '/home/pi/Muzyka')
MUSIC_EXTENSIONS = {'flac', 'wav', 'mp3', 'ogg', 'm4a', 'mp4'}

def get_db():
    conn = psycopg2.connect('dbname=holopsicon user=holopsicon')
    conn.set_client_encoding('UTF8')
    return conn

def find_all_files():
    return itertools.chain.from_iterable([glob.glob(os.path.join(MUSIC_DIR, '*.{}'.format(ext))) for ext in MUSIC_EXTENSIONS] + [glob.glob(os.path.join(MUSIC_DIR, '**', '*.{}'.format(ext)), recursive=True) for ext in MUSIC_EXTENSIONS])

@app.route('/update')
def update_database():
    conn = get_db()
    cur = conn.cursor()
    for f in find_all_files():
        cur.execute('INSERT INTO tracks (path) VALUES (%s) ON CONFLICT DO NOTHING;', (f,))
    conn.commit()
    cur.close()
    conn.close()
    return ""

@app.route('/scrobble', methods=['POST'])
def scrobble():
    p = request.get_json().get('path')
    conn = get_db()
    cur = conn.cursor()
    cur.execute('INSERT INTO tracks (path) VALUES (%s) ON CONFLICT DO NOTHING;', (p,))
    cur.execute('INSERT INTO scrobbles (track) VALUES ((SELECT pk FROM tracks WHERE path = %s));', (p,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({})

@app.route('/new_random')
def new_random():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT tracks.path, tracks.pk, tracks.title, tracks.artist, tracks.album, date_trunc('hour', NOW()-scrobbles.start_time) AS last_played FROM tracks LEFT OUTER JOIN scrobbles ON tracks.pk = scrobbles.track ORDER BY last_played DESC, RANDOM() LIMIT 1;")
    ret = (lambda r: dict(path=r[0], pk=r[1], title=r[2], artist=r[3], album=r[4], last_played=(r[5].total_seconds() if r[5] is not None else None)))(cur.fetchone())
    cur.close()
    conn.close()
    return jsonify(ret)

if __name__ == '__main__':
    update_database()
    app.run(port=8012, debug=True)
