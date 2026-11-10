from django.contrib import admin
from django.contrib.auth.views import PasswordChangeView
from django.urls import path, include, reverse_lazy
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/password-change/", PasswordChangeView.as_view(template_name="registration/password_change_form.html", success_url=reverse_lazy("portal_redirect")), name="password_change"),
    path("", include("core.urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
