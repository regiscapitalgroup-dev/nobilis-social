from django import forms
from waitinglist.models import WaitingList


class WaitingListForm(forms.ModelForm):
    class Meta:
        model = WaitingList
        fields = ['name', 'lastname', 'phone_number', 'email', 'city', 'occupation', 'referenced']

