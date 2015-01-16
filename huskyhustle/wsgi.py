"""
WSGI config for huskyhustle project.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It should expose a module-level variable
named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
this application via the ``WSGI_APPLICATION`` setting.

Usually you will have the standard Django WSGI application here, but it also
might make sense to replace the whole Django WSGI application with a custom one
that later delegates to the Django one. For example, you could introduce WSGI
middleware here, or combine a Django application with an application of another
framework.

"""
import os, sys, site

app_path = os.path.dirname(__file__)
base_path = os.path.dirname(app_path)
virtual_env = '/Users/useevil/.virtualenvs/husky-hustle'
site_path = os.path.dirname(os.path.join(virtual_env, 'lib/python2.7/site-packages/'))
site.addsitedir(site_path)
if base_path not in sys.path:
    sys.path.append(base_path)

activate_env=os.path.expanduser(os.path.join(virtual_env, 'bin/activate_this.py'))
execfile(activate_env, dict(__file__=activate_env))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "huskyhustle.settings-local")

# This application object is used by any WSGI server configured to use this
# file. This includes Django's development server, if the WSGI_APPLICATION
# setting points here.
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()


# import newrelic.agent
# ini = os.path.join(app_path, 'local_newrelic.default.ini')
# newrelic.agent.initialize(ini, 'development')
# application = newrelic.agent.wsgi_application()(application)

from django.conf import settings
if settings.DEBUG == True:
    import huskyhustle.monitor
    huskyhustle.monitor.start(interval=1.0)

#     import newrelic.agent
#     application_path = os.path.dirname(__file__)
#     ini = os.path.join(application_path, 'newrelic.ini')
#     newrelic.agent.initialize(ini)
#     application = newrelic.agent.wsgi_application()(application)
