"""
WSGI config for huskyhustle project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""

import os
import huskyhustle.monitor

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "huskyhustle.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from django.conf import settings
if settings.DEBUG == False:
    import newrelic.agent
    application_path = os.path.dirname(__file__)
    ini = os.path.join(application_path, 'newrelic.ini')
    newrelic.agent.initialize(ini)
    application = newrelic.agent.wsgi_application()(application)

