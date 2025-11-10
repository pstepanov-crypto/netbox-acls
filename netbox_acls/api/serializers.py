"""
Serializers control the translation of client data to and from Python objects,
while Django itself handles the database abstraction.
"""

from dcim.api.serializers import DeviceSerializer
from django.contrib.contenttypes.models import ContentType
from drf_spectacular.utils import extend_schema_field
from ipam.api.serializers import PrefixSerializer
from netbox.api.fields import ContentTypeField
from netbox.api.serializers import NetBoxModelSerializer
from rest_framework import serializers
from utilities.api import get_serializer_for_model

from ..constants import ACL_HOST_ASSIGNMENT_MODELS, ACL_INTERFACE_ASSIGNMENT_MODELS
from ..models import (
    AccessList,
    ACLExtendedRule,
    ACLInterfaceAssignment,
    ACLStandardRule,
)

__all__ = [
    "AccessListSerializer",
    "ACLInterfaceAssignmentSerializer",
    "ACLStandardRuleSerializer",
    "ACLExtendedRuleSerializer",
]

# Sets a standard error message for ACL rules with an action of remark, but no remark set.
error_message_no_remark = "Action is set to remark, you MUST add a remark."
# Sets a standard error message for ACL rules with an action of remark, but no source_prefix is set.
error_message_action_remark_source_prefix_set = "Action is set to remark, Source Prefix CANNOT be set."
# Sets a standard error message for ACL rules with an action not set to remark, but no remark is set.
error_message_remark_without_action_remark = "CANNOT set remark unless action is set to remark."
# Sets a standard error message for ACL rules no associated with an ACL of the same type.
error_message_acl_type = "Provided parent Access List is not of right type."
# Sets a standard error message for when both source_device and source_prefix are set.
error_message_source_device_and_prefix = "Cannot set both Source Device and Source Prefix."
# Sets a standard error message for when both destination_device and destination_prefix are set.
error_message_destination_device_and_prefix = "Cannot set both Destination Device and Destination Prefix."


class AccessListSerializer(NetBoxModelSerializer):
    """
    Defines the serializer for the django AccessList model and associates it with a view.
    """

    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_acls-api:accesslist-detail",
    )
    rule_count = serializers.IntegerField(read_only=True)
    assigned_object_type = ContentTypeField(
        queryset=ContentType.objects.filter(ACL_HOST_ASSIGNMENT_MODELS),
    )
    assigned_object = serializers.SerializerMethodField(read_only=True)

    class Meta:
        """
        Associates the django model AccessList & fields to the serializer.
        """

        model = AccessList
        fields = (
            "id",
            "url",
            "display",
            "name",
            "assigned_object_type",
            "assigned_object_id",
            "assigned_object",
            "type",
            "default_action",
            "comments",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
            "rule_count",
        )
        brief_fields = ("id", "url", "display", "name")

    @extend_schema_field(serializers.JSONField(allow_null=True))
    def get_assigned_object(self, obj):
        if obj.assigned_object is None:
            return None
        serializer = get_serializer_for_model(obj.assigned_object)
        context = {"request": self.context["request"]}
        return serializer(obj.assigned_object, nested=True, context=context).data

    def validate(self, data):
        """
        Validates api inputs before processing:
          - Check that the GFK object is valid.
          - Check if Access List has no existing rules before change the Access List's type.
        """
        error_message = {}

        # Check if Access List has no existing rules before change the Access List's type.
        if self.instance and self.instance.type != data.get("type") and self.instance.rule_count > 0:
            error_message["type"] = [
                "This ACL has ACL rules associated, CANNOT change ACL type.",
            ]

        if error_message:
            raise serializers.ValidationError(error_message)

        return super().validate(data)


