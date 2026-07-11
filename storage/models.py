from django.contrib.auth.models import User
from django.db import models


class Folder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="folders")
    name = models.CharField(max_length=255)
    folder = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subfolders",
    )
    full_path = models.CharField(max_length=1024, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class File(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name="files"
    )
    name = models.CharField(max_length=255)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name="files")
    full_path = models.CharField(max_length=255)
    size = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
