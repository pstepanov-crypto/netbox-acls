"""
Defines each django model for the plugin.
"""

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from netbox.models import NetBoxModel, PrimaryModel
from utilities.querysets import RestrictedQuerySet

from .choices import (
    ACLActionChoices,
    ACLAssignmentDirectionChoices,
    ACLProtocolChoices,
    ACLRuleActionChoices,
    ACLTypeChoices,
)


class AccessList(NetBoxModel):
    """
    Defines an ACL bound to a Device, Virtual Chassis or Virtual Machine.
    """

    assigned_object_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.PROTECT,
        related_name="+",
        blank=True,
        null=True,
    )
    assigned_object_id = models.PositiveIntegerField(
        blank=True,
        null=True,
    )
    assigned_object = GenericForeignKey(
        ct_field="assigned_object_type",
        fk_field="assigned_object_id",
    )

    name = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
        help_text=_("The name uniqueness per device is case insensitive."),
    )
    type = models.CharField(
        max_length=30,
        choices=ACLTypeChoices,
        default=ACLTypeChoices.TYPE_STANDARD,
        verbose_name=_("Type"),
        help_text=_("Standard or extended ACL."),
    )
    default_action = models.CharField(
        max_length=30,
        choices=ACLActionChoices,
        default=ACLActionChoices.ACTION_DENY,
        verbose_name=_("Default Action"),
        help_text=_("The default behavior of the ACL."),
    )

    objects = RestrictedQuerySet.as_manager()

    class Meta:
        ordering = ("name", "assigned_object_type", "assigned_object_id")
        unique_together = (
            ("assigned_object_type", "assigned_object_id", "name"),
        )
        verbose_name = _("Access List")
        verbose_name_plural = _("Access Lists")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("plugins:netbox_acls:accesslist", args=[self.pk])

    def get_type_color(self):
        return ACLTypeChoices.colors.get(self.type)

    @property
    def device(self):
        from dcim.models import Device

        if isinstance(self.assigned_object, Device):
            return self.assigned_object
        return None

    @property
    def virtual_machine(self):
        from virtualization.models import VirtualMachine

        if isinstance(self.assigned_object, VirtualMachine):
            return self.assigned_object
        return None

    @property
    def virtual_chassis(self):
        from dcim.models import VirtualChassis

        if isinstance(self.assigned_object, VirtualChassis):
            return self.assigned_object
        return None

    @property
    def rule_count(self):
        if self.type == ACLTypeChoices.TYPE_STANDARD:
            return self.aclstandardrules.count()
        else:
            return self.aclextendedrules.count()


class ACLStandardRule(NetBoxModel):
    """
    Defines a Standard ACL rule.
    """

    access_list = models.ForeignKey(
        to=AccessList,
        on_delete=models.CASCADE,
        related_name="aclstandardrules",
        limit_choices_to={"type": ACLTypeChoices.TYPE_STANDARD},
    )
    index = models.PositiveIntegerField(
        verbose_name=_("Index"),
        help_text=_("Determines the order of the rule in the ACL processing. AKA Sequence Number."),
    )
    action = models.CharField(
        max_length=30,
        choices=ACLRuleActionChoices,
        verbose_name=_("Action"),
        help_text=_("Action the rule will take (remark, deny, or allow)."),
    )
    remark = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_("Remark"),
    )
    
    # ИЗМЕНЕНО: ForeignKey заменен на CharField
    source_prefix = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Source Prefix/Host"),
        help_text=_("IP prefix, network or host (e.g., 192.168.1.0/24, 192.168.1.0 255.255.255.0, host 10.1.1.1)"),
    )
    
    description = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Description"),
    )

    objects = RestrictedQuerySet.as_manager()

    class Meta:
        ordering = ("access_list", "index")
        unique_together = (
            ("access_list", "index"),
        )
        verbose_name = _("ACL Standard Rule")
        verbose_name_plural = _("ACL Standard Rules")

    def __str__(self):
        return f"{self.access_list.name} - {self.index}: {self.action}"

    def get_absolute_url(self):
        return reverse("plugins:netbox_acls:aclstandardrule", args=[self.pk])

    def clean(self):
        super().clean()

        if self.action == ACLRuleActionChoices.ACTION_REMARK and self.source_prefix:
            raise ValidationError(
                {"source_prefix": _("Source prefix must be empty when action is remark.")}
            )


