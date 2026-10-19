# Módulo 00 — da notificação bruta ao modelo do curso

Este módulo documenta a origem dos dados SRAG/COVID, sua preparação e o
preditor explicado nas aulas. Comece pelo percurso **Usar o caso nas aulas**.
O percurso **Auditar a construção** reúne a procedência, as decisões e os
estudos que sustentam essa referência.

<a id="coorte-partições-e-treino-efetivamente-usado"></a>
<a id="o-modelo-histórico-do-curso"></a>

## O que está em uso

A tarefa é retrospectiva: estimar o desfecho registrado na coorte hospitalizada
COVID definida no [manifesto Gold](gold/MANIFEST.md). O alvo admite cura e óbito
nos códigos da receita; óbito por outras causas, ignorado e vazio ficam fora.
A unidade analisada é a notificação. A separação por pessoa e a disponibilidade
de todos os preditores na admissão não foram demonstradas nesta extração.

As aulas mantêm o XGBoost da referência histórica, ajustado na amostra de treino
até 2022, com validação em 2023 e teste histórico em 2024 (walkthrough do modelo
§1–§2). A logística fornece um contraste. Exemplares, painéis e conjuntos de
apoio das explicações dependem da pergunta de cada método.

As comparações concluídas por log loss estão em [COURSE_STUDY.md](COURSE_STUDY.md).
Elas preservam a procedência dos próprios ajustes; não substituem silenciosamente
o preditor das aulas. O teste histórico já foi observado e suas avaliações são
exploratórias. Esse material não demonstra utilidade clínica na admissão.

## Usar o caso nas aulas

