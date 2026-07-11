from rest_framework import serializers

from storage.models import File, Folder
from storage.services import utils


class ResourceResponseSerializer(serializers.Serializer):
    path = serializers.CharField()
    name = serializers.CharField()
    size = serializers.IntegerField(allow_null=True, required=False)
    type = serializers.CharField()

    def to_representation(self, instance):
        if isinstance(instance, Folder):
            name, parent_path = utils.get_name_and_parent_path(instance.full_path)
            return {"path": parent_path, "name": name, "type": "FOLDER"}
        elif isinstance(instance, File):
            name, parent_path = utils.get_name_and_parent_path(instance.full_path)
            return {
                "path": parent_path,
                "name": name,
                "size": instance.size,
                "type": "FILE",
            }
        return super().to_representation(instance)


class ResourceCreateSerializer(serializers.Serializer):
    path = serializers.CharField(required=False, default="")
    name = serializers.CharField()
    type = serializers.ChoiceField(choices=["FILE", "FOLDER"])
    file = serializers.FileField(required=False, write_only=True)

    def validate(self, data):
        if data["type"] == "FILE" and not data.get("file"):
            raise serializers.ValidationError("File is required for FILE type")

        if data["type"] == "FOLDER" and data.get("file"):
            raise serializers.ValidationError(
                "File should not be provided for FOLDER type"
            )

        return data

    def validate_name(self, value):
        forbidden = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]
        for char in forbidden:
            if char in value:
                raise serializers.ValidationError(
                    f"Name cannot contain character: {char}"
                )
        return value
