import calendar
from datetime import date, timedelta
from decimal import Decimal
import razorpay
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from . import cashfree
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from io import BytesIO
import uuid
from django.urls import reverse
from .models import SiteSettings, MembershipPlan, Trainer, Member, Attendance, Payment, Enquiry, UserProfile, Exercise, WorkoutPlan, WorkoutItem, FitnessMeasurement, FitnessGoal, Notification, MembershipPeriod, RefundRequest, InventoryItem, Expense, GymStaff
from .forms import EnquiryForm, MemberForm, AttendanceForm, PaymentForm, MemberSignupForm, TrainerAccountForm, ProfileForm, FitnessMeasurementForm, ExerciseForm, WorkoutPlanForm, WorkoutItemForm, FitnessGoalForm, InventoryItemForm, ExpenseForm, GymStaffForm

User = get_user_model()

def site_context():
    return {"site": SiteSettings.objects.first() or SiteSettings(gym_name="Golden Gym", address="Bangarupalyam, Andhra Pradesh")}

def user_role(user):
    if user.is_superuser or user.is_staff:
        return "owner"
    profile, _ = UserProfile.objects.get_or_create(user=user, defaults={"role":"member"})
    return profile.role

def role_required(*roles):
    def decorate(view):
        @login_required
        def wrapped(request, *args, **kwargs):
            if user_role(request.user) not in roles:
                messages.error(request, "You do not have permission to access that portal.")
                return redirect("portal_redirect")
            return view(request, *args, **kwargs)
        return wrapped
    return decorate

def add_months(day, months):
    month = day.month - 1 + months
    year = day.year + month // 12
    month = month % 12 + 1
    return date(year, month, min(day.day, calendar.monthrange(year, month)[1]))

def home(request):
    plans = MembershipPlan.objects.filter(active=True).order_by("sort_order", "price")
    trainers = Trainer.objects.filter(active=True)[:4]
    form = EnquiryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Thank you! Your enquiry has been received. The gym team will contact you.")
        return redirect("home")
    return render(request, "core/home.html", {**site_context(), "plans":plans, "trainers":trainers, "form":form})

@login_required
def portal_redirect(request):
    role = user_role(request.user)
    if role == "owner": return redirect("dashboard")
    if role == "trainer": return redirect("trainer_portal")
    return redirect("member_portal")

@role_required("owner")
def dashboard(request):
    today = timezone.localdate()
    context = {
        **site_context(),
        "members_count": Member.objects.count(),
        "active_count": Member.objects.filter(status="active").count(),
        "pending_count": Member.objects.filter(status="pending").count(),
        "today_count": Attendance.objects.filter(checked_in_at__date=today).count(),
        "revenue": Payment.objects.filter(status="paid", paid_on__month=today.month, paid_on__year=today.year).aggregate(total=Sum("amount"))["total"] or 0,
        "recent_payments": Payment.objects.select_related("member")[:6],
        "recent_enquiries": Enquiry.objects.filter(resolved=False)[:5],
        "expired_count": Member.objects.filter(expires_on__lt=today).exclude(status="expired").count(),
        "expiring_count": Member.objects.filter(expires_on__range=(today, today + timezone.timedelta(days=7))).count(),
        "monthly_members": Member.objects.filter(created_at__month=today.month, created_at__year=today.year).count(),
        "year_revenue": Payment.objects.filter(status="paid", paid_on__year=today.year).aggregate(total=Sum("amount"))["total"] or 0,
        "year_expenses": Expense.objects.filter(spent_on__year=today.year).aggregate(total=Sum("amount"))["total"] or 0,
        "current_year": today.year,
        "monthly_revenue": [float(Payment.objects.filter(status="paid", paid_on__year=today.year, paid_on__month=m).aggregate(total=Sum("amount"))["total"] or 0) for m in range(1, 13)],
        "expired_count": Member.objects.filter(expires_on__lt=today).exclude(status="expired").count(),
        "expiring_count": Member.objects.filter(expires_on__range=(today, today + timezone.timedelta(days=7))).count(),
        "monthly_members": Member.objects.filter(created_at__month=today.month, created_at__year=today.year).count(),
        "year_revenue": Payment.objects.filter(status="paid", paid_on__year=today.year).aggregate(total=Sum("amount"))["total"] or 0,
        "current_year": today.year,
        "monthly_revenue": [float(Payment.objects.filter(status="paid", paid_on__year=today.year, paid_on__month=m).aggregate(total=Sum("amount"))["total"] or 0) for m in range(1, 13)],
        "plan_counts": MembershipPlan.objects.annotate(member_count=Count("member")).order_by("-member_count"),
    }
    return render(request, "core/dashboard.html", context)

