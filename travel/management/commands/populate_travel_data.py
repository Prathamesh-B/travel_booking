from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, time, timedelta
from decimal import Decimal
import random
from travel.models import TravelOption

class Command(BaseCommand):
    help = 'Populate the database with sample travel data'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Number of travel options to create'
        )
    
    def handle(self, *args, **options):
        count = options['count']
        
        # Sample data
        cities = [
            'New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix',
            'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose',
            'Austin', 'Jacksonville', 'Fort Worth', 'Columbus', 'Charlotte',
            'San Francisco', 'Indianapolis', 'Seattle', 'Denver', 'Washington DC',
            'Boston', 'El Paso', 'Nashville', 'Detroit', 'Oklahoma City',
            'Portland', 'Las Vegas', 'Memphis', 'Louisville', 'Baltimore',
            'Milwaukee', 'Albuquerque', 'Tucson', 'Fresno', 'Sacramento',
            'Kansas City', 'Mesa', 'Atlanta', 'Colorado Springs', 'Omaha',
            'Raleigh', 'Miami', 'Long Beach', 'Virginia Beach', 'Oakland',
            'Minneapolis', 'Tampa', 'Tulsa', 'Arlington', 'New Orleans'
        ]
        
        travel_types = ['flight', 'train', 'bus']
        
        created_count = 0
        
        for i in range(count):
            # Generate random travel option
            travel_type = random.choice(travel_types)
            source = random.choice(cities)
            destination = random.choice([city for city in cities if city != source])
            
            # Generate dates (next 30 days)
            departure_date = date.today() + timedelta(days=random.randint(1, 30))
            
            # Generate times
            departure_hour = random.randint(6, 22)
            departure_minute = random.choice([0, 15, 30, 45])
            departure_time = time(departure_hour, departure_minute)
            
            # Calculate arrival (1-8 hours later for flights/trains, 2-12 hours for buses)
            if travel_type == 'flight':
                travel_duration = random.randint(1, 6)
            elif travel_type == 'train':
                travel_duration = random.randint(2, 8)
            else:  # bus
                travel_duration = random.randint(3, 12)
            
            arrival_datetime = timezone.datetime.combine(departure_date, departure_time) + timedelta(hours=travel_duration)
            arrival_date = arrival_datetime.date()
            arrival_time = arrival_datetime.time()
            
            # Generate pricing based on type
            if travel_type == 'flight':
                base_price = random.randint(150, 800)
            elif travel_type == 'train':
                base_price = random.randint(50, 300)
            else:  # bus
                base_price = random.randint(25, 150)
            
            price = Decimal(str(base_price + random.randint(-50, 100)))
            
            # Generate capacity
            if travel_type == 'flight':
                total_seats = random.choice([150, 180, 200, 250, 300])
            elif travel_type == 'train':
                total_seats = random.choice([100, 150, 200, 250])
            else:  # bus
                total_seats = random.choice([40, 50, 55])
            
            available_seats = random.randint(0, total_seats)
            
            # Generate travel ID
            type_prefix = travel_type[0].upper()
            travel_id = f"{type_prefix}{str(i+1).zfill(4)}"
            
            try:
                travel_option = TravelOption.objects.create(
                    travel_id=travel_id,
                    type=travel_type,
                    source=source,
                    destination=destination,
                    departure_date=departure_date,
                    departure_time=departure_time,
                    arrival_date=arrival_date,
                    arrival_time=arrival_time,
                    price=price,
                    available_seats=available_seats,
                    total_seats=total_seats
                )
                created_count += 1
                
                if created_count % 10 == 0:
                    self.stdout.write(f'Created {created_count} travel options...')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creating travel option {travel_id}: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} travel options')
        )