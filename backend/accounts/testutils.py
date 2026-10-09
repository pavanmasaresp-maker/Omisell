from rest_framework.test import APIClient
from accounts.models import User


def make_user(tenant, name, role):
    return User.objects.create_user(username=name, password="x", tenant=tenant, role=role)


def client_for(user):
    c = APIClient()
    c.force_authenticate(user=user)
    return c
