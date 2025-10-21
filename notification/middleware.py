# tu_app/middleware.py (CORREGIDO)

from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from urllib.parse import parse_qs


@database_sync_to_async
def get_user_from_token(token_key):
    """
    Intenta autenticar al usuario basado en el token JWT.
    """
    # 1. Importa y obtén el modelo User AQUÍ DENTRO.
    from django.contrib.auth import get_user_model
    User = get_user_model()

    try:
        # 2. Decodificar el token
        token = AccessToken(token_key)

        # 3. Obtener el ID de usuario del token
        user_id = token['user_id']

        # 4. Obtener el usuario de la base de datos
        return User.objects.get(id=user_id)

    except (InvalidToken, TokenError, User.DoesNotExist, KeyError):
        # 5. Si el token es inválido o el usuario no existe,
        # devolver un usuario anónimo.
        return AnonymousUser()


class JwtAuthMiddleware:
    """
    Middleware de Channels para autenticar usuarios vía JWT en query parameters.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # 1. Obtener la query string del scope
        query_string = scope.get('query_string', b'').decode('utf-8')

        # 2. Parsear la query string para obtener los parámetros
        params = parse_qs(query_string)

        # 3. Buscar el parámetro 'token'
        token_key = params.get('token', [None])[0]

        if token_key:
            # 4. Si hay un token, obtener el usuario
            scope['user'] = await get_user_from_token(token_key)
        else:
            # 5. Si no hay token, establecer usuario anónimo
            scope['user'] = AnonymousUser()

        # 6. Continuar con el siguiente middleware o consumidor
        return await self.app(scope, receive, send)
