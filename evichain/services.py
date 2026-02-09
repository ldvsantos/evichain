from __future__ import annotations

from dataclasses import dataclass

from blockchain_simulator import EviChainBlockchain
from ia_engine_openai_padrao import IAEngineOpenAIPadrao
from assistente_denuncia import AssistenteDenuncia
from investigador_digital import InvestigadorDigital
from consultor_registros import ConsultorRegistrosProfissionais

from .settings import Settings


@dataclass
class Services:
    blockchain: EviChainBlockchain
    ia_engine: IAEngineOpenAIPadrao
    assistente: AssistenteDenuncia
    investigador: InvestigadorDigital
    consultor_registros: ConsultorRegistrosProfissionais


def create_services(settings: Settings) -> Services:
    blockchain = EviChainBlockchain(data_file=str(settings.data_file))

    # IAEngineOpenAIPadrao já lida com fallback quando credenciais não existem.
    ia_engine = IAEngineOpenAIPadrao()

    return Services(
        blockchain=blockchain,
        ia_engine=ia_engine,
        assistente=AssistenteDenuncia(),
        investigador=InvestigadorDigital(),
        consultor_registros=ConsultorRegistrosProfissionais(),
    )
