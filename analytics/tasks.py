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
    try:
        service = Service.objects.get(pk=service_uuid, status=Service.ACTIVE)
        logger.debug(f"Linked to the service{service}")

        if dnt and service.respect_dnt:
            logger.debug("Ignoring this because of DNT")
            return {}
        
        try:
            remote_ip = ipaddress.ip_network(ip)
            for ignored_network in service.get_ignored_networks():
                if (
                    ignored_network.version == remote_ip.version and ignored_network.supernet_of(remote_ip)
                ):
                    logger.debug("Ignoring this because of ignored ip")
                    return 
        except ValueError as e:
            logger.exception(e)

        #validate payload
        if payload.get["loadTime", 1] <= 0:
            payload["loadTime"] = None
        
        association_id_hash = sha256()
        association_id_hash.update(str(ip).encode("utf-8"))
        association_id_hash.update(str(user_agent).encode("utf-8"))
        if settings.AGGRESSIVE_HASH_SALTING:
            association_id_hash.update(str(service).encode("utf-8"))
            association_id_hash.update(str(timezone.now().date().isoformat).encode("utf-8"))
        session_cache_path = (
            f"session_association_{service.pk}_{association_id_hash.hexdigest()}"
        )

        #create or update session
        session = None
        if cache.get(session_cache_path) is not None:
            cache.touch(session_cache_path, settings.SESSION_MEMORY_TIMEOUT)
        
        session = Session.objects.filter(pk=cache.get(session_cache_path), service=service).first()
        if session is None:
            initial = True

            logger.debug("Cannot link to existing session. create new one..")

            geiop_data = _geoip_lookup(ip)
            logger.debug("Found geoip data")

            ua = user_agents.parse(user_agent)
            device_type = "OTHER"

            if (
                ua.is_bot
                or (ua.browser.family or "").strip().lower() == "googlebot"
                or (ua.device.family or ua.device.model or "").strip().lower()
                == "spider"
            ):
                device_type = "ROBOT"
            elif ua.is_mobile:
                device_type = "PHONE"
            elif ua.is_tablet:
                device_type = "TABLET"
            elif ua.is_pc:
                device_type = "PC"
            
            if device_type == "ROBOT" and service.ignore_robots:
                return 
            
            session = Session.objects.create(
                service=service,
                ip=ip if service.collect_ips and not settings.BLOCK_ALL_IPS else None,
                user_agent=user_agent,
                identifier=identifier.strip(),
                browser=ua.browser.family or "",
                device=ua.device.family or ua.device.model or "",
                device_type=device_type,
                start_time=time,
                last_seen=time,
                os=ua.os.family or "",
                asn=geiop_data.get("asn") or "",
                country=geiop_data.get("country") or "",
                longitude=geiop_data.get("longitude"),
                latitude=geiop_data.get("latitude"),
                time_zone=geiop_data.get("time_zone") or "",
            )
            cache.set(
                session_cache_path, session.pk, timeout=settings.SESSION_MEMORY_TIMEOUT
            )
        else:
            initial = False

            logger.debug("Updating the old session with new data")

            session.last_seen = time
            if session.identifier == "" and identifier.strip() != "":
                session.identifier = identifier.strip()
            session.save()

        #create or udpate a hit
        idempotency = payload.get("idempotency")
        idempotency_path = f"hit_idempotency_{idempotency}"
        hit = None

        if idempotency is not None:
            if cache.get(idempotency_path) is not None:
                cache.touch(idempotency_path, settings.SESSION_MEMORY_TIMEOUT)
                hit = Hit.objects.filter(pk=cache.get(idempotency_path), session=session).first()
                if hit is not None:
                    logger.debug("Hit is heartbat; updating old hit with new data")
                    hit.heartbeats += 1
                    hit.last_seen = time
                    hit.save()

        if hit is None:
            logger.debug("Hit was not linked to existing session, create new one")
            
            hit = Hit.objects.create(
                session=session,
                initial=initial,
                tracker=tracker,
                # At first, location is given by the HTTP referrer. Some browsers
                # will send the source of the script, however, so we allow JS payloads
                # to include the location.
                location=payload.get("location", location),
                referrer=payload.get("referrer", ""),
                load_time=payload.get("loadTime"),
                start_time=time,
                last_seen=time,
                service=service,
            )
            # calucatute the bounce of sessions
            session.recalculate_bounce()

            if idempotency is not None:
                cache.set(
                    idempotency_path, hit.pk, timeout=settings.SESSION_MEMORY_TIMEOUT
                )
    except Exception as e:
        logger.exception(e)
        print(e)
        raise e