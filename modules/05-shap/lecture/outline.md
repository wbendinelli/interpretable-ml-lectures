# Aula — SHAP no modelo COVID (forma viva)

> Módulo novo (2026-09-01), direto sobre o modelo do curso — não há deck
> histórico; esta é a única forma da aula.

## Arco (50 min)

1. **Do jogo cooperativo à floresta** (8 min) — Shapley em uma frase:
   média do efeito marginal sobre todas as ordens de chegada. O que a
   eficiência promete; por que na margem e não na probabilidade. O
   TreeSHAP exato mora no XGBoost (`pred_contribs`) — e por que a lib
   `shap` ficou fora (decisão pinada e registrada).

2. **A soma exata** (10 min) — `shap_passo_1_soma.png`: +0,0000 na
   margem, sigmoide 0,5000, dígito por dígito; desvio máximo 7,6×10⁻⁶ no
   teste inteiro. Contraste imediato com o módulo 03: lá um R² sobre uma
   nuvem; aqui um axioma sobre ESTA predição.

3. **SHAP × LIME, mesmo paciente** (8 min) — `shap_passo_2_vs_lime.png`:
   7/8 direções batem; a que diverge (`meses`) é o "plano no CP" do
   módulo 03 — discordância onde não há sinal. Escala não compara:
   margem exata vs peso de reta.

4. **Global e a deriva** (8 min) — `shap_passo_3_global.png`: média|SHAP|
   de 2024 vs gain de 2020–2022 (`meses` 3º vs 16º) — importância "para
   prever agora" não é "para construir a árvore". Módulo 02 por outro
   ângulo; internals: o par que mais interage é idade × meses.

5. **Caminho × intervenção, e os Frankensteins** (12 min) —
   `shap_passo_4_interventional.png`: a permutação na mão concorda em
   direção e diverge onde as correlações moram; as estimativas convergem
   para OUTRA condicional. E as 2.460 linhas híbridas avaliadas são
   26,3% impossíveis pela mesma `gate_impossible` — o curso fecha com a
   pergunta com que abriu: quem são as linhas?

6. **Fechamento do curso** (4 min) — a tabela dos cinco métodos (uma
   pergunta, cinco entregas ao modelo, uma cerca só).

## Números citados nesta aula

Todos impressos por células dos dois notebooks deste módulo.