@role_required("owner")
def members(request):
    q = request.GET.get("q","").strip()
    qs = Member.objects.select_related("plan").all()
    if q: qs = qs.filter(full_name__icontains=q) | Member.objects.filter(phone__icontains=q)
    return render(request, "core/members.html", {**site_context(), "members":qs, "q":q})

@role_required("owner")
def member_add(request):
    form = MemberForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Member added successfully.")
        return redirect("members")
    return render(request, "core/form.html", {**site_context(), "form":form, "heading":"Add member", "back":"members"})

@role_required("owner","trainer")
def attendance(request):
    form = AttendanceForm(request.POST or None)
    if user_role(request.user) == "trainer":
        trainer = getattr(request.user.gym_profile, "trainer", None)
        form.fields["member"].queryset = trainer.members.all() if trainer else Member.objects.none()
    if form.is_valid():
        member = form.cleaned_data["member"]
        today = timezone.localdate()
        if member.status != "active" or (member.expires_on and member.expires_on < today):
            messages.error(request, "This membership is not active. Please ask the owner to renew or verify it.")
        elif Attendance.objects.filter(member=member, checked_in_at__date=today).exists():
            messages.info(request, f"{member.full_name} is already checked in today.")
        else:
            form.save()
            messages.success(request, f"Attendance checked in for {member.full_name}.")
        return redirect("attendance")
    records = Attendance.objects.select_related("member")
    if user_role(request.user) == "trainer":
        records = records.filter(member__trainers__account__user=request.user)
    records = records[:30]
    return render(request, "core/attendance.html", {**site_context(), "form":form, "records":records})

@role_required("owner")
def payments(request):
    form = PaymentForm(request.POST or None)
    if form.is_valid():
        payment = form.save()
        if payment.status == "paid":
            payment.receipt_no = payment.receipt_no or f"GG-{timezone.localdate():%Y%m%d}-{payment.pk:06d}"
            payment.save(update_fields=["receipt_no"])
            # Only a payment linked to a registered member can activate/extend membership.
            if payment.member_id:
                member = payment.member
                member.status = "active"
                member.joined_on = timezone.localdate()
                member.expires_on = add_months(member.joined_on, member.plan.duration_months if member.plan else 1)
                member.save(update_fields=["status","joined_on","expires_on"])
                if member.plan:
                    MembershipPeriod.objects.create(member=member, plan=member.plan, starts_on=member.joined_on, ends_on=member.expires_on, payment=payment)
                profile = UserProfile.objects.filter(member=member).select_related("user").first()
                if profile:
                    Notification.objects.create(user=profile.user, member=member, kind="payment", title="Payment recorded", message=f"Your payment of ₹{payment.amount} has been recorded by Golden Gym.")
        messages.success(request, "Payment record saved. A paid walk-in transaction does not create or activate a membership.")
        return redirect("payments")
    records = Payment.objects.select_related("member")[:50]
    return render(request, "core/payments.html", {**site_context(), "form":form, "records":records})

@role_required("owner")
def trainers(request):
    return render(request, "core/trainers_admin.html", {**site_context(), "trainers":Trainer.objects.all()})

@role_required("owner")
def trainer_create(request):
    form = TrainerAccountForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        user = User.objects.create_user(username=data["username"], email=data["email"], password=data["password"], first_name=data["name"])
        trainer = Trainer.objects.create(name=data["name"], specialty=data["specialty"])
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role, profile.trainer = "trainer", trainer
        profile.save()
        messages.success(request, "Trainer account created. Share the credentials privately.")
        return redirect("trainers_admin")
    return render(request, "core/form.html", {**site_context(), "form":form, "heading":"Create trainer login", "back":"trainers_admin"})

@role_required("owner")
def enquiries(request):
    return render(request, "core/enquiries.html", {**site_context(), "enquiries":Enquiry.objects.all()})

@role_required("owner")
def resolve_enquiry(request, pk):
    item = get_object_or_404(Enquiry, pk=pk)
    if request.method == "POST":
        item.resolved = not item.resolved
        item.save(update_fields=["resolved"])
    return redirect("enquiries")

