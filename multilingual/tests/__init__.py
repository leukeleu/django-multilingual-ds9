# -*- coding: utf-8 -*-
"""
Tests of multilingual application.
"""
from django.utils import unittest


def suite():
    from multilingual.tests import test_admin, test_forms, test_languages, test_models

    test = unittest.TestSuite()
    test.addTest(test_admin.suite())
    test.addTest(test_forms.suite())
    test.addTest(test_languages.suite())
    test.addTest(test_models.suite())

    return test
