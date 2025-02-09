import json
import hashlib

from pathlib import Path

from album_selector import UpcomingAlbums, Album

DIR_PATH = Path(__file__).parent.resolve()
LOG_DIR_PATH = DIR_PATH / "logs"
DATA_DIR_PATH = DIR_PATH / "data"

ALBUM_INFO_PATH = DATA_DIR_PATH / "album_info.json"
UPCOMING_PATH = DATA_DIR_PATH / "upcoming.json"
HISTORY_PATH = DATA_DIR_PATH / "history.json"

ABSOLUTE_IMAGES_PATH = DIR_PATH / "static" / "images"

def get_current_album() -> Album:
    return Album.load_from_file(ALBUM_INFO_PATH)

def save_current_album(album: Album):
    with open(ALBUM_INFO_PATH, 'w') as fp:
        json.dump(album.to_dict(), fp, indent=2)
    add_current_to_history()

def load_upcoming_albums() -> UpcomingAlbums:
    ua = UpcomingAlbums.load_from_file(UPCOMING_PATH)
    return ua

def add_album_upcoming(album: Album):
    ua = load_upcoming_albums()
    ua.add_album(album)
    ua.save(UPCOMING_PATH)

def add_album_json(album: dict):
    albumObj = Album.load_from_dict(album)
    add_album_upcoming(albumObj)

def get_next_album_persist() -> Album:
    ua = load_upcoming_albums()
    if ua.length_queue() == 0:
        return None
    album = ua.get_next_album()
    ua.save(UPCOMING_PATH)
    return album

def get_ip_address_hash(access_route, remote_addr) -> str:
    ip_string = ""

    if len(access_route) < 2:
        if remote_addr is not None:
            ip_string = remote_addr
    else:
        ip_string = access_route[0]

    if ip_string == "":
        return ip_string

    #hash ip address
    h = hashlib.sha256()
    h.update(ip_string.encode())
    return h.hexdigest()

def add_current_to_history():
    current = get_current_album()

    if not HISTORY_PATH.is_file():
        with open(HISTORY_PATH, 'w') as fp:
            json.dump([], fp)

    with open(HISTORY_PATH, 'r') as fp:
        history = json.load(fp)

    history.append(current.to_dict())

    with open(HISTORY_PATH, 'w') as fp:
        json.dump(history, fp, indent=2)

def get_absolute_image_path(album_name: str) -> Path:
    return ABSOLUTE_IMAGES_PATH / f"{album_name}.jpg"

def get_relative_image_path(album_name: str) -> str:
    abs = get_absolute_image_path(album_name)
    return str(abs.relative_to(DIR_PATH))
