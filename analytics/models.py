import uuid
from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.utils.translation import gettext_lazy as _ 
from core.models import Service, ACTIVE_USER_TIMEDELTA


def _default_uuid():
    return uuid.uuid4()


class Session(models.Model):
    uuid = models.UUIDField(_("uuid"), default=_default_uuid)

    service = models.ForeignKey(Service, verbose_name=_("services"), related_name="sessions", on_delete=models.CASCADE)
    identifier = models.TextField(_("identifier"), blank=True)

    start_time = models.DateTimeField(_("start time"), auto_now_add=True, null=True)
    last_seen = models.DateTimeField(_("last seen"), auto_now=True, null=True)

    user_agent = models.CharField(_("user agent"), max_length=50, null=True)
    browser = models.CharField(_("browser"), max_length=50, null=True)
    devices = models.CharField(_("devices"), max_length=50, null=True)
    device_type = models.CharField(
        max_length=7,
        choices=[
            ("PHONE", _("Phone")),
            ("TABLET", _("Tablet")),
            ("DESKTOP", _("Desktop")),
            ("ROBOT", _("Robot")),
            ("OTHER", _("Other")),
        ],
        default="OTHER",
        verbose_name=_("Device type"),
    )

    os = models.TextField(_("operating system"), null=True)
    ip = models.GenericIPAddressField(_("IP"), db_index=True, null=True)

    # geoip data
    asn = models.TextField(_("asn"), blank=True)
    country = models.TextField(_("country"), null=True)
    longitude = models.FloatField(_("longitude"), null=True)
    latitude = models.FloatField(_("latitude"), null=True)
    time_zone = models.CharField(_("time zone"), max_length=100, db_index=True, null=True)
    is_bounce = models.BooleanField(_("is bounce"), default=False)

    class Meta:
        verbose_name = _("Session")
        verbose_name_plural = _("Sessions")
        ordering = ["-start_time"]
        indexes = [
            models.Index(fields=["service", "-start_time"]),
            models.Index(fields=["service", "-last_seen"]),
            models.Index(fields=["service", "identifier"]),
        ]

    @property
    def _is_currently_active(self):
        return timezone.now() - self.last_seen < ACTIVE_USER_TIMEDELTA
    
    @property
    def duration(self):
        return self.last_seen - self.start_time
    
    def __str__(self):
        return f"{self.identifier if self.identifier else 'Anonymous'} @ {self.service.name} [{str(self.uuid)[:6]}]"
    
    def get_absolute_url(self):
        return reverse(
            "dashboard:service_session",
            kwargs={"pk": self.service.pk, "session_pk": self.uuid},
        )
    
    def recalculate_bounce(self):
        bounce = self.hit_set.count() == 1
        if bounce != self.is_bounce:
            self.is_bounce = bounce
            self.save()
    

class Hit(models.Model):
    session = models.ForeignKey(Session, verbose_name=_("session"), on_delete=models.CASCADE)
    initial = models.BooleanField(_("initial"), db_index=True, default=False)

    start_time = models.DateTimeField(_("start time"), auto_now_add=True, null=True)
    last_seen = models.DateTimeField(_("last seen"), auto_now=True, null=True)
    heartbeats = models.IntegerField(_("heartbeats"), default=0)
    tracker = models.CharField(
        _("tracker"),
        max_length=10,
        choices=[("JS", "JavaScript"), ("PIXEL", "Pixel (noscript)")],
        default="JS",
    )

    location = models.TextField(_("location"), db_index=True, blank=True)
    referrer = models.TextField(_("referrer"), db_index=True, blank=True)
    load_time = models.CharField(_("load time"), max_length=50, null=True, db_index=True)

    service = models.ForeignKey(Service, verbose_name=_("services"), on_delete=models.CASCADE, db_index=True)

    class Meta:
        verbose_name = _("Hit")
        verbose_name_plural = _("Hits")
        ordering = ["-start_time"]
        indexes = [
            models.Index(fields=["session", "-start_time"]),
            models.Index(fields=["service", "-start_time"]),
            models.Index(fields=["session", "location"]),
            models.Index(fields=["session", "referrer"]),
        ]

    @property
    def duration(self):
        return self.last_seen - self.start_time
    
    def get_absolute_url(self):
        return reverse(
            "dashboard:service_session",
            kwargs={"pk": self.service.pk, "session_pk": self.session.pk},
        )
