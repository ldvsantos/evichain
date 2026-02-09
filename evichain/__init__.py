"""EviChain package.

Este pacote concentra configuração e composição (services) para manter os entrypoints
(api_server.py, search_server.py) pequenos e mais fáceis de manter/testar.
"""

from .settings import Settings, load_settings
from .services import Services, create_services