@role_required("member")
def member_portal(request):
    member = request.user.gym_profile.member
    payments = member.payments.all()[:10] if member else []
    refundable_payment_ids = set()
    if member:
        cutoff = timezone.localdate() - timedelta(days=7)
        refundable_payment_ids = set(member.payments.filter(status="paid", method="gateway", cashfree_order_id__gt="", paid_on__gte=cutoff).values_list("id", flat=True))
    workouts = member.workout_plans.filter(active=True).prefetch_related("items__exercise") if member else []
    measurements = member.measurements.all()[:12] if member else []
    notifications = request.user.gym_notifications.filter(read_at__isnull=True)[:8]
    periods = member.periods.select_related("plan").all()[:12] if member else []
    qr_url = reverse("member_qr") if member else ""
    return render(request, "core/member_portal.html", {**site_context(), "member":member, "payments":payments, "refundable_payment_ids":refundable_payment_ids, "workouts":workouts, "measurements":measurements, "notifications":notifications, "periods":periods, "qr_url":qr_url})

@role_required("member")
def request_refund(request, payment_id):
    member = request.user.gym_profile.member
    payment = get_object_or_404(Payment, pk=payment_id, member=member)
    if request.method != "POST":
        return redirect("member_portal")
    reason = (request.POST.get("reason") or "").strip()
    if payment.status != "paid" or payment.method != "gateway" or not payment.cashfree_order_id:
        messages.error(request, "Only successful Cashfree online payments can be requested for refund here. Contact the gym for other payment methods.")
    elif payment.paid_on < timezone.localdate() - timedelta(days=7):
        messages.error(request, "Refund requests are available only within 7 days of payment.")
    elif len(reason) < 5:
        messages.error(request, "Please provide a short reason for the refund request.")
    elif payment.refund_requests.exclude(status="rejected").exists():
        messages.info(request, "A refund request already exists for this payment.")
    else:
        RefundRequest.objects.create(payment=payment, member=member, amount=payment.amount, reason=reason)
        messages.success(request, "Your refund request was sent to Golden Gym for review.")
    return redirect("member_portal")


@role_required("owner")
def refund_requests(request):
    if request.method == "POST":
        refund = get_object_or_404(RefundRequest.objects.select_related("payment"), pk=request.POST.get("refund_id"))
        action = request.POST.get("action")
        note = (request.POST.get("admin_note") or "").strip()
        if action == "reject" and refund.status == "requested":
            refund.status = "rejected"; refund.admin_note = note; refund.reviewed_at = timezone.now()
            refund.save(update_fields=["status", "admin_note", "reviewed_at"])
            messages.success(request, "Refund request rejected.")
        elif action == "approve" and refund.status in {"requested", "failed"}:
            if not refund.payment.cashfree_order_id or refund.payment.status != "paid":
                messages.error(request, "This payment is not eligible for a Cashfree refund.")
            else:
                try:
                    if not refund.refund_id:
                        refund.refund_id = f"ggr{refund.pk}{uuid.uuid4().hex[:10]}"
                    refund.status = "processing"; refund.admin_note = note; refund.reviewed_at = timezone.now()
                    refund.save(update_fields=["refund_id", "status", "admin_note", "reviewed_at"])
                    result = cashfree.create_refund(refund.payment.cashfree_order_id, refund.refund_id, refund.amount, note or "Golden Gym member refund")
                    refund.gateway_refund_id = str(result.get("cf_refund_id") or result.get("refund_id") or "")
                    state = (result.get("refund_status") or "PENDING").upper()
                    if state == "SUCCESS":
                        refund.status = "processed"; refund.processed_at = timezone.now()
                        refund.payment.status = "refunded"; refund.payment.save(update_fields=["status"])
                    elif state in {"FAILED", "CANCELLED"}:
                        refund.status = "failed"
                    refund.save(update_fields=["gateway_refund_id", "status", "processed_at"])
                    messages.success(request, "Refund submitted to Cashfree. Its status is " + state + ".")
                except Exception as exc:
                    # Keep the stable refund ID for safe retry/status reconciliation.
                    messages.error(request, f"Cashfree could not confirm the refund submission. Check status before retrying. ({exc})")
        elif action == "refresh" and refund.refund_id:
            try:
                result = cashfree.fetch_refund(refund.payment.cashfree_order_id, refund.refund_id)
                state = (result.get("refund_status") or "PENDING").upper()
                refund.gateway_refund_id = str(result.get("cf_refund_id") or result.get("refund_id") or refund.gateway_refund_id)
                if state == "SUCCESS":
                    refund.status = "processed"; refund.processed_at = refund.processed_at or timezone.now()
                    refund.payment.status = "refunded"; refund.payment.save(update_fields=["status"])
                elif state in {"FAILED", "CANCELLED"}: refund.status = "failed"
                else: refund.status = "processing"
                refund.save(update_fields=["gateway_refund_id", "status", "processed_at"])
                messages.info(request, f"Cashfree refund status: {state}.")
            except Exception as exc:
                messages.error(request, f"Could not refresh refund status. ({exc})")
        return redirect("refund_requests")
    records = RefundRequest.objects.select_related("member", "payment").all()
    return render(request, "core/refund_requests.html", {**site_context(), "refunds": records})


