"""
Defines each django model's GUI form to add or edit objects for each django model.
"""

from dcim.models import Device, Interface, Region, Site, SiteGroup, VirtualChassis
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from ipam.models import Prefix
from netbox.forms import NetBoxModelForm
from utilities.forms.fields import CommentField, DynamicModelChoiceField
from utilities.forms.rendering import FieldSet, TabbedGroups
from virtualization.models import (
    Cluster,
    ClusterGroup,
    ClusterType,
    VirtualMachine,
    VMInterface,
)

from ..choices import ACLTypeChoices
from ..models import (
    AccessList,
    ACLExtendedRule,
    ACLInterfaceAssignment,
    ACLStandardRule,
)

__all__ = (
    "AccessListForm",
    "ACLInterfaceAssignmentForm",
    "ACLStandardRuleForm",
    "ACLExtendedRuleForm",
)

help_text_acl_rule_logic = mark_safe(
    "<b>*Note:</b> CANNOT be set if action is set to remark.",
)
help_text_acl_action = "Action the rule will take (remark, deny, or allow)."
help_text_acl_rule_index = "Determines the order of the rule in the ACL processing. AKA Sequence Number."
help_text_acl_ports = "Port numbers or ranges (e.g., 80, 443, 1000-2000, eq www, range 445 1050)"
help_text_acl_prefix = "IP prefix, network or host (e.g., 192.168.1.0/24, host 10.1.1.1)"


class AccessListForm(NetBoxModelForm):

    region = DynamicModelChoiceField(
        queryset=Region.objects.all(),
        required=False,
        initial_params={"sites": "$site"},
    )
    site_group = DynamicModelChoiceField(
        queryset=SiteGroup.objects.all(),
        required=False,
        label="Site Group",
        initial_params={"sites": "$site"},
    )
    site = DynamicModelChoiceField(
        queryset=Site.objects.all(),
        required=False,
        query_params={"region_id": "$region", "group_id": "$site_group"},
    )
    device = DynamicModelChoiceField(
        queryset=Device.objects.all(),
        required=False,
        query_params={
            "region_id": "$region",
            "group_id": "$site_group",
            "site_id": "$site",
        },
    )

    virtual_chassis = DynamicModelChoiceField(
        queryset=VirtualChassis.objects.all(),
        required=False,
        label="Virtual Chassis",
    )

    cluster_type = DynamicModelChoiceField(
        queryset=ClusterType.objects.all(),
        required=False,
    )
    cluster_group = DynamicModelChoiceField(
        queryset=ClusterGroup.objects.all(),
        required=False,
        query_params={"type_id": "$cluster_type"},
    )
    cluster = DynamicModelChoiceField(
        queryset=Cluster.objects.all(),
        required=False,
        query_params={"type_id": "$cluster_type", "group_id": "$cluster_group"},
    )

    virtual_machine = DynamicModelChoiceField(
        queryset=VirtualMachine.objects.all(),
        required=False,
        query_params={
            "cluster_id": "$cluster",
            "cluster_type_id": "$cluster_type",
            "cluster_group_id": "$cluster_group",
        },
    )

    comments = CommentField()

    fieldsets = (
        FieldSet(
            "name",
            "type",
            "default_action",
            "tags",
            name=_("Access List Details"),
        ),
        FieldSet(
            TabbedGroups(
                FieldSet("region", "site_group", "site", "device", name=_("Device")),
                FieldSet("virtual_chassis", name=_("Virtual Chassis")),
                FieldSet(
                    "cluster_type",
                    "cluster_group",
                    "cluster",
                    "virtual_machine",
                    name=_("Virtual Machine"),
                ),
            ),
            name=_("Host Assignment"),
        ),
    )

    class Meta:
        model = AccessList
        fields = (
            "region",
            "site_group",
            "site",
            "device",
            "virtual_machine",
            "virtual_chassis",
            "name",
            "type",
            "default_action",
            "comments",
            "tags",
        )

        help_texts = {
            "default_action": "The default behavior of the ACL.",
            "name": "The name uniqueness per device is case insensitive.",
            "type": mark_safe(
                "<b>*Note:</b> CANNOT be changed if ACL Rules are associated to this Access List.",
            ),
        }

    def clean(self):
        super().clean()

        device = self.cleaned_data.get("device")
        virtual_chassis = self.cleaned_data.get("virtual_chassis")
        virtual_machine = self.cleaned_data.get("virtual_machine")

        if sum(bool(x) for x in (device, virtual_chassis, virtual_machine)) != 1:
            raise ValidationError(
                "__all__",
                "Access Lists must be assigned to exactly one host.",
            )

    def save(self, *args, **kwargs):
        self.instance.assigned_object = (
            self.cleaned_data.get("device")
            or self.cleaned_data.get("virtual_chassis")
            or self.cleaned_data.get("virtual_machine")
        )
        return super().save(*args, **kwargs)


