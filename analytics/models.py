import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _ 
from core.models import Service


class Session(models.Model):
    service = models.ForeignKey(Service, verbose_name=_("service"), null=True, on_delete=models.SET_NULL)
    session_key = models.CharField(_("session key"), max_length=128)
    first_seen = models.DateTimeField(_("first seen"), auto_now_add=True)
    last_seen = models.DateTimeField(_("last seen"), auto_now=True)
    hits = models.PositiveIntegerField(_("hits"), default=0)



class Hit(models.Model):
    service = models.ForeignKey(Service, verbose_name=_("service hit"), on_delete=models.CASCADE)
    session = models.ForeignKey(Session, verbose_name=_("session hit"), null=True, on_delete=models.SET_NULL)
    path = models.CharField(_("path"), max_length=2000)
    referrer = models.CharField(_("referrer"), max_length=50, null=True, blank=True)
    user_agent = models.CharField(_("user agent"), blank=True)
    ip_hash = models.CharField(_("ip hash"), max_length=64)
    timestamp = models.DateTimeField(_("time stamp"),auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["service", "timestamp"]),
            models.Index(fields=["session"]),
        ]