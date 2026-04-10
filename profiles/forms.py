from django import forms
from accounts.models import CustomUser

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'bio', 'status_message', 'profile_image']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
        }
