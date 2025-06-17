# simple no-op test so tox doesn't keep complaining until I get real tests...

from pathlib import Path

import icalendar

from ymcacals.ymcacals import CalendarMerger

def test_basic():
    ics_path = Path(__file__).parent / "skip.ics"
    calendar = icalendar.Calendar.from_ical(ics_path.read_bytes())
    assert calendar.events
