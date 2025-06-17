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
url,SUMMARY
https://www.paycomonline.net/v4/ee/web.php/c/.blah1.,"Skip M"
https://www.paycomonline.net/v4/ee/web.php/c/.blah2.,"Anna F"
```

the program will fetch each URL, and for each event in the incoming
calendar, change the SUMMARY attribute's value to the given
string.

If an output file is named using the `--output` command line argument,
the merged calendar will be written to the named file in ICS
format. That file can then be imported into Google Calendar (and
problem others as well).