@role_required("trainer")
def trainer_portal(request):
    trainer = request.user.gym_profile.trainer
    assigned = trainer.members.select_related("plan").all() if trainer else Member.objects.none()
    return render(request, "core/trainer_portal.html", {**site_context(), "trainer":trainer, "members":assigned})


def _cashfree_checkout(request, payment, member, plan):
    """Create a hosted Cashfree checkout. Never mark a payment paid here."""
    if not (settings.CASHFREE_APP_ID and settings.CASHFREE_SECRET_KEY):
        raise RuntimeError("Cashfree is not configured. Add Sandbox credentials to .env.")
    order_id = f"gg{payment.pk}{uuid.uuid4().hex[:12]}"
    base = request.build_absolute_uri("/").rstrip("/")
    return_url = base + reverse("cashfree_return") + "?order_id={order_id}"
    notify_url = base + reverse("cashfree_webhook")
    response = cashfree.create_order(
        order_id=order_id,
        amount=payment.amount,
        customer_id=f"member-{member.pk}",
        customer_name=member.full_name,
        customer_email=member.email or member.account.user.email,
        customer_phone=(member.phone or "").strip(),
        return_url=return_url,
        notify_url=notify_url,
    )
    payment.cashfree_order_id = response["order_id"]
    payment.cashfree_payment_session_id = response["payment_session_id"]
    payment.save(update_fields=["cashfree_order_id", "cashfree_payment_session_id"])
    return render(request, "core/cashfree_checkout.html", {
        **site_context(), "payment": payment, "plan": plan,
        "payment_session_id": response["payment_session_id"],
        "cashfree_mode": "sandbox" if settings.CASHFREE_ENV == "sandbox" else "production",
    })

def _activate_verified_payment(payment, gateway_payment_id=""):
    """Idempotently activate/extend membership after server-side gateway verification."""
    with transaction.atomic():
        locked = Payment.objects.select_for_update().select_related("member", "member__plan").get(pk=payment.pk)
        if locked.status == "paid":
            return locked
        member = locked.member
        if not member or not member.plan:
            raise ValueError("This payment is not linked to a membership.")
        today = timezone.localdate()
        start = max(today, member.expires_on or today)
        end = add_months(start, member.plan.duration_months)
        locked.status = "paid"
        locked.method = "gateway"
        locked.reference = str(gateway_payment_id)[:120]
        locked.paid_on = today
        locked.receipt_no = locked.receipt_no or f"GG-{today:%Y%m%d}-{locked.pk:06d}"
        locked.save(update_fields=["status", "method", "reference", "paid_on", "receipt_no"])
        member.status, member.joined_on, member.expires_on = "active", start, end
        member.save(update_fields=["status", "joined_on", "expires_on"])
        MembershipPeriod.objects.get_or_create(
            payment=locked,
            defaults={"member": member, "plan": member.plan, "starts_on": start, "ends_on": end},
        )
        profile = UserProfile.objects.filter(member=member).select_related("user").first()
        if profile:
            Notification.objects.get_or_create(
                member=member, kind="payment", title="Payment confirmed",
                defaults={"user": profile.user, "message": f"Your payment of ₹{locked.amount} was verified. Membership is active until {end:%d %b %Y}."},
            )
        return locked

def join_plan(request, plan_id):
    plan = get_object_or_404(MembershipPlan, pk=plan_id, active=True)
    form = MemberSignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        with transaction.atomic():
            user = User.objects.create_user(username=data["username"], email=data["email"], password=data["password1"], first_name=data["first_name"], last_name=data["last_name"])
            member = Member.objects.create(full_name=f'{data["first_name"]} {data["last_name"]}'.strip(), phone=data["phone"], email=data["email"], plan=plan, status="pending")
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role, profile.member = "member", member
            profile.save()
            payment = Payment.objects.create(member=member, amount=plan.price, method="gateway", status="pending", note=f"Membership signup: {plan.name}")
        request.session["pending_payment_id"] = payment.pk
        if settings.CASHFREE_APP_ID and settings.CASHFREE_SECRET_KEY:
            try:
                return _cashfree_checkout(request, payment, member, plan)
            except Exception as exc:
                messages.error(request, f"Online checkout could not start. Your account is saved and payment remains pending. Please try again or contact the gym. ({exc})")
        elif settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
            try:
                client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                order = client.order.create({"amount":int(plan.price * Decimal("100")), "currency":"INR", "receipt":f"gg-{payment.pk}", "payment_capture":1})
                payment.razorpay_order_id = order["id"]
                payment.save(update_fields=["razorpay_order_id"])
                return render(request, "core/checkout.html", {**site_context(), "plan":plan, "order":order, "key_id":settings.RAZORPAY_KEY_ID})
            except Exception:
                messages.error(request, "Online checkout could not start. Your account is saved and payment remains pending.")
        login(request, user)
        messages.info(request, "Your account is ready. Membership stays pending until the gym confirms payment.")
        return redirect("member_portal")
    return render(request, "core/join.html", {
        **site_context(), "plan":plan, "form":form,
        "online_payment_ready": bool(
            (settings.CASHFREE_APP_ID and settings.CASHFREE_SECRET_KEY)
            or (settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET)
        ),
    })


