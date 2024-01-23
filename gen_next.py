import json
from pathlib import Path
import os
from dotenv import load_dotenv
import requests
import urllib.parse

env = load_dotenv()
dir_path = os.path.dirname(os.path.realpath(__file__))

def load_json():
    persist_file = Path(dir_path) / "upcoming.json"
    with open(persist_file, "r") as fp:
        json_obj = json.load(fp)
    return json_obj

def save_json(json_obj):
    persist_file = Path(dir_path) / "upcoming.json"
    with open(persist_file, "w") as fp:
        json.dump(json_obj, fp, indent=2)

def load_album(album):
    print(album)

    title = album.get("title", "")
    artist = album.get("artist", "")

    api_key = os.environ.get("LASTFM_API_KEY", "")

    query = urllib.parse.quote(title)
    base = "http://ws.audioscrobbler.com/2.0/"
    method = "method=album.search"
    url = f"{base}?{method}&album={query}&api_key={api_key}&format=json"

    print("Sending request to", url)
    resp = requests.get(url)

    json_obj = resp.json()

    matches = json_obj.get("results", "{}").get("albummatches", {})

    final_match = {}

    if artist != "":
        for match in matches.get("album", []):
            if match.get("artist", "") == artist:
                final_match = match
                break
    else:
        final_match = matches.get("album", [])[0]
        album['title'] = final_match['name']
        album['artist'] = final_match['artist']

    mbid = final_match.get("mbid", "")
    if mbid != "":
        if load_from_mbid(album, mbid) is False:
            return load_without_mbid(album, final_match)
    else:
        return load_without_mbid(album, final_match)

    return True


def load_from_mbid(album, mbid):
    date, success = musicbrainz_query(mbid)
    if success:
        album["date"] = date
    print("album art")
    image_path = f"static/images/{album['title']}.jpg"
    if get_album_art(mbid, image_path) is False:
        return False

    album['image'] = image_path

    with open("album_info.json", "w") as fp:
        json.dump(album, fp, indent=2)

    return True

def load_without_mbid(album, final_match):
    image_url = ""
    image_path = f"static/images/{album['title']}.jpg"
    album['image'] = image_path

    for image in final_match['image']:
        if image['size'] == "extralarge":
            image_url = image['#text']
    if image_url != "":
        if get_and_save_image(image_url, image_path) is False:
            return False
        with open("album_info.json", "w") as fp:
            json.dump(album, fp, indent=2)
    else:
        return False
    return True

def get_and_save_image(url, image_path):
    r = requests.get(url, allow_redirects=True)
    if r.status_code == 200:
        open(image_path, "wb").write(r.content)
        return True
    return False

def musicbrainz_query(mbid):
    url = f"https://musicbrainz.org/ws/2/release/{mbid}?fmt=json"
    r = requests.get(url)
    if r.status_code < 200 or r.status_code > 299:
        return 0, False
    json_obj = r.json()
    date = json_obj.get("date", "")
    if date != "":
        s = date.split("-")
        if len(s) > 0:
            date = s[0]
    return date, True

def get_album_art(mbid, image_path):
    url = f"http://coverartarchive.org/release/{mbid}/front"
    print(url)
    r = requests.get(url, allow_redirects=True)
    if r.status_code == 200:
        open(image_path, "wb").write(r.content)
        return True
    return False

def main():
    json_obj = load_json()
    albums = json_obj.get("albums", [])

    succeeded = False

    while succeeded is False:
        album = ""
        if len(albums) == 0:
            return
        album = albums.pop(0)

        succeeded = load_album(album)

    json_obj['albums'] = albums
    save_json(json_obj)

if __name__ == '__main__':
    main()
