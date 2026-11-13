import unittest
from preferences import parse_games, serialize_games


class Preferences(unittest.TestCase):
    def test_invalid_and_unknown_values(self):
        for raw in ('', None, '{}', '"cs2"', '["unknown"]'):
            self.assertEqual(parse_games(raw), [])
        self.assertEqual(parse_games('["fivem","cs2","cs2",null]'), ['cs2', 'fivem'])
        with self.assertRaises(ValueError):
            serialize_games([])

    def test_round_trip_keeps_order(self):
        self.assertEqual(parse_games(serialize_games({'fivem', 'cs2'})), ['cs2', 'fivem'])


if __name__ == '__main__':
    unittest.main()
