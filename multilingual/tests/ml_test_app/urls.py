from django.conf.urls import include, patterns, url
from django.contrib.admin.sites import AdminSite

from multilingual.admin import MultilingualModelAdmin

from .models import Multiling

SITE = AdminSite()

SITE.register(Multiling, MultilingualModelAdmin)

urlpatterns = patterns('',
    url(r'^admin/', include(SITE.urls)),
)
