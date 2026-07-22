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
            return {"path": parent_path, "name": name, "type": "DIRECTORY"}
        elif isinstance(instance, File):
            name, parent_path = path_utils.get_name_and_parent_path(instance.full_path)
            return {
                "path": parent_path,
                "name": name,
                "size": instance.size,
                "type": "FILE",
            }
        return super().to_representation(instance)
