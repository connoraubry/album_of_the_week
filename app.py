import os
import json
import requests
import urllib.parse

from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request

import helper
from album_selector import Album

app = Flask(__name__)
env = load_dotenv()

@app.route("/")
def index():
    album = helper.get_current_album()
    values = {"album": album.to_dict()}
    return render_template("index.html", **values)

@app.route("/history")
def history():
    values = {"albums": []}
    album_list = []
    for entry in helper.get_history():
        date = datetime.fromisoformat(entry.get("chosen_on"))
        new_album = {
            "title": entry.get('title'),
            "artist": entry.get('artist'),
            "date": date.strftime("%B %d, %Y"),
        }
        album_list.append(new_album)
    album_list.reverse()
    values = {'albums': album_list}
    return render_template("history.html", **values)

@app.route("/search", methods=["GET"])
def options():
    title = request.args.get("title")
    resp_json = query_options(title)
    matches = parse_album_matches(resp_json)

    return render_template("options.html", albums=matches)

@app.route("/submit", methods=["POST"])
def submit():
    query = request.form.get("title", "")

    album_name = query
    artist_name = ""

    idx = query.rfind("(")
    if (idx != -1):
        album_name = query[:idx].strip()
        artist_name = query[idx:].strip("()")

    ip_addr_hash = helper.get_ip_address_hash(request.access_route, request.remote_addr)
    album = Album(title=album_name, artist=artist_name,
                  submitted_by=ip_addr_hash)

    helper.add_album_upcoming(album)
    return render_template("form.html", form_result="Submitted an album!")

def query_options(query):
    api_key = os.environ.get("LASTFM_API_KEY", "")
    if api_key == "" or query == "":
        return {}

    query = urllib.parse.quote(query)
    base = "http://ws.audioscrobbler.com/2.0/"
    method = "method=album.search"
    url = f"{base}?{method}&album={query}&api_key={api_key}&format=json"

    resp = requests.get(url)
    return resp.json()

def parse_album_matches(json_obj):
    matches = json_obj.get("results", {}).get("albummatches", {})
    print(len(matches.get("album", [])))
    first_5_albums = [
        {
            "title": a.get("name", ""),
            "artist": a.get("artist", ""),
            "mbid": a.get("mbid", "")
        } for a in matches.get("album", [])[:5]
    ]
    return first_5_albums
