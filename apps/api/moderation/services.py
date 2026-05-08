from django.contrib.auth import get_user_model

from .models import Block


User = get_user_model()


def get_blocked_user_ids(user) -> set:
    blocked_by_user = Block.objects.filter(user=user).values_list("blocked_user_id", flat=True)
    blocked_user = Block.objects.filter(blocked_user=user).values_list("user_id", flat=True)
    return set(blocked_by_user) | set(blocked_user)


def is_blocked_pair(first_user, second_user) -> bool:
    return Block.objects.filter(user=first_user, blocked_user=second_user).exists() or Block.objects.filter(
        user=second_user,
        blocked_user=first_user,
    ).exists()
