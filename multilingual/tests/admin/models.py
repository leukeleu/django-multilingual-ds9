from django.db import models
from multilingual.db.models.base import MultilingualModel


class AdminTests(MultilingualModel):
    """
    Model for testing administration
    """
    description = models.CharField(max_length=20)

    class Translation:
        title = models.CharField(max_length=20)