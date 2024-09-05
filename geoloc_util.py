"""Tool for looking up geolocations. See README for details."""

import argparse
import json
import re
from typing import List, Optional, Tuple
import requests


# ================
# Useful constants
# ================

APPID = 'f897a99d971b5eef57be6fafa0d83239'
OPENWEATHERMAP_BASE_URL = 'http://api.openweathermap.org/geo/1.0'
STATES = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL",
          "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME",
          "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH",
          "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI",
          "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]
US_COUNTRY_CODE = 'US'

# ==============
# Helper classes
# ==============

# pylint: disable=R0903
class SearchType:
    """Enum-style class to express type of search"""
    NAME_STATE = 'Name,State'
    ZIP_CODE = 'Zip code'


# pylint: disable=R0903
class FakeWebResponse:
    """Represents a fake, failed web response"""
    def __init__(self):
        self.status_code = 999

class Search:
    """Represents a single search request"""

    def __init__(self, search_type: str, value: str):
        self.search_type = search_type
        self.value = value

    def __repr__(self):
        return f"{self.search_type} {self.value}"

# ================
# Helper functions
# ================

def locations_to_searches(locations: List[str]) -> Tuple[List[Search], List[str]]:
    """Converts location queries (either zipcode or city/state) into Search instances)"""
    searches = []
    errors = []
    for location in locations:
        if re.match(r'\d{5}', location):
            searches.append(Search(SearchType.ZIP_CODE, location))
        else:  # maybe it's a Name/State location?
            tokens = location.split(',')
            if len(tokens) != 2:
                errors.append(f"Location {location} does not contain one-and-only-one comma")
                continue
            city_candidate, state_candidate = tokens[0].strip(), tokens[1].strip()
            state_candidate = state_candidate.upper()
            local_errors = []
            if not city_candidate:
                local_errors.append(f"Location {location}'s city is an empty string")
            if state_candidate not in STATES:
                local_errors.append(
                    f"Location {location}'s state {state_candidate} not a valid US state")
            if local_errors:
                errors.extend(local_errors)
            else:
                searches.append(
                    Search(SearchType.NAME_STATE, f'{city_candidate},{state_candidate}'))
    return searches, errors


def perform_searches(
        searches: List[Search],
        simulate_web_failure: bool) -> Tuple[List[Tuple[Search, dict]], List[Tuple[Search, str]]]:
    """Performs a list of searches; returns a list of successful search/dict responses,
    and a list of failed search/error_message tuples"""
    successful_searches = []
    failed_searches = []

    for search in searches:
        if search.search_type == SearchType.NAME_STATE:
            path, query_param = 'direct', 'q'
        else:
            path, query_param = 'zip', 'zip'
        full_url = f'{OPENWEATHERMAP_BASE_URL}/{path}'
        params = [
            (query_param, f'{search.value},{US_COUNTRY_CODE}'),
            ('limit', '1'),
            ('appid', APPID),
        ]

        if simulate_web_failure:
            response = FakeWebResponse()
        else:
            response = requests.get(full_url, params)

        if response.status_code == 200:
            response_object = json.loads(response.text)
            if search.search_type == SearchType.NAME_STATE:
                if len(response_object):
                    first_response = response_object[0]
                else:
                    failed_searches.append((search, 'Webserver response had no matching responses'))
                    continue
            else:  # SearchType.ZIP_CODE -> just use the whole response
                first_response = response_object
            if 'local_names' in first_response:
                del first_response['local_names']
            successful_searches.append((search, first_response))
        else:  # error in the API request
            failed_searches.append(
                (search, f'Webserver returned error code: {response.status_code}'))

    return successful_searches, failed_searches

# ===================
# Main business logic
# ===================

def main(raw_args: Optional[List[str]] = None, simulate_web_failure=False) -> Tuple[str, int]:
    """Returns 0 on success, 1 if --locations has problems, 2 if lookup errors occur"""
    # Parse arguments
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, description="""
Welcome to geoloc_util, the newest, fanciest way to lookup geolocations!
                  
USAGE
 
Lookup by city/state:      python geoloc_util.py --locations "cleveland, oh"
Lookup by zip code:        python geoloc_util.py --locations "12345"
Lookup multiple locations: python geoloc_util.py --locations "12345" "cleveland, oh"

KNOWN LIMITATIONS
* All locations are assumed to be in the United States
* If you get rate-limited and need to change the API key, edit the APPID variable in this file
""")
    output_lines = []
    parser.add_argument(
        '--locations',
        nargs='+',
        help="""<Required> List of locations, where each location is either 
"<name>, <state_abbreviation>" or <5_digit_zip_code>""",
        required=True)
    args = parser.parse_args() if raw_args is None else parser.parse_args(raw_args)
    locations_set = set(args.locations)
    locations_delta = len(args.locations) - len(locations_set)
    if locations_delta:
        output_lines.append(f"Removed {locations_delta} duplicative location(s) from search")

    # Convert arguments to searches
    searches, errors = locations_to_searches(locations_set)
    if errors:
        for error in errors:
            output_lines.append(error)
        return ('\n'.join(output_lines).strip(), 1)

    # Perform searches
    successful_searches, failed_searches = perform_searches(searches, simulate_web_failure)
    if successful_searches:
        output_lines.append(f"{len(successful_searches)} successful search(es):")
        for successful_search in successful_searches:
            output_lines.append(f"Search: {successful_search[0]}\nResult: {successful_search[1]}")
    if failed_searches:
        output_lines.append(f"{len(failed_searches)} failed search(es):")
        for failed_search in failed_searches:
            output_lines.append(f"Search: {failed_search[0]}\nError: {failed_search[1]}")

    # Join it into a human-readable string and return it:
    return ('\n'.join(output_lines).strip(), 2 if failed_searches else 0)


if __name__ == '__main__':
    print(main())
