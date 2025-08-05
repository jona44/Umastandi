# customuser/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('register/', views.register_tenant, name='register_tenant'),
    path('create-manager/', views.create_manager, name='create_manager'),
    path('manager/edit_manager/<int:manager_id>/', views.edit_manager, name='edit_manager'),
    path('manager_profile/<int:user_id>/', views.manager_profile, name='manager_profile'),
    path('activate-lease/', views.activate_lease, name='activate_lease'),
    path('logout/', views.logout_view, name='logout'),
    path('tenant-profile/<int:user_id>/create/', views.create_tenant_profile, name='create_tenant_profile'),
    path('tenant-profile/<int:user_id>/edit/', views.update_tenant_profile, name='update_tenant_profile'),
    path('tenant/<int:user_id>/profile/', views.tenant_profile_detail, name='tenant_profile_detail'),
    path('tenant/<int:user_id>/profile/delete/', views.delete_tenant_profile, name='delete_tenant_profile'),
    path('tenant/list/', views.tenant_list, name='tenant_list'),
    path('tenant/<int:user_id>/deactivate/', views.deactivate_user, name='deactivate_user'),

  
]   

