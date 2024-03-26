# -*- coding:utf-8 -*-
"""
WSGI config for dyh project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""

import os, sys
this_path = os.path.dirname(__file__)
if this_path not in sys.path:
    sys.path.append(this_path)
    p_path = os.path.dirname(this_path)
    sys.path.append(p_path)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dyh.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
