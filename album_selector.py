import json
import random
import logging

from pathlib import Path
from datetime import datetime, timedelta

dir_path = Path(__file__).parent.resolve()
logger = logging.getLogger(__name__)
logging.basicConfig(filename=dir_path / "logs" / "album_selection.log",
                    encoding="utf-8",
                    format='%(asctime)s %(levelname)s: %(message)s',
                    datefmt="%Y-%m-%d %H:%M:%S",
                    level=logging.DEBUG)

class Album():
    def __init__(self, title: str, artist: str,
                 submitted_on: datetime = datetime.now(),
                 submitted_by: str = "",
                 date: str = "",
                 chosen_on: datetime = datetime.min,
                 image: str = ""):
        self.title = title
        self.artist = artist
        self.submitted_on = submitted_on
        self.submitted_by = submitted_by

        self.date = date
        self.chosen_on = chosen_on
        self.image = image

    def to_dict(self):
        return {
            'title': self.title,
            'artist': self.artist,
            'submitted_on': self.submitted_on.isoformat(),
            'submitted_by': self.submitted_by,
            'chosen_on': self.chosen_on.isoformat(),
            'image': self.image,
            'date': self.date
        }

    @classmethod
    def load_from_dict(cls, album_info: dict):
        return cls(
            title=album_info.get("title"),
            artist=album_info.get("artist"),
            submitted_by=album_info.get("submitted_by", ""),
            submitted_on=datetime.fromisoformat(album_info.get("submitted_on")),
            chosen_on=datetime.fromisoformat(album_info.get("chosen_on")),
            image=album_info.get("image", ""),
            date=album_info.get("date", "")
        )

    @classmethod
    def load_from_file(cls, filepath: str | Path):
        with open(filepath, 'r') as fp:
            obj = json.load(fp)
        return cls.load_from_dict(obj)

    def __eq__(self, other):
        if not isinstance(other, Album):
            return NotImplemented
        return self.title == other.title and self.artist == other.artist and \
            self.submitted_by == other.submitted_by and \
            self.submitted_on == other.submitted_on

class Bin():
    def __init__(self, start: datetime, id: int):
        self.elements: list[Album] = []
        self.start = start
        self.id = id

    def is_album_valid_entry(self, album: Album) -> bool:
        return abs(album.submitted_on - self.start) < timedelta(hours=16)

    def add_album(self, album: Album):
        self.elements.append(album)

    def to_dict(self):
        return {
            'elements': [album.to_dict() for album in self.elements],
            'start': self.start.isoformat(),
            'id': self.id
        }

    @classmethod
    def from_dict(cls, data: dict):
        start = datetime.fromisoformat(data['start'])
        id = data['id']

        newBin = cls(start, id)
        for album_dict in data['elements']:
            newBin.elements.append(Album.load_from_dict(album_dict))
        return newBin

    def __len__(self) -> int:
        return len(self.elements)

    def __eq__(self, other):
        if not isinstance(other, Bin):
            return NotImplemented
        return self.id == other.id and self.start == other.start and \
            self.elements == other.elements

class UpcomingAlbums():
    def __init__(self):
        self.bins: list[Bin] = []
        self.next_id: int = 1
        self.streak_len: int = 0
        self.streak_id: int = -1

    def length_queue(self) -> int:
        return sum([len(bin) for bin in self.bins])

    def add_album(self, album: Album):
        logger.debug("Adding album %s", album.title)
        added = False
        for bin in self.bins:
            if bin.is_album_valid_entry(album):
                bin.add_album(album)
                added = True
                break
        if not added:
            newBin = Bin(album.submitted_on, self.next_id)
            self.next_id += 1
            newBin.add_album(album)
            self.bins.append(newBin)

    def get_next_album(self) -> Album:
        if self.length_queue() == 0:
            return None

        # bins = self.make_bins()
        selected_bin_idx = self.select_random_bin_idx()

        selected_bin = self.bins[selected_bin_idx]
        r_idx = random.randrange(len(selected_bin.elements))
        album = self.bins[selected_bin_idx].elements.pop(r_idx)
        if len(self.bins[selected_bin_idx].elements) == 0:
            self.bins.pop(selected_bin_idx)

        return album

    def select_random_bin_idx(self) -> int:
        logger.debug("Selecting random bin index")

        num_bins = min(len(self.bins), 6)
        relative_odds = [1 for _ in range(num_bins)]

        # iterate backwards with second to last idx
        for i in range(num_bins - 2, -1, -1):
            bin = self.bins[i]
            mult = len(bin) + 1
            if self.streak_id == bin.id:
                mult -= self.streak_len
                if mult < 1:
                    mult = pow(2, mult)
            relative_odds[i] = mult * relative_odds[i + 1]

        probabilities = [p / sum(relative_odds) for p in relative_odds]
        logger.debug(f"random bin idx relative probabilities {probabilities}")

        random_value = random.random()
        logger.debug(f"random value selected: {random_value}")

        for idx, p in enumerate(probabilities):
            if random_value >= p:
                random_value -= p
                continue

            bin = self.bins[idx]
            if self.streak_id == bin.id:
                self.streak_len += 1
            else:
                self.streak_id = bin.id
                self.streak_len = 1
            return idx

        bin = self.bins[0]
        if self.streak_id == bin.id:
            self.streak_len += 1
        else:
            self.streak_id = bin.id
            self.streak_len = 1
        return idx

    def save(self, filename: str | Path):
        data = {
            'bins': [bin.to_dict() for bin in self.bins],
            'next_id': self.next_id,
            'streak_len': self.streak_len,
            'streak_id': self.streak_id,
        }
        with open(filename, 'w') as fp:
            json.dump(data, fp, indent=2)

    @classmethod
    def load_from_file(cls, filename: Path):

        # no file exists, init
        if not filename.is_file():
            obj = cls()
            obj.save(filename)
            return obj

        with open(filename, 'r') as fp:
            data = json.load(fp)

        upcoming = cls()
        for bin_data in data.get('bins', []):
            upcoming.bins.append(Bin.from_dict(bin_data))
        upcoming.next_id = data.get('next_id', 1)
        upcoming.streak_len = data.get('streak_len', 0)
        upcoming.streak_id = data.get('streak_id', -1)

        return upcoming

    def __eq__(self, other):
        if not isinstance(other, UpcomingAlbums):
            return NotImplemented
        return self.bins == other.bins and \
            self.next_id == other.next_id and \
            self.streak_len == other.streak_len and \
            self.streak_id == other.streak_id
