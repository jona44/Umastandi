from django.db import models
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.forms import ValidationError
from customuser.models import CustomUser
from django.utils import timezone
from customuser.models import CustomUser
from django.core.validators import MinValueValidator
from decimal import Decimal

class Property(models.Model):
    PROPERTY_TYPE_CHOICES = [
        ('apartment', 'Apartment'),('house', 'House'),('condo', 'Condo'),('townhouse', 'Townhouse'),
        ('flat', 'Flat'),
        
    ]

    tenant   = models.ForeignKey('TenantProfile', on_delete=models.CASCADE, related_name='tenant_properties', null=True, blank=True)
    name     = models.CharField(max_length=255, null=True, blank=True)
    address  = models.TextField(null=True, blank=True)
    type     = models.CharField(max_length=255, choices=PROPERTY_TYPE_CHOICES, default='apartment')
    details  = models.TextField(null=True, blank=True)
    property_owner = models.ForeignKey('PropertyOwner', on_delete=models.CASCADE, related_name='properties', null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    is_occupied = models.BooleanField(default=False)
    bedrooms    = models.PositiveIntegerField(null=True, blank=True, default=1)
    bathrooms   = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True, default=1.0)  # type: ignore
    square_footage = models.PositiveIntegerField(null=True, blank=True, default=40)

    def __str__(self):
        return f"{self.name } -> is a ({self.type})"

    class Meta:
        verbose_name_plural = "Properties"
        ordering = ['-created_at']


class TenantProfile(models.Model):
    user        = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='tenant_profile',null=True, blank=True, unique=True)
    image         = models.ImageField(upload_to='tenant_images/', null=True, blank=True)
    occupation    = models.CharField(max_length=255, null=True, blank=True)
    phone_number  = models.CharField(max_length=15, null=True, blank=True)
    national_id   = models.CharField(max_length=20, null=True, blank=True)
    property_manager = models.ForeignKey('PropertyManager', on_delete=models.CASCADE, related_name='managed_tenants', null=True, blank=True)
    last_address = models.TextField(null=True, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True,null=True, blank=True)
    updated_at    = models.DateTimeField(auto_now=True,null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    
    def __str__(self):
        return f"{self.user}"
    
    def clean(self):
        if self.user:
            if self.user.user_type != 'tenant':
                raise ValidationError("Assigned user must be a tenant")
        if self.property_manager:
            if self.property_manager.user.user_type != 'manager':
                raise ValidationError("Assigned property manager must be a manager")
            

class Issue(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),('in_progress', 'In Progress'),('resolved', 'Resolved'),('closed', 'Closed'),('rejected', 'Rejected')
    ]
    PRIORITY_CHOICES = [('low', 'Low'),('medium', 'Medium'),('high', 'High'),('critical', 'Critical'),
    ]
    ISSUE_TYPE_CHOICES = [('electrical', 'Electrical'),('plumbing', 'Plumbing'),('painting', 'Painting'),('windows', 'Windows '),('doors', 'Doors'),('other', 'Other'),]
    
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    assigned_to = models.ForeignKey('PropertyManager', on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey('TenantProfile', on_delete=models.CASCADE, related_name='issues')
    property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='issues')
    issue_type = models.CharField(max_length=255, choices=ISSUE_TYPE_CHOICES, default='other', null=True, blank=True)
    description = models.TextField()
    image = models.ImageField(upload_to='issue_images/', null=True, blank=True)  # optional legacy
    status = models.CharField(max_length=255, choices=STATUS_CHOICES, default='open')
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Cost of servicing the issue (in Rands)")

    def __str__(self):
        return f"Issue {self.id} - {self.user.user} - {self.property.name}"  # type: ignore

    def save(self, *args, **kwargs):
        if self.status == 'resolved' and not self.resolved_at:
            self.resolved_at = timezone.now()
        super().save(*args, **kwargs)

    def get_status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)

    def get_priority_display(self):
        return dict(self.PRIORITY_CHOICES).get(self.priority, self.priority)

    def get_issue_type_display(self):
        return dict(self.ISSUE_TYPE_CHOICES).get(self.issue_type, self.issue_type)  # type: ignore

    def total_property_maintenance_cost(property_id):  # type: ignore
        return Issue.objects.filter(property_id=property_id).aggregate(
            total=models.Sum('cost')
        )['total'] or 0
    

class IssueMedia(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='media')
    file  = models.FileField(upload_to='issue_media/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def is_image(self):
        return self.file.url.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))

    def is_video(self):
        return self.file.url.lower().endswith(('.mp4', '.webm', '.ogg'))    


class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ('rent_due', 'Rent Due'),('announcement', 'Announcement'),('rate_increase', 'Rate Increase'),
    ]
    user        = models.ForeignKey(TenantProfile, on_delete=models.CASCADE, related_name='notifications')
    message     = models.TextField()
    notification_type = models.CharField(max_length=255, choices=NOTIFICATION_TYPE_CHOICES)
    created_at      = models.DateTimeField(auto_now_add=True)
    read            = models.BooleanField(default=False)
    priority        = models.PositiveIntegerField(default=1)  # 1-5 scale
    action_url      = models.URLField(null=True, blank=True)  # Link for action
    expires_at      = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Notification {self.id} - {self.user.user.username} - {self.notification_type}" # type: ignore


class PropertyManager(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, default='Unnamed Property Manager', related_name='property_manager_profile') # type: ignore
    created_by =models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_property_managers', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)
    properties = models.ManyToManyField(Property, related_name='property_managers', blank=True)

    
    def __str__(self):
        return f"{self.user}"


class LeaseAgreement(models.Model):
    property    = models.OneToOneField(Property, on_delete=models.CASCADE)
    user      = models.ForeignKey(TenantProfile, on_delete=models.CASCADE)
    lease_start = models.DateField(null=True, blank=True)
    lease_end   = models.DateField(null=True, blank=True)
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    terms       = models.TextField(null=True, blank=True)  # Lease terms and conditions
    is_active   = models.BooleanField(default=False, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at  = models.DateTimeField(auto_now=True)
    date_activated = models.DateField(null=True, blank=True)  # Only set when lease is activated

    def __str__(self):
        return f"Lease for {self.property.name} ({self.property.type}) - Tenant: {self.user.user.email if self.user and self.user.user else 'N/A'}"

    def activate(self):
        self.is_active = True
        self.date_activated = timezone.now().date()
        self.save()


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'), ('bank_transfer', 'Bank Transfer'), ('mobile_money', 'Mobile Money'), ('cheque', 'Cheque'),
        ('other', 'Other'),
    ]

    lease    = models.ForeignKey('LeaseAgreement', on_delete=models.CASCADE, null=True, blank=True)
    amount   = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # type: ignore
    payment_date   = models.DateField( auto_now_add=True, null=True, blank=True) # type: ignore
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, default='cash')
    reference_number = models.CharField(max_length=100, null=True, blank=True)
    is_rent   = models.BooleanField(default=False)
    for_month = models.CharField(max_length=7)

    class Meta:
        unique_together = ('lease', 'for_month')

    @property
    def tenant(self):
        return self.lease.user if self.lease else None

    def __str__(self):
        try:
            return f"{self.tenant.user.email} - {self.for_month}" # type: ignore
        except AttributeError:
            return f"N/A - {self.for_month}"




class PropertyOwner(models.Model):
    first_name   = models.CharField(max_length=100, null=True, blank=True)
    last_name    = models.CharField(max_length=100, null=True, blank=True)
    email        = models.EmailField(unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    address      = models.TextField(null=True, blank=True)
    image      = models.ImageField(upload_to='owner_images/', null=True, blank=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_property_owners', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.email}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()