from django.contrib import admin
from .models import SiteSettings, MembershipPlan, Trainer, Member, Attendance, Payment, Enquiry, UserProfile, Exercise, WorkoutPlan, WorkoutItem, FitnessMeasurement, FitnessGoal, Notification, MembershipPeriod, RefundRequest, InventoryItem, Expense, GymStaff

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ("gym_name","phone","email","address")
    def has_add_permission(self, request): return not SiteSettings.objects.exists()

@admin.register(MembershipPlan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name","duration_months","price","active","sort_order")
    list_editable = ("active","sort_order")

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ("full_name","phone","plan","status","joined_on","expires_on")
    list_filter = ("status","plan")
    search_fields = ("full_name","phone","email")

@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    list_display = ("name","specialty","active")
    list_filter = ("active",)
    filter_horizontal = ("members",)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user","role","member","trainer")
    list_filter = ("role",)
    search_fields = ("user__username","user__email")

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("member","checked_in_at")
    list_filter = ("checked_in_at",)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("member","amount","method","status","paid_on","reference")
    list_filter = ("status","method","paid_on")
    search_fields = ("member__full_name","reference")

@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ("name","phone","interest","created_at","resolved")
    list_filter = ("resolved","created_at")
    search_fields = ("name","phone","email")


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ("name", "category")
    search_fields = ("name", "category")

class WorkoutItemInline(admin.TabularInline):
    model = WorkoutItem
    extra = 1

@admin.register(WorkoutPlan)
class WorkoutPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "trainer", "active", "created_at")
    list_filter = ("active", "trainer")
    filter_horizontal = ("members",)
    inlines = [WorkoutItemInline]

@admin.register(FitnessMeasurement)
class FitnessMeasurementAdmin(admin.ModelAdmin):
    list_display = ("member", "recorded_on", "weight_kg", "waist_cm")
    list_filter = ("recorded_on",)
    search_fields = ("member__full_name",)

@admin.register(FitnessGoal)
class FitnessGoalAdmin(admin.ModelAdmin):
    list_display = ("member", "title", "due_date", "completed")
    list_filter = ("completed",)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "member", "kind", "scheduled_for", "sent_at", "read_at")
    list_filter = ("kind", "sent_at")

@admin.register(MembershipPeriod)
class MembershipPeriodAdmin(admin.ModelAdmin):
    list_display = ("member", "plan", "starts_on", "ends_on", "payment")


@admin.register(RefundRequest)
class RefundRequestAdmin(admin.ModelAdmin):
    list_display = ("member", "payment", "amount", "status", "requested_at", "processed_at")
    list_filter = ("status", "requested_at")
    search_fields = ("member__full_name", "payment__cashfree_order_id", "refund_id")
    readonly_fields = ("requested_at", "reviewed_at", "processed_at", "refund_id", "gateway_refund_id")


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "quantity", "unit", "reorder_level", "unit_cost")
    search_fields = ("name", "category")


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "amount", "spent_on")
    list_filter = ("category", "spent_on")
    search_fields = ("title",)


@admin.register(GymStaff)
class GymStaffAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "phone", "active")
    list_filter = ("active", "role")
    search_fields = ("name", "phone", "email")
