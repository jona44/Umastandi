from decimal import Decimal
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from customuser.models import CustomUser
from .forms import  IssueForm, LeaseAgreementForm,PaymentCaptureForm,  PropertyForm, PropertyOwnerForm, SelectTenantPaymentForm
from .models import LeaseAgreement,  Payment,  Property, PropertyOwner,  TenantProfile,  Issue
from datetime import datetime
from django.utils.dateparse import parse_date
from django.db import IntegrityError
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods
import csv
from django.db.models import Q
from django.core.mail import EmailMessage, get_connection,send_mail
import ssl
import certifi

@login_required
def register_property(request):
    if request.method == 'POST':
        form = PropertyForm(request.POST)
        if form.is_valid():
            property = form.save()
            if request.htmx:
                response = HttpResponse(status=204)
                response['HX-Trigger'] = 'ownerAddedSuccess'
                return response
            messages.success(request, "Property registered successfully.")
            return redirect('property_list')
    else:
        form = PropertyForm()

    template = 'property/partials/property_register_form.html' if request.htmx else 'property/property_register.html'
    return render(request, template, {'form': form})


from django.template.loader import render_to_string
from django.http import HttpResponse

@login_required
def property_list(request):
    properties = Property.objects.all()
    total_properties_count = properties.count()
    occupied_properties_count = properties.filter(is_occupied=True).count()

    context = {
        'properties': properties,
        'total_properties_count': total_properties_count,
        'occupied_properties_count': occupied_properties_count,
    }

    if request.htmx:
        html = render_to_string('property/partials/_property_list_table.html', context, request=request)
        return HttpResponse(html)
    return render(request, 'property/property_list.html', context)



