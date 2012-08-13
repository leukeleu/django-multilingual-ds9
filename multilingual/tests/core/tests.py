# -*- coding: utf-8 -*-
"""
This tests standard behaviour of multilingual models
"""
import unittest

from multilingual.languages import lock, release

from models import Basic, Managing


class ModelTest(unittest.TestCase):
    def tearDown(self):
        # Remove language locks if any remains
        # TODO: rollback after each test, to get database to the same initial state
        release()

    # Model tests
    def test01_fixtures(self):
        # Just test whether fixtures were loaded properly
        obj = Basic.objects.get(pk=1)
        self.assertEqual(obj.description, u'regular ěščřžýáíé')

    def test02_proxy_fields(self):
        # Test proxy fields reading
        obj = Basic.objects.get(pk=1)
        self.assertEqual(obj.title, u'obsah ěščřžýáíé')
        self.assertEqual(obj.title_cs, u'obsah ěščřžýáíé')
        self.assertEqual(obj.title_en, u'content')

    def test03_proxy_fields_fallbacks(self):
        # Test proxy fields reading
        obj = Basic.objects.get(pk=2)
        self.assertEqual(obj.title, u'pouze čeština')
        self.assertEqual(obj.title_cs, u'pouze čeština')
        self.assertEqual(obj.title_en, None)
        lock('en')
        self.assertEqual(obj.title, u'pouze čeština')
        release()

        obj = Basic.objects.get(pk=3)
        # Do not forget we have activated czech language
        self.assertEqual(obj.title, None)
        self.assertEqual(obj.title_cs, None)
        self.assertEqual(obj.title_en, u'only english')

        obj = Basic.objects.get(pk=4)
        self.assertEqual(obj.title, None)
        self.assertEqual(obj.title_cs, None)
        self.assertEqual(obj.title_en, None)

    # Manager tests
    def test10_manager_filter(self):
        queryset = Managing.objects.filter(name_cs=u'č')
        self.assertEqual(len(queryset), 1)
        self.assertEqual(queryset[0].shortcut, u'c2')

    def test11_manager_exclude(self):
        queryset = Managing.objects.exclude(name_en__isnull=True)
        result = set(obj.shortcut for obj in queryset)
        self.assertEqual(len(queryset), 11)
        self.assertEqual(len(result), 11)
        self.assertEqual(result, set([u'a', u'b', u'c', u'd', u'e', u'h', u'i', u'w', u'x', u'y', u'z']))

    def test12_manager_create(self):
        obj = Managing.objects.create(shortcut=u'n2', name_cs=u'ň')
        self.assertEqual(obj.shortcut, u'n2')
        self.assertEqual(obj.name, u'ň')

    def test13_manager_get_or_create(self):
        obj, created = Managing.objects.get_or_create(shortcut=u'n2', name_cs=u'ň')
        self.assertEqual(created, False)
        self.assertEqual(obj.shortcut, u'n2')
        self.assertEqual(obj.name, u'ň')

    def test14_manager_delete(self):
        ManagingTranslation = Managing._meta.translation_model
        obj = ManagingTranslation.objects.get(name=u'ň')
        self.assertEqual(obj.master.shortcut, u'n2')
        Managing.objects.filter(shortcut=u'n2').delete()
        self.assertRaises(ManagingTranslation.DoesNotExist, ManagingTranslation.objects.get, name=u'ň')

    def test15_manager_order_by(self):
        # If you do not know it, ordering is dependent on locales.
        # So if you apply ordering rules on set of words from different language it will be
        # ordered differently than it should. That also may cause problems if application is run
        # with different locales than database.
        proper_result = [u'a', u'b', u'c', u'č', u'd', u'ď', u'e', u'é', u'ě', u'h', u'ch', u'i', u'ř', u'ž']
        # Re-sort to avoid false failure if your database does not run with czech locales
        proper_result.sort()
        queryset = Managing.objects.filter(name_cs__isnull=False).order_by('name_cs')
        result = list(obj.name_cs for obj in queryset)
        self.assertEqual(result, proper_result)

    def test16_manager_select_related(self):
        obj = Managing.objects.select_related('translations').get(pk=1)
        #TODO: we should check instead that translation cache is created without subsequent SQL request
        self.assertEqual(obj._trans_name_cs, u'a')

    def test17_manager_values(self):
        names = [u'e', u'é', u'ě']
        values = Managing.objects.filter(shortcut__startswith=u'e').values('name')
        for item in values:
            names.pop(names.index(item['name']))
        self.assertEqual(names, [])

    def test18_manager_values_list(self):
        names = set([u'e', u'é', u'ě'])
        values = Managing.objects.filter(shortcut__startswith=u'e').values_list('name', flat=True)
        self.assertEqual(set(values), names)

    #TODO: test other manager methods
