import unittest
import album_selector
from datetime import datetime
from collections import defaultdict

class TestAlbumSelector(unittest.TestCase):

    def test_album_obj(self):
        album = album_selector.Album("testName", "artist")
        album_json = album.to_dict()
        album_two = album_selector.Album.load_from_dict(album_json)

        self.assertEqual(album, album_two)

    def test_bin_obj(self):
        bin = album_selector.Bin(start=datetime.now(), id=14)
        bin.add_album(album_selector.Album("testName", "artist"))
        bin.add_album(album_selector.Album("testName2", "artist"))

        bin_json = bin.to_dict()
        bin2 = album_selector.Bin.from_dict(bin_json)

        self.assertEqual(bin, bin2)

    def test_upcoming_albums(self):
        ua = album_selector.UpcomingAlbums()
        for album in generate_dummy_data():
            ua.add_album(album)

        self.assertEqual(len(ua.bins), 5)
        self.assertEqual(len(ua.bins[0]), 4)
        self.assertEqual(len(ua.bins[1]), 3)
        self.assertEqual(len(ua.bins[2]), 1)
        self.assertEqual(len(ua.bins[3]), 2)
        self.assertEqual(len(ua.bins[4]), 2)
        self.assertEqual(ua.length_queue(), len(generate_dummy_data()))

    def test_selector_works(self):
        ua = album_selector.UpcomingAlbums()
        for album in generate_dummy_data():
            ua.add_album(album)

        count = 0
        albums = []
        while ua.length_queue() > 0:
            albums.append(ua.get_next_album())
            count += 1
        self.assertEqual(count, len(generate_dummy_data()))

    def test_bin_selection(self):

        albums = generate_dummy_data()
        instances_of_first = {x: 0 for x in range(5)}

        n = 10000
        for i in range(n):
            ua = album_selector.UpcomingAlbums()
            for album in albums:
                ua.add_album(album)
            bin = ua.select_random_bin_idx()
            instances_of_first[bin] += 1

        expec_prob = [96, 24, 6, 3, 1]
        probabilities = [x / sum(expec_prob) for x in expec_prob]

        for bin_num, count in instances_of_first.items():
            prob = probabilities[bin_num]
            actual = count / n
            self.assertGreater(actual, prob - .05, "More than 5% difference")
            self.assertGreater(prob + .05, actual, "More than 5% difference")

    def test_empty_ua(self):
        ua = album_selector.UpcomingAlbums()
        next = ua.get_next_album()
        self.assertIsNone(next)

    def test_pop_all(self):
        ua = album_selector.UpcomingAlbums()
        for album in generate_dummy_data():
            ua.add_album(album)
        while ua.length_queue() > 0:
            album = ua.get_next_album()
        self.assertEqual(len(ua.bins), 0)

def generate_dummy_data() -> list[album_selector.Album]:
    return [
        album_selector.Album("A", "artist", datetime(2024, 10, 1, 8, 0), 'ip1'),
        album_selector.Album("B", "artist", datetime(2024, 10, 1, 8, 1), 'ip1'),
        album_selector.Album("C", "artist", datetime(2024, 10, 1, 8, 2), 'ip1'),
        album_selector.Album("D", "artist", datetime(2024, 10, 1, 9, 0), 'ip1'),
        album_selector.Album("E", "artist", datetime(2024, 10, 13, 8, 0), 'ip2'),
        album_selector.Album("F", "artist", datetime(2024, 10, 13, 8, 1), 'ip2'),
        album_selector.Album("G", "artist", datetime(2024, 10, 13, 8, 2), 'ip2'),
        album_selector.Album("H", "artist", datetime(2024, 12, 1, 8, 0), 'ip1'),
        album_selector.Album("I", "artist", datetime(2025, 1, 1, 8, 0), 'ip3'),
        album_selector.Album("J", "artist", datetime(2025, 1, 1, 8, 1), 'ip3'),
        album_selector.Album("K", "artist", datetime(2025, 2, 3, 8, 0), 'ip4'),
        album_selector.Album("L", "artist", datetime(2025, 2, 3, 8, 13), 'ip3'),
    ]

if __name__ == '__main__':
    unittest.main()
