import mock

from .lib.tf_test_case import TFTestCase
from ..prompt import prompt


class TestPrompt(TFTestCase):

    def test_can_prompt_user_for_response(self):
        def validate(user_input):
            if user_input not in ('yes', 'no'):
                return False
            return True

        with mock.patch('six.moves.input', side_effect=lambda _: 'yes'):
            validated_input = prompt("Continue? (yes/no): ", "yes or no", is_valid=validate)
            self.assertEqual('yes', validated_input)

    def test_invalid_response_repeats_prompt(self):
        def validate(user_input):
            if user_input not in ('yes', 'no'):
                return False
            return True

        with mock.patch('six.moves.input', side_effect=['invalid', 'yes']) as mock_input:
            validated_input = prompt("Continue? (yes/no): ", "yes or no", is_valid=validate)
            self.assertEqual(mock_input.call_count, 2)  # prompted twice
            self.assertEqual('yes', validated_input)

    def test_user_can_press_enter_for_default_if_defined(self):
        def validate(user_input):
            if user_input not in ('yes', 'no'):
                return False
            return True

        with mock.patch('six.moves.input', side_effect=lambda _: '') as mock_input:
            validated_input = prompt("Continue? (yes/no): ", "yes or no", is_valid=validate, default='no')
            self.assertEqual(mock_input.call_count, 1)
            self.assertEqual('no', validated_input)
