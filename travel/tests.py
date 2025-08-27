from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from datetime import date, time, timedelta
from .models import TravelOption, Booking
from .forms import TravelSearchForm, BookingForm

class TravelOptionModelTest(TestCase):
    def setUp(self):
        self.travel_option = TravelOption.objects.create(
            travel_id='FL001',
            type='flight',
            source='New York',
            destination='Los Angeles',
            departure_date=date.today() + timedelta(days=7),
            departure_time=time(10, 30),
            arrival_date=date.today() + timedelta(days=7),
            arrival_time=time(13, 45),
            price=Decimal('299.99'),
            available_seats=150,
            total_seats=150
        )
    
    def test_travel_option_creation(self):
        self.assertEqual(self.travel_option.travel_id, 'FL001')
        self.assertEqual(self.travel_option.type, 'flight')
        self.assertEqual(str(self.travel_option), 'FL001 - Flight from New York to Los Angeles')
    
    def test_is_available(self):
        self.assertTrue(self.travel_option.is_available(1))
        self.assertTrue(self.travel_option.is_available(50))
        self.assertFalse(self.travel_option.is_available(151))
    
    def test_is_fully_booked(self):
        self.assertFalse(self.travel_option.is_fully_booked)
        self.travel_option.available_seats = 0
        self.assertTrue(self.travel_option.is_fully_booked)

class BookingModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.travel_option = TravelOption.objects.create(
            travel_id='TR001',
            type='train',
            source='Boston',
            destination='Philadelphia',
            departure_date=date.today() + timedelta(days=5),
            departure_time=time(14, 00),
            arrival_date=date.today() + timedelta(days=5),
            arrival_time=time(18, 30),
            price=Decimal('89.50'),
            available_seats=200,
            total_seats=200
        )
    
    def test_booking_creation(self):
        booking = Booking.objects.create(
            user=self.user,
            travel_option=self.travel_option,
            number_of_seats=2
        )
        
        self.assertTrue(booking.booking_id.startswith('BK'))
        self.assertEqual(booking.total_price, Decimal('179.00'))
        self.assertEqual(booking.status, 'confirmed')
        self.assertEqual(str(booking), f'Booking {booking.booking_id} - testuser')
    
    def test_booking_cancellation(self):
        booking = Booking.objects.create(
            user=self.user,
            travel_option=self.travel_option,
            number_of_seats=3
        )
        
        initial_seats = self.travel_option.available_seats
        self.travel_option.available_seats -= booking.number_of_seats
        self.travel_option.save()
        
        self.assertTrue(booking.cancel_booking())
        self.travel_option.refresh_from_db()
        self.assertEqual(self.travel_option.available_seats, initial_seats)
        self.assertEqual(booking.status, 'cancelled')
    
    def test_can_be_cancelled(self):
        # Future booking
        booking = Booking.objects.create(
            user=self.user,
            travel_option=self.travel_option,
            number_of_seats=1
        )
        self.assertTrue(booking.can_be_cancelled)
        
        # Past booking
        past_travel = TravelOption.objects.create(
            travel_id='TR002',
            type='train',
            source='Boston',
            destination='New York',
            departure_date=date.today() - timedelta(days=1),
            departure_time=time(9, 00),
            arrival_date=date.today() - timedelta(days=1),
            arrival_time=time(13, 00),
            price=Decimal('75.00'),
            available_seats=100,
            total_seats=100
        )
        past_booking = Booking.objects.create(
            user=self.user,
            travel_option=past_travel,
            number_of_seats=1
        )
        self.assertFalse(past_booking.can_be_cancelled)

class TravelViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.travel_option = TravelOption.objects.create(
            travel_id='BUS001',
            type='bus',
            source='Chicago',
            destination='Detroit',
            departure_date=date.today() + timedelta(days=3),
            departure_time=time(8, 00),
            arrival_date=date.today() + timedelta(days=3),
            arrival_time=time(12, 30),
            price=Decimal('45.00'),
            available_seats=40,
            total_seats=40
        )
    def test_home_view(self):
        response = self.client.get(reverse('travel:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Find Your Perfect Journey')
        self.assertContains(response, self.travel_option.source)
    
    def test_travel_detail_view(self):
        response = self.client.get(
            reverse('travel:travel_detail', kwargs={'pk': self.travel_option.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.travel_option.travel_id)
        self.assertContains(response, self.travel_option.price)
    
    def test_book_travel_requires_login(self):
        response = self.client.get(
            reverse('travel:book_travel', kwargs={'pk': self.travel_option.pk})
        )
        self.assertRedirects(response, f'/accounts/login/?next=/travel/{self.travel_option.pk}/book/')
    
    def test_book_travel_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('travel:book_travel', kwargs={'pk': self.travel_option.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Complete Your Booking')
    
    def test_booking_creation_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('travel:book_travel', kwargs={'pk': self.travel_option.pk}),
            {
                'number_of_seats': 2,
                'passenger_names': 'John Doe\nJane Doe',
                'contact_phone': '+1234567890'
            }
        )
        
        self.assertEqual(Booking.objects.count(), 1)
        booking = Booking.objects.first()
        self.assertEqual(booking.user, self.user)
        self.assertEqual(booking.number_of_seats, 2)
        self.assertRedirects(response, reverse('travel:booking_detail', kwargs={'pk': booking.pk}))
    
    def test_booking_list_view(self):
        self.client.login(username='testuser', password='testpass123')
        
        # Create a booking
        Booking.objects.create(
            user=self.user,
            travel_option=self.travel_option,
            number_of_seats=1
        )
        
        response = self.client.get(reverse('travel:booking_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'My Bookings')

class TravelFormsTest(TestCase):
    def setUp(self):
        self.travel_option = TravelOption.objects.create(
            travel_id='TEST001',
            type='flight',
            source='Miami',
            destination='Orlando',
            departure_date=date.today() + timedelta(days=10),
            departure_time=time(15, 30),
            arrival_date=date.today() + timedelta(days=10),
            arrival_time=time(16, 45),
            price=Decimal('120.00'),
            available_seats=5,
            total_seats=100
        )
    
    def test_travel_search_form(self):
        form_data = {
            'type': 'flight',
            'source': 'Miami',
            'destination': 'Orlando',
            'departure_date': date.today() + timedelta(days=10)
        }
        form = TravelSearchForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_booking_form_valid(self):
        form_data = {
            'number_of_seats': 2,
            'passenger_names': 'Alice Smith\nBob Johnson',
            'contact_phone': '+1987654321'
        }
        form = BookingForm(data=form_data, travel_option=self.travel_option)
        self.assertTrue(form.is_valid())
    
    def test_booking_form_too_many_seats(self):
        form_data = {
            'number_of_seats': 10,  # More than available
            'passenger_names': 'Test Name',
            'contact_phone': '+1987654321'
        }
        form = BookingForm(data=form_data, travel_option=self.travel_option)
        self.assertFalse(form.is_valid())
        self.assertIn(f"Only {self.travel_option.available_seats} seats available", str(form.errors))
    
    def test_booking_form_passenger_names_mismatch(self):
        form_data = {
            'number_of_seats': 2,
            'passenger_names': 'Only One Name',  # Should be 2 names
            'contact_phone': '+1987654321'
        }
        form = BookingForm(data=form_data, travel_option=self.travel_option)
        self.assertFalse(form.is_valid())
        self.assertIn('Please provide exactly 2 passenger names', str(form.errors))