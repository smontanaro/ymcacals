#!/usr/bin/env python3

"Merge multiple ICS URLs, transforming user-defined attributes"

import argparse
import os.path
import sys

from icalendar import Calendar, Event
import requests


class CalendarMerger:
    "The meat of the operation"
    def __init__(self):
        self._verbose = False
        self._urls = "/dev/null"

    @property
    def verbose(self):
        "Verbose flag"
        return self._verbose

    @verbose.setter
    def verbose(self, value):
        assert value in (True, False)
        self._verbose = value

    @property
    def urls(self):
        "file containing urls and params to process"
        return self._urls

    @urls.setter
    def urls(self, urlfile):
        assert os.path.exists(urlfile)
        self._urls = urlfile

    def merge_cals(self):
        combined_cal = Calendar()
        combined_cal.add('prodid', '-//icalcombine//NONSGML//EN')
        combined_cal.add('version', '2.0')
        combined_cal.add('x-wr-calname', "Lifeguard Schedule")
        with open(self.urls, encoding="utf-8") as urlf:
            for line in urlf:
                try:
                    url, pstr = line.split(maxsplit=1)
                    params = {}
                    for pair in pstr.strip().split(","):
                        key, val = pair.split("=")
                        params[key] = val
                except ValueError:
                    url = line
                    params = {}
                url = url.strip()
                req = requests.get(url, timeout=20.0)
                cal = Calendar.from_ical(req.text)
                for event in cal.walk("VEVENT"):
                    if event["UID"] in ("calendarExpiredEvent",
                                        "calendarExpiringEvent"):
                        continue
                    copied_event = Event()
                    for attr in event:
                        param = params.get(attr) or event[attr]
                        if self.verbose:
                            print("attr:", attr, param)
                        if isinstance(event[attr], list):
                            for element in event[attr]:
                                copied_event.add(attr, element)
                        else:
                            copied_event.add(attr, param)
                    combined_cal.add_component(copied_event)
        return combined_cal


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--urls", dest="urls", required=True)
    parser.add_argument("-o", "--output", dest="output")
    parser.add_argument("-v", "--verbose", dest="verbose", default=False,
                        action="store_true")
    args = parser.parse_args()

    merger = CalendarMerger()
    merger.urls = args.urls
    merger.verbose = args.verbose
    combined_cal = merger.merge_cals()
    if args.output is not None:
        with open(args.output, mode="w", encoding="utf-8") as outf:
            print(combined_cal.to_ical().decode(), file=outf)


if __name__ == "__main__":
    sys.exit(main())
