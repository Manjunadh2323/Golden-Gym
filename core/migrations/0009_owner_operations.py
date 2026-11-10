from django.db import migrations, models
import django.utils.timezone

class Migration(migrations.Migration):
    dependencies = [("core", "0008_refund_requests")]
    operations = [
        migrations.CreateModel(name="InventoryItem", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("name", models.CharField(max_length=120)), ("category", models.CharField(blank=True, max_length=80)),
            ("quantity", models.PositiveIntegerField(default=0)), ("unit", models.CharField(default="pcs", max_length=24)),
            ("reorder_level", models.PositiveIntegerField(default=5)), ("unit_cost", models.DecimalField(decimal_places=2, default=0, max_digits=9)),
            ("updated_at", models.DateTimeField(auto_now=True)),
        ]),
        migrations.CreateModel(name="Expense", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("title", models.CharField(max_length=140)),
            ("category", models.CharField(choices=[("rent","Rent"),("utilities","Utilities"),("salary","Salary"),("equipment","Equipment"),("maintenance","Maintenance"),("supplies","Supplies"),("marketing","Marketing"),("other","Other")], default="other", max_length=20)),
            ("amount", models.DecimalField(decimal_places=2, max_digits=10)), ("spent_on", models.DateField(default=django.utils.timezone.localdate)),
            ("note", models.CharField(blank=True, max_length=240)), ("created_at", models.DateTimeField(auto_now_add=True)),
        ], options={"ordering":["-spent_on","-id"]}),
        migrations.CreateModel(name="GymStaff", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("name", models.CharField(max_length=120)), ("role", models.CharField(max_length=80)),
            ("phone", models.CharField(blank=True, max_length=20)), ("email", models.EmailField(blank=True, max_length=254)),
            ("joined_on", models.DateField(default=django.utils.timezone.localdate)), ("monthly_salary", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
            ("active", models.BooleanField(default=True)), ("notes", models.TextField(blank=True)),
        ], options={"ordering":["name"]}),
    ]
