from django.db import models
from django.utils import timezone
import uuid

class SiteSettings(models.Model):
    gym_name = models.CharField(max_length=100, default="Golden Gym")
    tagline = models.CharField(max_length=180, default="Changing bodies. Changing lives.")
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, default="Bangarupalyam, Andhra Pradesh")
    opening_hours = models.CharField(max_length=120, default="Monday – Saturday · 5:00 AM – 10:00 PM")
    instagram_url = models.URLField(blank=True)
    def __str__(self): return self.gym_name
    class Meta: verbose_name_plural = "Site settings"

class MembershipPlan(models.Model):
    name = models.CharField(max_length=80)
    duration_months = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=9, decimal_places=2)
    description = models.CharField(max_length=220, blank=True)
    features = models.TextField(blank=True, help_text="One feature per line")
    active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    def __str__(self): return f"{self.name} — ₹{self.price}"

class Member(models.Model):
    STATUS = [("pending","Payment pending"),("active","Active"),("paused","Paused"),("expired","Expired")]
    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    plan = models.ForeignKey(MembershipPlan, on_delete=models.SET_NULL, null=True, blank=True)
    joined_on = models.DateField(default=timezone.localdate)
    expires_on = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=STATUS, default="pending")
    notes = models.TextField(blank=True)
    qr_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    address = models.CharField(max_length=255, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_photo = models.ImageField(upload_to="members/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.full_name

class Trainer(models.Model):
    name = models.CharField(max_length=100)
    specialty = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to="trainers/", blank=True, null=True)
    active = models.BooleanField(default=True)
    members = models.ManyToManyField("Member", blank=True, related_name="trainers")
    def __str__(self): return self.name

class UserProfile(models.Model):
    ROLE_CHOICES = [("owner","Owner"),("member","Member"),("trainer","Trainer")]
    user = models.OneToOneField("auth.User", on_delete=models.CASCADE, related_name="gym_profile")
    role = models.CharField(max_length=12, choices=ROLE_CHOICES, default="member")
    member = models.OneToOneField(Member, on_delete=models.SET_NULL, null=True, blank=True, related_name="account")
    trainer = models.OneToOneField(Trainer, on_delete=models.SET_NULL, null=True, blank=True, related_name="account")
    def __str__(self): return f"{self.user.username} · {self.role}"

class Attendance(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="attendance")
    checked_in_at = models.DateTimeField(default=timezone.now)
    note = models.CharField(max_length=160, blank=True)
    class Meta: ordering = ["-checked_in_at"]
    def __str__(self): return f"{self.member} · {self.checked_in_at:%d %b %Y %H:%M}"

class Payment(models.Model):
    METHODS = [("cash","Cash"),("upi","UPI"),("card","Card / POS terminal"),("bank","Bank transfer"),("gateway","Online gateway")]
    STATUS = [("paid","Paid"),("pending","Pending"),("refunded","Refunded"),("failed","Failed")]
    member = models.ForeignKey(Member, on_delete=models.PROTECT, related_name="payments", null=True, blank=True)
    payer_name = models.CharField(max_length=120, blank=True)
    payer_phone = models.CharField(max_length=20, blank=True)
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    method = models.CharField(max_length=12, choices=METHODS, default="cash")
    status = models.CharField(max_length=12, choices=STATUS, default="paid")
    reference = models.CharField(max_length=120, blank=True)
    razorpay_order_id = models.CharField(max_length=100, blank=True, db_index=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    cashfree_order_id = models.CharField(max_length=100, blank=True, db_index=True)
    cashfree_payment_session_id = models.TextField(blank=True)
    receipt_no = models.CharField(max_length=40, blank=True, unique=True, null=True)
    paid_on = models.DateField(default=timezone.localdate)
    note = models.CharField(max_length=220, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["-paid_on", "-created_at"]
    def __str__(self): return f"{self.member or self.payer_name or 'Walk-in'} · ₹{self.amount}"

class Enquiry(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    interest = models.CharField(max_length=100, blank=True)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    class Meta: ordering = ["-created_at"]
    def __str__(self): return f"{self.name} · {self.phone}"


# Golden Gym V2.1 features
import uuid

class Exercise(models.Model):
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=80, blank=True)
    description = models.TextField(blank=True)
    video_url = models.URLField(blank=True)
    def __str__(self): return self.name

class WorkoutPlan(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    trainer = models.ForeignKey(Trainer, on_delete=models.SET_NULL, null=True, blank=True, related_name="workout_plans")
    members = models.ManyToManyField(Member, blank=True, related_name="workout_plans")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name

class WorkoutItem(models.Model):
    plan = models.ForeignKey(WorkoutPlan, on_delete=models.CASCADE, related_name="items")
    exercise = models.ForeignKey(Exercise, on_delete=models.PROTECT)
    day_label = models.CharField(max_length=40, blank=True, help_text="Example: Monday or Day 1")
    sets = models.PositiveSmallIntegerField(default=3)
    reps = models.CharField(max_length=40, default="10")
    rest_seconds = models.PositiveSmallIntegerField(default=60)
    notes = models.CharField(max_length=220, blank=True)
    class Meta: ordering = ["day_label", "id"]
    def __str__(self): return f"{self.plan}: {self.exercise}"

class FitnessMeasurement(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="measurements")
    recorded_on = models.DateField(default=timezone.localdate)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    height_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    waist_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    chest_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    body_fat_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    notes = models.CharField(max_length=220, blank=True)
    class Meta: ordering = ["-recorded_on", "-id"]
    def __str__(self): return f"{self.member} · {self.recorded_on}"

class FitnessGoal(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="fitness_goals")
    title = models.CharField(max_length=120)
    target_value = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    target_unit = models.CharField(max_length=30, blank=True)
    due_date = models.DateField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.member}: {self.title}"

class Notification(models.Model):
    TYPES = [("payment","Payment"),("expiry","Membership expiry"),("renewal","Renewal"),("general","General")]
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE, null=True, blank=True, related_name="gym_notifications")
    member = models.ForeignKey(Member, on_delete=models.CASCADE, null=True, blank=True, related_name="notifications")
    title = models.CharField(max_length=140)
    message = models.TextField()
    kind = models.CharField(max_length=12, choices=TYPES, default="general")
    scheduled_for = models.DateTimeField(default=timezone.now)
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["-created_at"]
    def __str__(self): return self.title

class MembershipPeriod(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="periods")
    plan = models.ForeignKey(MembershipPlan, on_delete=models.PROTECT)
    starts_on = models.DateField()
    ends_on = models.DateField()
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True, related_name="membership_periods")
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["-starts_on"]
    def __str__(self): return f"{self.member} · {self.starts_on}–{self.ends_on}"


class RefundRequest(models.Model):
    STATUS = [
        ("requested", "Requested"), ("approved", "Approved"),
        ("rejected", "Rejected"), ("processing", "Processing"),
        ("processed", "Refunded"), ("failed", "Failed"),
    ]
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="refund_requests")
    member = models.ForeignKey(Member, on_delete=models.PROTECT, related_name="refund_requests")
    reason = models.TextField(max_length=1000)
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    status = models.CharField(max_length=12, choices=STATUS, default="requested")
    refund_id = models.CharField(max_length=80, unique=True, null=True, blank=True)
    gateway_refund_id = models.CharField(max_length=100, blank=True)
    admin_note = models.TextField(blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        ordering = ["-requested_at"]
        constraints = [models.UniqueConstraint(fields=["payment"], condition=~models.Q(status="rejected"), name="one_active_refund_per_payment")]
    def __str__(self):
        return f"Refund ₹{self.amount} · {self.payment_id} · {self.status}"


class InventoryItem(models.Model):
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=80, blank=True)
    quantity = models.PositiveIntegerField(default=0)
    unit = models.CharField(max_length=24, default="pcs")
    reorder_level = models.PositiveIntegerField(default=5)
    unit_cost = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.name} ({self.quantity} {self.unit})"


class Expense(models.Model):
    CATEGORY_CHOICES = [
        ("rent", "Rent"), ("utilities", "Utilities"), ("salary", "Salary"),
        ("equipment", "Equipment"), ("maintenance", "Maintenance"),
        ("supplies", "Supplies"), ("marketing", "Marketing"), ("other", "Other"),
    ]
    title = models.CharField(max_length=140)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="other")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    spent_on = models.DateField(default=timezone.localdate)
    note = models.CharField(max_length=240, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-spent_on", "-id"]
    def __str__(self):
        return f"{self.title} — ₹{self.amount}"


class GymStaff(models.Model):
    name = models.CharField(max_length=120)
    role = models.CharField(max_length=80)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    joined_on = models.DateField(default=timezone.localdate)
    monthly_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    class Meta:
        ordering = ["name"]
    def __str__(self):
        return f"{self.name} — {self.role}"
