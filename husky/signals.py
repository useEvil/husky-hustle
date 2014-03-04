"""Signals functions

Consists of functions to typically be used for signal sending/receiving
"""
from django.core.signals import request_finished
from django.dispatch import Signal, receiver
from django.db.models.signals import post_save


from husky.models import Student, Donation

import logging
logger = logging.getLogger(__name__)


# @receiver(request_finished)
def calculate_totals_callback(sender, **kwargs):
    donation = kwargs.has_key('donation') and kwargs['donation'] or None
    if donation:
        donation.calculate_totals(donation.id)
        donation.student.calculate_totals(donation.student.id)

# calculate_totals_signal = Signal(providing_args=["sender", "donation"])
# calculate_totals_signal.connect(calculate_totals_callback, dispatch_uid='calculate_totals')