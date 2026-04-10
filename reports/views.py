from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def report_user(request, user_id):
    return render(request, 'reports/report_user.html')