class ACLInterfaceAssignmentSerializer(NetBoxModelSerializer):
    """
    Defines the serializer for the django ACLInterfaceAssignment model and associates it with a view.
    """

    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_acls-api:aclinterfaceassignment-detail",
    )
    access_list = AccessListSerializer(nested=True, required=True)
    assigned_object_type = ContentTypeField(
        queryset=ContentType.objects.filter(ACL_INTERFACE_ASSIGNMENT_MODELS),
    )
    assigned_object = serializers.SerializerMethodField(read_only=True)

    class Meta:
        """
        Associates the django model ACLInterfaceAssignment & fields to the serializer.
        """

        model = ACLInterfaceAssignment
        fields = (
            "id",
            "url",
            "display",
            "access_list",
            "direction",
            "assigned_object_type",
            "assigned_object_id",
            "assigned_object",
            "comments",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        )
        brief_fields = ("id", "url", "display", "access_list")

    @extend_schema_field(serializers.JSONField(allow_null=True))
    def get_assigned_object(self, obj):
        if obj.assigned_object is None:
            return None
        serializer = get_serializer_for_model(obj.assigned_object)
        context = {"request": self.context["request"]}
        return serializer(obj.assigned_object, nested=True, context=context).data

    def validate(self, data):
        """
        Validate the AccessList django model's inputs before allowing it to update the instance.
          - Check that the GFK object is valid.
          - Check that the associated interface's parent host has the selected ACL defined.
        """
        error_message = {}
        acl_host = data["access_list"].assigned_object

        if data["assigned_object_type"].model == "interface":
            interface_host = data["assigned_object_type"].get_object_for_this_type(id=data["assigned_object_id"]).device
        elif data["assigned_object_type"].model == "vminterface":
            interface_host = (
                data["assigned_object_type"].get_object_for_this_type(id=data["assigned_object_id"]).virtual_machine
            )
        else:
            interface_host = None
        # Check that the associated interface's parent host has the selected ACL defined.
        if acl_host != interface_host:
            error_acl_not_assigned_to_host = "Access List not present on the selected interface's host."
            error_message["access_list"] = [error_acl_not_assigned_to_host]
            error_message["assigned_object_id"] = [error_acl_not_assigned_to_host]

        if error_message:
            raise serializers.ValidationError(error_message)

        return super().validate(data)


class ACLStandardRuleSerializer(NetBoxModelSerializer):
    """
    Defines the serializer for the django ACLStandardRule model and associates it with a view.
    """

    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_acls-api:aclstandardrule-detail",
    )
    access_list = AccessListSerializer(nested=True, required=True)
    source_prefix = PrefixSerializer(
        nested=True,
        required=False,
        allow_null=True,
        default=None,
    )
    # Добавлено: сериализатор для устройства-источника
    source_device = DeviceSerializer(
        nested=True,
        required=False,
        allow_null=True,
        default=None,
    )
    # Добавлено: IP-адрес устройства-источника
    source_device_ip = serializers.SerializerMethodField(
        required=False,
        allow_null=True,
        read_only=True,
    )

    class Meta:
        """
        Associates the django model ACLStandardRule & fields to the serializer.
        """

        model = ACLStandardRule
        fields = (
            "id",
            "url",
            "display",
            "access_list",
            "index",
            "action",
            "remark",
            "source_prefix",
            "source_device",  # Добавлено
            "source_device_ip",  # Добавлено
            "description",
            "tags",
            "created",
            "custom_fields",
            "last_updated",
        )
        brief_fields = ("id", "url", "display", "access_list", "index")

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_source_device_ip(self, obj):
        """
        Returns the primary IP address of the source device.
        """
        if obj.source_device and obj.source_device.primary_ip:
            return str(obj.source_device.primary_ip.address.ip)
        return None

    def validate(self, data):
        """
        Validate the ACLStandardRule django model's inputs before allowing it to update the instance:
          - Check if action set to remark, but no remark set.
          - Check if action set to remark, but source_prefix set.
          - Check if both source_device and source_prefix are set.
        """
        error_message = {}

        # Check if both source_device and source_prefix are set.
        if data.get("source_device") and data.get("source_prefix"):
            error_message["source_device"] = [error_message_source_device_and_prefix]
            error_message["source_prefix"] = [error_message_source_device_and_prefix]

        if data.get("action") == "remark":
            # Check if action set to remark, but no remark set.
            if data.get("remark") is None:
                error_message["remark"] = [
                    error_message_no_remark,
                ]
            # Check if action set to remark, but source_prefix set.
            if data.get("source_prefix"):
                error_message["source_prefix"] = [
                    error_message_action_remark_source_prefix_set,
                ]
            # Check if action set to remark, but source_device set.
            if data.get("source_device"):
                error_message["source_device"] = [
                    "Action is set to remark, Source Device CANNOT be set.",
                ]

        if error_message:
            raise serializers.ValidationError(error_message)

        return super().validate(data)


