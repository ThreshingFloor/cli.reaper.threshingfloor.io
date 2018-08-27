import requests
from libtf.logparsers.tf_exceptions import TFAPIUnavailable

from .google_analytics import ga


class ReaperStatisticsReporter(object):
    api_endpoint = "/v2/reducer/stats"

    def __init__(self, config):
        self.config = config

    def report(self, log_file):
        post_data = dict()

        # Total number of lines processed
        post_data['lines_analyzed'] = len(log_file.parsed_lines)

        # Number of lines eliminated
        post_data['lines_removed'] = len(log_file.noisy_logs)

        # Number of lines unhandled
        post_data['lines_unhandled'] = len(log_file.unhandled_logs)

        # Get up to 10 unhandled logs and report them
        post_data['unhandled_items'] = log_file.unhandled_logs[:min(10, post_data['lines_unhandled'])]

        # Send the API key
        post_data['API_KEY'] = self.config.api_key

        try:
            response = requests.post(self.config.base_uri + self.api_endpoint, json=post_data,
                                     headers={'x-api-key': self.config.api_key})
        except requests.exceptions.ConnectionError as e:
            raise TFAPIUnavailable("The ThreshingFloor API appears to be unavailable.")

        ga('event', 'CLI', 'statistics', 'CLI Stats', self.config.api_key, extras=post_data)

        if response.status_code != 200:
            raise TFAPIUnavailable("Request failed and returned a status of: %s" % response.status_code)
