"""
Defines each django model's GUI filter/search options.
"""

from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from ipam.models import Prefix
from netbox.filtersets import NetBoxModelFilterSet
from tenancy.filtersets import TenancyFilterSet
from utilities.filters import MultiValueCharFilter, MultiValueNumberFilter

from .choices import ACLActionChoices, ACLDirectionChoices, ACLTypeChoices
from .models import (
    AccessList,
    ACLExtendedRule,
    ACLInterfaceAssignment,
    ACLStandardRule,
)


class AccessListFilterSet(NetBoxModelFilterSet, TenancyFilterSet):
    """FilterSet for AccessList model."""

    type = MultiValueCharFilter(
        field_name="type",
    )
    default_action = MultiValueCharFilter(
        field_name="default_action",
    )
    device_id = MultiValueNumberFilter(
        field_name="device__id",
    )
    device = MultiValueCharFilter(
        field_name="device__name",
        label="Device (name)",
    )
    virtual_machine_id = MultiValueNumberFilter(
        field_name="virtual_machine__id",
    )
    virtual_machine = MultiValueCharFilter(
        field_name="virtual_machine__name",
        label="Virtual Machine (name)",
    )
    virtual_chassis_id = MultiValueNumberFilter(
        field_name="virtual_chassis__id",
    )

    class Meta:
        model = AccessList
        fields = ("id", "name", "type", "default_action")

    def search(self, queryset, name, value):
        """Search across AccessList fields."""
        if not value.strip():
            return queryset
        qs_filter = Q(name__icontains=value) | Q(comments__icontains=value)
        return queryset.filter(qs_filter).distinct()


class ACLInterfaceAssignmentFilterSet(NetBoxModelFilterSet):
    """FilterSet for ACLInterfaceAssignment model."""

    access_list_id = MultiValueNumberFilter(
        field_name="access_list__id",
    )
    access_list = MultiValueCharFilter(
        field_name="access_list__name",
        label="Access List (name)",
    )
    direction = MultiValueCharFilter(
        field_name="direction",
    )
    device_id = MultiValueNumberFilter(
        field_name="assigned_object__device__id",
    )
    device = MultiValueCharFilter(
        field_name="assigned_object__device__name",
        label="Device (name)",
    )
    interface_id = MultiValueNumberFilter(
        field_name="assigned_object__id",
    )
    interface = MultiValueCharFilter(
        field_name="assigned_object__name",
        label="Interface (name)",
    )
    virtual_machine_id = MultiValueNumberFilter(
        field_name="assigned_object__virtual_machine__id",
    )
    virtual_machine = MultiValueCharFilter(
        field_name="assigned_object__virtual_machine__name",
        label="Virtual Machine (name)",
    )
    vminterface_id = MultiValueNumberFilter(
        field_name="assigned_object__id",
    )
    vminterface = MultiValueCharFilter(
        field_name="assigned_object__name",
        label="VM Interface (name)",
    )

    class Meta:
        model = ACLInterfaceAssignment
        fields = ("id", "access_list", "direction")

    def search(self, queryset, name, value):
        """Search across ACLInterfaceAssignment fields."""
        if not value.strip():
            return queryset
        qs_filter = Q(access_list__name__icontains=value) | Q(
            assigned_object__name__icontains=value
        )
        return queryset.filter(qs_filter).distinct()


class ACLStandardRuleFilterSet(NetBoxModelFilterSet):
    """FilterSet for ACLStandardRule model."""

    access_list_id = MultiValueNumberFilter(
        field_name="access_list__id",
    )
    access_list = MultiValueCharFilter(
        field_name="access_list__name",
        label="Access List (name)",
    )
    action = MultiValueCharFilter(
        field_name="action",
    )
    index = MultiValueNumberFilter(
        field_name="index",
    )
    source_prefix = MultiValueCharFilter(
        field_name="source_prefix",
        label="Source Prefix",
    )

    class Meta:
        model = ACLStandardRule
        fields = ("id", "access_list", "action", "index", "remark", "source_prefix")

    def search(self, queryset, name, value):
        """Search across ACLStandardRule fields."""
        if not value.strip():
            return queryset
        qs_filter = (
            Q(access_list__name__icontains=value)
            | Q(remark__icontains=value)
            | Q(source_prefix__icontains=value)
            | Q(description__icontains=value)
        )
        return queryset.filter(qs_filter).distinct()


class ACLExtendedRuleFilterSet(NetBoxModelFilterSet):
    """FilterSet for ACLExtendedRule model."""

    access_list_id = MultiValueNumberFilter(
        field_name="access_list__id",
    )
    access_list = MultiValueCharFilter(
        field_name="access_list__name",
        label="Access List (name)",
    )
    action = MultiValueCharFilter(
        field_name="action",
    )
    index = MultiValueNumberFilter(
        field_name="index",
    )
    protocol = MultiValueCharFilter(
        field_name="protocol",
    )
    source_prefix = MultiValueCharFilter(
        field_name="source_prefix",
        label="Source Prefix",
    )
    destination_prefix = MultiValueCharFilter(
        field_name="destination_prefix",
        label="Destination Prefix",
    )
    source_ports = MultiValueCharFilter(
        field_name="source_ports",
        label="Source Ports",
    )
    destination_ports = MultiValueCharFilter(
        field_name="destination_ports",
        label="Destination Ports",
    )

    class Meta:
        model = ACLExtendedRule
        fields = (
            "id",
            "access_list",
            "action",
            "index",
            "remark",
            "protocol",
            "source_prefix",
            "destination_prefix",
            "source_ports",
            "destination_ports",
        )

    def search(self, queryset, name, value):
        """Search across ACLExtendedRule fields."""
        if not value.strip():
            return queryset
        qs_filter = (
            Q(access_list__name__icontains=value)
            | Q(remark__icontains=value)
            | Q(source_prefix__icontains=value)
            | Q(destination_prefix__icontains=value)
            | Q(source_ports__icontains=value)
            | Q(destination_ports__icontains=value)
            | Q(description__icontains=value)
        )
        return queryset.filter(qs_filter).distinct()
