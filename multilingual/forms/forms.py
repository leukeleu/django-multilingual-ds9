"""
Model form for multilingual models
"""
from django.forms.forms import get_declared_fields
from django.forms.models import construct_instance, model_to_dict, fields_for_model, \
    ModelFormMetaclass, BaseModelForm, ModelFormOptions
from django.forms.util import ErrorList
from django.forms.widgets import media_property

from multilingual.languages import get_active


class MultilingualModelFormMetaclass(ModelFormMetaclass):
    """
    Alters django model form to include fields for translated model fields
    """
    #TODO: override and not copy whole __new__ function
    def __new__(cls, name, bases, attrs):
        formfield_callback = attrs.pop('formfield_callback', None)
        try:
            # HACK: Had to replace baseclass
            # TODO: Report that this can not overrode, there should be something else.
            parents = [b for b in bases if issubclass(b, MultilingualModelForm)]
        except NameError:
            # We are defining ModelForm itself.
            parents = None
        declared_fields = get_declared_fields(bases, attrs, False)
        new_class = super(MultilingualModelFormMetaclass, cls).__new__(cls, name, bases,
                attrs)
        if not parents:
            return new_class

        if 'media' not in attrs:
            new_class.media = media_property(new_class)
        opts = new_class._meta = ModelFormOptions(getattr(new_class, 'Meta', None))
        if opts.model:
            # If a model is defined, extract form fields from it.
            fields = fields_for_model(opts.model, opts.fields,
                                      opts.exclude, opts.widgets, formfield_callback)

            #HACK: This is update of original method. I should be able to change it to overrides
            translation_model = getattr(opts.model._meta, 'translation_model', None)
            if translation_model:
                if opts.exclude is None:
                    exclude = ('id', 'language_code', 'master')
                else:
                    exclude = list(opts.exclude) + ['id', 'language_code', 'master']
                translated_fields = fields_for_model(
                    translation_model, opts.fields, exclude, opts.widgets, formfield_callback
                )

                # Copy translated fields to fields, skipping empty fields
                for field_name, field in translated_fields.items():
                    if field:
                        fields[field_name] = field

            # Override default model fields with any custom declared ones
            # (plus, include all the other declared fields).
            fields.update(declared_fields)
        else:
            fields = declared_fields
        new_class.declared_fields = declared_fields
        new_class.base_fields = fields
        return new_class


class BaseMultilingualModelForm(BaseModelForm):
    """
    Alters django model form update initials with data from translation model
    """
    #TODO: unique checks and validation
    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, error_class=ErrorList, label_suffix=':',
                 empty_permitted=False, instance=None):
        opts = self._meta
        initial_data = {}
        if instance is not None:
            trans_model = getattr(instance._meta, 'translation_model', None)
            if trans_model is not None:
                try:
                    translation = instance._get_translation(get_active(), can_create=True)
                except trans_model.DoesNotExist:
                    pass
                else:
                    if opts.exclude is None:
                        exclude = ('id', 'language_code', 'master')
                    else:
                        exclude = list(opts.exclude) + ['id', 'language_code', 'master']
                    initial_data = model_to_dict(translation, opts.fields, exclude)
        initial_data.update(initial or {})
        super(BaseMultilingualModelForm, self).__init__(
            data, files, auto_id, prefix, initial_data, error_class, label_suffix, empty_permitted, instance
        )

    def _post_clean(self):
        """
        Stores translation data into translation instance
        """
        opts = self._meta
        translation = self.instance._get_translation(get_active(), can_create=True)
        if opts.exclude is None:
            exclude = ('id', 'language_code', 'master')
        else:
            exclude = list(opts.exclude) + ['id', 'language_code', 'master']
        # Update instance translation
        construct_instance(self, translation, opts.fields, exclude)
        super(BaseMultilingualModelForm, self)._post_clean()


class MultilingualModelForm(BaseMultilingualModelForm):
    __metaclass__ = MultilingualModelFormMetaclass


# TODO, HACK: I had to copy whole function because of hardcoded MetaClass at the end
# Report to django to use form.__metaclass__ instead.
def multilingual_modelform_factory(model, form=MultilingualModelForm, fields=None, exclude=None,
                       formfield_callback=None):
    # Create the inner Meta class. FIXME: ideally, we should be able to
    # construct a ModelForm without creating and passing in a temporary
    # inner class.

    # Build up a list of attributes that the Meta object will have.
    attrs = {'model': model}
    if fields is not None:
        attrs['fields'] = fields
    if exclude is not None:
        attrs['exclude'] = exclude

    # If parent form class already has an inner Meta, the Meta we're
    # creating needs to inherit from the parent's inner meta.
    parent = (object,)
    if hasattr(form, 'Meta'):
        parent = (form.Meta, object)
    Meta = type('Meta', parent, attrs)

    # Give this new form class a reasonable name.
    class_name = model.__name__ + 'Form'

    # Class attributes for the new form class.
    form_class_attrs = {
        'Meta': Meta,
        'formfield_callback': formfield_callback
    }

    # HACK: change meta class
    return MultilingualModelFormMetaclass(class_name, (form,), form_class_attrs)
