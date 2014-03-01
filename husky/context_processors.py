from django.conf import settings

from husky.models import Donation
from husky.helpers import *


def page_content(request):
    donate=Donation()
    return {
        'bar_height': donate.bar_height(),
        'arrow_height': donate.arrow_height(),
        'path': request.path,
        'user': request.user,
        'return_url': request.get_full_path(),
    }
