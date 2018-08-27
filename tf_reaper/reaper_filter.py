import itertools
import ntpath
import re
import signal
import sys
import time

from libtf.logparsers.tf_auth_log import TFAuthLog
from libtf.logparsers.tf_exceptions import TFLogParsingException, TFException, TFAPIUnavailable
from libtf.logparsers.tf_generic_log import TFGenericLog
from libtf.logparsers.tf_http_log import TFHttpLog
from six import StringIO

from .google_analytics import ga
from .loggers import default_logger, stats_logger
from .reaper_statistics_reporter import ReaperStatisticsReporter


class StreamExhausted(Exception):
    pass


class ReaperFilter(object):
    http_regex = "^\[(?P<timestamp>.+)?\]\s\"(?P<request>.+?)\"\s(?P<responseCode>\d+)\s(?P<size>\d+)" \
                 "(?P<combinedFields>.*)"

    # Default number of lines to process before log processing and reporting back statistics
    default_batch_size = 10000

    def __init__(self, config, stream, filename=None, log_type=None, ports=None, show_noise=False, show_stats=False,
                 dry_run=False, output_file=None, batch_size=None):
        self.config = config

        self.stream = stream
        if not hasattr(self.stream, 'readline'):
            self.stream = StringIO("\n".join(self.stream))

        self.filename = filename
        self.log_type = log_type
        self.ports = ports
        self.show_noise = show_noise
        self.show_stats = show_stats
        self.dry_run = dry_run
        self.output_file = output_file
        self.log_file = None
        self.stream_exhausted = False
        self.batch_size = batch_size or self.default_batch_size

        # User may opt out depending on the config
        self.stats_reporter = ReaperStatisticsReporter(config) if self.config.report_stats else None

        if not self.log_type:
            self._guess_type()

    def get_batched_lines_generator(self):
        """
        Yield lines until 'self.batch_size' is met or EOF. Once batch size is exceeded stop yielding
        so that the self.log_file object processes the chunk and stats are reported.
        """
        counter = 0
        while True:
            line = self.stream.readline()
            if not line:
                break

            counter += 1
            yield line
            if counter == self.batch_size:
                return

        self.stream_exhausted = True

    def run(self):
        while not self.stream_exhausted:
            try:
                if not self.log_type:
                    try:
                        self._guess_type()
                    except TFException as e:
                        if self.ports is not None:
                            self.log_type = 'generic'
                        else:
                            default_logger.error(e)
                            raise

                if self.log_type == 'auth':
                    self.log_file = TFAuthLog(self.get_batched_lines_generator(), self.config.api_key,
                                              base_uri=self.config.base_uri)
                elif self.log_type == 'http':
                    self.log_file = TFHttpLog(self.get_batched_lines_generator(), self.config.api_key,
                                              base_uri=self.config.base_uri)
                elif self.log_type == 'generic':

                    # Make sure the port is properly formatted
                    if self.ports is not None and re.search("^\d+:(tcp|udp|TCP|UDP)(\s\d+:(tcp|udp|TCP|UDP))*$",
                                                            " ".join(self.ports)):
                        self.log_file = TFGenericLog(self.get_batched_lines_generator(), self.config.api_key,
                                                     ports=self.ports, base_uri=self.config.base_uri)
                    else:
                        raise TFException('Generic mode requires a port and protocol be specified with the -p flag.')
                else:
                    raise TFException("Unhandled log type: %s" % self.log_type)

            # If the API is unavailable, we should fail somewhat gracefully
            except TFAPIUnavailable as e:
                default_logger.error(e)
                raise

            # Catch some general errors such as flag misconfiguration
            except TFException as e:
                default_logger.error(e)
                raise

            self.log_file.run()

            if not self.dry_run:
                self.output()

            if self.show_stats or self.dry_run:
                self.print_stats()

            try:
                if self.stats_reporter:
                    self.stats_reporter.report(self.log_file)
                    ga('event', 'CLI', 'execution', 'CLI Executed', self.config.api_key)
            except TFAPIUnavailable as e:
                stats_logger.error("Unable to report stats but continuing: %s" % e)
                pass

    def output(self):
        if self.output_file:
            with open(self.output_file, 'a+') as f:
                for line in self.log_file.reduce(self.show_noise):
                    f.write("%s\n" % line)
        else:
            for line in self.log_file.reduce(self.show_noise):
                sys.stdout.write("%s\n" % line)

    def print_stats(self):
        total_size = len(self.log_file.parsed_lines)
        noise_size = len(self.log_file.noisy_logs)
        quiet_size = len(self.log_file.quiet_logs)

        stats_logger.info('{TOTAL_SIZE} lines were analyzed in this batch.'
                          .format(TOTAL_SIZE=total_size))
        stats_logger.info('{NOISE_SIZE} lines were determined to be noise by ThreshingFloor.'
                          .format(NOISE_SIZE=noise_size))
        stats_logger.info('{QUIET_SIZE} lines were not determined to be noise by ThreshingFloor.'
                          .format(QUIET_SIZE=quiet_size))

        if total_size:
            percent = "{0:0.01f}".format((int(quiet_size) / float(total_size)) * 100)
            stats_logger.info("This batch was reduced to {PERCENT}% of its original size."
                              .format(PERCENT=percent))

    def _guess_type(self):
        """
        Guess the log type. First try by log file name if a filename was passed in,
        otherwise retrieve the first 10 log lines and pattern match to determine if
        http, auth, or other type of log.
        """

        def timeout_handler(signum, frame):
            raise TFException("Unable to automatically identify the log type because there are not enough lines "
                              "in the log stream. Please specify a type with the -t flag.")

        try:
            signal.signal(signal.SIGALRM, timeout_handler)

            if self.filename:
                base_name = ntpath.basename(self.filename)
                if base_name == 'auth.log':
                    default_logger.info('Processing as an auth log.')
                    self.log_type = 'auth'
                    return
                elif base_name == 'access.log':
                    default_logger.info('Processing as an http access log.')
                    self.log_type = 'http'
                    return

            signal.alarm(10)
            first_10_from_stream = itertools.islice(self.stream, 10)
            log_lines = "".join(["%s\n" % line for line in first_10_from_stream])
            signal.alarm(0)

            try:
                if self.is_http_log_line(log_lines):
                    self.log_type = 'http'
                elif self.is_auth_log_line(log_lines):
                    self.log_type = 'auth'
                else:
                    raise TFException("Unable to automatically identify the log type. "
                                      "Please specify a type with the -t flag.")
            except IOError as e:
                default_logger.error(e)
                raise
        except TFException as e:
            if self.ports is not None:
                self.log_type = 'generic'
            else:
                default_logger.error(e)
                raise

    @classmethod
    def is_http_log_line(cls, log_line):
        """
        Check if the line seems to be http
        """
        split_line = log_line.split()
        m = re.search(cls.http_regex, " ".join(split_line[3:]))
        if m:
            default_logger.info('Processing as an http access log.')
            return True
        return False

    @classmethod
    def is_auth_log_line(cls, log_line):
        split_line = log_line.split()
        try:
            # Try and make a timestamp from the beginning of the line
            if int(time.mktime(time.strptime(" ".join(split_line[0:3]) + " " + "2017", "%b %d %H:%M:%S %Y"))) > 0:
                default_logger.info('Processing as an auth log.')
                return True
        except Exception as e:
            return False
