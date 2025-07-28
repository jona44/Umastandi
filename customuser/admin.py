from django.contrib import admin
from .models import CustomUser

# Register your models here.
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'is_active','is_staff')
    search_fields = ('email', 'first_name', 'last_name', 'user_type' )
    list_filter = ('user_type', 'is_active', 'is_staff')
    ordering = ()
    
    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name')
        }),
        ('Permissions', {
            'fields': ('user_type', 'is_active', 'is_staff')
        }),
        # ('Important Dates', {
        #     'fields': ('date_joined',)
        # }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'user_type')}
        ),
    )
    
    filter_horizontal = ()
    readonly_fields = ()