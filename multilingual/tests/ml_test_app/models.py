"""
Models to test multilingual features.
"""
from django.db import models
from multilingual.db.models.base import MultilingualModel


class Multiling(MultilingualModel):
    name = models.CharField(max_length=100)

    class Translation:
        title = models.CharField(max_length=100)
