# -*- coding: utf-8 -*-
"""
Tests of multilingual app based on django gis app tests
"""
import unittest

from django.conf import settings
from django.test.simple import build_suite, DjangoTestSuiteRunner
from django.utils.translation import gettext, activate, get_language


def multilingual_apps(namespace=True, runtests=False):
    """
    Returns a list of GeoDjango test applications that reside in
    `django.contrib.gis.tests` that can be used with the current
    database and the spatial libraries that are installed.
    """
    apps = ['core', 'admin']

    if runtests:
        return [('multilingual.tests', app) for app in apps]
    elif namespace:
        return ['multilingual.tests.%s' % app for app in apps]
    else:
        return apps


def multilingual_suite(apps=True):
    """
    Returns a TestSuite consisting only of Multilingual tests that can be run.
    """
    from django.db.models import get_app

    suite = unittest.TestSuite()

    # Add tests outside of test apps
    from multilingual.tests import test_languages, test_models
    suite.addTest(test_languages.suite())
    suite.addTest(test_models.suite())

    # Finally, adding the suites for each of the GeoDjango test apps.
    if apps:
        for app_name in multilingual_apps(namespace=False):
            suite.addTest(build_suite(get_app(app_name)))

    return suite


class MultilingualTestSuiteRunner(DjangoTestSuiteRunner):
    def setup_test_environment(self, **kwargs):
        super(MultilingualTestSuiteRunner, self).setup_test_environment(**kwargs)

        # Save original values of several settings
        self.old_installed = getattr(settings, 'INSTALLED_APPS', None)
        self.old_languages = getattr(settings, 'LANGUAGES')
        self.old_language_code = getattr(settings, 'LANGUAGE_CODE')

        # Update settings to what is needed
        settings.INSTALLED_APPS = multilingual_apps()
        settings.LANGUAGES = (
            ('cs', gettext('Čeština')),
            ('en', gettext('English')),
        )
        settings.LANGUAGE_CODE = 'cs'

    def run_suite(self, *args, **kwargs):
        old_language_active = get_language()
        activate('cs')
        result = super(MultilingualTestSuiteRunner, self).run_suite(*args, **kwargs)
        activate(old_language_active)
        return result

    def teardown_test_environment(self, **kwargs):
        # Replace settings back to original first as opposite of setup
        settings.INSTALLED_APPS = self.old_installed
        settings.LANGUAGES = self.old_languages
        settings.LANGUAGE_CODE = self.old_language_code

        super(MultilingualTestSuiteRunner, self).teardown_test_environment(**kwargs)

    def build_suite(self, test_labels, extra_tests=None, **kwargs):
        return multilingual_suite()