def cashfree_return(request):
    """Browser return is not trusted; fetch payment status from Cashfree server-to-server."""
    order_id = request.GET.get("order_id", "")
    payment = get_object_or_404(Payment, cashfree_order_id=order_id)
    try:
        transactions = cashfree.fetch_order_payments(order_id)
        successful = next((item for item in transactions if item.get("payment_status") == "SUCCESS"), None)
        if successful:
            if str(successful.get("order_id")) != payment.cashfree_order_id:
                raise ValueError("Cashfree order mismatch.")
            if Decimal(str(successful.get("payment_amount", "0"))) != payment.amount:
                raise ValueError("Cashfree amount mismatch.")
            _activate_verified_payment(payment, successful.get("cf_payment_id", ""))
            profile = UserProfile.objects.filter(member=payment.member).select_related("user").first()
            if profile and request.user.is_anonymous:
                login(request, profile.user)
            messages.success(request, "Payment verified with Cashfree. Your membership is active.")
            return redirect("member_portal") if profile else redirect("home")
        messages.warning(request, "Cashfree has not confirmed a successful payment yet. Your membership remains pending.")
    except Exception:
        messages.error(request, "We could not verify this payment yet. Your membership remains pending; please contact the gym if money was debited.")
    return redirect("portal_redirect") if request.user.is_authenticated else redirect("home")

@csrf_exempt
@require_POST
def cashfree_webhook(request):
    """Verify Cashfree webhook signature; then independently confirm status via API."""
    timestamp = request.headers.get("x-webhook-timestamp", "")
    signature = request.headers.get("x-webhook-signature", "")
    if not cashfree.verify_webhook_signature(request.body, timestamp, signature):
        return HttpResponse(status=400)
    try:
        event = json.loads(request.body.decode("utf-8"))
        order_id = event.get("data", {}).get("order", {}).get("order_id", "")
        if order_id:
            payment = Payment.objects.filter(cashfree_order_id=order_id).first()
            if payment and payment.status != "paid":
                transactions = cashfree.fetch_order_payments(order_id)
                successful = next((item for item in transactions if item.get("payment_status") == "SUCCESS"), None)
                if successful and Decimal(str(successful.get("payment_amount", "0"))) == payment.amount:
                    _activate_verified_payment(payment, successful.get("cf_payment_id", ""))
    except Exception:
        # Acknowledge validly signed events to avoid noisy retries; reconciliation can retry.
        return HttpResponse(status=200)
    return HttpResponse(status=200)

