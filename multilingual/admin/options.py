"""
Model admin for multilingual models
"""
from django.contrib.admin import ModelAdmin
from django.contrib.admin.util import flatten_fieldsets, unquote
from django.utils.encoding import force_unicode
from django.utils.functional import curry
from django.utils.translation import ugettext as _
from django.conf.urls import patterns, url
from django.utils.functional import update_wrapper
from django.http import HttpResponseRedirect
from django.core.exceptions import PermissionDenied

from multilingual.forms.forms import multilingual_modelform_factory, MultilingualModelForm
from multilingual.languages import get_dict, get_active, lock, release

#TODO: Inline model admins


class MultilingualModelAdminMixin(object):
    form = MultilingualModelForm

    # use special template to render tabs for languages on top
    change_form_template = "multilingual/admin/change_form.html"

    #TODO: select_related on queryset of required
    #TODO: select_related on get_object if required

    def get_form(self, request, obj=None, **kwargs):
        """
        Returns a Form class for use in the admin add view. This is used by
        add_view and change_view.

        UPDATE: use multilingual_modelform_factory
        """
        if self.declared_fieldsets:
            fields = flatten_fieldsets(self.declared_fieldsets)
        else:
            fields = None
        if self.exclude is None:
            exclude = []
        else:
            exclude = list(self.exclude)
        exclude.extend(kwargs.get("exclude", []))
        exclude.extend(self.get_readonly_fields(request, obj))
        # if exclude is an empty list we pass None to be consistant with the
        # default on modelform_factory
        exclude = exclude or None
        defaults = {
            "form": self.form,
            "fields": fields,
            "exclude": exclude,
            "formfield_callback": curry(self.formfield_for_dbfield, request=request),
        }
        defaults.update(kwargs)
        return multilingual_modelform_factory(self.model, **defaults)

    def get_changelist_form(self, request, **kwargs):
        """
        Returns a Form class for use in the Formset on the changelist page.

        UPDATE: use multilingual_modelform_factory
        """
        defaults = {
            "formfield_callback": curry(self.formfield_for_dbfield, request=request),
        }
        defaults.update(kwargs)
        return multilingual_modelform_factory(self.model, **defaults)

    def render_change_form(self, request, context, **kwargs):
        # Django 1.4 postponed template rendering, so we have to pass updated language in context and avoid context
        # processor.
        # TODO: Make this a hidden form field.
        context['LANGUAGE'] = get_active()
        return super(MultilingualModelAdminMixin, self).render_change_form(request, context, **kwargs)

    def add_view(self, request, form_url='', extra_context=None):
        """
        Lock language over add_view and add extra_context
        """
        try:
            lock(request.POST.get('language', request.GET.get('language', get_active())))

            model = self.model
            opts = model._meta
            context = {
                'title': _('Add %s for language %s') % (
                    force_unicode(opts.verbose_name),
                    force_unicode(get_dict()[get_active()])
                ),
            }
            context.update(extra_context or {})
            return super(MultilingualModelAdminMixin, self).add_view(request, form_url, context)
        finally:
            release()

    def change_view(self, request, object_id, **kwargs):
        """
        Lock language over change_view and add extra_context
        """
        # In Django 1.4 number of arguments have changed.
        extra_context = kwargs.get('extra_context')
        try:
            lock(request.POST.get('language', request.GET.get('language', get_active())))

            model = self.model
            opts = model._meta
            context = {
                'title': _('Change %s for language %s') % (
                    force_unicode(opts.verbose_name),
                    force_unicode(get_dict()[get_active()])
                ),
            }
            context.update(extra_context or {})
            kwargs['extra_context'] = context
            return super(MultilingualModelAdminMixin, self).change_view(request, object_id, **kwargs)
        finally:
            release()

    def get_urls(self):
        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)

        urls = super(MultilingualModelAdminMixin, self).get_urls()

        new_urls = patterns('',
            url(r'^(.+)/delete-translations/$', wrap(self.delete_translations_view))
        )
        return new_urls + urls

    def delete_translations_view(self, request, object_id):
        obj = self.get_object(request, unquote(object_id))

        if not self.has_change_permission(request, obj):
            raise PermissionDenied

        # Delete all translations except English
        obj.translations.exclude(language_code='en').delete()

        self.message_user(request, 'Removed translations')
        return HttpResponseRedirect('../')


class MultilingualModelAdmin(MultilingualModelAdminMixin, ModelAdmin):
    """
    Model admin for multilingual models
    """
    pass