@login_required
def property_update(request, pk):
    property_instance = Property.objects.get(pk=pk)
    if request.method == 'POST':
        form = PropertyForm(request.POST, instance=property_instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Property updated successfully.")
            return redirect('property_list')
    else:
        form = PropertyForm(instance=property_instance)
    return render(request, 'property/property_update.html', {'form': form, 'property': property_instance})


from django.db.models import Sum

@login_required
def property_detail(request, pk):
    property = get_object_or_404(Property, pk=pk)
    issues = Issue.objects.filter(property=property).order_by('-created_at')  # latest first
    total_cost = issues.aggregate(Sum('cost'))['cost__sum'] or 0 # type: ignore

    template = 'property/partials/_property_detail_modal.html' if request.htmx else 'property/property_detail.html'
    return render(request, template, {
        'property': property,
        'issues': issues,
        'total_cost': total_cost,
    })




@login_required
def property_delete(request, pk):
    property_instance = Property.objects.get(pk=pk)
    if request.method == 'POST':
        property_instance.delete()
        messages.success(request, "Property deleted successfully.")
        return redirect('property_list')
    return render(request, 'property/property_confirm_delete.html', {'property': property_instance})



@login_required
@require_http_methods(["GET", "POST"])
def log_issue(request):
    try:
        tenant = request.user.tenant_profile
    except TenantProfile.DoesNotExist:
        messages.error(request, "You are not registered as a tenant.")
        return redirect('tenant_dashboard')

    lease = LeaseAgreement.objects.filter(user=tenant, is_active=True).first()

    if not lease or not lease.property:
        messages.error(request, "You are not assigned to a property through a lease.")
        return redirect('tenant_dashboard')

    property_instance = lease.property

    if request.method == 'POST':
        form = IssueForm(request.POST, request.FILES)
        if form.is_valid():
            issue = form.save(commit=False)
            issue.tenant = tenant
            issue.user = tenant
            issue.property = property_instance
            issue.save()

            if request.htmx:
                return HttpResponse('<script>window.location.reload()</script>')  # Close modal and reload page
            messages.success(request, "Your issue has been logged successfully.")
            return redirect('tenant_dashboard')
    else:
        form = IssueForm()

    context = {'form': form}

    if request.htmx:
        html = render_to_string('property/partials/_log_issue_form_modal.html', context, request=request)
        return HttpResponse(html)

    return render(request, 'property/log_issue.html', context)




@login_required
def issue_history(request):
    """Enhanced issue history view with search functionality"""
    
    issues = Issue.objects.select_related('property')
    
    # Get filters
    status = request.GET.get('status', '').strip()
    priority = request.GET.get('priority', '').strip()
    issue_type = request.GET.get('issue_type', '').strip()
    search = request.GET.get('search', '').strip()
    
    # Apply filters
    if status:
        issues = issues.filter(status=status)
    if priority:
        issues = issues.filter(priority=priority)
    if issue_type:
        issues = issues.filter(issue_type=issue_type)
    if search:
        issues = issues.filter(
            Q(property__name__icontains=search) |
            Q(tenant__icontains=search) |
            Q(description__icontains=search) |
            Q(id__icontains=search)
        )
    
    issues = issues.order_by('-created_at')
    
    context = {
        'issues': issues,
        'filters': {
            'status': status,
            'priority': priority,
            'issue_type': issue_type,
            'search': search,
        },
        'status_choices': Issue.STATUS_CHOICES,
        'priority_choices': Issue.PRIORITY_CHOICES,
        'type_choices': Issue.ISSUE_TYPE_CHOICES,
    }
    
    if request.htmx:
        return render(request, 'property/partials/issue_table.html', context)
    
    return render(request, 'property/issue_history.html', context)


@require_http_methods(["GET", "POST"])
@login_required
def update_issue_status(request, issue_id):
    issue = get_object_or_404(Issue, id=issue_id)

    if not hasattr(request.user, 'property_manager_profile'):
        return HttpResponse("Unauthorized", status=403)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        resolution_notes = request.POST.get('resolution_notes', '').strip()
        cost_str = request.POST.get('cost', '').strip()

        if new_status in dict(Issue.STATUS_CHOICES):
            issue.status = new_status
            issue.assigned_to = request.user.property_manager_profile

            if new_status == 'resolved':
                issue.resolved_at = timezone.now()
                issue.resolution_notes = resolution_notes

                cost_str = request.POST.get('cost', '').strip()
                if cost_str:
                    try:
                        issue.cost = Decimal(cost_str)
                    except:
                        issue.cost = None  # Or log invalid input
            else:
                issue.resolved_at = None
                issue.resolution_notes = ""
                issue.cost = None  # Clear cost if not resolved

            issue.save()


        return HttpResponse("""
            <div class="alert alert-success">Issue updated successfully.</div>
            <script>
                setTimeout(() => {
                    location.reload();
                }, 800);
            </script>
        """)

    return render(request, 'property/partials/_issue_form_modal.html', {
        'issue': issue,
        'status_choices': Issue.STATUS_CHOICES
    })


@login_required
def export_issues(request):
    """Export filtered issues to CSV"""
    
    issues = Issue.objects.select_related('property')
    
    # Apply same filters as main view
    status = request.GET.get('status', '').strip()
    priority = request.GET.get('priority', '').strip()
    issue_type = request.GET.get('issue_type', '').strip()
    search = request.GET.get('search', '').strip()
    
    if status:
        issues = issues.filter(status=status)
    if priority:
        issues = issues.filter(priority=priority)
    if issue_type:
        issues = issues.filter(issue_type=issue_type)
    if search:
        issues = issues.filter(
            Q(property__name__icontains=search) |
            Q(tenant__icontains=search) |
            Q(description__icontains=search) |
            Q(id__icontains=search)
        )
    
    issues = issues.order_by('-created_at')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    response['Content-Disposition'] = f'attachment; filename="issues_{timestamp}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ID', 'Property', 'Tenant', 'Status', 'Priority', 'Type', 'Created'])
    
    for issue in issues:
        writer.writerow([
            issue.id, # type: ignore
            issue.property.name,
            issue.user or 'N/A',
            issue.get_status_display(),
            issue.get_priority_display(),
            issue.get_issue_type_display(),
            issue.created_at.strftime('%Y-%m-%d')
        ])
    
    return response


@login_required
def create_lease_agreement(request, tenant_profile_id):
    tenant = get_object_or_404(TenantProfile, id=tenant_profile_id)

    # Get list of TenantProfile IDs, not CustomUser IDs
    tenants_with_lease = LeaseAgreement.objects.values_list('user_id', flat=True)
    if tenant.id in tenants_with_lease: # type: ignore
        messages.error(request, "This tenant already has a lease agreement.")
        return redirect('tenant_profile_detail', user_id=tenant.user.id)  # type: ignore # ✅ redirect with CustomUser.id

    if request.method == 'POST':
        form = LeaseAgreementForm(request.POST)
        form.fields['property'].queryset = Property.objects.filter(is_occupied=False) # type: ignore

        if form.is_valid():
            lease = form.save(commit=False)
            lease.user = tenant  # ✅ Assign the TenantProfile, not CustomUser
            property_obj = lease.property

            property_obj.is_occupied = True
            property_obj.save()

            lease.save()
            messages.success(request, "Lease Agreement created and property assigned successfully.")
            return redirect('lease_agreement_detail', tenant_profile_id=tenant.id) # type: ignore
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = LeaseAgreementForm()
        form.fields.pop('tenant', None)
        form.fields['property'].queryset = Property.objects.filter(is_occupied=False) # type: ignore

    return render(request, 'property/create_lease_agreement.html', {'form': form, 'tenant': tenant})



