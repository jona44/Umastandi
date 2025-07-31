import logging
from datetime import date
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.forms import ValidationError
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from customuser.models import CustomUser
from property.models import Property, PropertyManager, TenantProfile, LeaseAgreement
from .forms import (
    CustomUserRegistrationForm,
    ManagerProfileForm,
    SetPasswordForm,
    TenantProfileForm,
    LeaseAgreementForm
)
from django.views.decorators.http import require_http_methods
from django.core.mail import EmailMessage, get_connection ,send_mail
import ssl
import certifi
from .utils import redirect_after_login

logger = logging.getLogger(__name__)

@login_required
def register_tenant(request):
    if request.method == 'POST':
        form = CustomUserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.created_by = request.user
            user.user_type = 'tenant'
            user.set_password(form.cleaned_data['password'])
            user.save()

            activation_link = request.build_absolute_uri(
                reverse('activate_account', args=[user.activation_token])
            )

            # Use Django's simple send_mail function
            send_mail(
                subject='Activate Your Account',
                message=f'Click the link to activate your account: {activation_link}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            profile_form = TenantProfileForm(initial={'user': user})
            return render(request, 'customuser/partials/tenant_profile_form.html', {
                'form': profile_form,
                'user': user
            })
    else:
        form = CustomUserRegistrationForm()

    template = 'customuser/partials/register_form.html' if request.htmx else 'customuser/register.html'
    return render(request, template, {'form': form})




@login_required
def create_tenant_profile(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id, user_type='tenant')

    if request.method == 'POST':
        form = TenantProfileForm(request.POST)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = user
            profile.save()

            if request.htmx:
                return render(request, 'customuser/partials/success_message.html', {
                    'message': "Tenant profile successfully created."
                })

            return redirect('tenant_dashboard')  # or wherever you want

    else:
        form = TenantProfileForm(initial={'user': user})

    return render(request, 'customuser/partials/tenant_profile_form.html', {
        'form': form,
        'user': user
    })



@login_required
def tenant_profile_detail(request, user_id):
    # Get the tenant user
    user = get_object_or_404(CustomUser, id=user_id, user_type='tenant')
    
    # Get the tenant profile (linked via 'user', not 'tenant')
    tenant_profile = get_object_or_404(TenantProfile, user=user)

    return render(request, 'customuser/tenant_profile_detail.html', {
        'user': user,
        'tenant_profile': tenant_profile,
    })



@login_required
def update_tenant_profile(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id, user_type='tenant')
    profile = get_object_or_404(TenantProfile, user=user)

    if request.method == 'POST':
        form = TenantProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            try:
                tenant_profile = form.save(commit=False)
                tenant_profile.user = user  # Ensure tenant assignment
                tenant_profile.clean()
                tenant_profile.save()
                messages.success(request, "Tenant profile updated successfully.")
                return redirect('tenant_profile_detail', user_id=user.id) # type: ignore
            except ValidationError as e:
                messages.error(request, f"Validation error: {e}")
    else:
        form = TenantProfileForm(instance=profile)

    return render(request, 'customuser/profile_update.html', {
        'form': form,
        'profile': profile,
        'user': user
    })




@login_required
def tenant_list(request):
    tenants = TenantProfile.objects.select_related('user').all()
    tenant_count = tenants.count()

    context = {
        'tenants': tenants,
        'tenant_count': tenant_count,
    }

    if request.htmx:
        html = render_to_string('customuser/partials/tenant_list_table.html', context, request=request)
        return HttpResponse(html)
        
    return render(request, 'customuser/tenant_list.html', context)

@login_required
def delete_tenant_profile(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)

    if user.user_type != 'tenant':
        messages.error(request, "This user is not classified as a tenant.")
        return redirect('tenant_list')

    profile = get_object_or_404(TenantProfile, user=user)

    if request.method == 'POST':
        profile.delete()
        messages.success(request, "Tenant profile deleted successfully.")
        return redirect('tenant_list')

    return render(request, 'customuser/tenant_profile_confirm_delete.html', {
        'profile': profile,
        'user': user
    })



@require_http_methods(["GET", "POST"])
def create_manager(request):
    if request.method == 'POST':
        form = CustomUserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.created_by = request.user if request.user.is_authenticated else None
            user.user_type = 'manager'
            user.set_password(form.cleaned_data['password'])
            user.save()

            PropertyManager.objects.create(user=user)

            activation_link = f"http://127.0.0.1:8000/activate/{user.activation_token}/"
            send_mail(
                subject='Activate Your Account',
                message=f'Click the link to activate your account: {activation_link}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )

            # ✅ HTMX redirect via HX-Redirect header
            response = HttpResponse()
            response["HX-Redirect"] = f"/customuser/manager_profile/{user.id}/"
            return response

        # ❌ Invalid form
        html = render_to_string('customuser/partials/_create_manager_form.html', {'form': form}, request=request)
        return HttpResponse(html)

    # GET request – return form
    form = CustomUserRegistrationForm()
    html = render_to_string('customuser/partials/_create_manager_form.html', {'form': form}, request=request)
    return HttpResponse(html)


def manager_profile(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id, user_type='manager')
    profile, _ = PropertyManager.objects.get_or_create(user=user)

    if request.method == 'POST':
        form = ManagerProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Manager profile updated successfully.")
            return redirect('manager_dashboard')  # or 'manager_profile', user_id=user.id
    else:
        form = ManagerProfileForm(instance=profile)

    return render(request, 'customuser/manager_profile_form.html', {
        'form': form,
        'manager': user,
    })


@login_required
def edit_manager(request, manager_id):
    # Get the user first, then get the PropertyManager
    user = get_object_or_404(CustomUser, id=manager_id, user_type='manager')

    # Get or create PropertyManager instance
    manager, created = PropertyManager.objects.get_or_create(manager=user)

    if request.method == 'POST':
        form = CustomUserRegistrationForm(request.POST, instance=manager)
        if form.is_valid():
            form.save()
            messages.success(request, "Manager profile updated successfully.")
            return redirect('manager_dashboard')  # change as needed
    else:
        form = CustomUserRegistrationForm(instance=manager)

    return render(request, 'customuser/edit_manager.html', {
        'form': form, 
        'manager': manager,
        'user': user
    })



def logout_view(request):
    logout(request)
    return redirect('login')



def activate_account(request, token):
    user = get_object_or_404(CustomUser, activation_token=token, is_active=False)

    if request.method == 'POST':
        form = SetPasswordForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password1']
            user.password = make_password(password)
            user.activation_token = None
            user.is_active = True
            user.is_staff = True
            user.save()
            messages.success(request, 'Your account has been activated. Please log in.')
            return redirect('login')
    else:
        form = SetPasswordForm()

    return render(request, 'customuser/set_password_after_activation.html', {'form': form})


from django.utils import timezone  # ensure timezone import is present

@login_required
def activate_lease(request):
    try:
        tenant_profile = request.user.tenant_profile  # type: ignore
    except TenantProfile.DoesNotExist:
        messages.error(request, "Tenant profile not found.")
        return redirect('login')

    lease = LeaseAgreement.objects.filter(user=tenant_profile, is_active=False).first()


    if not lease:
        messages.info(request, "No lease requires activation or it is already active.")
        return redirect('tenant_dashboard')

    if request.method == 'POST':
        if 'agree' in request.POST:
            lease.activate()  # Clean call to the model method
            messages.success(request, "Lease has been activated.")
            return redirect('tenant_dashboard')
        else:
            messages.error(request, "You must agree to the lease terms before proceeding.")

    return render(request, 'customuser/activate_lease.html', {
        'lease': lease
    })



@login_required
def deactivate_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)

    if request.method == 'POST':
        if user.user_type != 'tenant':
            return HttpResponseBadRequest("Only tenant users can be deactivated.")

        user.is_active = False
        user.is_staff = False # type: ignore
        user.save()

        # Free properties
        properties = Property.objects.filter(tenant__user=user)
        for prop in properties:
            prop.tenant = None
            prop.is_occupied = False
            prop.save()

        return render(request, 'customuser/partials/success_message.html', {
            'message': f"{user.get_full_name()} has been deactivated and their property is now available."
        })

    return HttpResponseBadRequest("Invalid request method.")


