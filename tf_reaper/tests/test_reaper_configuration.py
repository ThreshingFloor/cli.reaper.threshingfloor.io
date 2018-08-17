import json
import os

import mock
from libtf.logparsers.tf_exceptions import TFException

from .lib.tf_test_case import TFTestCase
from ..reaper_configuration import ReaperConfiguration


class TestReaperConfiguration(TFTestCase):

    def setUp(self):
        # ensure tests don't interfere with real config file
        if os.path.exists('/tmp/.tf.cfg'):
            os.remove('/tmp/.tf.cfg')

    def test_prompts_user_for_configuration_if_needed(self):
        with mock.patch('tf_reaper.reaper_configuration.ReaperConfiguration.config_file_path',
                        new_callable=mock.PropertyMock) as mock_config_file_path:
            mock_config_file_path.return_value = '/tmp/.tf.cfg'
            with mock.patch('six.moves.input', side_effect=['yes', 'jzs7VFwYhmvLcJiCfpfGOM0LjItDp6O1kUt76S5C',
                                                            'http://localhost:8000']) as mock_input:
                config = ReaperConfiguration.prompt_user()
                self.assertEqual(mock_input.call_count, 3)
                expected_config = {"BASE_URI": "http://localhost:8000",
                                   "REPORT_STATS": True,
                                   "API_KEY": "jzs7VFwYhmvLcJiCfpfGOM0LjItDp6O1kUt76S5C"}
                self.assertDictEqual(expected_config, json.loads(open('/tmp/.tf.cfg').read()))
                self.assertEqual(config.api_key, 'jzs7VFwYhmvLcJiCfpfGOM0LjItDp6O1kUt76S5C')
                self.assertEqual(config.base_uri, 'http://localhost:8000')
                self.assertEqual(config.report_stats, True)

    def test_user_can_overwrite_config_even_if_already_exists(self):
        config_dict = {"BASE_URI": "http://localhost:8000",
                       "REPORT_STATS": True,
                       "API_KEY": "jzs7VFwYhmvLcJiCfpfGOM0LjItDp6O1kUt76S5C"}
        with open('/tmp/.tf.cfg', 'w') as f:
            f.write(json.dumps(config_dict))

        with mock.patch('tf_reaper.reaper_configuration.ReaperConfiguration.config_file_path',
                        new_callable=mock.PropertyMock) as mock_config_file_path:
            mock_config_file_path.return_value = '/tmp/.tf.cfg'

            with mock.patch('six.moves.input', side_effect=['yes', 'new7VFwYhmvLcJiCfpfGOM0LjItDp6O1kUt76S5C',
                                                            'http://localhost:10000']) as mock_input:
                ReaperConfiguration.prompt_user()
                self.assertEqual(mock_input.call_count, 0)
                self.assertDictEqual(config_dict, json.loads(open('/tmp/.tf.cfg').read()))

                ReaperConfiguration.prompt_user(overwrite=True)
                self.assertEqual(mock_input.call_count, 3)
                self.assertDictEqual({"BASE_URI": "http://localhost:10000",
                                      "REPORT_STATS": True,
                                      "API_KEY": "new7VFwYhmvLcJiCfpfGOM0LjItDp6O1kUt76S5C"},
                                     json.loads(open('/tmp/.tf.cfg').read()))

    def test_answering_no_for_api_key_prompt_raises_tf_exception(self):
        with mock.patch('tf_reaper.reaper_configuration.ReaperConfiguration.config_file_path',
                        new_callable=mock.PropertyMock) as mock_config_file_path:
            mock_config_file_path.return_value = '/tmp/.tf.cfg'

            with mock.patch('six.moves.input', side_effect=['no']) as mock_input:
                expected_message = 'Please contact ThreshingFloor or your system administrator if hosted on-premise ' \
                                   'for the API KEY.'
                with self.assertRaisesRegexp(TFException, expected_message):
                    ReaperConfiguration.prompt_user()

    def test_inputing_invalid_api_key_question_repeats_prompt(self):
        with mock.patch('tf_reaper.reaper_configuration.ReaperConfiguration.config_file_path',
                        new_callable=mock.PropertyMock) as mock_config_file_path:
            mock_config_file_path.return_value = '/tmp/.tf.cfg'
            with mock.patch('six.moves.input', side_effect=['invalid', 'yes',
                                                            'jzs7VFwYhmvLcJiCfpfGOM0LjItDp6O1kUt76S5C',
                                                            'http://localhost:8000']) as mock_input:
                ReaperConfiguration.prompt_user()
                self.assertEqual(mock_input.call_count, 4)

    def test_inputing_non_40_character_api_key_repeats_prompt(self):
        with mock.patch('tf_reaper.reaper_configuration.ReaperConfiguration.config_file_path',
                        new_callable=mock.PropertyMock) as mock_config_file_path:
            mock_config_file_path.return_value = '/tmp/.tf.cfg'
            with mock.patch('six.moves.input', side_effect=['yes', 'too-short', 'too-long'*6,
                                                            'jzs7VFwYhmvLcJiCfpfGOM0LjItDp6O1kUt76S5C',
                                                            'http://localhost:8000']) as mock_input:
                ReaperConfiguration.prompt_user()
                self.assertEqual(mock_input.call_count, 5)

    def test_inputing_invalid_base_url_repeats_prompt(self):
        with mock.patch('tf_reaper.reaper_configuration.ReaperConfiguration.config_file_path',
                        new_callable=mock.PropertyMock) as mock_config_file_path:
            mock_config_file_path.return_value = '/tmp/.tf.cfg'
            with mock.patch('six.moves.input', side_effect=['yes', 'jzs7VFwYhmvLcJiCfpfGOM0LjItDp6O1kUt76S5C',
                                                            'invalid://localhost:8000', # must be http/https
                                                            'http://localhost:8000/',  # cannot end in /
                                                            'https://foo.bar.baz:8000']) as mock_input:
                ReaperConfiguration.prompt_user()
                self.assertEqual(mock_input.call_count, 5)

    def test_pressing_enter_for_base_uri_defaults_to_public_threshing_floor_api(self):
        with mock.patch('tf_reaper.reaper_configuration.ReaperConfiguration.config_file_path',
                        new_callable=mock.PropertyMock) as mock_config_file_path:
            mock_config_file_path.return_value = '/tmp/.tf.cfg'
            with mock.patch('six.moves.input', side_effect=['yes', 'jzs7VFwYhmvLcJiCfpfGOM0LjItDp6O1kUt76S5C',
                                                            '']) as mock_input:
                ReaperConfiguration.prompt_user()
                self.assertEqual(mock_input.call_count, 3)
                self.assertDictEqual({"BASE_URI": "https://api.threshingfloor.io",
                                      "REPORT_STATS": True,
                                      "API_KEY": "jzs7VFwYhmvLcJiCfpfGOM0LjItDp6O1kUt76S5C"},
                                     json.loads(open('/tmp/.tf.cfg').read()))
