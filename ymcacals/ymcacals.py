#!/usr/bin/env python3

"Merge multiple ICS URLs, transforming user-defined attributes"

import argparse
import csv
import os.path
import re
import sys

from icalendar import Calendar, Event
import requests


class CalendarMerger:
    "The meat of the operation"
    def __init__(self, urls, confirmed):
        self.verbose = False
        self.urls = urls
        self.confirmed = confirmed

    @property
    def confirmed(self):
        "Confirmed flag"
        return self._confirmed

    @confirmed.setter
    def confirmed(self, value):
        assert value in (True, False)
        self._confirmed = value

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
        "CSV file containing urls and params to process"
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
        class NoMatch(Exception):
            "Exception raised when a filtering match fails"
            # pylint: disable=unnecessary-pass
            pass

        with open(self.urls, encoding="utf-8") as urlf:
            rdr = csv.DictReader(urlf)
            assert "url" in rdr.fieldnames
            # attribute/value pairs for substitution
            params = {}
            # regular expression patters for filtering
            matches = {}
            fieldnames = set(rdr.fieldnames) - set(["url"])
            uids = set()
            for row in rdr:
                url = row["url"].strip()
                for key in fieldnames:
                    if key.startswith("match:"):
                        # This is a filtering attribute
                        _, field = key.split(":", maxsplit=1)
                        matches[field] = row[key].strip()
                    else:
                        params[key] = row[key].strip()
                req = requests.get(url, timeout=20.0)
                cal = Calendar.from_ical(req.text)
                for event in cal.walk("VEVENT"):
                    try:
                        for field, pat in matches.items():
                            if re.match(pat, event[field], re.I) is None:
                                raise NoMatch(f"{pat}/{event[field]}")
                    except NoMatch as exc:
                        if self.verbose:
                            print("Filter miss:", exc.args[0], file=sys.stderr)
                        continue
                    copy = self.copy_event(event, params)
                    assert copy["UID"] not in uids
                    uids.add(copy["UID"])
                    combined_cal.add_component(copy)
        return combined_cal

    def copy_event(self, event, params):
        "Copy an event, making desired field substitutions"
        copied_event = Event()
        for attr in event:
            param = params.get(attr) or event[attr]
            if self.verbose and event[attr] != param:
                print("attr:", attr, event[attr], "->", param, file=sys.stderr)
            if isinstance(event[attr], list):
                for element in event[attr]:
                    copied_event.add(attr, element)
            else:
                copied_event.add(attr, param)

        # Confirmed status is special. We blindly override whatever is present
        # as the STATUS attribute, and require the event has a UID. If it
        # lacks one, we create one.
        if "UID" not in event:
            print("Cowardly refuse to set STATUS without a UID. Generating one.",
                  file=sys.stderr)
            # We use the copied event as the source for the UID because you
            # might have two lifeguards with identical start/end times and a
            # SUMMARY of "lifeguard." That wouldn't be very unique. We assume
            # the SUMMARY field is overwritten to reflect the lifeguard's name.
            copied_event["UID"] = self.generate_uid(copied_event)
        copied_event["STATUS"] = "CONFIRMED" if self.confirmed else "CANCELLED"
        return copied_event

    def generate_uid(self, event):
        "Generate repeatable uid."
        uid = ""
        for key in ("DTSTART", "DTEND"):
            if key in event:
                uid += event[key].dt.isoformat()
        if "SUMMARY" in event:
            uid += str(event["SUMMARY"])
        assert uid
        return hash(uid)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--urls", dest="urls", required=True)
    parser.add_argument("-o", "--output", dest="output")
    parser.add_argument("-v", "--verbose", dest="verbose", default=False,
                        action="store_true")
    parser.add_argument("-c", "--confirmed", dest="confirmed", default=True,
                        action="store_true")
    parser.add_argument("-C", "--cancelled", dest="confirmed", default=False,
                        action="store_false")
    args = parser.parse_args()

    merger = CalendarMerger(args.urls, args.confirmed)
    merger.verbose = args.verbose
    combined_cal = merger.merge_cals()
    if args.output is not None:
        with open(args.output, mode="w", encoding="utf-8") as outf:
            print(combined_cal.to_ical().decode(), file=outf)


if __name__ == "__main__":
    sys.exit(main())
