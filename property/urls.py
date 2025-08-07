from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_property, name='register_property'),
    path('list/', views.property_list, name='property_list'),
    path('detail/<int:property_id>/', views.property_detail, name='property_detail'),
    path('update/<int:property_id>/', views.property_update, name='property_update'),
    path('delete/<int:property_id>/', views.property_delete, name='property_delete'),
    path('log-issue/', views.log_issue, name='log_issue'),
    path('issue/history/', views.issue_history, name='issue_history'), # type: ignore
    path('issues/export/', views.export_issues, name='export_issues'),
    path('lease/create/<int:tenant_profile_id>/', views.create_lease_agreement, name='create_lease_agreement'),
    path('issues/<int:issue_id>/update/', views.update_issue_status, name='update_issue_status'),
    path('property/lease/<int:tenant_profile_id>/detail/', views.lease_agreement_detail, name='lease_agreement_detail'),    
    path('property/lease/<int:lease_id>/capture-payment/<str:for_month>/', views.capture_payment, name='capture_payment'),
    path('property/owner/register/', views.register_property_owner, name='register_property_owner'),
    path('property/owner/list/', views.property_owner_list, name='property_owner_list'),
    path('property-owner/<int:owner_id>/edit/', views.update_property_owner, name='update_property_owner'),
    path('property-owner/<int:owner_id>/delete/', views.delete_property_owner, name='delete_property_owner'),
    path('property-owner/<int:owner_id>/detail/', views.property_owner_detail, name='property_owner_detail'),
    path("issues/<int:issue_id>/media/", views.issue_media_view, name="issue_media_view"),

]
