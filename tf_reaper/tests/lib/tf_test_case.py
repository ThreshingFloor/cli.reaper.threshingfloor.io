from unittest import TestCase

from ... import google_analytics


class TFTestCase(TestCase):
    def run(self, result=None):
        google_analytics.enabled = False
        super(TFTestCase, self).run(result)
