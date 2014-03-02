"""Signals functions

Consists of functions to typically be used for signal sending/receiving
"""
from django.core.signals import request_finished
from django.dispatch import receiver
from django.db.models.signals import post_save

from husky.models import Student, Donation

import logging
logger = logging.getLogger(__name__)

@receiver(post_save, sender=Student)
@receiver(post_save, sender=Donation)
def calculate_totals_callback(sender, id=None):
    logger.debug('==== id [%s]'%(id))
    sender.calculate_totals(id)
