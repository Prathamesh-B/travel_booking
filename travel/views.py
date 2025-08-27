from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from .models import TravelOption, Booking
from .forms import TravelSearchForm, BookingForm
from django.views.generic import ListView, DetailView

def home(request):
    """Home page with search functionality"""
    form = TravelSearchForm(request.GET or None)
    travel_options = TravelOption.objects.filter(
        departure_date__gte=timezone.now().date(),
        available_seats__gt=0
    )
    
    if form.is_valid():
        # Apply filters
        if form.cleaned_data.get('type'):
            travel_options = travel_options.filter(type=form.cleaned_data['type'])
        if form.cleaned_data.get('source'):
            travel_options = travel_options.filter(
                source__icontains=form.cleaned_data['source']
            )
        if form.cleaned_data.get('destination'):
            travel_options = travel_options.filter(
                destination__icontains=form.cleaned_data['destination']
            )
        if form.cleaned_data.get('departure_date'):
            travel_options = travel_options.filter(
                departure_date=form.cleaned_data['departure_date']
            )
        if form.cleaned_data.get('min_price'):
            travel_options = travel_options.filter(
                price__gte=form.cleaned_data['min_price']
            )
        if form.cleaned_data.get('max_price'):
            travel_options = travel_options.filter(
                price__lte=form.cleaned_data['max_price']
            )
    
    # Pagination
    paginator = Paginator(travel_options, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'total_results': travel_options.count(),
    }
    return render(request, 'travel/home.html', context)

def travel_detail(request, pk):
    """Travel option detail view"""
    travel_option = get_object_or_404(TravelOption, pk=pk)
    context = {
        'travel_option': travel_option,
    }
    return render(request, 'travel/travel_detail.html', context)

@login_required
def book_travel(request, pk):
    """Book a travel option"""
    travel_option = get_object_or_404(TravelOption, pk=pk)
    
    # Check if travel option is still available
    if travel_option.available_seats == 0:
        messages.error(request, 'This travel option is fully booked.')
        return redirect('travel:travel_detail', pk=pk)
    
    if travel_option.departure_date < timezone.now().date():
        messages.error(request, 'This travel option has already departed.')
        return redirect('travel:travel_detail', pk=pk)
    
    if request.method == 'POST':
        form = BookingForm(request.POST, travel_option=travel_option)
        if form.is_valid():
            with transaction.atomic():
                # Create booking
                booking = form.save(commit=False)
                booking.user = request.user
                booking.travel_option = travel_option
                booking.total_price = travel_option.price * booking.number_of_seats
                
                # Store passenger details
                booking.passenger_details = {
                    'names': form.cleaned_data['passenger_names'],
                    'contact_phone': form.cleaned_data['contact_phone'],
                }
                
                # Update available seats
                travel_option.available_seats -= booking.number_of_seats
                travel_option.save()
                
                booking.save()
                
                messages.success(
                    request, 
                    f'Booking confirmed! Your booking ID is {booking.booking_id}'
                )
                return redirect('travel:booking_detail', pk=booking.pk)
    else:
        form = BookingForm(travel_option=travel_option)
    
    context = {
        'form': form,
        'travel_option': travel_option,
    }
    return render(request, 'travel/book_travel.html', context)

@login_required
def booking_list(request):
    """User's booking list"""
    bookings = Booking.objects.filter(user=request.user)
    
    # Filter by status if requested
    status_filter = request.GET.get('status')
    if status_filter in ['confirmed', 'cancelled']:
        bookings = bookings.filter(status=status_filter)
    
    paginator = Paginator(bookings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
    }
    return render(request, 'travel/booking_list.html', context)

@login_required
def booking_detail(request, pk):
    """Booking detail view"""
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    context = {
        'booking': booking,
    }
    return render(request, 'travel/booking_detail.html', context)

@login_required
def cancel_booking(request, pk):
    """Cancel a booking"""
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    
    if not booking.can_be_cancelled:
        messages.error(request, 'This booking cannot be cancelled.')
        return redirect('travel:booking_detail', pk=pk)
    
    if request.method == 'POST':
        if booking.cancel_booking():
            messages.success(request, 'Booking cancelled successfully.')
        else:
            messages.error(request, 'Unable to cancel booking.')
        return redirect('travel:booking_detail', pk=pk)
    
    context = {
        'booking': booking,
    }
    return render(request, 'travel/cancel_booking.html', context)