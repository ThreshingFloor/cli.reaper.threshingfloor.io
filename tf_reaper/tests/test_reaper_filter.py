import json
from tempfile import mkstemp

import mock
import requests
from libtf.logparsers.tf_exceptions import TFException

from tf_reaper.loggers import stats_logger
from tf_reaper.reaper_configuration import ReaperConfiguration
from tf_reaper.reaper_filter import ReaperFilter
from .lib.tf_test_case import TFTestCase


class TestReaperFilter(TFTestCase):

    def setUp(self):
        self.stream = ['1.1.1.1', '2.2.2.2']
        self.config = ReaperConfiguration(api_key='a'*40, base_uri='http://127.0.0.1:10000', report_stats=True)

    def test_batch_size_defaults_if_not_specified(self):
        reaper = ReaperFilter(self.config, self.stream, log_type='generic', ports=["22:tcp"])
        self.assertEqual(reaper.batch_size, ReaperFilter.default_batch_size)

        reaper = ReaperFilter(self.config, self.stream, batch_size=1, log_type='generic', ports=["22:tcp"])
        self.assertEqual(reaper.batch_size, 1)

    def test_can_guess_auth_log_if_type_not_specified_and_filename_matches_auth_log(self):
        reaper = ReaperFilter(self.config, self.stream, filename='auth.log')
        self.assertEqual(reaper.log_type, 'auth')

    def test_can_guess_http_log_if_type_not_specified_and_filename_matches_access_log(self):
        reaper = ReaperFilter(self.config, self.stream, filename='access.log')
        self.assertEqual(reaper.log_type, 'http')

    def test_can_guess_auth_log_if_type_not_specified_and_first_10_lines_in_10_seconds_matches_regex(self):
        self.stream = ['Feb 20 21:54:44 localhost sshd[3402]: Accepted publickey for john from 199.2.2.2 port 63673 '
                       'ssh2: RSA 39:33:99:e9:a0:dc:f2:33:a3:e5:72:3b:7c:3a:56:84']
        reaper = ReaperFilter(self.config, self.stream)
        self.assertEqual(reaper.log_type, 'auth')

    def test_can_guess_http_log_if_type_not_specified_and_first_10_lines_in_10_seconds_matches_regex(self):
        self.stream = ['192.168.1.20 - - [28/Jul/2006:10:27:10 -0300] "GET /cgi-bin/try/ HTTP/1.0" 200 3395']
        reaper = ReaperFilter(self.config, self.stream)
        self.assertEqual(reaper.log_type, 'http')

    def test_if_no_matches_in_first_10_lines_then_cannot_guess(self):
        self.stream = ['foo' for _ in range(0, 10)]
        self.stream.append('192.168.1.20 - - [28/Jul/2006:10:27:10 -0300] "GET /cgi-bin/try/ HTTP/1.0" 200 3395')
        with self.assertRaisesRegexp(TFException, "Unable to automatically identify the log type. "
                                                  "Please specify a type with the -t flag."):
            ReaperFilter(self.config, self.stream)

    # def test_if_no_10_seconds_then_cannot_guess(self):
    #     self.stream = sys.stdin
    #     start = datetime.now()
    #     with self.assertRaisesRegexp(TFException, "Unable to automatically identify the log type because there are "
    #                                               "not enough lines in the log stream. Please specify a type with the "
    #                                               "-t flag."):
    #         ReaperFilter(self.config, self.stream)
    #         self.assertGreaterEqual(datetime.now() - start, timedelta(seconds=10))

    def test_reaper_analyzes_in_batches_to_limit_memory_footprint(self):
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({"ips": [], "ports": []})

        with mock.patch.object(requests, 'post', autospec=True) as mock_post:
            reaper = ReaperFilter(self.config, self.stream, log_type='generic', ports=["22:tcp"])
            mock_post.return_value = mock_response

            original_get_batched_lines_generator = reaper.get_batched_lines_generator

            with mock.patch.object(reaper, 'get_batched_lines_generator', autospec=True,
                                   side_effect=original_get_batched_lines_generator) as mock_get_batched_lines_generator:
                reaper.run()
                self.assertEqual(mock_get_batched_lines_generator.call_count, 1)

        # Setting batch_size to 1 should call generator multiple times
        with mock.patch.object(requests, 'post', autospec=True) as mock_post:
            reaper = ReaperFilter(self.config, self.stream, log_type='generic', ports=["22:tcp"], batch_size=1)
            mock_post.return_value = mock_response

            original_get_batched_lines_generator = reaper.get_batched_lines_generator

            with mock.patch.object(reaper, 'get_batched_lines_generator', autospec=True,
                                   side_effect=original_get_batched_lines_generator) as mock_get_batched_lines_generator:
                reaper.run()
                self.assertEqual(mock_get_batched_lines_generator.call_count, 3)

    def test_generic_type_requires_ports_if_not_guessable(self):
        self.stream = ['192.168.1.20']
        reaper = ReaperFilter(self.config, self.stream, log_type='generic')

        with mock.patch.object(requests, 'post', autospec=True):
            with self.assertRaisesRegexp(TFException, "Generic mode requires a port and protocol be specified with the "
                                                      "-p flag."):
                reaper.run()

    def test_can_output_to_file(self):
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({"ips": ["192.168.1.254"], "ports": []})

        self.stream = ['192.168.1.20 foo bar baz',
                       '192.168.1.254 foo bar baz',
                       '192.168.1.100 foo bar baz']
        fh, filename = mkstemp(text=True)
        reaper = ReaperFilter(self.config, self.stream, log_type='generic', ports=["22:tcp"], output_file=filename)

        with mock.patch.object(requests, 'post', autospec=True) as mock_post:
            mock_post.return_value = mock_response
            reaper.run()

        self.assertEqual(open(filename).read(), "192.168.1.20 foo bar baz\n192.168.1.100 foo bar baz\n")

    def test_can_output_noise_if_desired(self):
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({"ips": ["192.168.1.254"], "ports": []})

        self.stream = ['192.168.1.20 foo bar baz',
                       '192.168.1.254 foo bar baz',
                       '192.168.1.100 foo bar baz']
        fh, filename = mkstemp(text=True)
        reaper = ReaperFilter(self.config, self.stream, log_type='generic', ports=["22:tcp"], output_file=filename,
                              show_noise=True)

        with mock.patch.object(requests, 'post', autospec=True) as mock_post:
            mock_post.return_value = mock_response
            reaper.run()

        # Outputs noise only
        self.assertEqual(open(filename).read(), "192.168.1.254 foo bar baz\n")

    def test_can_do_dry_run_and_print_stats(self):
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({"ips": ["192.168.1.254"], "ports": []})

        self.stream = ['192.168.1.20 foo bar baz',
                       '192.168.1.254 foo bar baz',
                       '192.168.1.100 foo bar baz']
        fh, filename = mkstemp(text=True)
        reaper = ReaperFilter(self.config, self.stream, log_type='generic', ports=["22:tcp"], output_file=filename,
                              dry_run=True)

        with mock.patch.object(requests, 'post', autospec=True) as mock_post:
            mock_post.return_value = mock_response

            with mock.patch.object(stats_logger, 'info') as mock_stats_logger:
                reaper.run()
                self.assertEqual(mock_stats_logger.call_args_list,
                                 [mock.call('3 lines were analyzed in this log file.'),
                                  mock.call('1 lines were determined to be noise by ThreshingFloor.'),
                                  mock.call('2 lines were not determined to be noise by ThreshingFloor.'),
                                  mock.call('The input file was reduced to 66.7% of its original size.')])

        # Should be no output since dry run
        self.assertEqual(open(filename).read(), "")
