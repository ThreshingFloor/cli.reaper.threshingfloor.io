# Reaper CLI Quickstart Guide 

<img src="https://s3.amazonaws.com/static.threshingfloor.io/threshingfloor_main_logo_transp.png" width="50%" height="50%">

The Reaper CLI helps you separate the signal from the noise in your logfiles. If you are running a service that faces the internet, you likely see thousands of scans, bots, and brute force attempts every day. These scans clog up your log files, and make it hard to find legitimate events of interest.

The Reaper CLI is a utility that leverages the ThreshingFloor API to reduce noisy entries from your log files. This tool is currently in closed ALPHA.

## How it Works

Reaper is powered by a network of sensors that are deployed across the internet. These sensors have no business value, but have a comprehensive set of logging rules. These logs are aggregated and analyzed before being loaded into a database that is made available through the ThreshingFloor API. Reaper analyzes your log files, and passes metadata to our API. The API returns a filter based on your metadata that is then applied to your file. The result is less noisy log files.

## Installation

From the source repository::

`$ python setup.py install`

Or via PyPi::

`$ pip install tf-reaper`

## Obtaining an API key

To obtain an API key, send an e-mail to info@threshingfloor.io requesting an API key.

## Configuration

This command will ask you to provide your API key, which you will need to obtain by request through info@threshingfloor.io

`$ reaper --configure`

## Usage

Commandline usage for reaper:

```
usage: reaper [-h] [--type {auth,http,generic}] [--noise] [--out-file OUTFILE]
              [--stats] [--dry-run] [--port PORTS] [--configure]
              [filename]

positional arguments:
  filename              Filename of log file to reduce

optional arguments:
  -h, --help            show this help message and exit
  --type {auth,http,generic}, -t {auth,http,generic}
                        Log type to analyze
  --noise, -n           Print the noise from the file rather than reducing it
  --out-file OUTFILE, -o OUTFILE
                        Output file for the result (default: STDOUT)
  --stats, -s           Print statistics to STDERR from the reduction
                        operation
  --dry-run, -d         Don't output the reduced log file, only print possible
                        reduction statistics to STDERR
  --port PORTS, -p PORTS
                        Port and protocol used by generic mode. Can be used
                        multiple times. Should be of the form "80:TCP" or
                        "53:UDP"
  --configure           Configure Reaper.
```

## Examples

Output a reduced auth log to the screen::

```
    $ reaper /var/log/auth.log
    [Results not shown]
```

Output a reduced auth log to a file and print aggregate statistics to the screen::

```
    $ reaper -o ~/auth.log.reduced -s /var/log/auth.log
    489 lines were analyzed in this log file.
    356 lines were determined to be noise by ThreshingFloor.
    133 lines were not determined to be noise by ThreshingFloor.
    The input file was reduced to 27.2% of it's original size.
```

Output a reduced HTTP access log to a file::

```
    $ reaper -t http -o ~/access.log.reduced /etc/log/access.log
```

Output lines from an HTTP access log that ThreshingFloor believed to be bots, crawlers, or other internet noise::

```
    $ cat /etc/log/access.log | reaper -t http -n
    [Results not shown]
```

Show statistics for reducing an access log by traffic seen by ThreshingFloor on TCP port 80, and do not display results to the screen::

```
    $ reaper -t generic -p 80:tcp --dry-run test/data/access.log.txt
```

## Privacy Notice

In order to reduce noise from your log files, we need to collect metadata from those file. This includes IP addresses, usernames, user agent strings, referrers, and request URI's. We use this metadata to enchance the results of our API. If you have sensitive data in your log files or prefer to not share this data with us, contact us at info@threshingfloor.io about a private on-premesis solution.

