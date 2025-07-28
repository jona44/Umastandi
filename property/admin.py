from django.contrib import admin
from.models import *
# Register your models here.
@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'address', 'type',   
        'is_occupied', 'bedrooms', 'bathrooms', 'square_footage', 'created_at'
    )
    search_fields = ('name', 'address',  'user__email', 'type')
    list_filter = ('type', 'is_occupied', 'bedrooms', 'bathrooms', 'created_at')
    ordering = ('-id',)

@admin.register(TenantProfile)
class TenantProfileAdmin(admin.ModelAdmin):
    list_display = ( 'id','user', 'image', 'occupation', 'phone_number', 'national_id')
    search_fields = ('tenant__email', 'occupation', 'phone_number', 'national_id')
    list_filter = ('occupation',)
    ordering = ('-id',)

class TenantAdmin(admin.ModelAdmin):
    list_display = ('id', 'user',)  
    search_fields = ('tenant__email',)
    list_filter = ()
    ordering = ()
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'amount', 'payment_date', 'payment_method', 'reference_number', 'is_rent', 'for_month')
    search_fields = ('tenant__user__email', 'payment_method', 'reference_number', 'for_month')
    list_filter = ('payment_method', 'is_rent', 'for_month')
    
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'notification_type', 'created_at', 'read')
    search_fields = ('tenant__user__email', 'notification_type')
    list_filter = ('notification_type', 'read', 'created_at')
    ordering = ('-created_at',)
    
admin.site.register(PropertyManager)

admin.site.register(PropertyOwner)
admin.site.register(Issue)
admin.site.register(LeaseAgreement)



