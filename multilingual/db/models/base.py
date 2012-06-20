"""
SomeMultilingualModel(MultilingualModel(Model))
  __metaclass__ = MultilingualModelBase(ModelBase)
    _prepare() - creates SomeTranslationModel

  base_field = models.Field()

  class Meta:
      pass

  class Translation:
      translated_field = models.Field()

  _meta = MultilingualOptions(Options)
    translation_model = SomeTranslationModel

  objects = MultilingualManager(Manager)
  save() - saves translations
  get_translation() - return translation for given language
  translated_field_{lang} - proxy property to get_translation
  translations - many to one descriptor

SomeTranslationModel(TranslationModel(Model))
  __metaclass__ = TranslationModelBase(ModelBase)
  language_code = models.CharField
  master = models.ForeignKey(SomeMultilingualModel, related_name = 'translations')
  translated_field = models.Field()

  class Meta:
    pass

  _meta = TranslationOptions(Options)
"""
from new import classobj

from django.db import models
from django.db.models.base import ModelBase

from multilingual.db.models.fields import TranslationProxyField
from multilingual.db.models.manager import MultilingualManager
from multilingual.db.models.options import MultilingualOptions
from multilingual.db.models.translation import TranslationModelBase, TranslationModel
from multilingual.languages import get_fallbacks, get_field_alias, get_all

# TODO: inheritance of multilingual models and translation models


class MultilingualModelBase(ModelBase):
    def __new__(cls, name, bases, attrs):
        ### START - Build translation model
        # At first we build translation model so we can add it to attrs
        # Purpose is to not call 'add_to_class' after model is registered

        # We have to copy attributes because they change during creation of a model
        trans_attrs = attrs.copy()

        # Make a copy of Meta, so changes in it when creating a translation model does not affect
        # creation of multilingual model
        if attrs.has_key('Meta'):
            trans_attrs['Meta'] = classobj.__new__(classobj, 'Meta', (attrs['Meta'],), attrs['Meta'].__dict__.copy())

        translation_name = name + "Translation"
        trans_attrs['multilingual_model_name'] = name
        c_trans_model = TranslationModelBase(translation_name, (TranslationModel, ), trans_attrs)
        ### END - Build translation model

        ### And some changes before we build multilingual model
        # Add translation model to attrs
        attrs['translation_model'] = c_trans_model

        # Add proxies for translated fields into attrs
        for field in (c_trans_model._meta.fields + c_trans_model._meta.many_to_many):
            if field.name in ('id', 'language_code', 'master'):
                continue
            for language_code in get_all():
                proxy = TranslationProxyField(field.name, language_code)
                attrs[proxy.name] = proxy

            # Fallback:
            # - default field has a fallback (this is different from the original multilingual)
            # - fields with language extension don't have a fallback
            #
            # e.g.:
            #  country.name -> fallback
            #  country.name_es -> no fallback

            proxy = TranslationProxyField(field.name, None, fallback=True)
            attrs[proxy.name] = proxy

        # Handle manager
        if not 'objects' in attrs:
            # If there is no manager, set MultilingualManager as manager
            attrs['objects'] = MultilingualManager()
        elif not isinstance(attrs['objects'], MultilingualManager):
            # Make sure that if the class specifies objects then it is a subclass of our Manager.

            # Don't check other managers since someone might want to have a non-multilingual manager, but assigning
            # a non-multilingual manager to objects would be a common mistake.
            raise ValueError("Model %s specifies translations, so its 'objects' manager must be a subclass of "\
                             "multilingual.Manager." % name)

        # And now just create multilingual model
        return super(MultilingualModelBase, cls).__new__(cls, name, bases, attrs)

    def add_to_class(cls, name, value):
        # Catch meta and change its class, it is HACK, but it is the least ugly one
        if name == '_meta':
            value = MultilingualOptions(value.meta, value.app_label)
        super(MultilingualModelBase, cls).add_to_class(name, value)


class MultilingualModel(models.Model):
    __metaclass__ = MultilingualModelBase

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        self._translation_cache = {}
        super(MultilingualModel, self).__init__(*args, **kwargs)

    def save(self, force_insert=False, force_update=False, using=None):
        """
        Change save method to save translations when multilingual object is saved.
        """
        super(MultilingualModel, self).save(force_insert, force_update, using)
        if not hasattr(self, '_translation_cache'):
            return
        for translation in self._translation_cache.values():
            # skip missing translations
            if translation is None:
                continue

            # set the translation ID just in case the translation was
            # created while self was not stored in the DB yet

            # note: we're using _get_pk_val here even though it is
            # private, since that's the most reliable way to get the value
            # on older Django (pk property did not exist yet)
            # TODO: is it still necessary?? There are probably other incompatible changes

            translation.master_id = self._get_pk_val()
            translation.save()

    def _fill_translation_cache(self, language_code):
        """
        Fill the translation cache using information from query.extra_fields if any.
        """
        # This can not be called in post_init because the extra fields are
        # assigned by QuerySet.iterator after model initialization.

        # unsaved instances does not have translations
        if not self.pk:
            return
        # skip if we already has translation, or we know there is not one
        elif self._translation_cache.has_key(language_code):
            return

        c_trans_model = self._meta.translation_model

        # see if translation was in the query
        # WARNING: This must fail if we do not have all fields in query
        translation_data = {}
        for field_name in [f.attname for f in c_trans_model._meta.fields]:
            # We know values of language_code and master_id, so we does not expect them to be in query
            if field_name in ('language_code', 'master_id'):
                continue

            try:
                translation_data[field_name] = getattr(self, get_field_alias(field_name, language_code))
            except AttributeError:
                # if any field is missing we can not store data in translation cache
                # and we need to use direct query
                translation_data = None
                break

        if translation_data is not None:
            translation = c_trans_model(language_code=language_code, master=self, **translation_data)
            self._translation_cache[language_code] = translation
        else:
            # If we do not have translation (e.g. was not part of query)
            # we will try direct query to load it
            try:
                # TODO, XXX: get correct related_name instead of 'translations' !!!
                self._translation_cache[language_code] = self.translations.get(language_code=language_code)
            except c_trans_model.DoesNotExist:
                # translation does not exist, we store None to avoid repetitive calls of this code
                self._translation_cache[language_code] = None

    def _get_translation(self, language_code, fallback=False, can_create=False):
        """
        Returns translation instance for given 'language_code'.

        If the translation does not exist:
        1. if 'can_create' is True, this function will create one
        2. otherwise, if 'fallback' is True, this function will try fallback languages
        3. if all of the above fails to find a translation, raise the
            TranslationModel.DoesNotExist exception
        """
        self._fill_translation_cache(language_code)

        translation = self._translation_cache.get(language_code)
        if translation is not None:
            return translation

        if can_create:
            translation = self._meta.translation_model(master=self, language_code=language_code)
            self._translation_cache[language_code] = translation
            return translation

        elif fallback:
            for language_code in get_fallbacks(language_code):
                self._fill_translation_cache(language_code)
                translation = self._translation_cache.get(language_code)
                if translation is not None:
                    return translation

        raise self._meta.translation_model.DoesNotExist(language_code)
