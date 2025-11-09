"""
ASGI config for TeCADE project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TeCADE.settings')

application = get_asgi_application()



"""
ASGI config for TeCADE project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

# import os

# from django.core.asgi import get_asgi_application

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TeCADE.settings')

# application = get_asgi_application()



# ===============================================
#  --------ASGI IMPORTATION STRATRS FROM HRE-----
# ================================================
# import os

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TeCADE.settings')

# from django.core.asgi import get_asgi_application
# from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.auth import AuthMiddlewareStack
# from channels.security.websocket import AllowedHostsOriginValidator
# import trainee.routing

# application = ProtocolTypeRouter({
#     "http": get_asgi_application(),
#     "websocket": AuthMiddlewareStack(
#         URLRouter(
#             trainee.routing.websocket_urlpatterns
#         )
#     ),
# })