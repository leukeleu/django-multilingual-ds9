# -*- coding: utf-8 -*-
"""
This tests multilingual forms
"""
from django import forms
from django.utils import unittest

from multilingual.forms.forms import MultilingualModelForm

from .base import MultilingualTestCase
from .ml_test_app.models import Multiling


class MinimalMultilingForm(MultilingualModelForm):
    class Meta:
        model = Multiling


class FieldsMultilingForm(MultilingualModelForm):
    class Meta:
        model = Multiling
        fields = ('name', 'title')


class ExcludeMultilingForm(MultilingualModelForm):
    class Meta:
        model = Multiling
        exclude = ('title', )


class CustomMultilingForm(MultilingualModelForm):
    custom = forms.IntegerField()

    class Meta:
        model = Multiling


class TestModelForm(MultilingualTestCase):
    def test_form_fields(self):
        self.assertEqual(MinimalMultilingForm.base_fields.keys(), ['name', 'title'])
        self.assertEqual(FieldsMultilingForm.base_fields.keys(), ['name', 'title'])
        self.assertEqual(ExcludeMultilingForm.base_fields.keys(), ['name'])
        self.assertEqual(CustomMultilingForm.base_fields.keys(), ['name', 'custom', 'title'])

    def test_form_unbound(self):
        form = MinimalMultilingForm()
        self.assertFalse(form.is_bound)
        self.assertEqual(form.initial, {})

        obj = Multiling.objects.get(name='first')
        form = MinimalMultilingForm(instance=obj)
        self.assertFalse(form.is_bound)
        self.assertEqual(form.initial, {'id': 1, 'name': 'first', 'title': u'obsah ěščřžýáíé'})

        obj = Multiling.objects.get(name='untranslated')
        form = MinimalMultilingForm(instance=obj)
        self.assertFalse(form.is_bound)
        self.assertEqual(form.initial, {'id': 4, 'name': 'untranslated', 'title': ''})

    def test_form_bound(self):
        data = {'name': 'new', 'title': 'Titulek'}
        form = MinimalMultilingForm(data)
        self.assertTrue(form.is_bound)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.instance.name, 'new')
        self.assertEqual(form.instance.title, 'Titulek')

        data = {'name': 'new'}
        form = ExcludeMultilingForm(data)
        self.assertTrue(form.is_bound)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.instance.name, 'new')


def suite():
    test = unittest.TestSuite()
    test.addTest(unittest.makeSuite(TestModelForm))
    return test
