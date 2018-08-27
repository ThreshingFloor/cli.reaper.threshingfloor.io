import logging
import sys
from argparse import ArgumentParser

from libtf.logparsers.tf_exceptions import TFAPIUnavailable, TFException, TFLogParsingException

from .reaper_configuration import ReaperConfiguration
from .reaper_filter import ReaperFilter


def main():
    logger = logging.getLogger('tf-reaper')
    logger.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter('[tf-reaper] [%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)s] %(message)s', )
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)
    logger.addHandler(console_handler)

    try:
        args = parse_args()

        if args.configure is True:
            ReaperConfiguration.prompt_user(overwrite=True)
            print('Reaper has been successfully configured.')
            exit(0)

        config = ReaperConfiguration.prompt_user()

        if args.filename is not None:
            stream = open(args.filename, 'r')
            filename = args.filename
        else:
            stream = sys.stdin
            filename = None

        try:
            ReaperFilter(config=config, stream=stream, filename=filename, log_type=args.type, show_noise=args.shownoise,
                         output_file=args.outfile, show_stats=args.showstats, dry_run=args.dryrun,
                         ports=args.ports).run()
        finally:
            if filename:
                stream.close()
    except (TFException, TFLogParsingException) as e:
        sys.stderr.write("\n\nFailed to parse: %s\n\n" % e)
        exit(1)
    except TFAPIUnavailable as e:
        sys.stderr.write("\n\nFailed to contact ThreshingFloor API: %s\n\n" % e)
        exit(1)
    except KeyboardInterrupt as e:
        exit()


def parse_args():
    parser = ArgumentParser()

    parser.add_argument('--type', '-t', help='Log type to analyze',
                        choices=['auth', 'http', 'generic'], type=str, action='store',
                        required=False, dest='type')

    parser.add_argument('--noise', '-n', help='Print the noise from the file rather than reducing it',
                        action='store_true', required=False, dest='shownoise')

    parser.add_argument('--out-file', '-o', help='Output file for the result (default: STDOUT)',
                        type=str, action='store', required=False, dest='outfile')

    parser.add_argument('--stats', '-s', help='Print statistics to STDERR from the reduction operation',
                        action='store_true', required=False, dest='showstats')

    parser.add_argument('--dry-run', '-d', help='Don\'t output the reduced log file, only print possible reduction '
                                                'statistics to STDERR',
                        action='store_true', required=False, dest='dryrun')

    parser.add_argument('--port', '-p', help='Port and protocol used by generic mode. Can be used multiple times. '
                                             'Should be of the form \"80:TCP\" or \"53:UDP\"',
                        type=str, action='append', required=False, dest='ports')

    parser.add_argument('--configure', help='Configure Reaper.',
                        action='store_true', required=False, dest='configure')

    parser.add_argument('filename', help='Filename of log file to reduce',
                        type=str, action='store', nargs='?')

    return parser.parse_args()
