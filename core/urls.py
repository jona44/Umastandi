from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include
from django.conf import settings
from django.contrib.auth import logout
from django.conf.urls.static import static
from customuser import views as customuser_views 
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', include('dashboard.urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('customuser/', include('customuser.urls')),
    path('property/', include('property.urls')),



    path('activate/<str:token>/', customuser_views.activate_account, name='activate_account'),
    path('login/', auth_views.LoginView.as_view(template_name='account/login.html'), name='login'),
    path('accounts/password/reset/', auth_views.PasswordResetView.as_view(template_name='password_reset.html'), name='account_reset_password'),
    path('accounts/password/reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='account/password_reset_done.html'), name='account_reset_password_done'),
    path('accounts/password/reset/key/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='account/password_reset_from_key.html'), name='account_reset_password_from_key'),
    path('accounts/password/reset/key/done/', auth_views.PasswordResetCompleteView.as_view(template_name='account/password_reset_complete.html'), name='account_reset_password_from_key_done'),

]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
