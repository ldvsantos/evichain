// ============================================================
// EviChain Desktop — Analysis Service (IA Local)
// ============================================================
const path = require('path');
const fs = require('fs');

class AnalysisService {
    constructor(db) {
        this.db = db;
        this.legislacao = this._loadLegislacao();
    }

    _loadLegislacao() {
        try {
            const dataPath = path.join(__dirname, '..', '..', 'data', 'legislacao_conselhos.json');
            if (fs.existsSync(dataPath)) {
                return JSON.parse(fs.readFileSync(dataPath, 'utf-8'));
            }
        } catch (e) { console.error('[ANALYSIS] Error loading legislacao:', e.message); }
        return {};
    }

    analyzeComplaint(complaintId, text, conselho, categoria) {
        try {
            const analysis = this._performAnalysis(text, conselho, categoria);

            if (complaintId) {
                this.db.updateComplaintAnalysis(complaintId, analysis);
            }

            return { success: true, analysis };
        } catch (err) {
            return { success: false, error: err.message };
        }
    }

    assistenteAnalise(text, conselho, categoria) {
        try {
            const analise = this._analyzeTextQuality(text, conselho, categoria);
            return { success: true, analise };
        } catch (err) {
            return { success: false, error: err.message };
        }
    }

    getLatestAnalysis() {
        try {
            const complaints = this.db.listComplaints({ limit: 1 });
            if (complaints.length === 0) return { success: false, error: 'Nenhuma denúncia encontrada' };
            const latest = complaints[0];
            return {
                success: true,
                complaint_id: latest.id,
                full_analysis: latest.ia_analysis || {}
            };
        } catch (err) {
            return { success: false, error: err.message };
        }
    }

    _performAnalysis(text, conselho, categoria) {
        const palavrasChave = this._extractKeywords(text);
        const gravidade = this._detectGravidade(text, categoria);
        const risco = this._calcularRisco(text, gravidade, categoria);
        const tipificacao = this._detectTipificacao(text, categoria);
        const legislacaoEspecifica = this._findLegislacao(conselho, categoria);
        const recomendacoes = this._generateRecomendacoes(gravidade, categoria, risco);

        return {
            analise_basica: {
                resumo: this._generateResumo(text, conselho, categoria),
                palavras_chave: palavrasChave,
                tamanho_texto: text.length,
                palavras: text.split(/\s+/).length
            },
            analise_juridica: {
                gravidade: gravidade,
                tipificacao: tipificacao,
                legislacao_especifica: legislacaoEspecifica
            },
            classificacao_risco: {
                nivel: risco.nivel,
                pontuacao: risco.pontuacao,
                cor: risco.cor,
                acao_recomendada: risco.acao
            },
            recomendacoes: recomendacoes
        };
    }