def lease_agreement_detail(request, tenant_profile_id):
    tenant_profile = get_object_or_404(TenantProfile, id=tenant_profile_id)
    lease = LeaseAgreement.objects.filter(user=tenant_profile).first()

    if not lease:
        messages.error(request, "No lease agreement found for this tenant.")
        return redirect('tenant_dashboard')  # or another logical place

    payments = Payment.objects.filter(lease=lease).order_by('-payment_date')
    for p in payments:
        try:
            p.month_label = datetime.strptime(p.for_month, "%Y-%m").strftime("%B %Y")  # type: ignore
        except (ValueError, TypeError):
            p.month_label = p.for_month  # type: ignore # fallback

    return render(request, 'property/lease_agreement_detail.html', {
        'lease': lease,
        'payments': payments,
    })





@login_required
@require_http_methods(["GET", "POST"])
def capture_payment(request, lease_id, for_month):
    lease = get_object_or_404(LeaseAgreement, id=lease_id)

    if Payment.objects.filter(lease=lease, for_month=for_month).exists():
        return HttpResponse(
            render_to_string("property/partials/alert.html", {
                "message": f"A payment for {for_month} already exists.",
                "alert_type": "warning"
            }),
            status=400
        )

    if request.method == 'POST':
        form = PaymentCaptureForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.lease = lease
            payment.is_rent = True
            payment.for_month = for_month
            try:
                payment.save()

                tenant_email = getattr(getattr(lease.user, 'tenant', None), 'email', None)
                if tenant_email:
                    send_mail(
                        subject="Payment Confirmation",
                        message=f"Dear {lease.user.user.get_full_name()},\n\n" # type: ignore
                                f"Your payment of R{payment.amount} for {payment.for_month} has been received.\n\n"
                                f"Thank you.",
                        from_email=None,
                        recipient_list=[tenant_email],
                        fail_silently=True,
                    )

                response = render_to_string("property/partials/alert.html", {
                    "message": "Payment successfully captured.",
                    "alert_type": "success"
                }, request=request)

                return HttpResponse(response)
            except IntegrityError:
                return HttpResponse(
                    render_to_string("property/partials/alert.html", {
                        "message": f"Payment already exists for {for_month}.",
                        "alert_type": "danger"
                    }),
                    status=400
                )
    else:
        form = PaymentCaptureForm(initial={
            'amount': lease.rent_amount,
            'for_month': for_month,
        })

    html = render_to_string("property/partials/payment_form_modal.html", {
        'form': form,
        'lease': lease,
        'for_month': for_month,
    }, request=request)
    return HttpResponse(html)


@login_required
def register_property_owner(request):
    if request.method == 'POST':
        form = PropertyOwnerForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            if request.htmx:
                # Send an HTMX trigger to show a success toast/message
                response = HttpResponse(status=204)
                response['HX-Trigger'] = 'ownerAddedSuccess'
                return response
            messages.success(request, "Property Owner registered successfully.")
            return redirect('property_owner_list')
    else:
        form = PropertyOwnerForm()

    return render(request,'property/partials/_register_owner_form.html', {'form': form})




@login_required
def property_owner_list(request):
    owners = PropertyOwner.objects.all()
    owner_count = owners.count()
    if owner_count == 0:
        messages.info(request, "No property owners found.")
    context = {
        'owners': owners,
        'owner_count': owner_count,
    }
    return render(request, 'property/property_owner_list.html', context)


@login_required
def update_property_owner(request, owner_id):
    owner = get_object_or_404(PropertyOwner, id=owner_id)

    if request.method == 'POST':
        form = PropertyOwnerForm(request.POST, request.FILES, instance=owner)
        if form.is_valid():
            form.save()
            messages.success(request, "Property Owner details updated successfully.")
            return redirect('property_owner_list')  # Or wherever you list owners
    else:
        form = PropertyOwnerForm(instance=owner)

    return render(request, 'property/update_property_owner.html', {'form': form, 'owner': owner})


@login_required
def delete_property_owner(request, owner_id):
    owner = get_object_or_404(PropertyOwner, id=owner_id)

    if request.method == 'POST':
        owner.delete()
        messages.success(request, "Property Owner deleted successfully.")
        return redirect('property_owner_list')

    return render(request, 'property/delete_property_owner.html', {'owner': owner})


@login_required
def property_owner_detail(request, owner_id):
    owner = get_object_or_404(PropertyOwner, id=owner_id)
    return render(request, 'property/property_owner_detail.html', {'owner': owner})