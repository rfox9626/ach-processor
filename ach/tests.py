import pytest

from ach_processor.celery import ping


def test_ping_returns_pong():
    assert ping() == "pong"


@pytest.mark.django_db
def test_admin_login_page_loads(client):
    assert client.get("/admin/login/").status_code == 200
