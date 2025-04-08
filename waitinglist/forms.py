from django import forms
from waitinglist.models import WaitingList


class WaitingListForm(forms.ModelForm):
    class Meta:
        model = WaitingList
        fields = ['first_name', 'last_name', 'phone_number', 'email', 'city', 'occupation', 'referenced']

