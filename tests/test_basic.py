# simple no-op test so tox doesn't keep complaining until I get real tests...

from pathlib import Path
import subprocess
import sys
import time

import icalendar
import requests

from ymcacals.ymcacals import CalendarMerger

def test_basic():
    server = subprocess.Popen([sys.executable, "-m", "http.server", "-d", "./tests"])
    for _i in range(10):
        # give server time to start
        time.sleep(0.25)
        try:
            x = requests.get("http://localhost:8000/skip.ics")
        except requests.exceptions.ConnectionError:
            continue
        break
    else:
        raise requests.exceptions.ConnectionError("Too many failed connection attempts")
    try:
        merger = CalendarMerger(Path(__file__).parent / "skip.csv", True)
        merger.verbose = False
        merged = merger.merge_cals()
        assert len(merged.events) == 29
        for event in merged.events:
            assert event["SUMMARY"].lower() == "skip m"
    finally:
        server.kill()
