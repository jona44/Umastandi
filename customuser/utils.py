from django.shortcuts import redirect

def redirect_after_login(user):
    if user.user_type == 'tenant':
        return redirect('tenant_dashboard')  # Replace with your actual URL name
    elif user.user_type == 'manager':
        return redirect('manager_dashboard')
    else:
        return redirect('home')  # Fallback
    
def get_user_display_name(user):
    if user.first_name and user.last_name:
        return f"{user.first_name} {user.last_name}"
    elif user.first_name:
        return user.first_name
    elif user.email: # Fallback to email if no name is available
        return user.email
    return str(user) # Fallback to default __str__