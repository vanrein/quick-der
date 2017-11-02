# Continuous Integration Tools

This directory holds data for Continuous Integration .. stuff.
Basically that means some shell scripts running on Travis as
part of the Travis CI which is triggered by GitHub.

 - `travis-continuous.sh` runs on every commit

It's conceivable we have other kinds of Travis runs, e.g. cron
jobs, in which case we can add a `travis.sh` that distinguishes
the runs and hands off to an appropriate other script.

