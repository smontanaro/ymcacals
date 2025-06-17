# YMCAcals

Simple little script to merge YMCA lifeguard calendars into something
printable for the pool office

## Simple Usage

The `ymcacals` program reads a file containing ICS calendar URLs, one
per line, merges the calendars and writes a new ICS file. Each line
can also include attribute substitutions. For example, given these
lines:

https://www.paycomonline.net/v4/ee/web.php/c/.blah1. SUMMARY=Skip M
https://www.paycomonline.net/v4/ee/web.php/c/.blah2. SUMMARY=Anna F

the program will fetch each URL, and for each event in the incoming
calendar, change the SUMMARY attribute's value to the given
string. Multiple key/value pairs can be given, separating them by
commas:

https://www.paycomonline.net/v4/ee/web.php/c/.blah1. SUMMARY=Skip M,DESCRIPTION=None

(This is just the first try. A CSV file is probably a better format
for the inputs.)

If an output file is named using the `--output` command line argument,
the merged calendar will be written to the named file in ICS
format. That file can then be imported into Google Calendar (and
problem others as well).
