# netbox_acls/migrations/0005_fix_prefix_fields.py
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('netbox_acls', '0004_netbox_acls'),
    ]

    operations = [
        # ТОЛЬКО добавляем новые CharField поля
        migrations.AddField(
            model_name='aclextendedrule',
            name='destination_prefix',
            field=models.CharField(
                blank=True,
                max_length=100,
                verbose_name='Destination Prefix/Host',
                help_text='IP prefix, network or host (e.g., 192.168.1.0/24, 192.168.1.0 255.255.255.0, host 10.1.1.1)'
            ),
        ),
        migrations.AddField(
            model_name='aclextendedrule',
            name='source_prefix',
            field=models.CharField(
                blank=True,
                max_length=100,
                verbose_name='Source Prefix/Host',
                help_text='IP prefix, network or host (e.g., 192.168.1.0/24, 192.168.1.0 255.255.255.0, host 10.1.1.1)'
            ),
        ),
        migrations.AddField(
            model_name='aclstandardrule',
            name='source_prefix',
            field=models.CharField(
                blank=True,
                max_length=100,
                verbose_name='Source Prefix/Host',
                help_text='IP prefix, network or host (e.g., 192.168.1.0/24, 192.168.1.0 255.255.255.0, host 10.1.1.1)'
            ),
        ),
    ]
