# -*- coding: utf-8 -*-
import os
import sys

from django.conf import settings
from django.core.management import call_command
from django.db.models.loading import cache, load_app
from django.test import TransactionTestCase
from django.test.utils import override_settings

from .ml_test_app.models import Multiling


#TODO: Make these test faster, flush database before each test is time consuming.
@override_settings(LANGUAGE_CODE='cs',
                   LANGUAGES=(('en', u'English'), ('cs', u'Česky')))
class MultilingualTestCase(TransactionTestCase):
    """
    Adds `ml_test_app` into installed applications. Defines language settings.
    """
    fixtures = ('ml_test_models.json', )

    @classmethod
    def setUpClass(cls):
        # Modify sys path
        cls.old_sys_path = sys.path[:]
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))

        # Install test app, we need to use it for syncdb, so we can not use `override_settings`
        cls.old_installed_apps = settings.INSTALLED_APPS
        settings.INSTALLED_APPS = list(settings.INSTALLED_APPS) + ['ml_test_app']
        # Install `ml_test_app`
        map(load_app, settings.INSTALLED_APPS)
        cache.register_models('ml_test_app', Multiling, Multiling._meta.translation_model)
        call_command('syncdb', verbosity=0)

    @classmethod
    def tearDownClass(cls):
        # Restore sys path
        sys.path = cls.old_sys_path

        # Restore settings
        settings.INSTALLED_APPS = cls.old_installed_apps

        # Reload app cache
        cache._get_models_cache.clear()
        cache.handled.clear()
        cache.loaded = False
        cache._populate()
