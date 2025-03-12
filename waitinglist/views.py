from django.shortcuts import render
from waitinglist.forms import WaitingListForm


def waiting_list(request):
    form = WaitingListForm()
    if request.method == "POST":
        if form.is_valid():
            form.save()
    return render(request, 'waiting-list.html', {'form': form})

