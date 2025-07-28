from django import forms
from .models import LeaseAgreement, Payment, Property, PropertyOwner, TenantProfile,Issue
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from customuser.models import  CustomUser
from django.contrib import messages
import datetime


class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = [
            'name','property_owner', 'address', 'type', 
            'details',  'bedrooms', 'bathrooms', 'square_footage'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'property_owner': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'details': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'bedrooms': forms.NumberInput(attrs={'class': 'form-control'}),
            'bathrooms': forms.NumberInput(attrs={'class': 'form-control'}),
            'square_footage': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class IssueForm(forms.ModelForm):
    class Meta:
        model = Issue
        fields = ['priority',  'description','issue_type' ,'image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'issue_type': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            
        }
        labels = {
            'priority': 'Priority',
            'description': 'Description',
            'issue_type': 'Issue Type',
            'image': 'Upload Image',
        }
        


class LeaseAgreementForm(forms.ModelForm):
    class Meta:
        model = LeaseAgreement
        fields = ['property',  'lease_start', 'lease_end', 'rent_amount', 'security_deposit','terms']
        widgets = {
            'property': forms.Select(attrs={'class': 'form-control'}),
            'lease_start': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'lease_end': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'rent_amount': forms.NumberInput(attrs={'step': '100', 'class': 'form-control'}),
            'security_deposit': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'terms': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }


class LeaseActivationForm(forms.Form):
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")
    agree_to_terms = forms.BooleanField(label="I have read and agree to the lease terms.")
    

class PaymentCaptureForm(forms.ModelForm):
    MONTH_CHOICES = []

    # Generate 6 months before and after today
    today = datetime.date.today().replace(day=1)
    for i in range(-6, 7):
        month = today + datetime.timedelta(days=i * 30)
        value = month.strftime('%Y-%m')
        label = month.strftime('%B %Y')
        MONTH_CHOICES.append((value, label))

    for_month = forms.ChoiceField(choices=MONTH_CHOICES, label='Month')

    class Meta:
        model = Payment
        fields = ['for_month', 'amount', 'payment_method', 'reference_number']
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
        }


class SelectTenantPaymentForm(forms.Form):
    MONTH_CHOICES = []

    today = datetime.date.today().replace(day=1)

    # Generate months: 6 past, current, 6 future
    for i in range(-6, 7):  # -6 to 6 inclusive
        month_date = today + datetime.timedelta(days=30 * i)
        MONTH_CHOICES.append((
            month_date.strftime("%Y-%m"),
            month_date.strftime("%B %Y")
        ))

    for_month = forms.ChoiceField(choices=MONTH_CHOICES, label="Select Month")
    tenant = forms.ModelChoiceField(queryset=CustomUser.objects.none(), required=True, label="Tenant")

    def __init__(self, *args, **kwargs):
        tenants_queryset = kwargs.pop('tenants_queryset', None)
        super().__init__(*args, **kwargs)
        if tenants_queryset is not None:
            self.fields['tenant'].queryset = tenants_queryset # type: ignore
        else:
            self.fields['tenant'].queryset = CustomUser.objects.none() # type: ignore



class PropertyOwnerForm(forms.ModelForm):
    class Meta:
        model = PropertyOwner
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'address']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }