import pytest
from rest_framework.test import APIClient

from forum.models import ForumComment, ForumPost
from notifications.models import Notification


@pytest.mark.django_db
def test_forum_post_crud_comment_reply_and_like(user_factory):
    author = user_factory(email="forum-author@example.com", password="securepass123")
    reader = user_factory(email="forum-reader@example.com", password="securepass123")

    author_client = APIClient()
    reader_client = APIClient()

    author_login = author_client.post(
        "/api/v1/auth/login/",
        {"email": "forum-author@example.com", "password": "securepass123"},
        format="json",
    )
    reader_login = reader_client.post(
        "/api/v1/auth/login/",
        {"email": "forum-reader@example.com", "password": "securepass123"},
        format="json",
    )

    author_client.credentials(HTTP_AUTHORIZATION=f"Bearer {author_login.data['access']}")
    reader_client.credentials(HTTP_AUTHORIZATION=f"Bearer {reader_login.data['access']}")

    create_response = author_client.post(
        "/api/v1/forum/posts/",
        {
            "title": "2027 保研时间线互助帖",
            "body": "整理夏令营、预推免和材料准备节点，希望一起更新信息。",
            "category": "保研",
            "tags": ["保研", "时间线"],
        },
        format="json",
    )

    assert create_response.status_code == 201
    post_id = create_response.data["id"]

    list_response = reader_client.get("/api/v1/forum/posts/?q=时间线&category=保研")
    assert list_response.status_code == 200
    assert len(list_response.data) == 1
    assert list_response.data[0]["summary"]
    assert list_response.data[0]["is_liked"] is False
    assert list_response.data[0]["comment_count"] == 0

    comment_response = reader_client.post(
        f"/api/v1/forum/posts/{post_id}/comments/",
        {"body": "这个帖子很有用，我愿意一起补充。"},
        format="json",
    )
    assert comment_response.status_code == 201
    comment_id = comment_response.data["id"]

    reply_response = author_client.post(
        f"/api/v1/forum/posts/{post_id}/comments/",
        {"body": "欢迎一起整理。", "parent": comment_id},
        format="json",
    )
    assert reply_response.status_code == 201

    detail_response = reader_client.get(f"/api/v1/forum/posts/{post_id}/")
    assert detail_response.status_code == 200
    assert detail_response.data["comment_count"] == 2
    assert len(detail_response.data["comments"]) == 1
    assert len(detail_response.data["comments"][0]["replies"]) == 1

    like_response = reader_client.post(f"/api/v1/forum/posts/{post_id}/like/")
    assert like_response.status_code == 200
    assert like_response.data == {"liked": True, "like_count": 1}
    assert Notification.objects.filter(recipient=author, type=Notification.Type.FORUM_LIKE).count() == 1

    liked_detail_response = reader_client.get(f"/api/v1/forum/posts/{post_id}/")
    assert liked_detail_response.status_code == 200
    assert liked_detail_response.data["is_liked"] is True
    assert liked_detail_response.data["like_count"] == 1

    assert Notification.objects.filter(recipient=author, type=Notification.Type.FORUM_COMMENT).count() == 1
    assert Notification.objects.filter(recipient=reader, type=Notification.Type.FORUM_REPLY).count() == 1

    update_response = author_client.patch(
        f"/api/v1/forum/posts/{post_id}/",
        {"title": "2027 保研时间线共建帖"},
        format="json",
    )
    assert update_response.status_code == 200
    assert update_response.data["title"] == "2027 保研时间线共建帖"

    forbidden_update = reader_client.patch(
        f"/api/v1/forum/posts/{post_id}/",
        {"title": "我来改标题"},
        format="json",
    )
    assert forbidden_update.status_code == 403

    mine_response = author_client.get("/api/v1/forum/posts/mine/")
    assert mine_response.status_code == 200
    assert len(mine_response.data) == 1
    assert mine_response.data[0]["id"] == post_id

    delete_response = author_client.delete(f"/api/v1/forum/posts/{post_id}/")
    assert delete_response.status_code == 204

    post = ForumPost.objects.get(id=post_id)
    assert post.is_deleted is True

    deleted_list_response = reader_client.get("/api/v1/forum/posts/")
    assert deleted_list_response.status_code == 200
    assert deleted_list_response.data == []


@pytest.mark.django_db
def test_forum_comment_parent_must_belong_to_same_post(user_factory):
    author = user_factory(email="forum-parent@example.com", password="securepass123")
    author_client = APIClient()
    login_response = author_client.post(
        "/api/v1/auth/login/",
        {"email": "forum-parent@example.com", "password": "securepass123"},
        format="json",
    )
    author_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")

    first_post = author_client.post(
        "/api/v1/forum/posts/",
        {"title": "A 帖子", "body": "A 帖子正文足够长。", "category": "论坛", "tags": []},
        format="json",
    )
    second_post = author_client.post(
        "/api/v1/forum/posts/",
        {"title": "B 帖子", "body": "B 帖子正文足够长。", "category": "论坛", "tags": []},
        format="json",
    )

    top_comment_response = author_client.post(
        f"/api/v1/forum/posts/{first_post.data['id']}/comments/",
        {"body": "第一条评论"},
        format="json",
    )
    parent_comment = ForumComment.objects.get(id=top_comment_response.data["id"])

    invalid_reply = author_client.post(
        f"/api/v1/forum/posts/{second_post.data['id']}/comments/",
        {"body": "错误回复", "parent": str(parent_comment.id)},
        format="json",
    )

    assert invalid_reply.status_code == 400
    assert "parent" in invalid_reply.data
