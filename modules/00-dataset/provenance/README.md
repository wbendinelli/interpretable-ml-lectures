# Ambiente histórico dos estudos

[`requirements-study.lock`](requirements-study.lock) preserva, byte a byte, o
`requirements.lock` registrado nos protocolos dos estudos de treino completo,
balanceamento amostrado e comparação entre famílias. Sua identidade é o
SHA-256 `f477ce0c78a92d0adc908a008fe0313c387765ac6024a5dc9f814d2a8d8f01fe`;
os protocolos e seus hashes permanecem inalterados.

O lock ativo na raiz recebe a correção do pypdf, usado para ler o dicionário
oficial. O [internals da comparação entre famílias](../notebooks/srag_sample_family_internals.ipynb)
confere o lock histórico e as fontes científicas contra o protocolo, verifica
as versões científicas em uso e recusa diferenças nos blocos das demais
dependências entre os dois locks. Sua saída identifica a diferença de ambiente.
Essa auditoria de registros não reexecuta os ajustes nem as previsões.

Para reproduzir um estudo histórico, use um checkout separado na revisão
`b3ba17a26cee7bdd37214c4195a5e9358e11e369` e prepare o ambiente com o `requirements.lock`
daquela revisão, com Python 3.12.13 e verificação de hashes. Por exemplo, dentro
desse checkout histórico:

```bash
uv venv --python 3.12.13 .venv
VIRTUAL_ENV="$PWD/.venv" uv pip install --require-hashes -r requirements.lock
```

Não substitua temporariamente o lock ativo e não reassine protocolos antigos
para aceitar outro ambiente. Os executores continuam recusando a retomada de
checkpoints quando fontes ou ambiente divergem. Um novo estudo exige diretório
próprio e novo protocolo, sem sobrescrever o histórico.

O checkout e o ambiente não fornecem os artefatos privados do estudo. Carregar
o preditor com `srag_63_course_reference.py` ou explicá-lo com
`srag_76_course_pfi.py` também exige uma seleção concluída, o modelo ajustado e
os dados e checkpoints correspondentes. O estudo com treino completo permanece
interrompido antes dessa seleção. Desativar a verificação do loader não torna
esses artefatos disponíveis nem demonstra reprodução.

## Identidade dos arquivos de origem

[`source-sha256.txt`](source-sha256.txt) registra o SHA-256 dos microdados anuais
e dos documentos oficiais da extração adotada neste repositório. Esses hashes
foram medidos nos arquivos usados no trabalho; identificam seus bytes e não
constituem assinatura nem autenticação publicada pelo Ministério da Saúde.
Correspondência com o manifesto também não atesta qualidade clínica dos dados.

O [adquiridor](../../../tools/srag_10_fetch.sh) confere os arquivos já existentes
e recusa divergências sem apagá-los. Um download fica em arquivo temporário
adjacente e só recebe o nome definitivo depois de terminar e conferir o hash;
falhas e interrupções removem o temporário. Uma nova extração deve ter sua
proveniência discutida e registrada separadamente, sem atualizar estes hashes
apenas para aceitar bytes diferentes.

A [comparação InfoGripe](../notebooks/srag_infogripe_validation.ipynb) fixa
separadamente a revisão do repositório de origem e o SHA-256 esperado do CSV.
O identificador LFS dessa revisão coincide com o arquivo já usado no estudo.
O caderno confere o cache e promove apenas downloads verificados, preservando
o conteúdo, os filtros e a janela da comparação registrada.

Sem arquivos adicionais, o script baixa o conjunto completo. Para um caderno
que lê um ano por vez, informe os arquivos desejados depois do destino:

```bash
bash tools/srag_10_fetch.sh /tmp/srag INFLUD23-26-06-2025.parquet
```

A seleção aceita somente os arquivos anuais e documentos adotados; arquivos
desconhecidos ou repetidos são recusados antes de qualquer download. A mesma
verificação de integridade se aplica a uma seleção parcial.
