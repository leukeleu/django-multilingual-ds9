## Django Multilingual Deep Space 9 ##

Django-multilingual-DS9 is a branch of django-multilingual,
forked from django-multilingual-ng compatible with
Django 1.2 and 1.3 with restructured core.

Django-multilingual-ds9 does not have to be fully compatible with django-multilingual-ng,
but basic should not differ.

**Some of this is now only a goal and does not have to work**

### Changes from django-multilingual-ng ###
* Always use only languages from `LANGUAGES` setting
* Database differs in changes of suffix from `_translation` to `translation`.
    Update your tables, indexes and sequences or alter db_table in multilingual model Meta options
* Model structure
  * `FIELD_NAME` access is mostly kept. It will return translation of field for current language or `None`
  * `FIELD_NAME_any` access differs in fallback. It will return translation of field for current language or
    fallback language or default language or `None`. Fallback language code are only two lettered and are used
    only if available in `LANGUAGES`.
  * `RELATED_NAME` returns manager for translation model with filter to master object.
* Queries
  Queries behaves as expected, lower is more a description of background
  * `get/filter/exclude(FIELD_NAME)` creates LEFT OUTER JOIN to translation table with condition for language
    and required filter.
    Take care if you are using `FIELD_NAME__isnull=True` lookup, because this query returns both
    objects with missing translations and objects with missing field in translation.
  * `order_by/values/values_list(FIELD_NAME)` works same as filter-like queries.
    Remember that these will keep objects with no translation in result set unless you manually remove them.
  * `select_related(RELATED_NAME)` does what expected, tries to cache translation in other query
  * `get/filter/exclude(RELATED_NAME)` selection by existence and parameters of whole translation object
* Administration
  * `search_fields` does not handle `FIELD_NAME_LANGCODE`, you need to use regular foreign key lookup `RELATED_NAME__FIELD_NAME`

### Old features ###
I have not yet decided what to do with following features:
* Model structure
  * `FIELD_NAME_language` access is mostly kept. It will return translation of field for current language or `None`
* Queries
  Queries behaves as expected, lower is more a description of background
  * `get/filter/exclude(FIELD_NAME_lanaguge)` creates LEFT OUTER JOIN to translation table with condition for language
    and required filter.
  * `order_by/values/values_list(FIELD_NAME_language)` works same as filter-like queries.

### Examples ###
You may see tests for more specific usage

    from django import models
    from multilingual import MultilingualModel

    class Example(MultilingualModel):
        some_field = models.IntegerField()

        class Translation:
            trans_field = models.CharField(max_length=20)

    e = Example.objects.create()
    # get translation for current language
    e.trans_field
    # get translation with fallback
    e.trans_field_any

    # returns all translation objects
    e.translations.all()

    # Filter objects by translation field
    qs = Example.objects.filter(trans_field='some')
    #!! This will return objects with no translation and objects with missing trans_field translation
    qs = Example.objects.filter(trans_field__isnull=True)
    #!! This also may contain several None objects if translations are missing
    qs = Example.objects.values_list('trans_field', flat=True)

    # Get object with translation in one query
    Example.objects.select_related('translations').get(pk=1)
    # Get objects with missing translation
    Example.objects.filter(translation__isnull=True)

    # Change current language
    from django.utils.translation import activate
    activate('cs')

    # Force usage of specific language in multilingual code
    from multilingual import language
    language.lock('cs')
    language.release()

### Tests ###
To run tests for multilingual just set

    TEST_RUNNER = 'multilingual.tests.MultilingualTestSuiteRunner'

in your settings. And run in your project

    python manage.py test multilingual
