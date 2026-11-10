from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("core", "0006_walkin_payments_optional_phone")]
    operations = [
        migrations.AddField(
            model_name="payment",
            name="cashfree_order_id",
            field=models.CharField(blank=True, db_index=True, max_length=100),
        ),
        migrations.AddField(
            model_name="payment",
            name="cashfree_payment_session_id",
            field=models.TextField(blank=True),
        ),
    ]
