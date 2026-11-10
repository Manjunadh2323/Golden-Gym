# Generated for Golden Gym V2.1 feature additions.
import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_payment_razorpay_order_id_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="member", name="qr_token",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AddField(
            model_name="member", name="address",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="member", name="date_of_birth",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="member", name="profile_photo",
            field=models.ImageField(blank=True, null=True, upload_to="members/"),
        ),
        migrations.AddField(
            model_name="payment", name="receipt_no",
            field=models.CharField(blank=True, max_length=40, null=True, unique=True),
        ),
        migrations.CreateModel(
            name="Exercise",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("category", models.CharField(blank=True, max_length=80)),
                ("description", models.TextField(blank=True)),
                ("video_url", models.URLField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name="WorkoutPlan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("description", models.TextField(blank=True)),
                ("active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("members", models.ManyToManyField(blank=True, related_name="workout_plans", to="core.member")),
                ("trainer", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="workout_plans", to="core.trainer")),
            ],
        ),
        migrations.CreateModel(
            name="WorkoutItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("day_label", models.CharField(blank=True, max_length=40)),
                ("sets", models.PositiveSmallIntegerField(default=3)),
                ("reps", models.CharField(default="10", max_length=40)),
                ("rest_seconds", models.PositiveSmallIntegerField(default=60)),
                ("notes", models.CharField(blank=True, max_length=220)),
                ("exercise", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.exercise")),
                ("plan", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="core.workoutplan")),
            ],
            options={"ordering": ["day_label", "id"]},
        ),
        migrations.CreateModel(
            name="FitnessMeasurement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("recorded_on", models.DateField(default=django.utils.timezone.localdate)),
                ("weight_kg", models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ("height_cm", models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ("waist_cm", models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ("chest_cm", models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ("body_fat_percent", models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ("notes", models.CharField(blank=True, max_length=220)),
                ("member", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="measurements", to="core.member")),
            ],
            options={"ordering": ["-recorded_on", "-id"]},
        ),
        migrations.CreateModel(
            name="FitnessGoal",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=120)),
                ("target_value", models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ("target_unit", models.CharField(blank=True, max_length=30)),
                ("due_date", models.DateField(blank=True, null=True)),
                ("completed", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("member", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="fitness_goals", to="core.member")),
            ],
        ),
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=140)),
                ("message", models.TextField()),
                ("kind", models.CharField(choices=[("payment", "Payment"), ("expiry", "Membership expiry"), ("renewal", "Renewal"), ("general", "General")], default="general", max_length=12)),
                ("scheduled_for", models.DateTimeField(default=django.utils.timezone.now)),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("member", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to="core.member")),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="gym_notifications", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="MembershipPeriod",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("starts_on", models.DateField()),
                ("ends_on", models.DateField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("member", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="periods", to="core.member")),
                ("payment", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="membership_periods", to="core.payment")),
                ("plan", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.membershipplan")),
            ],
            options={"ordering": ["-starts_on"]},
        ),
    ]
