from django import forms
from customuser.models import CustomUser
from property.models import Property, PropertyManager
from property.models import TenantProfile
from django_select2.forms import ModelSelect2MultipleWidget


class CustomUserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name',  'password']

    def clean_user_type(self):
        user_type = self.cleaned_data['user_type']
        if user_type not in ['tenant', 'manager']:
            raise forms.ValidationError("Invalid user type")
        return user_type

class SetPasswordForm(forms.Form):
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")

        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data


class TenantProfileForm(forms.ModelForm):
    class Meta:
        model = TenantProfile
        exclude = ['tenant','property_manager']  
        widgets = {
            'image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'occupation': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'national_id': forms.TextInput(attrs={'class': 'form-control'}),
            'last_address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),

        }

# Your ActivateAccountWithLeaseForm definition here (as you provided)

class ActivateAccountWithLeaseForm(forms.Form):
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)


# This form will only handle setting the password

# This form will handle the lease agreement acceptance later
class LeaseAgreementForm(forms.Form):
    agree_to_lease = forms.BooleanField(
        required=True,
        label="I have read and accept the lease agreement."
    )

    def clean_agree_to_lease(self):
        agree_to_lease = self.cleaned_data.get('agree_to_lease')
        if not agree_to_lease:
            raise forms.ValidationError("You must agree to the lease terms to activate your account.")
        return agree_to_lease
    
class ManagerProfileForm(forms.ModelForm):
    properties = forms.ModelMultipleChoiceField(
        queryset=Property.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Assign Properties",
    )

    class Meta:
        model = PropertyManager
        fields = ['properties']