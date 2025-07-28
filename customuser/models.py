# user/models.py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
import random
import string

def generate_unique_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=20))

class CustomUserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, first_name=first_name, last_name=last_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, first_name, last_name, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    USER_TYPE = (
        ('manager', 'manager'),
        ('tenant', 'tenant'),
    )

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name  = models.CharField(max_length=30)
    user_type  = models.CharField(max_length=30, choices=USER_TYPE)
    is_active  = models.BooleanField(default=False)
    is_staff   = models.BooleanField(default=False)
    activation_token = models.CharField(max_length=20, null=True, blank=True)
    created_by = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='created_users')

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def save(self, *args, **kwargs):
        if not self.pk:  # Only on creation
            if self.user_type in ['tenant', 'manager']:
                self.activation_token = generate_unique_token()
                self.set_unusable_password()
                self.is_active = False  # Account not active until user sets password
            else:
                self.is_active = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'

    class Meta:
        verbose_name = 'Custom User'
        verbose_name_plural = 'Custom Users'