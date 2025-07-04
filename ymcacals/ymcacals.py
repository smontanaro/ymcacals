#!/usr/bin/env python3

"Merge multiple ICS URLs, transforming user-defined attributes"

import argparse
import csv
import datetime
import re
import sys
import time
import urllib.parse

from icalendar import Calendar, Event
import requests

# pylint: disable=too-many-instance-attributes
class CalendarMerger:
    "The meat of the operation"
    def __init__(self, args):
        self.verbose = args.verbose
        self.confirmed = args.confirmed
        self.start = args.start
        self.end = args.end

    # pylint: disable=too-many-branches
    def merge_cals(self, calendars):
        combined_cal = Calendar()
        combined_cal.add('prodid', '-//icalcombine//NONSGML//EN')
        combined_cal.add('version', '2.0')
        combined_cal.add('x-wr-calname', "Lifeguard Schedule")
        class NoMatch(Exception):
            "Exception raised when a filtering match fails"
            # pylint: disable=unnecessary-pass
            pass

        for (cal, matches, params) in calendars:
            for event in cal.walk("VEVENT"):
                try:
                    for field, pat in matches.items():
                        if re.match(pat, event[field], re.I) is None:
                            raise NoMatch(f"{pat}/{event[field]}")
                except NoMatch as exc:
                    if self.verbose:
                        print("Filter miss:", exc.args[0], file=sys.stderr)
                    continue
                if "DTSTART" not in event or "DTEND" not in event:
                    if self.verbose:
                        print("Event without date/time details",
                              file=sys.stderr)
                    continue
                start_date = event["DTSTART"].dt.date()
                end_date = event["DTEND"].dt.date()
                if self.verbose:
                    print(self.start, start_date, end_date, self.end,
                          self.start <= start_date <= end_date <= self.end,
                          file=sys.stderr)
                if not self.start <= start_date <= end_date <= self.end:
                    if self.verbose:
                        print("Event date/time out of range",
                              file=sys.stderr)
                    continue
                copy = self.copy_event(event, params)
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

    @property
    def start(self):
        "Start flag"
        return self._start

    @start.setter
    def start(self, value):
        assert isinstance(value, datetime.date)
        self._start = value

    @property
    def end(self):
        "End flag"
        return self._end

    @end.setter
    def end(self, value):
        assert isinstance(value, datetime.date)
        self._end = value

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


EPOCH = datetime.datetime.fromtimestamp(0)

# pylint: disable=too-few-public-methods
class Fetcher:
    "url fetcher which tries to be kind to servers"
    def __init__(self, delta=5.0):
        self.last = {}
        self.min_delta = datetime.timedelta(seconds=delta)

    def get(self, url):
        parts = urllib.parse.urlparse(url)
        last_fetch = self.last.get(parts.netloc, EPOCH)
        if datetime.datetime.now() - last_fetch < self.min_delta:
            time.sleep(self.min_delta.total_seconds())
        self.last[parts.netloc] = datetime.datetime.now()
        return requests.get(url, timeout=20.0)

def fetch_urls(urls, delta=5.0, _test_pfx=""):
    "fetch the various ics files from the server(s)"
    # _test_pfx is only used for testing
    calendar_info = []
    fetcher = Fetcher(delta=delta)
    with open(urls, encoding="utf-8") as urlf:
        rdr = csv.DictReader(urlf)
        assert "url" in rdr.fieldnames
        fieldnames = set(rdr.fieldnames) - set(["url"])
        for row in rdr:
            # attribute/value pairs for substitution
            params = {}
            # regular expression patters for filtering
            matches = {}
            # hack for testing...
            url = row["url"].strip().replace("{server}", _test_pfx)
            req = fetcher.get(url)
            cal = Calendar.from_ical(req.text)
            for key in fieldnames:
                if key.startswith("match:"):
                    # This is a filtering attribute
                    _, field = key.split(":", maxsplit=1)
                    matches[field] = row[key].strip()
                else:
                    params[key] = row[key].strip()
            calendar_info.append([cal, matches, params])
    return calendar_info

# from https://gist.github.com/monkut/e60eea811ef085a6540f
def parse_date_arg(date_str):
    """custom argparse *date* type for user dates"""
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError as exc:
        msg = f"Date ({date_str}) not valid! Expected format, YYYY-MM-DD!"
        raise argparse.ArgumentTypeError(msg) from exc

def get_argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--urls", dest="urls", required=True,
                        help="CSV file containing ICS URLs, etc")
    parser.add_argument("-o", "--output", dest="output",
                        help="Output file for merged calendars")
    parser.add_argument("-s", "--start", dest="start", type=parse_date_arg,
                        default=datetime.date(2000, 1, 1),
                        help="Earliest date to include in output")
    parser.add_argument("-e", "--end", dest="end", type=parse_date_arg,
                        default=datetime.date(2050, 12, 31),
                        help="Last date to include in output")
    parser.add_argument("-v", "--verbose", dest="verbose", default=False,
                        action="store_true", help="Be chattier")
    parser.add_argument("-c", "--confirmed", dest="confirmed", default=True,
                        action="store_true",
                        help="Generate 'status=confirmed' records")
    parser.add_argument("-C", "--cancelled", dest="confirmed", default=False,
                        action="store_false",
                        help="Generate 'status=cancelled' records")
    parser.add_argument("-d", "--delta", dest="delta", default=0.5,
                        type=float,
                        help="Delay in seconds before querying the same server")
    parser.add_argument("--test_pfx", dest="_test_pfx", default="",
                        help="Ignore - TESTING ONLY!")
    return parser

def main():
    p = get_argument_parser()
    args = p.parse_args()

    calendars = fetch_urls(urls=args.urls, delta=args.delta,
        _test_pfx=args._test_pfx)

    merger = CalendarMerger(args)
    merger.verbose = args.verbose
    combined_cal = merger.merge_cals(calendars)
    if args.output is not None:
        with open(args.output, mode="w", encoding="utf-8") as outf:
            print(combined_cal.to_ical().decode(), file=outf)


if __name__ == "__main__":
    sys.exit(main())