@require_POST
def verify_checkout(request):
    payment = get_object_or_404(Payment, pk=request.session.get("pending_payment_id"), status="pending")
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    attrs = {"razorpay_order_id":request.POST.get("razorpay_order_id",""), "razorpay_payment_id":request.POST.get("razorpay_payment_id",""), "razorpay_signature":request.POST.get("razorpay_signature","")}
    try:
        if attrs["razorpay_order_id"] != payment.razorpay_order_id:
            raise ValueError("Order mismatch")
        client.utility.verify_payment_signature(attrs)
        gateway_payment = client.payment.fetch(attrs["razorpay_payment_id"])
        if gateway_payment.get("order_id") != payment.razorpay_order_id:
            raise ValueError("Payment order mismatch")
        if int(gateway_payment.get("amount", 0)) != int(payment.amount * Decimal("100")):
            raise ValueError("Payment amount mismatch")
        if gateway_payment.get("status") != "captured":
            raise ValueError("Payment has not been captured")
        if payment.status == "paid":
            return redirect("member_portal")
        payment.status = "paid"
        payment.method = "upi" if gateway_payment.get("method") == "upi" else "gateway"
        payment.razorpay_payment_id = attrs["razorpay_payment_id"]
        payment.reference = attrs["razorpay_payment_id"]
        payment.paid_on = timezone.localdate()
        payment.receipt_no = payment.receipt_no or f"GG-{timezone.localdate():%Y%m%d}-{payment.pk:06d}"
        payment.save()
        member = payment.member
        start = max(timezone.localdate(), member.expires_on or timezone.localdate())
        end = add_months(start, member.plan.duration_months if member.plan else 1)
        member.status, member.joined_on, member.expires_on = "active", start, end
        member.save(update_fields=["status","joined_on","expires_on"])
        MembershipPeriod.objects.create(member=member, plan=member.plan, starts_on=start, ends_on=end, payment=payment)
        Notification.objects.create(user=member.account.user, member=member, title="Payment confirmed", message=f"Your payment of ₹{payment.amount} was verified. Membership is active until {end:%d %b %Y}.", kind="payment")
        request.session.pop("pending_payment_id", None)
        login(request, member.account.user)
        messages.success(request, "Payment verified. Your membership is active.")
        return redirect("member_portal")
    except Exception:
        payment.status = "failed"
        payment.save(update_fields=["status"])
        messages.error(request, "Payment verification failed. Contact the gym before retrying.")
        return redirect("home")


# ---------------- Golden Gym V2.1 feature views ----------------
@role_required("member")
def member_qr(request):
    member = request.user.gym_profile.member
    if not member:
        raise PermissionDenied
    try:
        import qrcode
        image = qrcode.make(str(member.qr_token))
        stream = BytesIO()
        image.save(stream, format="PNG")
        return HttpResponse(stream.getvalue(), content_type="image/png")
    except ImportError:
        return HttpResponse("Install qrcode[pil] to generate QR passes.", status=503)

@role_required("owner","trainer")
@require_POST
def qr_checkin(request):
    token = request.POST.get("token", "").strip()
    try:
        member = Member.objects.get(qr_token=uuid.UUID(token), status="active", expires_on__gte=timezone.localdate())
    except (ValueError, Member.DoesNotExist):
        messages.error(request, "Invalid QR code or inactive membership.")
        return redirect("attendance")
    if user_role(request.user) == "trainer":
        trainer = getattr(request.user.gym_profile, "trainer", None)
        if not trainer or not trainer.members.filter(pk=member.pk).exists():
            raise PermissionDenied
    if Attendance.objects.filter(member=member, checked_in_at__date=timezone.localdate()).exists():
        messages.info(request, f"{member.full_name} is already checked in today.")
    else:
        Attendance.objects.create(member=member, note="QR check-in")
        messages.success(request, f"Attendance recorded for {member.full_name}.")
    return redirect("attendance")

@role_required("member")
def profile_settings(request):
    member = request.user.gym_profile.member
    if not member:
        raise PermissionDenied
    form = ProfileForm(request.POST or None, request.FILES or None, instance=member)
    if request.method == "POST" and form.is_valid():
        form.save()
        request.user.email = member.email
        request.user.save(update_fields=["email"])
        messages.success(request, "Your profile was updated.")
        return redirect("member_portal")
    return render(request, "core/profile.html", {**site_context(), "form":form})

@role_required("member")
def fitness_tracking(request):
    member = request.user.gym_profile.member
    if not member: raise PermissionDenied
    form = FitnessMeasurementForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        record = form.save(commit=False); record.member = member; record.save()
        messages.success(request, "Fitness measurement saved.")
        return redirect("fitness_tracking")
    goal_form = FitnessGoalForm, InventoryItemForm, ExpenseForm, GymStaffForm(request.POST or None, prefix="goal")
    if request.method == "POST" and request.POST.get("form_type") == "goal" and goal_form.is_valid():
        goal = goal_form.save(commit=False); goal.member = member; goal.save()
        messages.success(request, "Fitness goal added.")
        return redirect("fitness_tracking")
    return render(request, "core/fitness.html", {**site_context(), "form":form, "goal_form":goal_form, "goals":member.fitness_goals.all(), "records":member.measurements.all()})

@role_required("owner","trainer")
def workouts(request):
    role = user_role(request.user)
    if role == "owner":
        plans = WorkoutPlan.objects.prefetch_related("members","items__exercise").all()
        trainer = None
    else:
        trainer = getattr(request.user.gym_profile, "trainer", None)
        plans = WorkoutPlan.objects.filter(trainer=trainer).prefetch_related("members","items__exercise") if trainer else WorkoutPlan.objects.none()
    return render(request, "core/workouts.html", {**site_context(), "plans":plans})

