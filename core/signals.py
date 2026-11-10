from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserProfile

User = get_user_model()

@receiver(post_save, sender=User)
def ensure_gym_profile(sender, instance, created, **kwargs):
    if created:
        role = "owner" if instance.is_superuser or instance.is_staff else "member"
        UserProfile.objects.get_or_create(user=instance, defaults={"role": role})
    elif instance.is_superuser:
        profile, _ = UserProfile.objects.get_or_create(user=instance, defaults={"role":"owner"})
        if profile.role != "owner":
            profile.role = "owner"
            profile.save(update_fields=["role"])
