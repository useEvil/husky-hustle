from django.conf import settings

from husky.models import Donation
from husky.helpers import *


def page_content(request):
    donation=Donation()
    return {
        'bar_height': donation.bar_height(),
        'arrow_height': donation.arrow_height(),
        'path': request.path,
        'user': request.user,
        'return_url': request.get_full_path(),
        'cart': request.cart,
    }
