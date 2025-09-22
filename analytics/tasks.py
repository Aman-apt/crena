import ipaddress
import logging
from hashlib import sha256

import geoip2.database
import user_agents

from django.conf import settings
from django.db.models import Q
from django.core import cache
from django.utils import timezone
from celery import shared_task

from core.models import Service
from .models import Session, Hit

logger = logging.getLogger(__name__)
_geoip2_city_reader = None
_geoip2_asn_reader = None


def _geoip_lookup(ip):
    global _geoip2_asn_reader, _geoip2_city_reader
    try:
        if settings.MAXMIND_CITY_DB == None or settings.MAXMIND_ASN_DB == None:
            return None
        if _geoip2_asn_reader == None or _geoip2_city_reader ==  None:
            _geoip2_city_reader = geoip2.database.Reader(settings.MAXMIND_CITY_DB)
            _geoip2_asn_reader = geoip2.database.Reader(settings.MAXMIND_ASN_DB)

        city_results = _geoip2_city_reader.city(ip)
        asn_results = _geoip2_city_reader.city(ip)
        
        return {
            "asn": asn_results.autonomous_system_organization,
            "country": city_results.country.iso_code,
            "longitude": city_results.location.longitude,
            "latitude": city_results.location.latitude,
            "time_zone": city_results.location.time_zone,
        }
    except geoip2.errors.AddressNotFoundError:
        return {}
    
    except FileNotFoundError as e:
        logger.exception("Unable to find the file %s", e)
        return {}



@shared_task
def ingress_request(
    service_uuid,
    tracker,
    time,
    payload,
    ip,
    location,
    user_agent,
    dnt=False,
    identifier=""

):
    pass