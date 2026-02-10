// ============================================================
// EviChain Desktop — Investigation Service
// ============================================================
const { v4: uuidv4 } = require('uuid');

class InvestigationService {
    constructor(db) {
        this.db = db;
    }

    investigar(nome, registro, conselho, infoAdicionais = {}) {
        try {
            // Check cache
            const cached = this.db.getCachedInvestigation(nome, conselho || '');
            if (cached) {
                return { success: true, investigacao: cached.result, fromCache: true };
            }

            const resultado = {
                dados_basicos: {
                    nome: nome,
                    registro: registro,
                    conselho: conselho,
                    timestamp_investigacao: new Date().toISOString(),
                    informacoes_adicionais: infoAdicionais
                },
                registros_oficiais: this._verificarRegistro(nome, registro, conselho),
                redes_sociais: this._buscarRedesSociais(nome),
                busca_geral: this._buscarInternet(nome, conselho),
                alertas_e_bandeiras: this._gerarAlertas(nome, registro, conselho),
                resumo_investigacao: {}
            };

            resultado.resumo_investigacao = this._gerarResumo(resultado);

            // Cache result
            this.db.cacheInvestigation(uuidv4(), nome, conselho || '', resultado);

            return { success: true, investigacao: resultado };
        } catch (err) {
            return { success: false, error: err.message };
        }
    }

    buscarRedesSociais(nome) {
        try {
            const redes = this._buscarRedesSociais(nome);
            return { success: true, redes_sociais: redes };
        } catch (err) {
            return { success: false, error: err.message };
        }
    }

    consultarRegistro(nome, registro, conselho) {
        try {
            const resultado = this._verificarRegistro(nome, registro, conselho);
            return { success: true, consulta: resultado };
        } catch (err) {
            return { success: false, error: err.message };
        }
    }

    _verificarRegistro(nome, registro, conselho) {
        const nomeEncoded = encodeURIComponent(nome);
        const conselhoMap = {
            'CRM': {
                api_url: `https://portal.cfm.org.br/api/busca-medicos?nome=${nomeEncoded}&tipo=nome`,
                portal_url: 'https://portal.cfm.org.br/busca-medicos/',
                nome_conselho: 'Conselho Federal de Medicina'
            },
            'OAB': {
                api_url: null,
                portal_url: `https://cna.oab.org.br/`,
                nome_conselho: 'Ordem dos Advogados do Brasil'
            },
            'CREA': {
                api_url: null,
                portal_url: 'https://www.confea.org.br/',
                nome_conselho: 'Conselho Regional de Engenharia e Agronomia'
            },
            'CRP': {
                api_url: null,
                portal_url: 'https://cadastro.cfp.org.br/',
                nome_conselho: 'Conselho Regional de Psicologia'
            },
            'CRO': {
                api_url: null,
                portal_url: 'https://cfo.org.br/servicos-e-consultas/',
                nome_conselho: 'Conselho Regional de Odontologia'
            },
            'CREF': {
                api_url: null,
                portal_url: 'https://www.confef.org.br/confef/registrados/',
                nome_conselho: 'Conselho Regional de Educação Física'
            }
        };

        const info = conselhoMap[conselho] || {
            api_url: null,
            portal_url: null,
            nome_conselho: conselho || 'Conselho não especificado'
        };

        return {
            registro_encontrado: false,
            busca_realizada: {
                nome_pesquisado: nome,
                registro_informado: registro,
                conselho: conselho,
                timestamp: new Date().toISOString()
            },
            dados_profissional: null,
            urls_consulta: {
                portal: info.portal_url,
                api: info.api_url
            },
            instrucoes: `Para consulta oficial, acesse: ${info.portal_url || 'Site do conselho profissional'}`,
            nota: 'A verificação automática requer conexão com APIs externas. Para consulta oficial, use os links fornecidos.'
        };
    }

    _buscarRedesSociais(nome) {
        const nomeEncoded = encodeURIComponent(nome);
        const nomeQuery = nome.replace(/\s+/g, '+');

        return {
            facebook: {
                plataforma: 'Facebook',
                busca_manual: `https://www.facebook.com/search/people/?q=${nomeEncoded}`,
                perfis_encontrados: []
            },
            instagram: {
                plataforma: 'Instagram',
                busca_manual: `https://www.instagram.com/explore/search/keyword/?q=${nomeEncoded}`,
                perfis_encontrados: []
            },
            linkedin: {
                plataforma: 'LinkedIn',
                busca_manual: `https://www.linkedin.com/search/results/people/?keywords=${nomeEncoded}`,
                perfis_encontrados: []
            },
            twitter: {
                plataforma: 'Twitter/X',
                busca_manual: `https://twitter.com/search?q=${nomeEncoded}&f=user`,
                perfis_encontrados: []
            },
            youtube: {
                plataforma: 'YouTube',
                busca_manual: `https://www.youtube.com/results?search_query=${nomeQuery}`,
                perfis_encontrados: []
            },
            tiktok: {
                plataforma: 'TikTok',
                busca_manual: `https://www.tiktok.com/search/user?q=${nomeEncoded}`,
                perfis_encontrados: []
            },
            google: {
                plataforma: 'Google',
                busca_manual: `https://www.google.com/search?q="${nomeEncoded}"`,
                perfis_encontrados: []
            }
        };
    }

    _buscarInternet(nome, conselho) {
        const nomeEncoded = encodeURIComponent(nome);
        return {
            google_geral: {
                url: `https://www.google.com/search?q="${nomeEncoded}" ${conselho || ''} denúncia`,
                resultados: []
            },
            google_noticias: {
                url: `https://www.google.com/search?q="${nomeEncoded}" ${conselho || ''}&tbm=nws`,
                resultados: []
            },
            google_academico: {
                url: `https://scholar.google.com/scholar?q="${nomeEncoded}"`,
                resultados: []
            },
            jusbrasil: {
                url: `https://www.jusbrasil.com.br/busca?q=${nomeEncoded}`,
                resultados: [],
                nota: 'Verificar processos judiciais'
            }
        };
    }

    _gerarAlertas(nome, registro, conselho) {
        const alertas = [];
        if (!registro) {
            alertas.push({
                nivel: 'medio',
                tipo: 'registro_ausente',
                descricao: 'Número de registro profissional não informado. Verificação de legitimidade recomendada.'
            });
        }
        if (!conselho) {
            alertas.push({
                nivel: 'baixo',
                tipo: 'conselho_ausente',
                descricao: 'Conselho profissional não especificado. Identificar o órgão regulador.'
            });
        }
        return alertas;
    }

    _gerarResumo(resultado) {
        const registroEncontrado = resultado.registros_oficiais?.registro_encontrado;
        const totalAlertas = resultado.alertas_e_bandeiras?.length || 0;

        let pontuacao = 50;
        if (registroEncontrado) pontuacao += 20;
        if (totalAlertas === 0) pontuacao += 10;
        pontuacao = Math.min(100, Math.max(0, pontuacao));

        const achados = [];
        achados.push(registroEncontrado
            ? 'Registro profissional verificado'
            : 'Verificação de registro pendente (consulta manual necessária)'
        );
        if (totalAlertas > 0) achados.push(`${totalAlertas} alertas identificados`);
        achados.push('Links de busca em redes sociais gerados');
        achados.push('Links de busca geral na internet gerados');

        return {
            status_investigacao: 'concluida',
            pontuacao_confiabilidade: pontuacao,
            principais_achados: achados,
            recomendacao: 'Utilizar os links fornecidos para aprofundar a investigação manualmente.'
        };
    }
}

module.exports = InvestigationService;
