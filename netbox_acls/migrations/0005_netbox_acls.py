# netbox_acls/migrations/0005_fix_prefix_fields.py
from django.db import migrations, models
import django.contrib.postgres.fields


class Migration(migrations.Migration):
    dependencies = [
        # Укажите последнюю миграцию вашего плагина
        ('netbox_acls', '0004_netbox_acls'),  # ЗАМЕНИТЕ на актуальное имя
    ]

    operations = [
        # 1. Удаляем старые ForeignKey поля (если они ещё есть)
        migrations.RemoveField(
            model_name='aclextendedrule',
            name='destination_prefix_id',
        ),
        migrations.RemoveField(
            model_name='aclextendedrule',
            name='source_prefix_id',
        ),
        migrations.RemoveField(
            model_name='aclstandardrule',
            name='source_prefix_id',
        ),
        
        # 2. Добавляем новые CharField поля (если их ещё нет)
        migrations.AddField(
            model_name='aclextendedrule',
            name='destination_prefix',
            field=models.CharField(blank=True, max_length=100, verbose_name='Destination Prefix/Host', help_text='IP prefix, network or host (e.g., 192.168.1.0/24, 192.168.1.0 255.255.255.0, host 10.1.1.1)'),
        ),
        migrations.AddField(
            model_name='aclextendedrule',
            name='source_prefix',
            field=models.CharField(blank=True, max_length=100, verbose_name='Source Prefix/Host', help_text='IP prefix, network or host (e.g., 192.168.1.0/24, 192.168.1.0 255.255.255.0, host 10.1.1.1)'),
        ),
        migrations.AddField(
            model_name='aclstandardrule',
            name='source_prefix',
            field=models.CharField(blank=True, max_length=100, verbose_name='Source Prefix/Host', help_text='IP prefix, network or host (e.g., 192.168.1.0/24, 192.168.1.0 255.255.255.0, host 10.1.1.1)'),
        ),
    ]