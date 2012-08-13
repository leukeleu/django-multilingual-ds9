"""
Django-multilingual-ds9: multilingual model support for Django 1.2 and newer

Multilingual models automatically overrides base class of multilingual models

Multilingual must be installed before any application with multilingual model
or imported before any multilingual model class is loaded by django.
"""
#VERSION = ('0', '1', '44')
#__version__ = '.'.join(VERSION)

import warnings


class LazyInit(object):
    VERSION = ('0', '3', '0', '2')
    __version__ = '.'.join(VERSION)

    __deprecated__ = {
        'MultilingualModelAdmin': ('multilingual.admin.options', 'MultilingualModelAdmin'),
        'MultilingualInlineAdmin': ('multilingual.admin.inlines', 'MultilingualTabularInline'),
        'ModelAdmin': ('multilingual.admin.options', 'MultilingualModelAdmin'),
        'Manager': ('multilingual.db.models.manager', 'MultilingualManager'),
        'Translation': ('multilingual.db.models.translation', 'BaseTranslationMeta'),
        'set_default_language': ('django.utils.translation', 'activate'),
    }

    __newnames__ = {
        'MultilingualModelAdmin': 'admin.MultilingualModelAdmin',
        'MultilingualInlineAdmin': 'admin.MultilingualTabularInline',
        'ModelAdmin': 'admin.MultilingualModelAdmin',
        'Manager': 'MultilingualManager',
        'Translation': 'classobj',
        'set_default_language': 'django.utils.translation.activate',
    }

    __modules_cache__ = {}
    __objects_cache__ = {}

    def __init__(self, real):
        self.__real__ = real

    def __getattr__(self, attr):
        if not attr in self.__deprecated__:
            return getattr(self.__real__, attr)
        if attr in self.__objects_cache__:
            return self.__objects_cache__[attr]
        return self._load(attr)

    def _import(self, modname):
        if not hasattr(self, '_importlib'):
            mod = __import__('django.utils.importlib', fromlist=['django', 'utils'])
            self._importlib = mod
        return self._importlib.import_module(modname)

    def _load(self, attr):
        modname, objname = self.__deprecated__[attr]
        if not modname in self.__modules_cache__:
            self.__modules_cache__[modname] = self._import(modname)
        obj = self.__modules_cache__[modname]
        if objname is not None:
            obj = getattr(obj, objname)
        if attr in self.__newnames__:
            self._warn_newname(attr)
        self._warn_deprecated(attr, modname, objname)
        self.__objects_cache__[attr] = obj
        return obj

    def _warn_newname(self, attr):
        new = self.__newnames__[attr]
        warnings.warn("The name '%s' is deprecated in favor of '%s'" % (attr, new), DeprecationWarning)

    def _warn_deprecated(self, attr, modname, objname):
        if objname:
            msg = "'multilingual.%s' is deprecated in favor of '%s.%s'" % (attr, modname, objname)
        else:
            msg = "'multilingual.%s' is deprecated in favor of '%s'" % (attr, modname)
        warnings.warn(msg, DeprecationWarning)

import sys
sys.modules[__name__] = LazyInit(sys.modules[__name__])


from django.db.models.base import Model, ModelBase
from multilingual.db.models.base import MultilingualModel, MultilingualModelBase
from multilingual.db.models.manager import MultilingualManager

def install_translation_library():
    # Change parent of model if it has Translation class
    # thus changing model to multilingual model

    if getattr(ModelBase, '_multilingual_installed', False):
        # don't install it twice
        return

    _modelbase_new_original = ModelBase.__new__

    def _modelbase_new_override(cls, name, bases, attrs):
        if 'Translation' in attrs:
            if not issubclass(cls, MultilingualModelBase):
                if Model in bases:
                    bases = list(bases)
                    bases[bases.index(Model)] = MultilingualModel
                    bases = tuple(bases)
                return MultilingualModelBase.__new__(MultilingualModelBase, name, bases, attrs)

        return _modelbase_new_original(cls, name, bases, attrs)
    ModelBase.__new__ = staticmethod(_modelbase_new_override)
    ModelBase._multilingual_installed = True

# TODO: make this optional
# install the library
install_translation_library()
