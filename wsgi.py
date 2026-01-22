"""WSGI entrypoint para produção (ex.: Gunicorn/Elastic Beanstalk).

Exemplo:
  gunicorn wsgi:app
"""

from api_server import app  # noqa: F401
