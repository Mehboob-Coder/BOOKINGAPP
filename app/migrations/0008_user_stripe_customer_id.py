# Generated by Django 5.1.4 on 2025-01-09 13:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0007_appointment_payment_amount_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='stripe_customer_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
