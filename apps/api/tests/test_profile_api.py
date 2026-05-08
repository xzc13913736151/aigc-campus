import pytest
from django.core.files.uploadedfile import SimpleUploadedFile


def make_test_image(name: str = "avatar.png") -> SimpleUploadedFile:
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT\x08\xd7c\xf8\xcf"
        b"\xc0\x00\x00\x03\x01\x01\x00\xc9\xfe\x92\xef\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    return SimpleUploadedFile(name, png_bytes, content_type="image/png")


@pytest.mark.django_db
def test_profile_me_can_update_nickname(api_client, user_factory):
    user = user_factory(email="profile@example.com", password="securepass123", nickname="old-name")
    api_client.force_authenticate(user=user)

    response = api_client.put(
        "/api/v1/profile/me/",
        {
            "nickname": "new-name",
            "avatar_url": "",
            "headline": "AI product builder",
            "bio": "",
            "gender": "unknown",
            "major": "Computer Science",
            "grade": "2023",
            "interests": ["AI"],
        },
        format="json",
    )

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.nickname == "new-name"
    assert response.data["nickname"] == "new-name"
    assert response.data["user"]["nickname"] == "new-name"


@pytest.mark.django_db
def test_profile_avatar_upload_updates_avatar_url(api_client, user_factory):
    user = user_factory(email="avatar@example.com", password="securepass123")
    api_client.force_authenticate(user=user)

    response = api_client.post(
        "/api/v1/profile/me/avatar/",
        {"file": make_test_image()},
        format="multipart",
    )

    assert response.status_code == 200
    user.profile.refresh_from_db()
    assert "/media/avatars/" in user.profile.avatar_url
    assert response.data["avatar_url"] == user.profile.avatar_url
