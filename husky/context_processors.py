from django.conf import settings
from django.db.models import Sum

from husky.models import Donation, Grade
from husky.helpers import *

import logging
logger = logging.getLogger(__name__)

def page_content(request):
    context = {
        'path': request.path,
        'user': request.user,
        'return_url': request.get_full_path(),
        'grand_pledged': 0,
        'grand_donated': 0,
        'bar_height': 0,
        'arrow_height': 0,
    }
    if 'admin' in request.path:
        context['grades'] = Grade.objects.exclude(grade=101).all()
        context['grand_pledged'] = Donation.objects.filter(per_lap=False).aggregate(donated=Sum('donated')) or 0
        context['grand_donated'] = Donation.objects.filter(paid=True).aggregate(donated=Sum('donated')) or 0
        context['online_collected'] = Donation.objects.filter(paid=True, paid_by='online').aggregate(donated=Sum('donated')) or 0
        context['monies_collected'] = Donation.objects.filter(paid=True).exclude(paid_by='online').aggregate(donated=Sum('donated')) or 0
    else:
        donation=Donation()
        context['bar_height'] = donation.bar_height()
        context['arrow_height'] = donation.arrow_height()
        context['cart'] = request.cart
    return context
