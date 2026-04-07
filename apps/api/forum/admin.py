from django.contrib import admin

from .models import ForumComment, ForumPost, ForumPostLike


@admin.register(ForumPost)
class ForumPostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "category", "is_deleted", "created_at")
    list_filter = ("category", "is_deleted")
    search_fields = ("title", "body", "author__email")


@admin.register(ForumComment)
class ForumCommentAdmin(admin.ModelAdmin):
    list_display = ("post", "author", "created_at")
    search_fields = ("post__title", "author__email", "body")


@admin.register(ForumPostLike)
class ForumPostLikeAdmin(admin.ModelAdmin):
    list_display = ("post", "user", "created_at")
    search_fields = ("post__title", "user__email")
