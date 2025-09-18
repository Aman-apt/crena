import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _ 
from core.models import Service


def _default_uuid():
    return str(uuid.uuid4)


class Session(models.Model):
    pass


class Hit(models.Model):
    pass