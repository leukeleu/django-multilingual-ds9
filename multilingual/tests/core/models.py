from django.db import models
from multilingual.db.models.base import MultilingualModel


class Basic(MultilingualModel):
    """
    Model for testing basic multilingual functions
    """
    description = models.CharField(max_length=20)

    class Translation:
        title = models.CharField(max_length=20)


class Managing(MultilingualModel):
    """
    Model for testing manager of multilingual model
    """
    shortcut = models.CharField(max_length=20)

    class Translation:
        name = models.CharField(max_length=20)


class Untranslated(models.Model):
    """
    Model is not translated and has a reference to a translated model
    """
    name = models.CharField(max_length=20)
    basic = models.ForeignKey(Basic)
