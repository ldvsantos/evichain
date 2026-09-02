# Atualização da cápsula Code Ocean — EviChain

A cápsula publicada (`codeocean.com/capsule/5374568/`, DOI `10.24433/CO.5374568.v1`)
está várias revisões atrás do código que o manuscrito descreve. Este diretório
contém o pacote regenerado que a coloca em dia.

## Por que atualizar

A cápsula é o artefato que será de fato auditado. Hoje ela diverge do artigo em
pontos que um revisor conferiria de imediato:

| Item | Cápsula publicada | Código atual / manuscrito |
|---|---|---|
| Ameaças STRIDE | 9 (T-01…T-09) | **10** (inclui T-10, prompt injection) |
| T-03 reescrita da cadeia | `accepted` | **Partially Mitigated** |
| Garantias / não-garantias | 5 / 5 | **6 / 7** |
| `external_anchor.py` | 252 linhas, sem verificação CMS | **1 011 linhas**, SignerInfo, EKU, messageDigest, export off-box |
| `api_server.py` | ausente do pacote | **incluído** |
| `evichain/input_validation.py` | ausente do pacote | **incluído** |
| Matriz LGPD | 11 + 2 = 13 | 11 + 2 = 13 (sem mudança) |

Sem a atualização, a Seção IV-D do artigo (verificação de âncora em cinco
estágios) e o Princípio 2 (custódia externa do recibo) descrevem capacidade que
a cápsula auditada não possui.

## O que foi corrigido no código

1. **`run_replication.py`** — a lista `source_files` omitia `api_server.py` e
   `evichain/input_validation.py`, que o manuscrito cita nominalmente. Ambos
   foram incluídos, junto de `run_load_test.py`, `write_benchmark.py` e
   `plot_validation_scalability.py`.
2. **`run_replication.py`** — as streams padrão passam a ser forçadas para UTF-8.
   Vários módulos imprimem status com emoji; no console legado do Windows isso
   levantava `UnicodeEncodeError` e abortava o estágio de benchmark. O mesmo bug
   havia corrompido o campo `blockchain_integrity` do `evaluation_results.json`
   anterior, que agora é gerado corretamente.
3. **`evichain/lgpd_compliance.py`** — o texto do controle do Art. 38 dizia
   "9 catalogued threats" fixo no código. Passou a derivar a contagem do próprio
   catálogo, de modo que não volte a ficar defasado.

## Verificação do pacote gerado

Rodado em 6/6 estágios, sem erro. Os números conferem com o manuscrito:

- `threat_model.json` — 10 ameaças, 6 garantias, 7 não-garantias
- `dpia_report.json` — 13 requisitos, 11 `compliant`, 2 `partial`, texto do
  Art. 38 lendo "10 catalogued threats"
- `evaluation_results.json` — 8 denúncias, `cohens_d` 1.19, `improvement.min`
  −2.6, e `blockchain_integrity` preenchido
- `benchmark_results.json` — mineração em todos os níveis e validação de cadeia

## Como subir

1. Abrir `codeocean.com/capsule/5374568/`.
2. Em **Code**, substituir os arquivos pelos de `replication_package.zip → src/`.
   Os três arquivos novos são `api_server.py`, `evichain/input_validation.py` e
   os scripts de benchmark adicionais.
3. **Reproducible Run** para regerar `/results`.
4. Conferir no `threat_model.json` de saída que aparecem 10 ameaças e a postura
   6 / 7. Se aparecerem 9 e 5 / 5, o código antigo ainda está em cache.
5. Publicar nova versão da cápsula. Isso gera um DOI `...v2`.
6. Atualizar no manuscrito a Seção de Data Availability, hoje apontando para
   `10.24433/CO.5374568.v1`.

## Ponto de atenção sobre os tempos

Uma corrida nova não reproduz os milissegundos da Tabela 5. A mineração em
*d* = 4 é de cauda pesada: a tabela traz 705,8 ms, a cápsula anterior deu
460,5 ms e a regeração local deu 643,2 ms. O manuscrito já declara que a cápsula
reproduz o pipeline e o comportamento de escala, não os tempos absolutos, de
modo que essa variação é esperada e não exige mudança no texto.
