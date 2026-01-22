"""Entrypoint WSGI padrão para AWS Elastic Beanstalk (Python).

O EB procura por um objeto WSGI chamado `application` em `application.py`.
"""

from wsgi import app as application  # noqa: F401
