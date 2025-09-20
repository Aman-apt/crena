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
from django.db.utils import NotSupportedError
from django.urls import reverse
from django.utils import timezone
from secrets import token_urlsafe

#How long user needs to go without update to declare as inactive (i.e curenty online)
ACTIVE_USER_TIMEDELTA = timezone.timedelta(
    milliseconds=settings.SCRIPT_HEARTBEAT_FREQUENCY * 2
)
RESULT_LIMITS = 300

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
    return [ipaddress.ip_network(network.strip()) for network in networks.split(",")]

def _validate_regex(regex: str):
    try:
        re.compile(regex)
    except re.error:
        return ValidationError(f"Given {regex} is not valid regex")

def _api_token():
    return token_urlsafe(32)

class User(AbstractUser):
    username = models.CharField(_("username"), max_length=84, unique=True,  default=_default_uuid)
    email = models.EmailField(_("email"), max_length=254, unique=True)
    api_token = models.TextField(_(""), default=_api_token)

    def __str__(self):
        return self.email


class Service(models.Model):
    ACTIVE = "AC"
    ARCHIVED = "AR"
    SERVICE_STATUSES = [(ACTIVE, _("Active")), (ARCHIVED, _("Archived"))]

    #core attributes of the services
    uuid = models.UUIDField(_("uuid"), default=_default_uuid)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("user"), on_delete=models.CASCADE)
    name = models.CharField(_("name"), max_length=254)
    collaborators = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        default='',
        verbose_name=_("collaborator"),
        related_name="services",
        on_delete=models.CASCADE)
    
    created = models.DateTimeField(_("Created"), auto_now_add=True, null=True)
    link = models.URLField(_("link"), blank=True)
    origins = models.TextField(_("origins"), default="*")
    status = models.CharField(_("statuses"), max_length=2, choices=SERVICE_STATUSES, default=ACTIVE, db_index=True)
    hide_referrer_regex = models.TextField(
        default="",
        blank=True,
        validators=[_validate_regex],
        verbose_name=_("Hide referrer regex"),
    )
    respect_dnt = models.BooleanField(_("respect dnt"), default=True)
    ignore_robots = models.BooleanField(_("ignore robots"), default=False)
    collectd_ips = models.BooleanField(_("collected ips"), default=True)
    ignored_ips = models.TextField(_("ignored ips"), default="", blank=True, validators=[_valid_network_list])
    script_inject = models.TextField(_("script inject"), default="", blank=True)

    class Meta:
        verbose_name = ['Service']
        verbose_name_plural = ("Serices")
        ordering = ["name", "uuid"]


    def __str__(self):
        return self.name
    
    def get_ignored_networks(self):
        return _parse_networks(self.ignored_ips)
    
    def get_ignored_referrer_regex(self):
        if len(self.hide_referrer_regex.strip()) == 0:
            return re.compile(r".^")
        
        else:
            try:
                re.compile(self.hide_referrer_regex)
            except re.error:
                return re.compile(r".^")
            
    def get_daily_stats(self):
        return self.get_core_status(
            start_time=timezone.now() - timezone.timedelta(days=1)
        )

    def get_core_status(self, start_time=None, end_time=None):
        if start_time is None:
            start_time = timezone.now() - timezone.timedelta(days=30)
        elif end_time is None:
            end_time = timezone.now()
        
        main_data = self.get_relative_stats(start_time, end_time)
        comparsion_data = self.get_relative_stats(
            start_time - (end_time - start_time), start_time,
        )
        main_data["compare"] = comparsion_data
        return main_data


    def get_relative_stats(self, start_time, end_time):
        Session = apps.get_model('analytics', 'Session')
        Hit = apps.get_model('analytics', 'Hit')

        tz_now = timezone.now()

        currently_online = Session.objects.filter(service=self, last_seen__gt=tz_now - ACTIVE_USER_TIMEDELTA).count()
        sessions = Session.objects.filter(service=self, start_time__gt=start_time, start_time__lt=end_time).order_by("-start_time")
        session_count = sessions.count()

        hits = Hit.objects.filter(service=self, start_time__gt=start_time, start_time__lt=end_time).order_by("-start_time")
        hits_count = hits.count()
        has_hits = Hit.objects.filter(service=self).exists()

        bounces = sessions.filter(is_bounce=True)
        bounces_count = bounces.count()

        locations = hits.values("location").annotate(count=models.Count("location")).order_by("-count")[:RESULT_LIMITS]
        referrer_ignore = self.get_ignored_referrer_regex()

        referrers = [
            referrer 
            for referrer in (
                hits.values("referrer").annotate(models.Count("referrer")).order_by("-count")[:RESULT_LIMITS]
            )
            if not referrer_ignore.match(referrer["referrer"])
        ]

        countries = sessions.values("countries").annotate(models.Count("countries")).order_by("-count")[:RESULT_LIMITS]
        devices = sessions.values("devices").annotate(models.Count("devices")).order_by("-count")[:RESULT_LIMITS]
        devices_types = sessions.values("device_type").annotate(models.Count("device_type")).order_by("-count")[:RESULT_LIMITS]
        operating_system = sessions.values("os").annotate(models.Count("os")).order_by("-count")[:RESULT_LIMITS]
        browser = sessions.values("browser").annotate(models.Count("browser")).order_by("-count")[:RESULT_LIMITS]

        avg_load_time = hits.aggregate(load_time__avg=models.Avg('load_time'))["load_time__avg"]
        avg_hit_per_session = hits_count / session_count if session_count > 0 else None

        avg_session_duration = self._get_avg_session_duration(session=sessions, session_counts=session_count)
        
        
        chart_data, chart_tooltip_format, chart_granularity = self._get_chart_data(
            sessions, hits, start_time, end_time, tz_now
        )
        return {
            "currently_online": currently_online,
            "session_count": session_count,
            "hits_counts": hits_count,
            "has_hits": has_hits,
            "bounce_rate_pct": bounces_count * 100/ session_count if session_count > 0 else None,
            "avg_session_duration": avg_session_duration,
            "avg_load_time": avg_load_time,
            "avg_hits_per_session": avg_hit_per_session,
            "referrers": referrers,
            "locations": locations,
            "countries": countries,
            "devices": devices,
            "devices_types": devices_types,
            "operating_system": operating_system,
            "browser": browser,
            "chart_data": chart_data,
            "chart_tootlip_format": chart_tooltip_format,
            "chart_granularity": chart_granularity,
            "online": True,
        }
    

    def _get_avg_session_duration(self, sessions, session_count):
        try:
            avg_session_duration = sessions.annotate(
                duration=models.F("last_seen") - models.F("start_time")
            ).aggregate(time_delta=models.Avg("duration"))["time_delta"]
        except NotSupportedError:
            avg_session_duration = sum(
                [
                    (session.last_seen - session.start_time).total_seconds()
                    for session in sessions
                ]
            ) / max(session_count, 1)
        if session_count == 0:
            avg_session_duration = None

        return avg_session_duration

    def _get_chart_data(self, session, hits, start_time, end_time, tz_now):
        pass