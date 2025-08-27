from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
from decimal import Decimal

class TravelOption(models.Model):
    TRAVEL_TYPES = [
        ('flight', 'Flight'),
        ('train', 'Train'),
        ('bus', 'Bus'),
    ]
    
    travel_id = models.CharField(max_length=20, unique=True)
    type = models.CharField(max_length=10, choices=TRAVEL_TYPES)
    source = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    departure_date = models.DateField()
    departure_time = models.TimeField()
    arrival_date = models.DateField()
    arrival_time = models.TimeField()
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    available_seats = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    total_seats = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['departure_date', 'departure_time']
        
    def __str__(self):
        return f"{self.travel_id} - {self.get_type_display()} from {self.source} to {self.destination}"
    
    def get_absolute_url(self):
        return reverse('travel:travel_detail', kwargs={'pk': self.pk})
    
    def is_available(self, requested_seats=1):
        return self.available_seats >= requested_seats
    
    @property
    def is_fully_booked(self):
        return self.available_seats == 0

class Booking(models.Model):
    BOOKING_STATUS = [
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]
    
    booking_id = models.CharField(max_length=20, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    travel_option = models.ForeignKey(TravelOption, on_delete=models.CASCADE, related_name='bookings')
    number_of_seats = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    booking_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=BOOKING_STATUS, default='confirmed')
    passenger_details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-booking_date']
        
    def __str__(self):
        return f"Booking {self.booking_id} - {self.user.username}"
    
    def save(self, *args, **kwargs):
        if not self.booking_id:
            import uuid
            self.booking_id = f"BK{str(uuid.uuid4())[:8].upper()}"
        
        if not self.total_price:
            self.total_price = self.travel_option.price * self.number_of_seats
            
        super().save(*args, **kwargs)
    
    def cancel_booking(self):
        if self.status == 'confirmed':
            self.status = 'cancelled'
            # Return seats to travel option
            self.travel_option.available_seats += self.number_of_seats
            self.travel_option.save()
            self.save()
            return True
        return False
    
    @property
    def can_be_cancelled(self):
        from django.utils import timezone
        return (self.status == 'confirmed' and 
                self.travel_option.departure_date > timezone.now().date())