| Ordem | Abrir | O que obter |
|---|---|---|
| 1 | [Manifesto Gold](gold/MANIFEST.md) | População, alvo, entradas, partições e origem da amostra distribuída. |
| 2 | [Walkthrough do modelo](notebooks/srag_model_walkthrough.ipynb) | Reconstrução da referência na amostra, avaliação e regra de escolha dos exemplares. |
| 3 | [Ficha histórica do modelo](MODEL.md) | Parâmetros e resultados do ajuste que os métodos explicam. Leia as ressalvas de contexto abaixo. |
| 4 | [Módulos de interpretabilidade](../../README.md#modules) | Método, objetivo, walkthrough e verificações próprias de cada aula. |

Não é necessário baixar toda a série, executar novas buscas ou iniciar o banco
Docker para seguir esse percurso. Os arquivos distribuídos permitem reconstruir
a referência; a instalação das dependências requer acesso à rede quando o
ambiente ainda não está preparado.

<a id="o-mapa--do-download-ao-modelo"></a>
<a id="a-virada--do-fato-à-tarefa"></a>
<a id="as-cinco-escolhas-de-tarefa"></a>

## Auditar a construção

| Etapa | Percurso de leitura | Pergunta |
|---|---|---|
| Procedência e tratamento | [Silver walkthrough](notebooks/srag_silver_walkthrough.ipynb) → [Silver internals](notebooks/srag_silver_internals.ipynb) | Como os campos são tratados e o que muda entre os anos? |
| Qualidade e referência externa | [Contrato](COLUMNS.md) · [Qualidade](QUALITY.md) · [InfoGripe](notebooks/srag_infogripe_validation.ipynb) | Que regras foram verificadas, onde falham e qual janela externa foi comparada? |
| Definição da tarefa | [GOLD.md](GOLD.md) → [Manifesto](gold/MANIFEST.md) | Quais escolhas produziram a coorte, o alvo e as entradas? |
| Seleção histórica | [Walkthrough](notebooks/srag_selection_walkthrough.ipynb) → [Internals](notebooks/srag_selection_internals.ipynb) | Como a seleção por AUC estabeleceu a referência? |
| Modelo e estudos posteriores | [Model internals](notebooks/srag_model_internals.ipynb) · [COURSE_STUDY.md](COURSE_STUDY.md) | Quais sensibilidades foram medidas e quais comparações chegaram ao fim? |

Bronze preserva os arquivos de origem; Silver registra o tratamento e suas
verificações; Gold aplica as escolhas da tarefa. Os diagramas detalham o
[fluxo](PIPELINE.svg), os [regimes](REGIMES.svg), o [funil de campos](FUNIL.svg)
e a [seleção histórica](SELECTION.svg).

<a id="o-percurso-em-uma-tabela"></a>
<a id="escolher-o-modelo--um-protocolo-não-um-palpite"></a>
<a id="comparar-estratégias-de-balanceamento"></a>

## Estado dos cadernos

Os [estudos históricos](notebooks/archive/README.md) ficam em `notebooks/archive/`.
O [mapa de migração](../NOTEBOOK_MIGRATIONS.md) preserva a localização dos caminhos
registrados na proveniência. Os arquivos continuam cobertos pelas verificações.

“Concluído” descreve o estudo registrado, com seu protocolo e alcance.
Ler um agregado e conferir suas contas não equivale a refazer o treinamento
ou as previsões individuais. As buscas ficam fora da execução padrão das aulas.

| Caderno | Papel e estado | Execução padrão e condições |
|---|---|---|
| [Silver walkthrough](notebooks/srag_silver_walkthrough.ipynb) | Auditoria do tratamento em um ano. | Baixa o arquivo anual de referência e reconstrói o tratamento. |
| [Silver internals](notebooks/srag_silver_internals.ipynb) | Auditoria da série e das regras entre anos. | Lê os arquivos anuais; exige mais rede e memória que o walkthrough. |
| [InfoGripe](notebooks/srag_infogripe_validation.ipynb) | Comparação externa na janela histórica disponível. | Manual; depende da série externa e dos microdados da janela. |
| [Selection walkthrough](notebooks/srag_selection_walkthrough.ipynb) | Seleção histórica por AUC, concluída. | Usa a amostra e o agregado; reproduz partes da seleção. |
| [Selection internals](notebooks/srag_selection_internals.ipynb) | Auditoria e sensibilidades dessa seleção. | Refaz ajustes; as seções de treino completo dependem da Gold local. |
| [Model walkthrough](notebooks/srag_model_walkthrough.ipynb) | Referência em uso nas aulas. | Ajusta o modelo na amostra distribuída. |
| [Model internals](notebooks/srag_model_internals.ipynb) | Validação técnica e sensibilidades da referência. | Partes exigem Gold ou Silver local; a falta é declarada na saída. |
| [Balance comparison](notebooks/archive/srag_balance_comparison.ipynb) | Comparação concluída com hiperparâmetros fixos. | Lê o registro e a amostra; `RUN_REFIT` refaz o estudo. |
| [Sample balance walkthrough](notebooks/srag_sample_balance_walkthrough.ipynb) | Comparação concluída com ajuste próprio por estratégia. | Lê o agregado e apresenta os finalistas por log loss. |
| [Sample balance internals](notebooks/srag_sample_balance_internals.ipynb) | Auditoria desse protocolo amostrado. | Confere amostra, grade, seleção e aritmética do agregado. |
| [Sample family walkthrough](notebooks/srag_sample_family_walkthrough.ipynb) | Comparação concluída entre famílias por log loss. | Lê o agregado e distingue novos ajustes de candidatos reutilizados. |
| [Sample family internals](notebooks/srag_sample_family_internals.ipynb) | Auditoria dessa comparação entre famílias. | Confere proveniência, configurações e escolha no agregado. |
| [Course study walkthrough](notebooks/archive/srag_course_study_walkthrough.ipynb) | Registro da tentativa interrompida no treino completo. | Lê o estado preservado; não apresenta uma seleção final. |
| [Course study internals](notebooks/archive/srag_course_study_internals.ipynb) | Guardas e ensaios do protocolo interrompido. | Confere integridade e persistência; não conclui a comparação. |
| [PFI ranking](notebooks/archive/srag_pfi_ranking.ipynb) | Evidência histórica e estudos auxiliares de permutação. | Lê o ranking, reconstrói a referência e executa diagnósticos; `RUN_REFIT` refaz as permutações completas. |

A execução automática seleciona arquivos `*_walkthrough.ipynb` e
`*_internals.ipynb`. InfoGripe, Balance comparison e PFI ranking requerem
execução manual. Uma execução automática pode declarar o salto de uma seção
que exige os dados completos; esse salto não comprova a reprodução da seção.

<a id="pfi-erro-original-erro-após-permutar-e-estabilidade-do-ranking"></a>

### Onde estudar PFI

A aula vigente está no [módulo 10](../10-pfi/README.md), com walkthrough,
internals, roteiro e apresentação próprios. O módulo 00 conserva o
[registro do ranking](gold/pfi_ranking.json), a [ficha técnica histórica](PFI.md)
e os estudos que contribuíram para a aula. Os experimentos de associação e as
prévias de permutação no fim de PFI ranking são complementares à leitura principal.

## Mapa de referência

| Documento | Responsabilidade |
|---|---|
| [PROFILE.md](PROFILE.md) · [PROFILE.json](PROFILE.json) | Perfil por coluna e ano, antes do tratamento. |
| [DICTIONARY.md](DICTIONARY.md) | Significado e domínio oficial dos campos. |
| [COLUMNS.md](COLUMNS.md) | Contrato das colunas publicadas e derivadas. |
| [QUALITY.md](QUALITY.md) | Checagens de qualidade e resultados por ano. |
| [GOLD.md](GOLD.md) · [Manifesto](gold/MANIFEST.md) | Registro das decisões e receita efetivamente aplicada. |
| [SELECTION.md](SELECTION.md) · [MODEL.md](MODEL.md) | Fichas geradas dos estudos históricos de seleção e modelo. |
| [COURSE_STUDY.md](COURSE_STUDY.md) | Protocolos posteriores, resultados concluídos e tentativa interrompida. |
| [tools/README.md](../../tools/README.md) | Executores, entradas, saídas e reprodução. |

Os documentos identificados como gerados são produzidos e conferidos por seus
executores. `GOLD.md` e `COURSE_STUDY.md` são registros editoriais das decisões
e dos estudos. **Contexto das fichas históricas:** referências a “cinco módulos”,
“um modelo, um paciente” e “teste lido uma vez” descrevem a redação daquela
etapa. Hoje os métodos incluem explicações globais, escolhem seus próprios
exemplares quando necessário e reutilizam um teste já observado. As fichas
não devem ser lidas como certificado de teste independente ou de validade clínica.
Da mesma forma, os portões combinam aplicabilidade do formulário, calendário
e inclusão na coorte; o termo histórico “impossível” não constitui uma
validação biológica das combinações aceitas.

<a id="o-que-ficou-registrado-como-corrigido"></a>

<details>
<summary>Memória técnica e correções preservadas</summary>

- **Portão impossível.** Esta página afirmou que dois predicados rejeitados
  eram contraditos em todos os registros. A tabela identifica um, `TIPO_TRAT`
  (Silver internals §4). A correção pertence ao registro, não a uma nova regra.
- **Balanceamento.** A justificativa antiga dizia que “reponderar destruiria
  a história de calibração”. Os estudos concluídos medem as receitas declaradas;
  não demonstram uma impossibilidade geral de usar pesos ou reamostragem
  ([protocolo e resultados](COURSE_STUDY.md)).
- **Seleção e teste.** A seleção histórica exclui o teste da função de escolha,
  mas o período já havia sido observado. A guarda de código não transforma
  essa avaliação em confirmação independente.
- **Adoção histórica.** A pendência de sincronizar os módulos de método após
  a seleção foi resolvida; a redação histórica dos cadernos e fichas conserva
  o contexto da etapa. O [CHANGELOG](../../CHANGELOG.md) registra a adoção e
  as revisões dependentes.
- **Tratamento.** As correções de semana epidemiológica, catálogo de influenza
  e datas sem prefixo estão junto da evidência no Silver walkthrough §2 e §6
  e no Silver internals §8–§9. A cobertura vigente está em [COLUMNS.md](COLUMNS.md).

As referências por etapa mantêm as âncoras da versão anterior desta página:

<a id="1-aquisição--o-banco-congelado-direto-do-bucket"></a>
- **Aquisição:** [fonte e execução](../../tools/README.md#a-sequência).
<a id="2-perfilamento--medir-cada-ano-antes-de-tratar-qualquer-um"></a>
- **Perfilamento:** [PROFILE.md](PROFILE.md).
<a id="3-regimes--a-base-muda-de-problema-no-meio-da-série"></a>
- **Regimes:** [Silver internals §1 e §6](notebooks/srag_silver_internals.ipynb).
<a id="4-normalizar-a-forma--antes-de-ler-qualquer-domínio"></a>
- **Normalização:** [Silver walkthrough §2](notebooks/srag_silver_walkthrough.ipynb).
<a id="5-o-vazio-não-é-uma-coisa-só--três-estados-nunca-fundidos"></a>
- **Estados do vazio:** [Silver walkthrough §3](notebooks/srag_silver_walkthrough.ipynb).
<a id="6-criar-variáveis--226-derivadas-cada-uma-com-proveniência"></a>
- **Derivadas:** [COLUMNS.md](COLUMNS.md).
<a id="7-sujeira-visível-contrato-verificado--nada-some-nada-é-reparado"></a>
- **Cobertura e anomalias:** [COLUMNS.md](COLUMNS.md) · [QUALITY.md](QUALITY.md).
<a id="8-auditar--kahn-por-dentro-fiocruz-por-fora"></a>
- **Qualidade e referência externa:** [QUALITY.md](QUALITY.md) · [InfoGripe](notebooks/srag_infogripe_validation.ipynb).
<a id="9-o-alvo--óbito-nos-casos-fechados"></a>
<a id="10-a-coorte--um-funil-que-não-comuta"></a>
<a id="11-o-vazamento--uma-lista-gerada-nunca-digitada"></a>
<a id="12-o-split--temporal-porque-a-população-não-é-estacionária"></a>
<a id="13-a-codificação--o-que-se-funde-declarado"></a>
- **Alvo, coorte, exclusões, split e codificação:** [GOLD.md](GOLD.md) · [Manifesto](gold/MANIFEST.md).

</details>

## Rodar isto na sua máquina

A [sequência das ferramentas](../../tools/README.md#a-sequência) é a referência
para aquisição, tratamento, Gold e estudos. Ela distingue arquivos distribuídos,
microdados completos e saídas geradas. Reconstruir todo o percurso exige os
arquivos originais, rede e recursos locais; ler os resultados registrados não
refaz automaticamente esses experimentos.

<details>
<summary>Exploração opcional em Postgres, Metabase e Adminer</summary>

O [loader](docker/load.py) organiza os arquivos em tabelas locais. Parquets
continuam sendo a fonte dos dados; essa exploração não é requisito das aulas.

```bash
cd modules/00-dataset/docker
cp .env.example .env              # escolha uma senha; .env é git-ignored
set -a; . .env; set +a
docker compose up -d
python3 load.py                   # Bronze + Silver + Gold disponíveis localmente
python3 load.py --only-gold       # carregar apenas a parte Gold
```

A Gold completa exige o parquet local. A amostra, os dicionários e os registros
agregados distribuídos também podem ser carregados. O loader documenta as tabelas
que cria e substitui ao ser reexecutado.

Metabase: `localhost:3000`; Adminer: `localhost:8080`. No Metabase, crie a conta
local de administrador e conecte ao host `db`, porta `5432`, base e usuário
`srag`, com a senha escolhida no `.env`. A inicialização baixa imagens Docker
quando elas ainda não estão disponíveis na máquina.

</details>

## Privacidade, fonte e licença

A publicação de origem remove identificadores diretos. `DT_NASC` permanece
nos microdados e é um quase-identificador quando combinado a outros campos;
o contrato o classifica como `identifier`. A idade entra por derivados.
Evite publicar recortes que aproximem um indivíduo de identificação.

Fonte: Ministério da Saúde / SVSA — SIVEP-Gripe, via
[Portal de Dados Abertos do SUS](https://dadosabertos.saude.gov.br/dataset/srag-2019-a-2026).
Script de referência:
[CGCOVID — dados públicos](https://gitlab.com/cgcovid/dados-publicos) (MIT).
Série externa de comparação:
[FluVigilanciaBR/data](https://github.com/FluVigilanciaBR/data) (GPL-3.0).