class ACLExtendedRule(NetBoxModel):
    """
    Defines an Extended ACL rule.
    """

    access_list = models.ForeignKey(
        to=AccessList,
        on_delete=models.CASCADE,
        related_name="aclextendedrules",
        limit_choices_to={"type": ACLTypeChoices.TYPE_EXTENDED},
    )
    index = models.PositiveIntegerField(
        verbose_name=_("Index"),
        help_text=_("Determines the order of the rule in the ACL processing. AKA Sequence Number."),
    )
    action = models.CharField(
        max_length=30,
        choices=ACLRuleActionChoices,
        verbose_name=_("Action"),
        help_text=_("Action the rule will take (remark, deny, or allow)."),
    )
    remark = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_("Remark"),
    )
    
    # ИЗМЕНЕНО: ForeignKey заменен на CharField
    source_prefix = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Source Prefix/Host"),
        help_text=_("IP prefix, network or host (e.g., 192.168.1.0/24, 192.168.1.0 255.255.255.0, host 10.1.1.1)"),
    )
    
    # ИЗМЕНЕНО: ArrayField заменен на CharField
    source_ports = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Source Ports"),
        help_text=_("Port numbers or ranges (e.g., 80, 443, 1000-2000, eq www, range 445 1050)"),
    )
    
    # ИЗМЕНЕНО: ForeignKey заменен на CharField
    destination_prefix = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Destination Prefix/Host"),
        help_text=_("IP prefix, network or host (e.g., 192.168.1.0/24, 192.168.1.0 255.255.255.0, host 10.1.1.1)"),
    )
    
    # ИЗМЕНЕНО: ArrayField заменен на CharField
    destination_ports = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Destination Ports"),
        help_text=_("Port numbers or ranges (e.g., 80, 443, 1000-2000, eq www, range 445 1050)"),
    )
    
    protocol = models.CharField(
        max_length=30,
        choices=ACLProtocolChoices,
        blank=True,
        verbose_name=_("Protocol"),
        help_text=_("IP protocol (e.g., tcp, udp, icmp, ip)."),
    )
    
    description = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Description"),
    )

    objects = RestrictedQuerySet.as_manager()

    class Meta:
        ordering = ("access_list", "index")
        unique_together = (
            ("access_list", "index"),
        )
        verbose_name = _("ACL Extended Rule")
        verbose_name_plural = _("ACL Extended Rules")

    def __str__(self):
        return f"{self.access_list.name} - {self.index}: {self.action}"

    def get_absolute_url(self):
        return reverse("plugins:netbox_acls:aclextendedrule", args=[self.pk])

    def clean(self):
        super().clean()

        if self.action == ACLRuleActionChoices.ACTION_REMARK:
            fields_to_check = ["source_prefix", "source_ports", "destination_prefix", "destination_ports", "protocol"]
            for field in fields_to_check:
                if getattr(self, field):
                    raise ValidationError(
                        {field: _(f"Cannot set {field} when action is remark.")}
                    )


class ACLInterfaceAssignment(NetBoxModel):
    """
    Defines an ACL assignment to an interface.
    """

    assigned_object_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.PROTECT,
        related_name="+",
        blank=True,
        null=True,
    )
    assigned_object_id = models.PositiveIntegerField(
        blank=True,
        null=True,
    )
    assigned_object = GenericForeignKey(
        ct_field="assigned_object_type",
        fk_field="assigned_object_id",
    )

    access_list = models.ForeignKey(
        to=AccessList,
        on_delete=models.CASCADE,
        related_name="interface_assignments",
    )
    direction = models.CharField(
        max_length=30,
        choices=ACLAssignmentDirectionChoices,
        verbose_name=_("Direction"),
        help_text=_("Direction the ACL is applied (ingress or egress)."),
    )

    objects = RestrictedQuerySet.as_manager()

    class Meta:
        ordering = ("access_list", "direction", "assigned_object_type", "assigned_object_id")
        unique_together = (
            ("assigned_object_type", "assigned_object_id", "access_list", "direction"),
        )
        verbose_name = _("ACL Interface Assignment")
        verbose_name_plural = _("ACL Interface Assignments")

    def __str__(self):
        return f"{self.access_list} - {self.direction}"

    def get_absolute_url(self):
        return reverse("plugins:netbox_acls:aclinterfaceassignment", args=[self.pk])

    @property
    def interface(self):
        from dcim.models import Interface

        if isinstance(self.assigned_object, Interface):
            return self.assigned_object
        return None

    @property
    def vminterface(self):
        from virtualization.models import VMInterface

        if isinstance(self.assigned_object, VMInterface):
            return self.assigned_object
        return None

    def clean(self):
        super().clean()

        # Check that the interface's parent host matches the ACL's host
        if self.interface:
            host = self.interface.device
        elif self.vminterface:
            host = self.vminterface.virtual_machine
        else:
            raise ValidationError(_("Must assign to either an Interface or VMInterface."))

        if self.access_list.assigned_object != host:
            raise ValidationError(
                _("The ACL must be assigned to the same host as the interface.")
            )
