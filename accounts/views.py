from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm, UserProfileForm

def signup(request):
    """User registration view"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('travel:home')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def profile(request):
    """User profile view and update"""
    profile = request.user.profile
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=profile)
    
    context = {
        'form': form,
        'user': request.user,
    }
    return render(request, 'accounts/profile.html', context)