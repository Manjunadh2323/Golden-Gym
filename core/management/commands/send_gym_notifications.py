from datetime import timedelta
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from core.models import Member, Notification

class Command(BaseCommand):
    help = "Expire memberships and create/send due expiry reminders. Schedule daily."

    def handle(self, *args, **options):
        today = timezone.localdate()
        expired = Member.objects.filter(expires_on__lt=today, status="active")
        expired_count = expired.count()
        expired.update(status="expired")
        created = 0
        for member in Member.objects.filter(status="active", expires_on__range=(today, today + timedelta(days=7))).select_related("account__user"):
            user = member.account.user if hasattr(member, "account") else None
            already = Notification.objects.filter(member=member, kind="expiry", created_at__date=today).exists()
            if already:
                continue
            days = (member.expires_on - today).days
            note = Notification.objects.create(user=user, member=member, kind="expiry",
                title="Membership expires soon",
                message=f"Your Golden Gym membership expires in {days} day(s), on {member.expires_on:%d %b %Y}. Please renew to continue training.")
            created += 1
            if user and user.email and settings.EMAIL_HOST:
                sent = send_mail(note.title, note.message, None, [user.email], fail_silently=True)
                if sent:
                    note.sent_at = timezone.now()
                    note.save(update_fields=["sent_at"])
        self.stdout.write(self.style.SUCCESS(f"Expired {expired_count} memberships; created {created} expiry reminder(s)."))