@role_required("owner","trainer")
def workout_create(request):
    form = WorkoutPlanForm(request.POST or None)
    role = user_role(request.user)
    if role == "trainer":
        trainer = getattr(request.user.gym_profile, "trainer", None)
        form.fields["members"].queryset = trainer.members.all() if trainer else Member.objects.none()
    if request.method == "POST" and form.is_valid():
        plan = form.save(commit=False)
        if role == "trainer":
            plan.trainer = getattr(request.user.gym_profile, "trainer", None)
        plan.save(); form.save_m2m()
        messages.success(request, "Workout plan created. Add exercises from the plan page.")
        return redirect("workouts")
    return render(request, "core/form.html", {**site_context(), "form":form, "heading":"Create workout plan", "back":"workouts"})

@role_required("owner","trainer")
def workout_add_item(request, plan_id):
    plan = get_object_or_404(WorkoutPlan, pk=plan_id)
    if user_role(request.user) == "trainer" and plan.trainer_id != getattr(request.user.gym_profile, "trainer_id", None):
        raise PermissionDenied
    form = WorkoutItemForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False); item.plan = plan; item.save()
        messages.success(request, "Exercise added to workout.")
        return redirect("workouts")
    return render(request, "core/form.html", {**site_context(), "form":form, "heading":f"Add exercise · {plan.name}", "back":"workouts"})

@role_required("owner","trainer")
def exercise_create(request):
    form = ExerciseForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save(); messages.success(request, "Exercise added to library.")
        return redirect("workouts")
    return render(request, "core/form.html", {**site_context(), "form":form, "heading":"Add exercise", "back":"workouts"})

@role_required("member")
@require_POST
def renew_membership(request):
    member = request.user.gym_profile.member
    if not member or not member.plan:
        messages.error(request, "Contact the gym to select a membership plan.")
        return redirect("member_portal")
    payment = Payment.objects.create(member=member, amount=member.plan.price, method="gateway", status="pending", note=f"Membership renewal: {member.plan.name}")
    request.session["pending_payment_id"] = payment.pk
    if settings.CASHFREE_APP_ID and settings.CASHFREE_SECRET_KEY:
        try:
            return _cashfree_checkout(request, payment, member, member.plan)
        except Exception:
            payment.status = "failed"; payment.save(update_fields=["status"])
            messages.error(request, "Cashfree checkout could not start. Please try again or contact the gym.")
            return redirect("member_portal")
    if settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
        try:
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            order = client.order.create({"amount":int(member.plan.price * Decimal("100")), "currency":"INR", "receipt":f"gg-renew-{payment.pk}", "payment_capture":1})
            payment.razorpay_order_id = order["id"]; payment.save(update_fields=["razorpay_order_id"])
            return render(request, "core/checkout.html", {**site_context(), "plan":member.plan, "order":order, "key_id":settings.RAZORPAY_KEY_ID})
        except Exception:
            payment.status = "failed"; payment.save(update_fields=["status"])
            messages.error(request, "Checkout could not start. Please contact the gym.")
    else:
        payment.status = "pending"; payment.save(update_fields=["status"])
        messages.info(request, "Online payment is not configured. Please contact the gym.")
    return redirect("member_portal")

@role_required("member")
def payment_receipt(request, payment_id):
    member = request.user.gym_profile.member
    payment = get_object_or_404(Payment, pk=payment_id, member=member, status="paid")
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    buffer = BytesIO(); pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle(f"Golden Gym receipt {payment.receipt_no or payment.pk}")
    pdf.setFont("Helvetica-Bold", 20); pdf.drawString(55, 790, site_context()["site"].gym_name)
    pdf.setFont("Helvetica", 11)
    lines = [f"Payment receipt: {payment.receipt_no or ('GG-' + str(payment.pk))}", f"Member: {member.full_name}", f"Plan: {member.plan.name if member.plan else '—'}", f"Amount: INR {payment.amount}", f"Payment method: {payment.get_method_display()}", f"Reference: {payment.reference or payment.razorpay_payment_id or '—'}", f"Paid on: {payment.paid_on}", "Status: PAID"]
    y = 745
    for line in lines:
        pdf.drawString(55, y, line); y -= 28
    pdf.drawString(55, y-10, "Thank you for training with Golden Gym.")
    pdf.showPage(); pdf.save()
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="GoldenGym-{payment.pk}-receipt.pdf"'
    return response


