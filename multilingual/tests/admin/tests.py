# -*- coding: utf-8 -*-
"""
This tests standard behaviour of multilingual models
"""
import unittest

from django.contrib.admin.views.main import ChangeList
from django.test.client import RequestFactory

from multilingual.admin.options import MultilingualModelAdmin

from models import AdminTests


REQ_FACTORY = RequestFactory()


class ModelAdminTest(unittest.TestCase):
    """
    Tests of model admin interface
    """
    def test01_fixtures(self):
        """
        Check whether fixtures were loaded properly
        """
        obj = AdminTests.objects.get(pk=1)
        self.assertEqual(obj.description, u'description ěščřžýáíé')

    def test02_search(self):
        """
        Test full text searching in administration
        """
        request = REQ_FACTORY.get('/admin/admintests/', {'q': 'obsah'})
        # Second argument is admin_site, but it is not used in this test
        model_admin = MultilingualModelAdmin(AdminTests, None)
        cl = ChangeList(request, AdminTests, ('__str__', ), (), (), None, ('translations__title', ), False, 100, (),
                        model_admin)
        self.assertEqual(len(cl.get_query_set()), 1)
        self.assertEqual(cl.get_query_set()[0].description, u'description ěščřžýáíé')