class ACLExtendedRuleSerializer(NetBoxModelSerializer):
    """
    Defines the serializer for the django ACLExtendedRule model and associates it with a view.
    """

    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_acls-api:aclextendedrule-detail",
    )
    access_list = AccessListSerializer(nested=True, required=True)
    source_prefix = PrefixSerializer(
        nested=True,
        required=False,
        allow_null=True,
        default=None,
    )
    # Добавлено: сериализатор для устройства-источника
    source_device = DeviceSerializer(
        nested=True,
        required=False,
        allow_null=True,
        default=None,
    )
    # Добавлено: IP-адрес устройства-источника
    source_device_ip = serializers.SerializerMethodField(
        required=False,
        allow_null=True,
        read_only=True,
    )
    destination_prefix = PrefixSerializer(
        nested=True,
        required=False,
        allow_null=True,
        default=None,
    )
    # Добавлено: сериализатор для устройства-назначения
    destination_device = DeviceSerializer(
        nested=True,
        required=False,
        allow_null=True,
        default=None,
    )
    # Добавлено: IP-адрес устройства-назначения
    destination_device_ip = serializers.SerializerMethodField(
        required=False,
        allow_null=True,
        read_only=True,
    )

    class Meta:
        """
        Associates the django model ACLExtendedRule & fields to the serializer.
        """

        model = ACLExtendedRule
        fields = (
            "id",
            "url",
            "display",
            "access_list",
            "index",
            "action",
            "remark",
            "protocol",
            "source_prefix",
            "source_device",        # Добавлено
            "source_device_ip",     # Добавлено
            "source_ports",
            "destination_prefix",
            "destination_device",   # Добавлено
            "destination_device_ip", # Добавлено
            "destination_ports",
            "description",
            "tags",
            "created",
            "custom_fields",
            "last_updated",
        )
        brief_fields = ("id", "url", "display", "access_list", "index")

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_source_device_ip(self, obj):
        """
        Returns the primary IP address of the source device.
        """
        if obj.source_device and obj.source_device.primary_ip:
            return str(obj.source_device.primary_ip.address.ip)
        return None

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_destination_device_ip(self, obj):
        """
        Returns the primary IP address of the destination device.
        """
        if obj.destination_device and obj.destination_device.primary_ip:
            return str(obj.destination_device.primary_ip.address.ip)
        return None

    def validate(self, data):
        """
        Validate the ACLExtendedRule django model's inputs before allowing it to update the instance:
          - Check if action set to remark, but no remark set.
          - Check if action set to remark, but source_prefix set.
          - Check if action set to remark, but source_ports set.
          - Check if action set to remark, but destination_prefix set.
          - Check if action set to remark, but destination_ports set.
          - Check if action set to remark, but protocol set.
          - Check if both source_device and source_prefix are set.
          - Check if both destination_device and destination_prefix are set.
        """
        error_message = {}

        # Check if both source_device and source_prefix are set.
        if data.get("source_device") and data.get("source_prefix"):
            error_message["source_device"] = [error_message_source_device_and_prefix]
            error_message["source_prefix"] = [error_message_source_device_and_prefix]

        # Check if both destination_device and destination_prefix are set.
        if data.get("destination_device") and data.get("destination_prefix"):
            error_message["destination_device"] = [error_message_destination_device_and_prefix]
            error_message["destination_prefix"] = [error_message_destination_device_and_prefix]

        if data.get("action") == "remark":
            # Check if action set to remark, but no remark set.
            if data.get("remark") is None:
                error_message["remark"] = [
                    error_message_no_remark,
                ]
            # Check if action set to remark, but source_prefix set.
            if data.get("source_prefix"):
                error_message["source_prefix"] = [
                    error_message_action_remark_source_prefix_set,
                ]
            # Check if action set to remark, but source_device set.
            if data.get("source_device"):
                error_message["source_device"] = [
                    "Action is set to remark, Source Device CANNOT be set.",
                ]
            # Check if action set to remark, but source_ports set.
            if data.get("source_ports"):
                error_message["source_ports"] = [
                    "Action is set to remark, Source Ports CANNOT be set.",
                ]
            # Check if action set to remark, but destination_prefix set.
            if data.get("destination_prefix"):
                error_message["destination_prefix"] = [
                    "Action is set to remark, Destination Prefix CANNOT be set.",
                ]
            # Check if action set to remark, but destination_device set.
            if data.get("destination_device"):
                error_message["destination_device"] = [
                    "Action is set to remark, Destination Device CANNOT be set.",
                ]
            # Check if action set to remark, but destination_ports set.
            if data.get("destination_ports"):
                error_message["destination_ports"] = [
                    "Action is set to remark, Destination Ports CANNOT be set.",
                ]
            # Check if action set to remark, but protocol set.
            if data.get("protocol"):
                error_message["protocol"] = [
                    "Action is set to remark, Protocol CANNOT be set.",
                ]

        if error_message:
            raise serializers.ValidationError(error_message)

        return super().validate(data)