@role_required("owner")
def owner_payment_receipt(request, payment_id):
    payment = get_object_or_404(Payment, pk=payment_id, status="paid")
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    buffer = BytesIO(); pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle(f"Golden Gym receipt {payment.receipt_no or payment.pk}")
    pdf.setFont("Helvetica-Bold", 20); pdf.drawString(55, 790, site_context()["site"].gym_name)
    pdf.setFont("Helvetica", 11)
    payer = payment.member.full_name if payment.member_id else (payment.payer_name or "Walk-in customer")
    lines = [f"Payment receipt: {payment.receipt_no or ('GG-' + str(payment.pk))}", f"Payer: {payer}", f"Phone: {payment.member.phone if payment.member_id else (payment.payer_phone or '—')}", f"Plan: {payment.member.plan.name if payment.member_id and payment.member.plan else 'Not applicable'}", f"Amount: INR {payment.amount}", f"Payment method: {payment.get_method_display()}", f"Reference: {payment.reference or payment.razorpay_payment_id or '—'}", f"Paid on: {payment.paid_on}", "Status: PAID"]
    y = 745
    for line in lines:
        pdf.drawString(55, y, line); y -= 28
    pdf.drawString(55, y-10, "Thank you for visiting Golden Gym.")
    pdf.showPage(); pdf.save()
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="GoldenGym-{payment.pk}-receipt.pdf"'
    return response

@role_required("owner")
def export_report(request, kind):
    if kind not in {"members","payments","attendance"}: raise PermissionDenied
    rows = []
    if kind == "members":
        rows = [["Member","Phone","Email","Plan","Status","Joined","Expires"]] + [[m.full_name,m.phone,m.email,str(m.plan or ""),m.status,str(m.joined_on),str(m.expires_on or "")] for m in Member.objects.select_related("plan")]
    elif kind == "payments":
        rows = [["Member","Amount","Method","Status","Reference","Paid on"]] + [[x.member.full_name if x.member_id else (x.payer_name or "Walk-in"),str(x.amount),x.method,x.status,x.reference,str(x.paid_on)] for x in Payment.objects.select_related("member")]
    else:
        rows = [["Member","Checked in at","Note"]] + [[x.member.full_name,str(x.checked_in_at),x.note] for x in Attendance.objects.select_related("member")]
    fmt = request.GET.get("format","xlsx").lower()
    if fmt == "pdf":
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.pdfgen import canvas
        buf=BytesIO(); pdf=canvas.Canvas(buf,pagesize=landscape(A4)); y=560
        pdf.setFont("Helvetica-Bold",14); pdf.drawString(35,y,f"Golden Gym · {kind.title()} report"); y-=28
        pdf.setFont("Helvetica",8)
        for row in rows:
            line=" | ".join(str(c)[:32] for c in row)
            pdf.drawString(35,y,line[:160]); y-=16
            if y<35: pdf.showPage(); y=560; pdf.setFont("Helvetica",8)
        pdf.save(); response=HttpResponse(buf.getvalue(),content_type="application/pdf")
        response["Content-Disposition"]=f'attachment; filename="goldengym-{kind}.pdf"'; return response
    from openpyxl import Workbook
    wb=Workbook(); ws=wb.active; ws.title=kind.title()
    for row in rows: ws.append(row)
    out=BytesIO(); wb.save(out); response=HttpResponse(out.getvalue(),content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"]=f'attachment; filename="goldengym-{kind}.xlsx"'; return response

@role_required("member")
@require_POST
def notification_read(request, notification_id):
    notification = get_object_or_404(Notification, pk=notification_id, user=request.user)
    notification.read_at = timezone.now(); notification.save(update_fields=["read_at"])
    return redirect("member_portal")


# V4.1 owner operations: inventory, expenses, staff directory and printable member cards.
@role_required("owner")
def inventory(request):
    form = InventoryItemForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Inventory item saved.")
        return redirect("inventory")
    items = InventoryItem.objects.all()
    return render(request, "core/inventory.html", {**site_context(), "items": items, "form": form})


@role_required("owner")
def expenses(request):
    form = ExpenseForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Expense recorded.")
        return redirect("expenses")
    rows = Expense.objects.all()
    total = rows.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    return render(request, "core/expenses.html", {**site_context(), "expenses": rows, "form": form, "total": total})


@role_required("owner")
def staff_directory(request):
    form = GymStaffForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Staff record saved.")
        return redirect("staff_directory")
    return render(request, "core/staff.html", {**site_context(), "staff_members": GymStaff.objects.all(), "form": form})


@role_required("owner")
def member_id_card(request, member_id):
    member = get_object_or_404(Member, pk=member_id)
    return render(request, "core/member_id_card.html", {**site_context(), "member": member})
