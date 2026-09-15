"""
Autenticación simple por API key.

Es una app de un solo usuario (tú, desde el PC y el celular), así que no
hace falta un sistema de login completo: basta con una clave secreta que
guardas en el backend (variable de entorno API_KEY) y que el frontend envía
en cada petición con el header 'X-API-Key'. Sin esa clave, nadie puede leer
ni escribir tus datos aunque encuentren la URL de la API.
"""
import os
from fastapi import Header, HTTPException, status

API_KEY = os.environ.get("API_KEY", "")


def verificar_api_key(x_api_key: str = Header(default="")):
    if not API_KEY:
        # Si no se configuró ninguna clave, no arrancamos: mejor fallar
        # ruidosamente que dejar la base de datos abierta sin querer.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="El servidor no tiene configurada API_KEY.",
        )
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key inválida o ausente.",
        )
