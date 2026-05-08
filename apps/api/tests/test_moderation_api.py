import pytest
from rest_framework.test import APIClient

from forum.models import ForumComment, ForumPost
from moderation.models import Report


@pytest.mark.django_db
def test_admin_can_list_review_and_delete_report_target(user_factory):
    reporter = user_factory(email="reporter@example.com", password="securepass123")
    post_author = user_factory(email="post-author@example.com", password="securepass123")
    admin = user_factory(
        email="admin@example.com",
        password="securepass123",
        role="admin",
        is_staff=True,
    )

    post = ForumPost.objects.create(
        author=post_author,
        title="Need moderation",
        body="This is a test forum post.",
        category="test",
        tags=[],
    )
    report = Report.objects.create(
        reporter=reporter,
        target_type=Report.TargetType.FORUM_POST,
        target_id=post.id,
        reason="Spam",
        details="Looks suspicious",
    )

    admin_client = APIClient()
    login_response = admin_client.post(
        "/api/v1/auth/login/",
        {"email": "admin@example.com", "password": "securepass123"},
        format="json",
    )
    admin_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")

    stats_response = admin_client.get("/api/v1/moderation/admin/reports/stats/")
    assert stats_response.status_code == 200
    assert stats_response.data["all"] == 1
    assert stats_response.data["open"] == 1

    list_response = admin_client.get("/api/v1/moderation/admin/reports/")
    assert list_response.status_code == 200
    assert len(list_response.data) == 1
    assert list_response.data[0]["id"] == str(report.id)
    assert list_response.data[0]["target_snapshot"]["label"] == "Need moderation"

    review_response = admin_client.patch(
        f"/api/v1/moderation/admin/reports/{report.id}/",
        {"status": "resolved", "action": "delete_forum_post"},
        format="json",
    )
    assert review_response.status_code == 200

    report.refresh_from_db()
    post.refresh_from_db()
    assert report.status == Report.Status.RESOLVED
    assert post.is_deleted is True


@pytest.mark.django_db
def test_non_admin_cannot_access_admin_report_api(user_factory):
    user = user_factory(email="user@example.com", password="securepass123")
    Report.objects.create(
        reporter=user,
        target_type=Report.TargetType.USER,
        target_id=user.id,
        reason="Test",
        details="Test details",
    )

    client = APIClient()
    login_response = client.post(
        "/api/v1/auth/login/",
        {"email": "user@example.com", "password": "securepass123"},
        format="json",
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")

    response = client.get("/api/v1/moderation/admin/reports/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_can_delete_reported_comment(user_factory):
    reporter = user_factory(email="comment-reporter@example.com", password="securepass123")
    post_author = user_factory(email="comment-author@example.com", password="securepass123")
    admin = user_factory(
        email="comment-admin@example.com",
        password="securepass123",
        role="admin",
        is_staff=True,
    )

    post = ForumPost.objects.create(
        author=post_author,
        title="Reported comment post",
        body="Post body",
        category="test",
        tags=[],
    )
    comment = ForumComment.objects.create(
        post=post,
        author=post_author,
        body="This comment should be removed by admin review.",
    )
    report = Report.objects.create(
        reporter=reporter,
        target_type=Report.TargetType.COMMENT,
        target_id=comment.id,
        reason="Harassment",
        details="Comment is abusive",
    )

    admin_client = APIClient()
    login_response = admin_client.post(
        "/api/v1/auth/login/",
        {"email": "comment-admin@example.com", "password": "securepass123"},
        format="json",
    )
    admin_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")

    list_response = admin_client.get("/api/v1/moderation/admin/reports/?target_type=comment")
    assert list_response.status_code == 200
    assert len(list_response.data) == 1
    assert list_response.data[0]["id"] == str(report.id)
    assert "This comment should be removed" in list_response.data[0]["target_snapshot"]["label"]

    review_response = admin_client.patch(
        f"/api/v1/moderation/admin/reports/{report.id}/",
        {"status": "resolved", "action": "delete_forum_comment"},
        format="json",
    )
    assert review_response.status_code == 200

    report.refresh_from_db()
    assert report.status == Report.Status.RESOLVED
    assert ForumComment.objects.filter(id=comment.id).exists() is False
