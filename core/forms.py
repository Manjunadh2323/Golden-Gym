from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import Enquiry, Member, Attendance, Payment

User = get_user_model()

class EnquiryForm(forms.ModelForm):
    class Meta:
        model = Enquiry
        fields = ["name", "phone", "email", "interest", "message"]
        widgets = {"message": forms.Textarea(attrs={"rows": 4})}

class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ["full_name","phone","email","plan","joined_on","expires_on","status","notes"]
        widgets = {"joined_on": forms.DateInput(attrs={"type":"date"}), "expires_on": forms.DateInput(attrs={"type":"date"})}

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ["member","note"]

class PaymentForm(forms.ModelForm):
    payment_type = forms.ChoiceField(
        choices=[("registered", "Registered member"), ("walkin", "Walk-in / non-member")],
        initial="registered", label="Payment for",
    )
    payer_name = forms.CharField(max_length=120, required=False, label="Payer name (walk-in)")
    payer_phone = forms.CharField(max_length=20, required=False, label="Phone number (optional)")

    class Meta:
        model = Payment
        fields = ["payment_type", "member", "payer_name", "payer_phone", "amount", "method", "status", "reference", "paid_on", "note"]
        widgets = {"paid_on": forms.DateInput(attrs={"type":"date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["member"].required = False
        self.fields["member"].queryset = Member.objects.order_by("full_name")

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("payment_type") == "registered" and not cleaned.get("member"):
            self.add_error("member", "Choose a registered member, or select Walk-in / non-member.")
        if cleaned.get("payment_type") == "walkin" and not (cleaned.get("payer_name") or "").strip():
            self.add_error("payer_name", "Enter the walk-in payer's name.")
        return cleaned

    def save(self, commit=True):
        payment = super().save(commit=False)
        if self.cleaned_data.get("payment_type") == "walkin":
            payment.member = None
            payment.payer_name = self.cleaned_data.get("payer_name", "").strip()
            payment.payer_phone = self.cleaned_data.get("payer_phone", "").strip()
        else:
            payment.payer_name = payment.member.full_name if payment.member else ""
            payment.payer_phone = payment.member.phone if payment.member else ""
        if commit:
            payment.save()
            self.save_m2m()
        return payment

class MemberSignupForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cashfree requires a customer phone number for hosted checkout.
        # Phone remains optional for offline/manual member creation.
        if getattr(settings, "CASHFREE_APP_ID", "") and getattr(settings, "CASHFREE_SECRET_KEY", ""):
            self.fields["phone"].required = True
            self.fields["phone"].help_text = "Required for secure online payment checkout."
    username = forms.CharField(max_length=150)
    first_name = forms.CharField(max_length=150, label="First name")
    last_name = forms.CharField(max_length=150, required=False, label="Last name")
    email = forms.EmailField()
    phone = forms.CharField(max_length=20, required=False, label="Phone number (optional)")
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm password")
    def clean_username(self):
        value = self.cleaned_data["username"]
        if User.objects.filter(username__iexact=value).exists():
            raise forms.ValidationError("That username is already taken.")
        return value
    def clean_password2(self):
        first = self.cleaned_data.get("password1")
        second = self.cleaned_data["password2"]
        if first != second:
            raise forms.ValidationError("Passwords do not match.")
        if len(first or "") < 8:
            raise forms.ValidationError("Use at least 8 characters.")
        return second

class TrainerAccountForm(forms.Form):
    name = forms.CharField(max_length=100)
    specialty = forms.CharField(max_length=120, required=False)
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)
    def clean_username(self):
        value = self.cleaned_data["username"]
        if User.objects.filter(username__iexact=value).exists():
            raise forms.ValidationError("That username is already taken.")
        return value


from .models import Exercise, WorkoutPlan, WorkoutItem, FitnessMeasurement, FitnessGoal

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ["full_name", "phone", "email", "address", "date_of_birth", "profile_photo"]
        widgets = {"date_of_birth": forms.DateInput(attrs={"type":"date"})}

class FitnessMeasurementForm(forms.ModelForm):
    class Meta:
        model = FitnessMeasurement
        fields = ["recorded_on","weight_kg","height_cm","waist_cm","chest_cm","body_fat_percent","notes"]
        widgets = {"recorded_on": forms.DateInput(attrs={"type":"date"})}

class ExerciseForm(forms.ModelForm):
    class Meta:
        model = Exercise
        fields = ["name","category","description","video_url"]

class WorkoutPlanForm(forms.ModelForm):
    class Meta:
        model = WorkoutPlan
        fields = ["name","description","trainer","members","active"]
        widgets = {"members": forms.SelectMultiple(attrs={"size":8})}

class WorkoutItemForm(forms.ModelForm):
    class Meta:
        model = WorkoutItem
        fields = ["exercise","day_label","sets","reps","rest_seconds","notes"]


class FitnessGoalForm(forms.ModelForm):
    class Meta:
        model = FitnessGoal
        fields = ["title","target_value","target_unit","due_date"]
        widgets = {"due_date": forms.DateInput(attrs={"type":"date"})}


from .models import InventoryItem, Expense, GymStaff

class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ["name", "category", "quantity", "unit", "reorder_level", "unit_cost"]

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["title", "category", "amount", "spent_on", "note"]
        widgets = {"spent_on": forms.DateInput(attrs={"type": "date"})}

class GymStaffForm(forms.ModelForm):
    class Meta:
        model = GymStaff
        fields = ["name", "role", "phone", "email", "joined_on", "monthly_salary", "active", "notes"]
        widgets = {"joined_on": forms.DateInput(attrs={"type": "date"})}
