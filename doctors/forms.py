from django import forms
from accounts.models import User
from .models import Doctor


class DoctorUserForm(forms.ModelForm):
    """Creates the login (User) for the doctor."""
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone']
        widgets = {f: forms.TextInput(attrs={'class': 'form-control'}) for f in
                   ['username', 'first_name', 'last_name', 'email', 'phone']}

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.DOCTOR
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class DoctorProfileForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ['specialization', 'qualification', 'experience_years', 'consultation_fee',
                   'available_days', 'available_from', 'available_to']
        widgets = {
            'available_from': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'available_to': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name not in self.Meta.widgets:
                field.widget.attrs['class'] = 'form-control'
