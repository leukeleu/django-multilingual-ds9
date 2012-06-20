"""
Provides virtual field to access to translation from multilingual model instance.
"""
from django.conf import settings

from multilingual.languages import get_active
try:
    from django.utils.log import logger
except ImportError:
    from logging import root as logger


# It would be better if field could be derived just from object, but property is currently
# easiest way to enable initiation of multilingual models with translations
# Problem reported to Django: #16508
#class TranslationProxyField(object):
class TranslationProxyField(property):
    """
    Provides an access to translated fields

    Based on code for GenericForeignKey field
    """
    def __init__(self, field_name, language_code=None, fallback=False):
        self._field_name = field_name
        self._language_code = language_code
        self._fallback = fallback
        names = [field_name]
        if language_code is not None:
            names.append(language_code.replace('-', '_'))

        # Changed: don't set fallback field suffix

        self.name = '_'.join(names)
        super(TranslationProxyField, self).__init__()

    def contribute_to_class(self, cls, name):
        if self.name != name:
            raise ValueError('Field proxy %s is added to class under bad attribute name.' % self)
        self.model = cls
        cls._meta.add_virtual_field(self)

        #===============================================================================================================
        # # For some reason I don't totally understand, using weakrefs here doesn't work.
        # signals.pre_init.connect(self.instance_pre_init, sender=cls, weak=False)
        #===============================================================================================================

        # Connect myself as the descriptor for this field
        setattr(cls, name, self)

    #===================================================================================================================
    # def instance_pre_init(self, signal, sender, args, kwargs, **_kwargs):
    #    """
    #    Handles initializing an object with the generic FK instaed of
    #    content-type/object-id fields.
    #    """
    #    if self.name in kwargs:
    #        value = kwargs.pop(self.name)
    #        kwargs[self.ct_field] = self.get_content_type(obj=value)
    #        kwargs[self.fk_field] = value._get_pk_val()
    #===================================================================================================================

    @property
    def language_code(self):
        """
        If _language_code is None we are the _current field, so we use the
        currently used language for lookups.
        """
        if self._language_code is not None:
            return self._language_code
        return get_active()

    @property
    def fallback(self):
        return self._fallback

    def __get__(self, instance, instance_type=None):
        """
        Returns field translation or None
        """
        if instance is None:
            return self

        try:
            return getattr(
                instance._get_translation(self.language_code, fallback=self.fallback),
                self._field_name
            )
        except instance._meta.translation_model.DoesNotExist:
            logger.info("Translation '%s' for '%s' (pk='%s') does not exist.", self.name, type(instance), instance.pk)
            return None

    def __set__(self, instance, value):
        """
        Sets field translation
        """
        if instance is None:
            raise AttributeError(u"%s must be accessed via instance" % self.name)

        translation = instance._get_translation(
            self.language_code,
            can_create=True
        )
        setattr(translation, self._field_name, value)
