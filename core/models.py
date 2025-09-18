import uuid
import ipaddress
import re

from django.apps import apps
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.functions import TruncDate, TruncHour
from django.utils.translation import gettext_lazy as _ 
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone
from secrets import token_urlsafe

#How long user needs to go without update to declare as inactive (i.e curenty online)
ACTIVE_USER_TIMEDELTA = timezone.timedelta(
    milliseconds=settings.SCRIPT_HEARTBEAT_FREQUENCY * 2
)

def _default_uuid():
    return str(uuid.uuid4())


def _valid_network_list(networks: str):
    try:
        _parse_networks(networks)
    except ValueError as e:
        return ValidationError(str(e))

def _parse_networks(networks: str):
    if len(networks.strip()) == 0:
        return []
    return [ipaddress.ip_network(networks.strip()) for network in networks.split(",")]

def _validate_regex(regex: str):
    try:
        re.compile(regex)
    except re.error:
        return ValidationError(f"Given {regex} is not valid regex")

def _api_token():
    return token_urlsafe(32)

class User(AbstractUser):
    username = models.CharField(_("username"), max_length=84, default=_default_uuid)
    email = models.EmailField(_("email"), max_length=254, unique=True)
    api_token = models.TextField(_(""), default=_api_token)

    def __str__(self):
        return self.email


class Service(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("user"), on_delete=models.CASCADE)
    name = models.CharField(_("name"), max_length=254)
    domain = models.CharField(_("domain"), max_length=300, blank=False, null=False)
    tracking_id = models.UUIDField(_("tracking id"), default=uuid.uuid4, unique=True)

    def __str__(self):
        return f"{self.name}, {self.domain}"
