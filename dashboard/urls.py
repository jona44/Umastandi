from django.urls import path
from . import views

urlpatterns = [ 
        path('tenant/dashboard/', views.tenant_dashboard, name='tenant_dashboard'),
        path('manager/dashboard/', views.manager_dashboard, name='manager_dashboard'),
        path('', views.home, name='home'),
        
        
   ]