// ============================================================
// EviChain Desktop — Report Service (PDF Generation)
// ============================================================
const PDFDocument = require('pdfkit');
const fs = require('fs');

class ReportService {
    constructor(db) {
        this.db = db;
    }

    generateComplaintPDF(complaintId, outputPath) {
        try {
            const complaint = this.db.getComplaint(complaintId);
            if (!complaint) return { success: false, error: 'Denúncia não encontrada' };

            const doc = new PDFDocument({ size: 'A4', margin: 50 });
            const stream = fs.createWriteStream(outputPath);
            doc.pipe(stream);

            // Header
            doc.fontSize(20).fillColor('#1e40af')
                .text('EVICHAIN - RELATÓRIO DE DENÚNCIA', { align: 'center' });
            doc.moveDown(0.5);
            doc.fontSize(10).fillColor('#666')
                .text(`Gerado em: ${new Date().toLocaleString('pt-BR')}`, { align: 'center' });
            doc.moveDown(1);
            doc.moveTo(50, doc.y).lineTo(545, doc.y).stroke('#ddd');
            doc.moveDown(1);

            // Basic Info
            doc.fontSize(14).fillColor('#000').text('INFORMAÇÕES BÁSICAS', { underline: true });
            doc.moveDown(0.5);
            doc.fontSize(10).fillColor('#333');

            const info = [
                ['ID:', complaint.id],
                ['Título:', complaint.titulo || 'N/A'],
                ['Denunciado:', complaint.nome_denunciado || 'N/A'],
                ['Conselho:', complaint.conselho || 'N/A'],
                ['Categoria:', complaint.categoria || 'N/A'],
                ['Assunto:', complaint.assunto || 'N/A'],
                ['Prioridade:', complaint.prioridade || 'N/A'],
                ['Finalidade:', complaint.finalidade || 'N/A'],
                ['Status:', complaint.status || 'pending'],
                ['Data:', complaint.created_at || 'N/A']
            ];

            info.forEach(([label, value]) => {
                doc.font('Helvetica-Bold').text(label, { continued: true });
                doc.font('Helvetica').text(` ${value}`);
            });

            doc.moveDown(1);

            // Description
            doc.fontSize(14).fillColor('#000').text('DESCRIÇÃO', { underline: true });
            doc.moveDown(0.5);
            doc.fontSize(10).fillColor('#333').text(complaint.descricao || 'Não disponível');
            doc.moveDown(1);

            // IA Analysis
            if (complaint.ia_analysis) {
                const ia = complaint.ia_analysis;
                doc.addPage();
                doc.fontSize(14).fillColor('#000').text('ANÁLISE INTELIGENTE (IA)', { underline: true });
                doc.moveDown(0.5);
                doc.fontSize(10).fillColor('#333');

                if (ia.analise_basica?.resumo) {
                    doc.font('Helvetica-Bold').text('Resumo:');
                    doc.font('Helvetica').text(ia.analise_basica.resumo);
                    doc.moveDown(0.5);
                }

                if (ia.analise_juridica) {
                    doc.font('Helvetica-Bold').text('Gravidade:', { continued: true });
                    doc.font('Helvetica').text(` ${ia.analise_juridica.gravidade || 'N/A'}`);
                    doc.font('Helvetica-Bold').text('Tipificação:', { continued: true });
                    doc.font('Helvetica').text(` ${ia.analise_juridica.tipificacao || 'N/A'}`);
                }

                if (ia.classificacao_risco) {
                    doc.moveDown(0.5);
                    doc.font('Helvetica-Bold').text('Risco:', { continued: true });
                    doc.font('Helvetica').text(` ${ia.classificacao_risco.nivel || 'N/A'} (${ia.classificacao_risco.pontuacao || 0}/100)`);
                    doc.font('Helvetica-Bold').text('Ação Recomendada:');
                    doc.font('Helvetica').text(ia.classificacao_risco.acao_recomendada || 'N/A');
                }

                if (ia.analise_juridica?.legislacao_especifica) {
                    const leg = ia.analise_juridica.legislacao_especifica;
                    doc.moveDown(1);
                    doc.fontSize(12).fillColor('#1e40af').text('LEGISLAÇÃO RECOMENDADA');
                    doc.moveDown(0.5);
                    doc.fontSize(10).fillColor('#333');
                    doc.font('Helvetica-Bold').text('Legislação:', { continued: true });
                    doc.font('Helvetica').text(` ${leg.legislacao_sugerida || 'N/A'}`);
                    if (leg.artigos?.length) {
                        doc.font('Helvetica-Bold').text('Artigos:', { continued: true });
                        doc.font('Helvetica').text(` ${leg.artigos.join(', ')}`);
                    }
                    if (leg.penalidades?.length) {
                        doc.font('Helvetica-Bold').text('Penalidades:', { continued: true });
                        doc.font('Helvetica').text(` ${leg.penalidades.join(', ')}`);
                    }
                }

                if (ia.recomendacoes?.length) {
                    doc.moveDown(1);
                    doc.fontSize(12).text('RECOMENDAÇÕES');
                    doc.moveDown(0.5);
                    doc.fontSize(10);
                    ia.recomendacoes.forEach((rec, i) => {
                        doc.text(`${i + 1}. ${rec}`);
                    });
                }
            }

            // Footer
            const pages = doc.bufferedPageRange();
            for (let i = 0; i < pages.count; i++) {
                doc.switchToPage(i);
                doc.fontSize(8).fillColor('#999')
                    .text('EviChain Desktop - Plataforma de Inovação Probatória',
                        50, doc.page.height - 40, { align: 'center' });
            }

            doc.end();

            return new Promise((resolve) => {
                stream.on('finish', () => resolve({ success: true, path: outputPath }));
                stream.on('error', (err) => resolve({ success: false, error: err.message }));
            });
        } catch (err) {
            return { success: false, error: err.message };
        }
    }

