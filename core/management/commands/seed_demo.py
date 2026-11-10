from django.core.management.base import BaseCommand
from core.models import SiteSettings, MembershipPlan, Trainer

class Command(BaseCommand):
    help = "Create starter Golden Gym site settings, plans and trainer examples."
    def handle(self, *args, **options):
        SiteSettings.objects.get_or_create(pk=1, defaults={
            "gym_name":"Golden Gym", "tagline":"Changing bodies. Changing lives.",
            "address":"Bangarupalyam, Andhra Pradesh",
            "opening_hours":"Monday – Saturday · 5:00 AM – 10:00 PM"
        })
        plans = [
            ("Starter",1,799,"A focused start to your fitness routine","Gym access\nFitness orientation\nBasic workout guidance"),
            ("Quarterly",3,1999,"Build consistency with a three-month plan","Gym access\nFitness assessment\nWorkout guidance"),
            ("Half Year",6,3499,"Make strength a habit","Gym access\nProgress check-ins\nWorkout guidance"),
        ]
        for i,(name,duration,price,description,features) in enumerate(plans):
            MembershipPlan.objects.get_or_create(name=name, defaults={"duration_months":duration,"price":price,"description":description,"features":features,"sort_order":i})
        self.stdout.write(self.style.SUCCESS("Golden Gym demo content is ready. Review prices with the owner before publishing."))
