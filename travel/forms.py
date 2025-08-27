from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import TravelOption, Booking
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit, Row, Column

class TravelSearchForm(forms.Form):
    TRAVEL_TYPES = [
        ('', 'All Types'),
        ('flight', 'Flight'),
        ('train', 'Train'),
        ('bus', 'Bus'),
    ]
    
    type = forms.ChoiceField(choices=TRAVEL_TYPES, required=False)
    source = forms.CharField(max_length=100, required=False)
    destination = forms.CharField(max_length=100, required=False)
    departure_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    min_price = forms.DecimalField(max_digits=10, decimal_places=2, required=False, min_value=0)
    max_price = forms.DecimalField(max_digits=10, decimal_places=2, required=False, min_value=0)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.layout = Layout(
            Row(
                Column('type', css_class='form-group col-md-6 mb-0'),
                Column('departure_date', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('source', css_class='form-group col-md-6 mb-0'),
                Column('destination', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('min_price', css_class='form-group col-md-6 mb-0'),
                Column('max_price', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Submit('submit', 'Search', css_class='btn btn-primary')
        )

class BookingForm(forms.ModelForm):
    passenger_names = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        help_text="Enter passenger names (one per line)",
        required=True
    )
    contact_phone = forms.CharField(max_length=15, required=True)
    
    class Meta:
        model = Booking
        fields = ['number_of_seats', 'passenger_names', 'contact_phone']
        widgets = {
            'number_of_seats': forms.NumberInput(attrs={'min': 1, 'max': 10}),
        }
    
    def __init__(self, *args, **kwargs):
        self.travel_option = kwargs.pop('travel_option', None)
        super().__init__(*args, **kwargs)
        
        if self.travel_option:
            max_seats = min(10, self.travel_option.available_seats)
            self.fields['number_of_seats'].widget.attrs['max'] = max_seats
            self.fields['number_of_seats'].validators = [
                MinValueValidator(1)
            ]
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'number_of_seats',
            'passenger_names',
            'contact_phone',
            Submit('submit', 'Confirm Booking', css_class='btn btn-success btn-lg')
        )
    
    def clean_number_of_seats(self):
        seats = self.cleaned_data['number_of_seats']
        if self.travel_option and not self.travel_option.is_available(seats):
            raise forms.ValidationError(f"Only {self.travel_option.available_seats} seats available.")
        return seats
    
    def clean_passenger_names(self):
        names = self.cleaned_data['passenger_names']
        name_list = [name.strip() for name in names.split('\n') if name.strip()]
        
        if hasattr(self, 'cleaned_data') and 'number_of_seats' in self.cleaned_data:
            required_names = self.cleaned_data['number_of_seats']
            if len(name_list) != required_names:
                raise forms.ValidationError(f"Please provide exactly {required_names} passenger names.")
        
        return name_list