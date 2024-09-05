"""Unit tests of geoloc_util"""

import unittest
import geoloc_util

class GeolocUtilTests(unittest.TestCase):
    """Tests of geoloc_util"""

    # ===========
    # Error cases
    # ===========

    def test_no_locations_argument(self):
        """Tests what happens when --locations is not given"""
        self.assertRaises(BaseException, geoloc_util.main, [])

    def test_locations_argument_empty(self):
        """Tests what happens when --locations is given but is empty"""
        self.assertRaises(BaseException, geoloc_util.main, ['--locations'])

    def test_zipcode_malformed(self):
        """Tests what happens when zipcode is given but isn't 5 digits"""
        self.assertEqual(
            geoloc_util.main(['--locations', '123']),
            ('Location 123 does not contain one-and-only-one comma', 1))

    def test_missing_city(self):
        """Tests what happens what city/state is given but city is empty"""
        self.assertEqual(
            geoloc_util.main(['--locations', ',OH']),
            ("Location ,OH's city is an empty string", 1))

    def test_missing_state(self):
        """Tests what happens when city/state is given but state is empty"""
        self.assertEqual(
            geoloc_util.main(['--locations', 'cleveland,']),
            ("Location cleveland,'s state  not a valid US state", 1))

    def test_invalid_state(self):
        """Tests what happens when city/state is given but state is malformed"""
        self.assertEqual(
            geoloc_util.main(['--locations', 'cleveland,ZZ']),
            ("Location cleveland,ZZ's state ZZ not a valid US state", 1))

    def test_bad_web_response(self):
        """Tests what happens when we simulate an underlying web response failure"""
        self.assertEqual(
            geoloc_util.main(['--locations', 'cleveland,OH'], simulate_web_failure=True),
            ("""1 failed search(es):
Search: Name,State cleveland,OH
Error: Webserver returned error code: 999""", 2))

    # ===========
    # Happy paths
    # ===========

    def test_valid_zipcode(self):
        """Tests what happens when a valid zipcode is given"""
        # pylint: disable=C0301
        self.assertEqual(
            geoloc_util.main(['--locations', '12345']),
            ("""1 successful search(es):
Search: Zip code 12345
Result: {'zip': '12345', 'name': 'Schenectady', 'lat': 42.8142, 'lon': -73.9396, 'country': 'US'}""", 0))

    def test_valid_zipcode_duplicated(self):
        """Tests what happens what a valid zipcode is given twice"""
        # pylint: disable=C0301
        self.assertEqual(
            geoloc_util.main(['--locations', '12345', '12345']),
            ("""Removed 1 duplicative location(s) from search
1 successful search(es):
Search: Zip code 12345
Result: {'zip': '12345', 'name': 'Schenectady', 'lat': 42.8142, 'lon': -73.9396, 'country': 'US'}""", 0))

    def test_valid_city_state(self):
        """Tests what happens when a valid city/state is given"""
        # pylint: disable=C0301
        self.assertEqual(
            geoloc_util.main(['--locations', 'cleveland, oh']),
            ("""1 successful search(es):
Search: Name,State cleveland,OH
Result: {'name': 'Cleveland', 'lat': 41.4996574, 'lon': -81.6936772, 'country': 'US', 'state': 'Ohio'}""", 0))


if __name__ == '__main__':
    unittest.main()
