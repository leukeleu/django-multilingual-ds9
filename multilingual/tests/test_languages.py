# -*- coding: utf-8 -*-
"""
Test language setters, getters and fallbacks
"""
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import unittest
from django.utils.datastructures import SortedDict
from django.utils.translation import activate, deactivate_all

from multilingual import languages


@override_settings(LANGUAGE_CODE='cs',
                   LANGUAGES = (('cs', u'Čeština'), ('en', u'English'), ('en-us', u'American english')))
class TestLanguages(TestCase):

    def setUp(self):
        activate('cs')

    def tearDown(self):
        # Reset old language
        deactivate_all()
        languages.release()

    def test_basics(self):
        self.assertEqual(languages.get_dict(),
                         SortedDict((('cs', u'Čeština'), ('en', u'English'), ('en-us', u'American english'))))
        self.assertEqual(languages.get_all(), ['cs', 'en', 'en-us'])
        self.assertEqual(languages.get_settings_default(), 'cs')
        self.assertEqual(languages.get_active(), 'cs')

    def test_fallbacks(self):
        self.assertEqual(languages.get_fallbacks('cs'), [])
        self.assertEqual(languages.get_fallbacks('en'), ['cs'])
        self.assertEqual(languages.get_fallbacks('en-us'), ['en', 'cs'])

    def test_language_change(self):
        activate('en')
        self.assertEqual(languages.get_active(), 'en')

    def test_incorrect_language(self):
        activate('INCORRECT_LANGUAGE')
        self.assertEqual(languages.get_active(), 'cs')

    def test_lock(self):
        languages.lock('en')
        self.assertEqual(languages.is_locked(), True)
        self.assertEqual(languages.get_active(), 'en')
        languages.release()
        self.assertEqual(languages.is_locked(), False)
        self.assertEqual(languages.get_active(), 'cs')

    #TODO: check thread safety


def suite():
    test = unittest.TestSuite()
    test.addTest(unittest.makeSuite(TestLanguages))
    return test
