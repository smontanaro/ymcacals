# YMCAcals

Simple little script to merge YMCA lifeguard calendars into something
printable for the pool office

## Simple Usage

The `ymcacals` program reads a CSV file containing ICS calendar URLs,
one per line, merges the calendars and writes a new ICS file. Each
line can also include attribute substitutions. A column named "url"
must exist in the file. Any other columns are assumed to be event
attribute names. For example, given this file:

```
url,SUMMARY,match:SUMMARY
https://www.paycomonline.net/v4/ee/web.php/c/.blah1.,"Skip M",lifeguard
https://www.paycomonline.net/v4/ee/web.php/c/.blah2.,"Anna F",lifeguard
```

the program will fetch each URL, and for each event in the incoming
calendar, change the SUMMARY attribute's value to the given
string. Events whose SUMMARY field start with "lifeguard" (case
insensitive) are the only ones which will be included in the merged
calendar. As might be obvious from the above example, the filter test
for inclusion is performed before attribute values are
overwritten. ;-)

If an output file is named using the `--output` command line argument,
the merged calendar will be written to the named file in ICS
format. That file can then be imported into Google Calendar (and
problem others as well).

## Refreshing the schedule

What happens if you filter a calendar to spec then grab and filter it
again from the Paycom server sometime later? Paycom doesn't appear to
understand the concept of "confirmed" or "cancelled" events, despite
the fact that the ICS spec does. The `ymcacals` program understands
`--confirmed` and `--cancelled` status. To handle changes, you can run
the program once to get all the current (confirmed) events of
interest, then a second time to cancel them. The workflow would look
something like this:

```
% ymcacals -u calendars.csv --confirmed -o confirmed.ics
% ymcacals -u calendars.csv --cancelled -o cancelled.ics
```

You'd then import the `confirmed.ics` calendar into your empty Google
calendar. Later on, when you want to refresh the currently active
events, you'd import the `cancelled.ics` file into your Google
calendar to wipe the slate clean, then repeat the above two steps to
refresh the schedule. Note that we generate both confirmed and
cancelled versions of the schedule at the same time, but don't use the
`cancelled.ics` file until we want to refresh the schedule.

This is a hack because Paycom, as I indicated, doesn't have the notion
of confirmed or cancelled events. In a similar vein, Google Calendar
doesn't support bulk deletion of events. Imagine having to delete
hundreds of events one-by-one to refresh the schedule.
