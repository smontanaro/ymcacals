# simple no-op test so tox doesn't keep complaining until I get real tests...

from pathlib import Path
import subprocess
import sys
import time

import icalendar
import requests

from ymcacals.ymcacals import CalendarMerger


def test_basic(httpserver):
    with open("./tests/skip.ics") as ics:
        httpserver.expect_request("/skip.ics"). \
            respond_with_data(ics.read(), content_type="text/plain")
        x = requests.get(httpserver.url_for("/skip.ics"))
        merger = CalendarMerger(Path(__file__).parent / "skip.csv", True)
        merger.test_pfx = httpserver.url_for("/")
        merger.verbose = False
        merged = merger.merge_cals()
        assert len(merged.events) == 29
        uids = set()
        for event in merged.events:
            assert event["SUMMARY"].lower() == "skip m"
            uids.add(event["UID"])
        assert len(uids) == len(merged.events)
