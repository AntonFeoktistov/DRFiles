from rest_framework import serializers

from storage.models import File, Folder
from storage.services import path_utils


class ResourceGetSerializer(serializers.Serializer):
    path = serializers.CharField(required=False, default="", allow_blank=True)


class ResourceResponseSerializer(serializers.Serializer):
    path = serializers.CharField()
    name = serializers.CharField()
    size = serializers.IntegerField(allow_null=True, required=False)
    type = serializers.CharField()

    def to_representation(self, instance):
        if isinstance(instance, Folder):
            name, parent_path = path_utils.get_name_and_parent_path(instance.full_path)
            return {"path": parent_path, "name": name, "type": "FOLDER"}
        elif isinstance(instance, File):
            name, parent_path = path_utils.get_name_and_parent_path(instance.full_path)
            return {
                "path": parent_path,
                "name": name,
                "size": instance.size,
                "type": "FILE",
            }
        return super().to_representation(instance)


class ResourceUploadSerializer(serializers.Serializer):
    path = serializers.CharField(required=False, default="", allow_blank=True)
    files = serializers.ListField(
        child=serializers.FileField(), required=True, write_only=True
    )

    def validate_files(self, value):
        if not value:
            raise serializers.ValidationError("No files provided")

        if len(value) > 100:
            raise serializers.ValidationError("Too many files (max 100)")

        max_size = 5 * 1024 * 1024
        for file in value:
            if file.size > max_size:
                raise serializers.ValidationError(
                    f"File '{file.name}' exceeds maximum size of 5MB"
                )

        return value
