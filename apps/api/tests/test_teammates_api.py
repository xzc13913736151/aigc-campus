import pytest
from rest_framework.test import APIClient

from teammates.models import TeamApplication, TeamPost


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
            "title": "寻找保研项目队友",
            "summary": "希望找 2 位同学一起冲夏令营材料。",
            "details": "我负责产品和材料，想找算法或前端方向同学一起做校园项目。",
            "target_size": 3,
            "tags": ["保研", "产品"],
            "required_skills": ["算法", "前端"],
        },
        format="json",
    )

    assert post_response.status_code == 201
    post = TeamPost.objects.get(id=post_response.data["id"])

    apply_response = applicant_client.post(
        f"/api/v1/teammates/posts/{post.id}/apply/",
        {"message": "我可以负责前端实现。"},
        format="json",
    )
    assert apply_response.status_code == 201

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
