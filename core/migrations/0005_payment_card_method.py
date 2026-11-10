from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0004_alter_workoutitem_day_label")]

    operations = [
        migrations.AlterField(
            model_name="payment",
            name="method",
            field=models.CharField(
                choices=[
                    ("cash", "Cash"),
                    ("upi", "UPI"),
                    ("card", "Card / POS terminal"),
                    ("bank", "Bank transfer"),
                    ("gateway", "Online gateway"),
                ],
                default="cash",
                max_length=12,
            ),
        ),
    ]
