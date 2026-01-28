# netbox_acls/migrations/0005_change_all_field_types.py
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('netbox_acls', '0004_netbox_acls'),
    ]

    operations = [
        # Изменяем тип полей префиксов
        migrations.AlterField(
            model_name='aclextendedrule',
            name='destination_prefix',
            field=models.CharField(
                blank=True,
                max_length=100,
                verbose_name='Destination Prefix/Host',
                help_text='IP prefix, network or host (e.g., 192.168.1.0/24, 192.168.1.0 255.255.255.0, host 10.1.1.1)',
            ),
        ),
        migrations.AlterField(
            model_name='aclextendedrule',
            name='source_prefix',
            field=models.CharField(
                blank=True,
                max_length=100,
                verbose_name='Source Prefix/Host',
                help_text='IP prefix, network or host (e.g., 192.168.1.0/24, 192.168.1.0 255.255.255.0, host 10.1.1.1)',
            ),
        ),
        migrations.AlterField(
            model_name='aclstandardrule',
            name='source_prefix',
            field=models.CharField(
                blank=True,
                max_length=100,
                verbose_name='Source Prefix/Host',
                help_text='IP prefix, network or host (e.g., 192.168.1.0/24, 192.168.1.0 255.255.255.0, host 10.1.1.1)',
            ),
        ),
        # Изменяем тип полей портов
        migrations.AlterField(
            model_name='aclextendedrule',
            name='destination_ports',
            field=models.CharField(
                blank=True,
                max_length=100,
                verbose_name='Destination Ports',
                help_text='Port numbers or ranges (e.g., 80, 443, 1000-2000, eq www, range 445 1050)',
            ),
        ),
        migrations.AlterField(
            model_name='aclextendedrule',
            name='source_ports',
            field=models.CharField(
                blank=True,
                max_length=100,
                verbose_name='Source Ports',
                help_text='Port numbers or ranges (e.g., 80, 443, 1000-2000, eq www, range 445 1050)',
            ),
        ),
    ]