    generateBlockchainPDF(outputPath) {
        try {
            const info = this.db.getChainInfo();
            const blocks = this.db.getRecentBlocks(20);

            const doc = new PDFDocument({ size: 'A4', margin: 50 });
            const stream = fs.createWriteStream(outputPath);
            doc.pipe(stream);

            doc.fontSize(20).fillColor('#1e40af')
                .text('EVICHAIN - RELATÓRIO DA BLOCKCHAIN', { align: 'center' });
            doc.moveDown(1);
            doc.fontSize(10).fillColor('#333');

            doc.font('Helvetica-Bold').text('Total de Blocos:', { continued: true });
            doc.font('Helvetica').text(` ${info.total_blocks}`);
            doc.font('Helvetica-Bold').text('Total de Denúncias:', { continued: true });
            doc.font('Helvetica').text(` ${info.total_complaints}`);
            doc.font('Helvetica-Bold').text('Chain Válida:', { continued: true });
            doc.font('Helvetica').text(` ${info.chain_valid ? 'Sim' : 'Não'}`);
            doc.font('Helvetica-Bold').text('Último Hash:', { continued: true });
            doc.font('Helvetica').text(` ${info.last_block_hash || 'N/A'}`);
            doc.moveDown(1);

            doc.fontSize(14).text('BLOCOS RECENTES');
            doc.moveDown(0.5);

            blocks.forEach(block => {
                doc.fontSize(9).fillColor('#333');
                doc.font('Helvetica-Bold').text(`Bloco #${block.block_index}`);
                doc.font('Helvetica').text(`Hash: ${block.hash}`);
                doc.text(`Timestamp: ${block.timestamp}`);
                doc.text(`Nonce: ${block.nonce}`);
                doc.moveDown(0.5);
                doc.moveTo(50, doc.y).lineTo(545, doc.y).stroke('#eee');
                doc.moveDown(0.5);
            });

            doc.end();
            return new Promise((resolve) => {
                stream.on('finish', () => resolve({ success: true, path: outputPath }));
            });
        } catch (err) {
            return { success: false, error: err.message };
        }
    }

    exportCSV(outputPath) {
        try {
            const complaints = this.db.listComplaints();
            const headers = ['ID', 'Título', 'Denunciado', 'Conselho', 'Categoria', 'Assunto', 'Prioridade', 'Status', 'Data'];
            const rows = complaints.map(c => [
                c.id, c.titulo, c.nome_denunciado, c.conselho, c.categoria,
                c.assunto, c.prioridade, c.status, c.created_at
            ]);

            const csvContent = [headers, ...rows]
                .map(row => row.map(cell => `"${(cell || '').toString().replace(/"/g, '""')}"`).join(','))
                .join('\n');

            fs.writeFileSync(outputPath, '\uFEFF' + csvContent, 'utf-8');
            return { success: true, path: outputPath, total: complaints.length };
        } catch (err) {
            return { success: false, error: err.message };
        }
    }
}

module.exports = ReportService;
