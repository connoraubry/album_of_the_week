import os
import json
import logging
import requests
import urllib.parse

from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

import helper
from album_selector import Album
from http.client import HTTPConnection

env = load_dotenv()
dir_path = Path(__file__).parent.resolve()
logger = logging.getLogger(__name__)
logging.basicConfig(filename=dir_path / "logs" / "generator.log",
                    encoding="utf-8",
                    format='%(asctime)s %(levelname)s: %(message)s',
                    datefmt="%Y-%m-%d %H:%M:%S",
                    level=logging.DEBUG)
logger.addHandler(logging.StreamHandler())

requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

HTTPConnection.debuglevel = 1

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True


def get_album_matches_from_name(api_key: str, name: str):
    query = urllib.parse.quote(name)
    url = "http://ws.audioscrobbler.com/2.0/"
    # method = "method=album.search"
    # url = f"{base}?{method}&album={query}&api_key={api_key}&format=json"
    params = {
        "method": "album.search",
        "album": query,
        "api_key": api_key,
        "format": "json",
        "limit": 15
    }

    logger.debug(f"Sending request to {url}")
    try:
        resp = requests.get(url, params=params, timeout=10)
    except requests.exceptions.Timeout:
        logger.error(
            "Error sending request to server: timeout after 10 seconds")
        return []
    logger.info("request returned, attempting to get json")
    json_obj = resp.json()
    matches = json_obj.get("results", "{}").get("albummatches", {})
    return matches


def get_album_matches_from_artist(api_key: str, artist: str):
    base = "http://ws.audioscrobbler.com/2.0/"
    method = "method=artist.gettopalbums"
    url = f"{base}?{method}&artist={artist}&api_key={api_key}&format=json"

    logger.debug(f"Sending request to {url}")
    resp = requests.get(url)
    json_obj = resp.json()
    albums = json_obj.get("topalbums", "{}").get("album", [])
    return albums


def find_match(matches: dict, api_key: str, album: Album):
    if album.artist == "":
        return matches.get("album", [])[0]

    for match in matches.get("album", []):
        if match.get("artist", "") == album.artist:
            return match

    # if name, artist combo not in album search, filter by artist
    for match in get_album_matches_from_artist(api_key, album.artist):
        if match.get("name", "") == album.title:
            return match

    return matches.get("album", [])[0]


def load_album(album):
    logger.debug(f"loading album: {album.title}")
    album.chosen_on = datetime.now()

    api_key = os.environ.get("LASTFM_API_KEY", "")

    matches = get_album_matches_from_name(api_key, album.title)
    if matches == []:
        return False
    final_match = find_match(matches, api_key, album)

    mbid = final_match.get("mbid", "")
    if mbid != "":
        date, ok = get_date_from_mbid(mbid)
        image_ok = load_image_from_mbid(mbid, album.title)

        if ok and image_ok:
            album.date = date
            album.image = helper.get_relative_image_path(album.title)
            helper.save_current_album(album)
            return True

    # not successful in loading with mbid
    return load_without_mbid(album, final_match)


def load_image_from_mbid(mbid: str, title: str):
    url = f"http://coverartarchive.org/release/{mbid}/front"
    r = requests.get(url, allow_redirects=True)
    if r.status_code == 200:
        open(helper.get_absolute_image_path(title), "wb").write(r.content)
        return True
    return False


def load_without_mbid(album: Album, final_match):
    logger.info(f"Attempting to load album {album.title} without mbid")

    image_url = ""
    for image in final_match['image']:
        if image['size'] == "extralarge":
            image_url = image['#text']

    if image_url != "":
        image_ok = get_and_save_image(
            image_url, helper.get_absolute_image_path(album.title))
        if image_ok:
            album.image = helper.get_relative_image_path(album.title)
            helper.save_current_album(album)
            return True
    return False


def get_and_save_image(url, image_path):
    r = requests.get(url, allow_redirects=True)
    if r.status_code == 200:
        open(image_path, "wb").write(r.content)
        return True
    return False


def get_date_from_mbid(mbid):
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
    r = requests.get(url, allow_redirects=True)
    if r.status_code == 200:
        open(image_path, "wb").write(r.content)
        return True
    return False


def get_current_album_info():
    obj = {}
    with open("album_info.json") as fp:
        obj = json.load(fp)
    return obj


def get_history():
    h = Path("history.json")
    if not h.is_file():
        with open(h, "w") as fp:
            json.dump([], fp)

    history_list = []
    with open(h, "r") as fp:
        history_list = json.load(fp)
    return history_list


def main():
    succeeded = False
    while succeeded is False:

        album = helper.get_next_album_persist()
        print(album, type(album))
        if album is None:
            logger.info("No more albums to load. Exiting")
            return

        succeeded = load_album(album)
        logger.debug(f"Album {album} success status: {succeeded}")


if __name__ == '__main__':
    main()
