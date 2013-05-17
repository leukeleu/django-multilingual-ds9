## Django Multilingual Deep Space 9 ##

Django-multilingual-DS9 is a branch of django-multilingual, forked from django-multilingual-ng, with restructured core.

Compatibility:
* Django 1.3
* Django 1.4

Django-multilingual-ds9 does not have to be fully compatible with django-multilingual-ng, but basic features should not
differ.

### Features ###
* Use only language codes from `LANGUAGES` setting.
* Model structure
  * `FIELD_NAME` returns translation of field for current language or `None` if no translation exists.
  * `FIELD_NAME_any` returns translation of field for current language or fallback language or default language or
    `None` if neither translation exists. Fallback language codes are only those with two letters and are used
    only if available in `LANGUAGES` setting.
  * `FIELD_NAME_language` returns translation of field for the language or `None` if translation does not exist.
  * `RELATED_NAME` (default: translations) returns manager for translation model with filter to master object.
* Queries
  * `get/filter/exclude(FIELD_NAME)` creates LEFT OUTER JOIN to translation table with condition for current language
    and required filter.
    Take care if you are using `FIELD_NAME__isnull=True` lookup, because this query returns both
    objects with missing translations and objects with missing field in translation.
  * `get/filter/exclude(FIELD_NAME_lanaguge)` creates LEFT OUTER JOIN to translation table with condition for the
    language and required filter.
  * `order_by/values/values_list(FIELD_NAME)` works same as filter-like queries.
    Remember that these will keep objects with no translation in result set unless you manually remove them.
  * `order_by/values/values_list(FIELD_NAME_language)` same as above.
  * `select_related(RELATED_NAME)` works as expected, tries to cache translation in other query.
  * `get/filter/exclude(RELATED_NAME)` selection by existence and parameters of whole translation object.
* Administration
  * `search_fields` does not handle `FIELD_NAME_LANGCODE`, you need to use regular foreign key lookup
    `RELATED_NAME__FIELD_NAME`

### Known bugs ###
* Django admin validation is rigid and does not handle customized models, especially virtual fields which are used here.
Thus it the supported solution is to write your own form for ModelAdmins if you want to do some changes and not to use
ModelAdmin attributes for form customizing.


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
To test multilingual just run

    python manage.py test multilingual
