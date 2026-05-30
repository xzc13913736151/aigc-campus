import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_forum_post_list_endpoint_is_available():
    client = APIClient()
    response = client.get("/api/v1/forum/posts/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
