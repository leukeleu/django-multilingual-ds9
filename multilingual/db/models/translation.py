"""
Base model for tranlsation models
"""
from new import classobj

from django.db import models
from django.db.models.base import ModelBase

from multilingual.languages import get_dict


# Translation meta options that will replaced with options from multilingual meta
META_INHERITES = ('abstract', 'app_label')


class BaseTranslationMeta:
    """
    Dummy class to be used as parent for Meta class of Translation model

    Deprecated: Serves as parent class for Translation class of multilingual model.
    """
    pass


class TranslationModelBase(ModelBase):
    def __new__(cls, name, bases, attrs):
        # This only happens for base multilingual models
        if bases[0] == models.Model:
            #TODO: CHECK attrs here
            super_new = super(TranslationModelBase, cls).__new__
            return super_new(cls, name, bases, attrs)

        # multilingual meta
        attr_meta = attrs.pop('Meta', None)

        # Prepare attributes for translation model
        if 'Translation' in attrs:
            trans_attrs = attrs['Translation'].__dict__.copy()
            trans_attrs.pop('__doc__')
        else:
            trans_attrs = dict(__module__=attrs['__module__'])

        # original Meta of Translation Model
        trans_meta = trans_attrs.pop('Meta', None)

        ### START - Create Meta for TranslationModel
        meta_attrs = getattr(trans_meta, '__dict__', {})
        for key in META_INHERITES:
            if hasattr(attr_meta, key):
                meta_attrs[key] = getattr(attr_meta, key)

        # Append suffix to db_table of multilingual class
        if not meta_attrs.has_key('db_table') and hasattr(attr_meta, 'db_table'):
            meta_attrs['db_table'] = attr_meta.db_table + 'translation'

        is_abstract = meta_attrs.get('abstract', False)
        if not is_abstract:
            # Handle unique constraints
            meta_attrs['unique_together'] = list(meta_attrs.get('unique_together', []))
            meta_attrs['unique_together'] = [
                tuple(list(item) + ['language_code'])
                for item in meta_attrs['unique_together']
            ]
            # append all unique fields to unique_together with 'language_code' field
            # and remove their uniqueness
            for item_name, item in trans_attrs.items():
                if isinstance(item, models.Field) and item.unique and not item.primary_key:
                    meta_attrs['unique_together'].append((item_name, 'language_code'))
                    trans_attrs[item_name]._unique = False
            # TODO: use TranslationModel.Meta instead of hardcoding
            # Appending necessary unique together
            meta_attrs['unique_together'].append(('language_code', 'master'))

            # TODO: enable related_name in Options
            related_name = meta_attrs.pop('related_name', 'translations')

            # Add 'master' field
            trans_attrs['master'] = models.ForeignKey(
                attrs['multilingual_model_name'],
                related_name = related_name
            )

        # TODO: use something already existing instead of BaseTranslationMeta
        trans_attrs['Meta'] = classobj.__new__(classobj, 'Meta', (BaseTranslationMeta,), meta_attrs)
        ### END - Create Meta for TranslationModel

        return super(TranslationModelBase, cls).__new__(cls, name, bases, trans_attrs)


class TranslationModel(models.Model):
    """
    Base class for translations
    """
    __metaclass__ = TranslationModelBase

    # Create explicit primary key, to prevent creation of other primary key
    id = models.AutoField(primary_key=True)
    # TODO: rename to 'language' or 'lang'
    language_code = models.CharField(max_length=15, choices=get_dict().iteritems(), db_index=True)
    # ForeignKey to master is defined in class constructor
    #master = ForeignKey(cls, related_name=related_name)

    # This is not used now, should I use it as inherited or just hard code that three attributes
    class Meta:
        # Abstract is here, so TranslationModel itself is abstract
        # All other models inherited from TranslationModel will have abstract taken from their multilingual model
        abstract = True
        #unique_together = [('language_code', 'master')]
        # This must be enabled in Options
        #related_name = 'translations'
        # This is temporarily disabled
        #ordering = ('language_code',)

    @classmethod
    def contribute_to_class(cls, main_cls, name):
        main_cls._meta.translation_model = cls
