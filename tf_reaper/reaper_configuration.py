import json
import os
import re
import sys

from libtf.logparsers.tf_exceptions import TFException

from .google_analytics import ga
from .prompt import prompt


class ReaperConfiguration(object):
    config_file_path = os.path.expanduser('~/.tf.cfg')
    default_base_uri = 'https://api.threshingfloor.io'

    def __init__(self, api_key=None, base_uri=None, report_stats=None):
        config_arg_check = [api_key, base_uri, report_stats is not None]

        if any(config_arg_check) and not all(config_arg_check):
            raise TFException("All configuration must be set, none at all to use file configuration.")

        if all(config_arg_check):
            self.api_key = api_key
            self.base_uri = base_uri
            self.report_stats = report_stats
        else:
            config = json.loads(open(self.config_file_path).read())
            self.api_key = config['API_KEY']
            self.base_uri = config['BASE_URI']
            self.report_stats = config['REPORT_STATS']

    @classmethod
    def configuration_file_exists(cls):
        return os.path.exists(cls.config_file_path)

    @classmethod
    def prompt_user(cls, overwrite=False):
        """
        Prompt user if config is needed or if wanting to overwrite

        overwrite: Whether to prompt user even if a configuration file already exists
        """
        if not cls.configuration_file_exists() or overwrite:
            new_config = {}

            try:
                has_account = prompt("Do you already have a registered API key? [y/N]",
                                     "Please respond (y)es or (n)o.",
                                     lambda v: re.search(r"(^(y|yes)|(n|no))$", v, re.IGNORECASE))
            except EOFError as e:
                raise TFException('Please run ./reaper --configure')

            if has_account[:1].lower() == 'y':
                new_config['API_KEY'] = prompt("Please enter your API key",
                                               "Please enter a valid API key that is 40 characters.",
                                               is_valid=lambda v: re.search(r"^\w{40}", v))

                new_config['BASE_URI'] = prompt("Please enter the base API URI",
                                                "Please enter a valid URI beginning with 'http://' or 'https://' "
                                                "with no trailing slash.",
                                                is_valid=lambda v: re.search(r"^https?://.*[^/]$", v),
                                                default=cls.default_base_uri)
            else:
                raise TFException('Please contact ThreshingFloor or your system administrator if hosted on-premise '
                                  'for the API KEY.')

            # Always report stats
            new_config['REPORT_STATS'] = True

            try:
                with open(cls.config_file_path, 'w') as f:
                    sys.stdout.write("Storing ThreshingFloor API key in ~/.tf.cfg\n")
                    f.write(json.dumps(new_config))
            except Exception as e:
                sys.stderr.write("Unable to write configuration file: \n%s\n" % e)
                raise

            ga('event', 'CLI', 'configured', 'CLI Configured', new_config['API_KEY'])

        return ReaperConfiguration()
