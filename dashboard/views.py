from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseForbidden
from property. models import Issue, LeaseAgreement, Notification, Payment, Property, TenantProfile
from django.utils import timezone
from datetime import date, timedelta



def get_rent_cycle_table(leases):
    from calendar import monthrange
    today = date.today()

    # Get the upcoming rent cycle month as YYYY-MM
    next_month = today.replace(day=1) + timedelta(days=32)
    next_month = next_month.replace(day=1)
    for_month_str = next_month.strftime('%Y-%m')

    table_data = []

    for lease in leases:
        tenant = lease.user.user  # This should be the TenantProfile instance
        property_obj = lease.property

        payment = Payment.objects.filter(
            lease=lease,
            for_month=for_month_str,
            is_rent=True
        ).first()

        table_data.append({
            'tenant': tenant.get_full_name(), # type: ignore
            'amount': lease.rent_amount,
            'for_month': for_month_str,
            'property': property_obj.name,
            'reference': payment.reference_number if payment else '',
            'status': 'Paid' if payment else 'Unpaid',
            'lease_id': lease.id,
            'tenant_profile_id': tenant.id,  # Add this line
            'lease': lease,  # Also include the lease object itself
        })

    return table_data

@login_required
def tenant_dashboard(request):
    tenant = get_object_or_404(TenantProfile, user=request.user)

    lease = LeaseAgreement.objects.filter(user=tenant).first()  # ✅ FIXED HERE

    # 🔐 Redirect to lease activation page if lease exists but is not active
    if lease and not lease.is_active:
        messages.info(request, "Please review and activate your lease before proceeding.")
        return redirect('activate_lease')

    payments = Payment.objects.filter(lease=lease).order_by('-payment_date')[:3] if lease else []
    issues = Issue.objects.filter(user=tenant).order_by('-created_at')[:3]
    notifications = Notification.objects.filter(user=tenant).order_by('-created_at')[:3]

    context = {
        'tenant': tenant,
        'lease': lease,
        'payments': payments,
        'issues': issues,
        'notifications': notifications,
    }

    return render(request, 'dashboard/tenant_dashboard.html', context)



@login_required
def manager_dashboard(request):
    manager = request.user.property_manager_profile
    total_properties = Property.objects.count()
    total_tenants = TenantProfile.objects.count()
    
    properties = Property.objects.all()
    leases = LeaseAgreement.objects.filter(property__in=properties, is_active=True)

    combined_payments = get_rent_cycle_table(leases)  # 👈 use helper here

    open_issues = Issue.objects.filter(status='open').count()
    in_progress_issues = Issue.objects.filter(status='in_progress').count()
    resolved_issues = Issue.objects.filter(status='resolved').count()
    unread_notifications = Notification.objects.filter(read=False).count()

    recent_issues = Issue.objects.order_by('-created_at')[:5]

    context = {
        'properties': properties,
        'leases': leases,
        'combined_payments': combined_payments,
        'total_properties': total_properties,
        'total_tenants': total_tenants,
        'open_issues': open_issues,
        'in_progress_issues': in_progress_issues,
        'resolved_issues': resolved_issues,
        'unread_notifications': unread_notifications,
        'recent_issues': recent_issues,
        
    }

    return render(request, 'dashboard/manager_dashboard.html', context)


def home(request):
    if request.user.is_authenticated:
        if request.user.user_type == 'tenant':
            return tenant_dashboard(request)
        elif request.user.user_type == 'manager':
            return manager_dashboard(request)
    return render(request, 'dashboard/home.html')



