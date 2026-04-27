
from django import forms
from .models import Testimonial, Agent  
 
 
class TestimonialForm(forms.ModelForm):
    # Zgjidhja e agjentit — dropdown nga databaza
    agent = forms.ModelChoiceField(
        queryset=Agent.objects.none(),  
        required=False,
        empty_label='— Zgjidhni agjentin —',
        label='Agjenti',
        widget=forms.Select(attrs={'class': 'kr-input kr-select'}),
    )
    agent_label = forms.CharField(
        required=False,
        label='Ose shkruani emrin e agjentit',
        widget=forms.TextInput(attrs={
            'class': 'kr-input',
            'placeholder': 'P.sh. Ilirjana Shordja',
        }),
    )
    honeypot = forms.CharField(required=False, widget=forms.HiddenInput())
 
    class Meta:
        model  = Testimonial
        fields = [
            'client_name', 'client_city', 'client_email', 'client_phone',
            'agent', 'agent_label',
            'message', 'rating',
            'honeypot',
        ]
        widgets = {
            'client_name': forms.TextInput(attrs={
                'class': 'kr-input',
                'placeholder': 'Emri juaj i plotë',
            }),
            'client_city': forms.TextInput(attrs={
                'class': 'kr-input',
                'placeholder': 'P.sh. Tiranë',
            }),
            'client_email': forms.EmailInput(attrs={
                'class': 'kr-input',
                'placeholder': 'email@juaj.com',
            }),
            'client_phone': forms.TextInput(attrs={
                'class': 'kr-input',
                'placeholder': '+355 6X XXX XXXX',
            }),
            'message': forms.Textarea(attrs={
                'class': 'kr-input',
                'rows': 5,
                'placeholder': 'Ndani përvojën tuaj me ne...',
            }),
            'rating': forms.RadioSelect(attrs={'class': 'testi-rating-radio'}),
        }
        labels = {
            'client_name':  'Emri juaj *',
            'client_city':  'Qyteti',
            'client_email': 'Email (nuk shfaqet)',
            'client_phone': 'Telefon (nuk shfaqet)',
            'message':      'Mesazhi juaj *',
            'rating':       'Vlerësimi *',
        }
 
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Agent
        self.fields['agent'].queryset = Agent.objects.filter(
            is_active=True
        ).order_by('full_name')
 
    def clean_honeypot(self):
        val = self.cleaned_data.get('honeypot', '')
        if val:
            raise forms.ValidationError('Spam i zbuluar.')
        return val
 
    def clean(self):
        cleaned = super().clean()
        agent       = cleaned.get('agent')
        agent_label = cleaned.get('agent_label', '').strip()
        if not agent and not agent_label:
            self.add_error(
                'agent_label',
                'Ju lutem zgjidhni ose shkruani emrin e agjentit.'
            )
        return cleaned