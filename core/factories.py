import factory
from .models import Service, User


class TestFactory(factory.django.DjangoModelFactory):
    service = Service.objects.create(
        
    )