class ACLInterfaceAssignmentForm(NetBoxModelForm):

    device = DynamicModelChoiceField(
        queryset=Device.objects.all(),
        required=False,
    )
    interface = DynamicModelChoiceField(
        queryset=Interface.objects.all(),
        required=False,
        query_params={"device_id": "$device"},
    )
    virtual_machine = DynamicModelChoiceField(
        queryset=VirtualMachine.objects.all(),
        required=False,
        label="Virtual Machine",
    )
    vminterface = DynamicModelChoiceField(
        queryset=VMInterface.objects.all(),
        required=False,
        query_params={"virtual_machine_id": "$virtual_machine"},
        label="VM Interface",
    )

    access_list = DynamicModelChoiceField(
        queryset=AccessList.objects.all(),
        label="Access List",
    )

    comments = CommentField()

    fieldsets = (
        FieldSet("access_list", "direction", "tags", name=_("Access List Details")),
        FieldSet(
            TabbedGroups(
                FieldSet("device", "interface", name=_("Device")),
                FieldSet("virtual_machine", "vminterface", name=_("Virtual Machine")),
            ),
            name=_("Interface Assignment"),
        ),
    )

    class Meta:
        model = ACLInterfaceAssignment
        fields = (
            "access_list",
            "direction",
            "device",
            "interface",
            "virtual_machine",
            "vminterface",
            "comments",
            "tags",
        )

    def clean(self):
        super().clean()

        interface = self.cleaned_data.get("interface")
        vminterface = self.cleaned_data.get("vminterface")

        if bool(interface) == bool(vminterface):
            raise ValidationError(
                "Specify exactly one interface (physical or VM interface)."
            )

    def save(self, *args, **kwargs):
        self.instance.assigned_object = self.cleaned_data.get(
            "interface"
        ) or self.cleaned_data.get("vminterface")
        return super().save(*args, **kwargs)


class ACLStandardRuleForm(NetBoxModelForm):

    access_list = DynamicModelChoiceField(
        queryset=AccessList.objects.all(),
        query_params={"type": ACLTypeChoices.TYPE_STANDARD},
        label="Access List",
    )

    source_prefix = forms.CharField(
        required=False,
        max_length=100,
        label="Source Prefix",
        help_text=help_text_acl_prefix,
    )

    fieldsets = (
        FieldSet("access_list", "description", "tags", name=_("Access List Details")),
        FieldSet(
            "index",
            "action",
            "remark",
            "source_prefix",
            name=_("Rule Definition"),
        ),
    )

    class Meta:
        model = ACLStandardRule
        fields = (
            "access_list",
            "index",
            "action",
            "remark",
            "source_prefix",
            "tags",
            "description",
        )


class ACLExtendedRuleForm(NetBoxModelForm):

    access_list = DynamicModelChoiceField(
        queryset=AccessList.objects.all(),
        query_params={"type": ACLTypeChoices.TYPE_EXTENDED},
        label="Access List",
    )

    source_prefix = forms.CharField(
        required=False,
        max_length=100,
        label="Source Prefix",
        help_text=help_text_acl_prefix,
    )
    source_ports = forms.CharField(
        required=False,
        max_length=100,
        label="Source Ports",
        help_text=help_text_acl_ports,
    )
    destination_prefix = forms.CharField(
        required=False,
        max_length=100,
        label="Destination Prefix",
        help_text=help_text_acl_prefix,
    )
    destination_ports = forms.CharField(
        required=False,
        max_length=100,
        label="Destination Ports",
        help_text=help_text_acl_ports,
    )

    fieldsets = (
        FieldSet("access_list", "description", "tags", name=_("Access List Details")),
        FieldSet(
            "index",
            "action",
            "remark",
            "source_prefix",
            "source_ports",
            "destination_prefix",
            "destination_ports",
            "protocol",
            name=_("Rule Definition"),
        ),
    )

    class Meta:
        model = ACLExtendedRule
        fields = (
            "access_list",
            "index",
            "action",
            "remark",
            "source_prefix",
            "source_ports",
            "destination_prefix",
            "destination_ports",
            "protocol",
            "tags",
            "description",
        )
