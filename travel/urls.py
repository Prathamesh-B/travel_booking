from django.urls import path
from . import views

app_name = 'travel'

urlpatterns = [
    path('', views.home, name='home'),
    path('travel/<int:pk>/', views.travel_detail, name='travel_detail'),
    path('travel/<int:pk>/book/', views.book_travel, name='book_travel'),
    path('bookings/', views.booking_list, name='booking_list'),
    path('booking/<int:pk>/', views.booking_detail, name='booking_detail'),
    path('booking/<int:pk>/cancel/', views.cancel_booking, name='cancel_booking'),
]