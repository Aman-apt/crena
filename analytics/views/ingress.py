import base64
import json

from django.conf import settings
from django.core.cache import cache
from django.http.response import (
    Http404, HttpResponse,HttpResponseBadRequest, HttpResponseForbidden
)
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.utils import timezone

from ipware import get_client_ip

from core.models import Service
from ..tasks import ingress_request


def ingress(request, service_uuid, tracker, identifier, payload):
    time = timezone.now()
    client_ip, is_routeable = get_client_ip(request)
    location = request.META.get("HTTP_REFERER", "").strip()
    user_agent = request.META.get("HTTP_USER_AGENT", "").strip()
    dnt = request.META.get("HTTP_DNT", "0").strip() == "1"
    gpc = request.META.get("HTTP_SEC_GPC", "0").strip() == "1"
    if gpc or dnt:
        dnt = True

    ingress_request.delay(
        service_uuid,
        tracker,
        time,
        payload,
        client_ip,
        location,
        user_agent,
        dnt=dnt,
        identifier=identifier,
    )


class ValidateServiceOriginMixin:
    def dispatch(self, request, *args, **kwargs):
        try:
            service_uuid = self.kwargs.get("service_uuid")
            origins = cache.get(f"service_uuid_{service_uuid}")

            if origins is None:
                service = Service.objects.get(uuid=service_uuid)
                origins = service.origins
                cache.set(f"service_origins{service_uuid}", origins, timeout=3600)

            allow_origins = "*"
            
            if origins != "*":
                pass

        except Exception as e:
            pass

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    


class PixelView(ValidateServiceOriginMixin, View):
    pass


@method_decorator(csrf_exempt, name="dispatch")
class ScriptView(ValidateServiceOriginMixin, View):
    pass