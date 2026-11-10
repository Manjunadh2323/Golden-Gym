from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("core", "0005_payment_card_method")]

    operations = [
        migrations.AlterField(
            model_name="member", name="phone",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name="payment", name="member",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="payments", to="core.member"),
        ),
        migrations.AddField(
            model_name="payment", name="payer_name",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="payment", name="payer_phone",
            field=models.CharField(blank=True, max_length=20),
        ),
    ]
