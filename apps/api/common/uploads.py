from pathlib import Path

from rest_framework import serializers


ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
ALLOWED_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
DEFAULT_IMAGE_MAX_SIZE = 5 * 1024 * 1024


def validate_uploaded_image(upload, *, max_size=DEFAULT_IMAGE_MAX_SIZE, label="图片"):
    if upload is None:
        raise serializers.ValidationError(f"请上传{label}文件。")

    extension = Path(upload.name or "").suffix.lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        allowed = "、".join(sorted(ALLOWED_IMAGE_EXTENSIONS))
        raise serializers.ValidationError(f"{label}格式不支持，请上传 {allowed} 格式。")

    content_type = (getattr(upload, "content_type", "") or "").lower()
    if content_type and content_type != "application/octet-stream" and content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise serializers.ValidationError(f"{label}类型不支持，请重新选择图片。")

    size = getattr(upload, "size", 0) or 0
    if size > max_size:
        max_mb = max_size // 1024 // 1024
        raise serializers.ValidationError(f"{label}不能超过 {max_mb}MB。")

    return upload
