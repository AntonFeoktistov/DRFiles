from rest_framework import serializers

from storage.models import File, Folder
from storage.services import utils


class ResourceGetSerializer(serializers.Serializer):
    path = serializers.CharField(required=False, default="", allow_blank=True)

    def validate_path(self, value):
        if value and not isinstance(value, str):
            raise serializers.ValidationError("Path must be a string")
        return value.strip()


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
    name = serializers.CharField(max_length=255)
    type = serializers.ChoiceField(choices=["FILE", "FOLDER"])
    file = serializers.FileField(required=False, write_only=True)

    def validate(self, data):
        if data["type"] == "FILE" and not data.get("file"):
            raise serializers.ValidationError(
                {"file": "File is required for FILE type"}
            )

        if data["type"] == "FOLDER" and data.get("file"):
            raise serializers.ValidationError(
                {"file": "File should not be provided for FOLDER type"}
            )

        forbidden = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]
        name = data.get("name", "")
        for char in forbidden:
            if char in name:
                raise serializers.ValidationError(
                    {"name": f"Name cannot contain character: {char}"}
                )

        return data


class ResourceRenameSerializer(serializers.Serializer):
    old_path = serializers.CharField()
    new_name = serializers.CharField(max_length=255)

    def validate_new_name(self, value):
        forbidden = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]
        for char in forbidden:
            if char in value:
                raise serializers.ValidationError(
                    f"Name cannot contain character: {char}"
                )
        return value

    def validate(self, data):
        if data["old_path"] == data["new_name"]:
            raise serializers.ValidationError(
                {"new_name": "New name must be different from old name"}
            )
        return data
