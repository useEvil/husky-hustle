from django.conf import settings
from django.db.models import Sum

from husky.models import Donation
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
        results1 = Donation.objects.filter(per_lap=False).aggregate(donated=Sum('donated'))
        results2 = Donation.objects.filter(paid=True).aggregate(donated=Sum('donated'))
        context['grand_pledged'] = results1['donated'] or 0
        context['grand_donated'] = results2['donated'] or 0
    else:
        donation=Donation()
        context['bar_height'] = donation.bar_height()
        context['arrow_height'] = donation.arrow_height()
        context['cart'] = request.cart,
    return context
