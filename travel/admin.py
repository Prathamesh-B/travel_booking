from django.contrib import admin
from django.utils.html import format_html
from .models import TravelOption, Booking

@admin.register(TravelOption)
class TravelOptionAdmin(admin.ModelAdmin):
    list_display = ['travel_id', 'type', 'source', 'destination', 'departure_date', 
                   'departure_time', 'price', 'available_seats', 'total_seats']
    list_filter = ['type', 'departure_date', 'source', 'destination']
    search_fields = ['travel_id', 'source', 'destination']
    ordering = ['departure_date', 'departure_time']
    date_hierarchy = 'departure_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('travel_id', 'type', 'source', 'destination')
        }),
        ('Schedule', {
            'fields': ('departure_date', 'departure_time', 'arrival_date', 'arrival_time')
        }),
        ('Pricing & Capacity', {
            'fields': ('price', 'total_seats', 'available_seats')
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return ['travel_id'] + list(self.readonly_fields)
        return self.readonly_fields

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['booking_id', 'user', 'travel_option', 'number_of_seats', 
                   'total_price', 'status', 'booking_date']
    list_filter = ['status', 'booking_date', 'travel_option__type']
    search_fields = ['booking_id', 'user__username', 'user__email', 
                    'travel_option__travel_id']
    ordering = ['-booking_date']
    date_hierarchy = 'booking_date'
    readonly_fields = ['booking_id', 'total_price', 'booking_date']
    
    fieldsets = (
        ('Booking Information', {
            'fields': ('booking_id', 'user', 'travel_option', 'status')
        }),
        ('Details', {
            'fields': ('number_of_seats', 'total_price', 'passenger_details')
        }),
        ('Timestamps', {
            'fields': ('booking_date', 'created_at', 'updated_at'),
            'classes': ['collapse']
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj:  # editing an existing object
            readonly.extend(['user', 'travel_option', 'number_of_seats'])
        return readonly
    
    def colored_status(self, obj):
        colors = {
            'confirmed': 'green',
            'cancelled': 'red',
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    colored_status.short_description = 'Status'