    _extractKeywords(text) {
        const stopWords = new Set([
            'de', 'da', 'do', 'em', 'no', 'na', 'para', 'com', 'por', 'que',
            'uma', 'um', 'os', 'as', 'se', 'ao', 'ou', 'mas', 'foi', 'ser',
            'ter', 'como', 'não', 'mais', 'muito', 'já', 'quando', 'mesmo',
            'este', 'esta', 'isso', 'ele', 'ela', 'sua', 'seu', 'meu', 'minha'
        ]);
        
        const words = text.toLowerCase()
            .replace(/[^\w\sáàâãéèêíìîóòôõúùûç]/g, '')
            .split(/\s+/)
            .filter(w => w.length > 3 && !stopWords.has(w));

        const freq = {};
        words.forEach(w => { freq[w] = (freq[w] || 0) + 1; });

        return Object.entries(freq)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10)
            .map(([word]) => word);
    }

    _detectGravidade(text, categoria) {
        const textLower = text.toLowerCase();
        const grave = ['morte', 'óbito', 'lesão grave', 'sequela permanente', 'abuso sexual', 'estupro', 'fraude', 'falsificação'];
        const media = ['negligência', 'erro', 'dano', 'prejuízo', 'lesão', 'assédio moral', 'irregularidade'];
        const leve = ['atraso', 'descortesia', 'propaganda', 'inadequado'];

        if (grave.some(p => textLower.includes(p))) return 'grave';
        if (media.some(p => textLower.includes(p))) return 'média';
        if (leve.some(p => textLower.includes(p))) return 'leve';

        if (['Assédio', 'Exercício Ilegal'].includes(categoria)) return 'grave';
        if (categoria === 'Negligência') return 'média';
        return 'média';
    }

    _calcularRisco(text, gravidade, categoria) {
        let pontuacao = 50;

        if (gravidade === 'grave') pontuacao += 30;
        else if (gravidade === 'média') pontuacao += 15;

        if (['Assédio', 'Exercício Ilegal'].includes(categoria)) pontuacao += 15;
        if (text.length > 500) pontuacao += 5;
        if (text.length > 1000) pontuacao += 5;

        pontuacao = Math.min(100, Math.max(0, pontuacao));

        let nivel, cor, acao;
        if (pontuacao >= 75) {
            nivel = 'ALTO'; cor = '#ef4444';
            acao = 'Ação imediata recomendada. Encaminhar para análise prioritária.';
        } else if (pontuacao >= 50) {
            nivel = 'MÉDIO'; cor = '#f59e0b';
            acao = 'Análise padrão com acompanhamento. Verificar procedimentos aplicáveis.';
        } else {
            nivel = 'BAIXO'; cor = '#10b981';
            acao = 'Monitoramento de rotina. Avaliar necessidade de ação adicional.';
        }

        return { nivel, pontuacao, cor, acao };
    }

    _detectTipificacao(text, categoria) {
        const textLower = text.toLowerCase();
        if (textLower.includes('exercício ilegal') || textLower.includes('sem registro')) return 'Exercício Ilegal da Profissão';
        if (textLower.includes('assédio sexual')) return 'Assédio Sexual';
        if (textLower.includes('assédio moral')) return 'Assédio Moral';
        if (textLower.includes('negligência') || textLower.includes('negligente')) return 'Negligência Profissional';
        if (textLower.includes('fraude') || textLower.includes('falsific')) return 'Fraude/Falsificação';
        if (textLower.includes('imprudência') || textLower.includes('imprudente')) return 'Imprudência';
        if (textLower.includes('imperícia')) return 'Imperícia';
        return categoria || 'Infração Ética';
    }

    _findLegislacao(conselho, categoria) {
        if (!conselho || !this.legislacao[conselho]) {
            return { conselho: conselho || 'N/A', legislacao_sugerida: 'Legislação geral aplicável', artigos: [], penalidades: [] };
        }

        const conselhoData = this.legislacao[conselho];
        const categoriaMap = {
            'Negligência': 'negligencia',
            'Assédio': 'assedio',
            'Exercício Ilegal': 'ma_conduta',
            'Fraude em Estágio': 'fraude',
            'Outras': 'ma_conduta'
        };

        const tipoInfracao = categoriaMap[categoria] || 'ma_conduta';
        const infracao = conselhoData.infrações?.[tipoInfracao];

        if (!infracao) {
            return { conselho, legislacao_sugerida: conselhoData.codigo_etica || 'N/A', artigos: [], penalidades: [] };
        }

        return {
            conselho: conselhoData.nome_completo,
            legislacao_sugerida: conselhoData.codigo_etica,
            tipo: tipoInfracao,
            descricao: infracao.descricao,
            artigos: infracao.artigos || [],
            penalidades: infracao.penalidades || [],
            gravidade: infracao.gravidade
        };
    }

    _generateResumo(text, conselho, categoria) {
        const palavras = text.split(/\s+/);
        const resumoText = palavras.length > 30 ? palavras.slice(0, 30).join(' ') + '...' : text;
        return `Denúncia de ${categoria || 'infração'} registrada junto ao ${conselho || 'conselho profissional'}. ${resumoText}`;
    }

    _generateRecomendacoes(gravidade, categoria, risco) {
        const recs = [];
        recs.push('Verificar registro profissional do denunciado junto ao conselho competente.');

        if (gravidade === 'grave') {
            recs.push('URGENTE: Encaminhar para análise prioritária pela comissão de ética.');
            recs.push('Considerar medida cautelar de suspensão preventiva.');
        }
        if (categoria === 'Assédio') {
            recs.push('Acionar protocolo de proteção à vítima.');
            recs.push('Verificar existência de denúncias anteriores contra o mesmo profissional.');
        }
        if (categoria === 'Exercício Ilegal') {
            recs.push('Notificar órgão de fiscalização competente.');
            recs.push('Verificar documentação e credenciais do denunciado.');
        }
        recs.push('Solicitar documentação comprobatória adicional ao denunciante.');
        recs.push('Registrar evidências na blockchain para preservação da cadeia de custódia.');

        return recs;
    }

    _analyzeTextQuality(text, conselho, categoria) {
        const palavras = text.split(/\s+/).length;
        const caracteres = text.length;

        const elementos = {
            quem: /\b(dr\.|dra\.|nome|profissional|médico|advogado|engenheiro|psicólogo|dentista|professor)\b/i.test(text),
            o_que: /\b(fez|praticou|cometeu|realizou|negligenciou|assediou|fraudou)\b/i.test(text),
            quando: /\b(dia|data|em |durante|202[0-9]|mês|ano|janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\b/i.test(text),
            onde: /\b(hospital|consultório|clínica|escritório|obra|local|academia|escola|universidade)\b/i.test(text),
            consequencias: /\b(dano|prejuízo|lesão|morte|sequela|perda|sofreu|resultado|consequência)\b/i.test(text)
        };

        const elementosPresentes = Object.values(elementos).filter(v => v).length;
        const totalElementos = Object.keys(elementos).length;
        let pontuacao = Math.min(100, (elementosPresentes / totalElementos) * 80 + (caracteres > 200 ? 20 : caracteres > 100 ? 10 : 0));

        const sugestoes = [];
        if (!elementos.quem) sugestoes.push('Identifique o profissional: nome completo, número de registro e local de trabalho.');
        if (!elementos.o_que) sugestoes.push('Descreva a ação: o que o profissional fez ou deixou de fazer.');
        if (!elementos.quando) sugestoes.push('Informe a data ou período: dia/mês/ano ou período aproximado.');
        if (!elementos.onde) sugestoes.push('Descreva o local: nome do estabelecimento e endereço.');
        if (!elementos.consequencias) sugestoes.push('Descreva as consequências: danos físicos, prejuízos financeiros, sequelas.');
        if (caracteres < 200) sugestoes.push('Amplie a descrição: quanto mais detalhes, melhor a análise.');
        sugestoes.push('Se possível, mencione documentos, fotos ou testemunhas.');

        let textoMelhorado = text;
        if (caracteres < 100) {
            textoMelhorado = `Denúncia contra profissional do ${conselho || '[CONSELHO]'} por ${categoria || '[CATEGORIA]'}.

FATOS:
${text}

[ADICIONE: Quando ocorreu - data ou período]
[ADICIONE: Onde ocorreu - local específico]
[ADICIONE: Consequências - danos ou prejuízos causados]

DOCUMENTOS/PROVAS:
[Se houver, mencione: documentos, fotos, laudos, testemunhas, etc.]`;
        }

        return {
            pontuacao_qualidade: Math.round(pontuacao),
            tamanho: caracteres,
            palavras: palavras,
            elementos_presentes: elementosPresentes,
            elementos_faltantes: totalElementos - elementosPresentes,
            elementos_detalhes: elementos,
            sugestoes,
            texto_melhorado: textoMelhorado
        };
    }
}

module.exports = AnalysisService;
