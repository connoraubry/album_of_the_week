from flask import Flask, render_template, request
import json
from pathlib import Path
from dotenv import load_dotenv
import os
import requests
import urllib.parse

app = Flask(__name__)
count = 1
env = load_dotenv()


def load_album_info():
    album_info_file = Path(app.root_path) / "album_info.json"
    with open(album_info_file, "r") as fp:
        album_info = json.load(fp)

    return {"album": album_info}


@app.route("/")
def index():
    values = load_album_info()
    return render_template("index.html", **values)


@app.route("/test")
def test():
    resp_json = query_options("com")
    matches = parse_album_matches(resp_json)
    return render_template("options.html", albums=matches)


def query_options(query):
    print(query)
    api_key = os.environ.get("LASTFM_API_KEY", "")
    if api_key == "" or query == "":
        return {}

    query = urllib.parse.quote(query)
    base = "http://ws.audioscrobbler.com/2.0/"
    method = "method=album.search"
    url = f"{base}?{method}&album={query}&api_key={api_key}&format=json"

    resp = requests.get(url)
    return resp.json()


@app.route("/search", methods=["GET"])
def options():
    title = request.args.get("title")
    resp_json = query_options(title)
    matches = parse_album_matches(resp_json)

    return render_template("options.html", albums=matches)

@app.route("/submit", methods=["POST"])
def submit():
    query = request.form.get("title", "")

    album = parse_album_query(query)

    add_album(album)
    return render_template("form.html", form_result="Submitted an album!")

def parse_album_query(query):
    album_name = query
    artist_name = ""

    idx = query.rfind("(")  # ) line breaks formatting without close
    if (idx != -1):
        album_name = query[:idx].strip()
        artist_name = query[idx:].strip("()")

    album = {
        "title": album_name,
        "artist": artist_name,
    }
    return album

def add_album(title):
    json_obj = load_json()
    json_obj['albums'].append(title)
    save_json(json_obj)
    return 0

def load_json():
    persist_file = Path(app.root_path) / "upcoming.json"
    with open(persist_file, "r") as fp:
        json_obj = json.load(fp)
    return json_obj

def save_json(json_obj):
    persist_file = Path(app.root_path) / "upcoming.json"
    with open(persist_file, "w") as fp:
        json.dump(json_obj, fp, indent=2)

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
