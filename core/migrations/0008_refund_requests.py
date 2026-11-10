from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("core", "0007_cashfree_checkout_fields")]
    operations = [
        migrations.CreateModel(
            name="RefundRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reason", models.TextField(max_length=1000)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=9)),
                ("status", models.CharField(choices=[("requested", "Requested"), ("approved", "Approved"), ("rejected", "Rejected"), ("processing", "Processing"), ("processed", "Refunded"), ("failed", "Failed")], default="requested", max_length=12)),
                ("refund_id", models.CharField(blank=True, max_length=80, null=True, unique=True)),
                ("gateway_refund_id", models.CharField(blank=True, max_length=100)),
                ("admin_note", models.TextField(blank=True)),
                ("requested_at", models.DateTimeField(auto_now_add=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
                ("member", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="refund_requests", to="core.member")),
                ("payment", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="refund_requests", to="core.payment")),
            ],
            options={"ordering": ["-requested_at"]},
        ),
        migrations.AddConstraint(
            model_name="refundrequest",
            constraint=models.UniqueConstraint(condition=~models.Q(status="rejected"), fields=("payment",), name="one_active_refund_per_payment"),
        ),
    ]
