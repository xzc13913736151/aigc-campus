import pytest
from rest_framework.test import APIClient

from notifications.models import Notification
from teammates.models import TeamApplication, TeamPost


@pytest.mark.django_db
def test_team_post_list_allows_empty_public_result():
    client = APIClient()

    response = client.get("/api/v1/teammates/posts/")

    assert response.status_code == 200
    assert response.data == []


@pytest.mark.django_db
def test_team_post_creation_application_and_acceptance(user_factory):
    author = user_factory(email="author@example.com", password="securepass123")
    applicant = user_factory(email="applicant@example.com", password="securepass123")

    author_client = APIClient()
    applicant_client = APIClient()

    author_login = author_client.post(
        "/api/v1/auth/login/",
        {"email": "author@example.com", "password": "securepass123"},
        format="json",
    )
    applicant_login = applicant_client.post(
        "/api/v1/auth/login/",
        {"email": "applicant@example.com", "password": "securepass123"},
        format="json",
    )

    author_client.credentials(HTTP_AUTHORIZATION=f"Bearer {author_login.data['access']}")
    applicant_client.credentials(HTTP_AUTHORIZATION=f"Bearer {applicant_login.data['access']}")

    post_response = author_client.post(
        "/api/v1/teammates/posts/",
        {
            "title": "招募 AI 校园工具项目成员",
            "summary": "想找 2 位同学一起做可上线的校园效率工具。",
            "details": "项目已经有基础方向，希望补齐前端和设计同学，一起快速做出首个可用版本。",
            "target_size": 3,
            "tags": ["AI", "校园工具"],
            "required_skills": ["前端", "设计"],
        },
        format="json",
    )

    assert post_response.status_code == 201
    post = TeamPost.objects.get(id=post_response.data["id"])

    apply_response = applicant_client.post(
        f"/api/v1/teammates/posts/{post.id}/apply/",
        {"message": "我能负责前端开发，也有一定产品经验。"},
        format="json",
    )
    assert apply_response.status_code == 201
    assert Notification.objects.filter(recipient=author, type=Notification.Type.TEAM_APPLICATION_CREATED).count() == 1

    application = TeamApplication.objects.get(post=post, applicant=applicant)
    review_response = author_client.patch(
        f"/api/v1/teammates/applications/{application.id}/review/",
        {"status": "accepted"},
        format="json",
    )

    assert review_response.status_code == 200
    application.refresh_from_db()
    post.refresh_from_db()

    assert application.status == TeamApplication.Status.ACCEPTED
    assert post.current_size == 2
    assert Notification.objects.filter(recipient=applicant, type=Notification.Type.TEAM_APPLICATION_ACCEPTED).count() == 1
