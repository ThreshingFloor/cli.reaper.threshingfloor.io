import mock
import requests
from libtf.logparsers.tf_exceptions import TFAPIUnavailable

from .lib.tf_test_case import TFTestCase
from ..reaper_configuration import ReaperConfiguration
from ..reaper_statistics_reporter import ReaperStatisticsReporter


class TestReaperStatisticsReporter(TFTestCase):

    def setUp(self):
        self.log_file = mock.MagicMock()
        self.log_file.parsed_lines = [
            'Aug 18 23:08:26 foo sshd[5768]: Failed password for root from 1.1.1.1 port 12345 ssh2',
            'Aug 18 23:08:27 foo sshd[5768]: Failed password for root from 2.2.2.2 port 23456 ssh2',
            'Aug 18 23:08:28 foo sshd[5768]: Failed password for root from 3.3.3.3 port 45678 ssh2',
            'Aug 18 23:08:29  sshd[24648]: last message repeated 5 times'
        ]
        self.log_file.noisy_logs = [
            'Aug 18 23:08:26 foo sshd[5768]: Failed password for root from 2.2.2.2 port 23456 ssh2'
        ]
        self.log_file.unhandled_logs = [
            'Aug 18 23:08:29  sshd[24648]: last message repeated 5 times'
        ]

        config = ReaperConfiguration(api_key='1' * 40, base_uri='http://localhost:8000', report_stats=False)

        self.stats_reporter = ReaperStatisticsReporter(config=config)

    def test_can_report_statistics(self):
        mock_response = mock.MagicMock()
        mock_response.status_code = 200

        with mock.patch.object(requests, 'post', autospec=True) as mock_post:
            mock_post.return_value = mock_response
            self.stats_reporter.report(self.log_file)
            self.assertTrue(mock_post.called)
            expected_call = mock.call('http://localhost:8000/reducer/stats',
                                      headers={'x-api-key': '1111111111111111111111111111111111111111'},
                                      json={'lines_analyzed': 4,
                                            'API_KEY': '1111111111111111111111111111111111111111',
                                            'lines_removed': 1,
                                            'lines_unhandled': 1,
                                            'unhandled_items': ['Aug 18 23:08:29  sshd[24648]: '
                                                                'last message repeated 5 times']})
            self.assertEqual(mock_post.call_args_list[0], expected_call)

    def test_api_non_200_response_raises_tf_api_exception(self):
        mock_response = mock.MagicMock()
        mock_response.status_code = 500

        with mock.patch.object(requests, 'post', autospec=True) as mock_post:
            mock_post.return_value = mock_response
            with self.assertRaisesRegexp(TFAPIUnavailable, "Request failed and returned a status of: 500"):
                self.stats_reporter.report(self.log_file)
