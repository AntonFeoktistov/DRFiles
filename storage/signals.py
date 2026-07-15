from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from storage.models import Folder


@receiver(post_save, sender=User)
def create_user_root_folder(sender, instance, created, **kwargs):
    if created:
        Folder.objects.get_or_create(
            user=instance, full_path="", defaults={"name": "", "folder": None}
        )
