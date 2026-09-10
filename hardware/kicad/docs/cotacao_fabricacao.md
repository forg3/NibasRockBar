# Cotação de fabricação PCB — protótipo (5 unidades)

**Data:** 2026-09-10 · **Status:** PESQUISA, nenhum pedido submetido (sem conta, sem upload, sem checkout)
**Escopo:** 3 designs, 2 camadas, acabamento ENIG, 5 peças por design
- Pulseira discreta: circular Ø32 mm, 0,8 mm espessura
- Pulseira módulo: circular Ø32 mm, 0,8 mm espessura
- Gateway: retangular 62×36 mm, 1,6 mm espessura

> Nota de divergência: o board do gateway hoje no repo está em 60×32 mm
> (`docs/layout_status.md`); a cotação usa 62×36 mm conforme escopo solicitado.
> Diferença de área é pequena (~7 %) e não muda a faixa de preço abaixo.

---

## 1. Premissas

| Item | Premissa |
|---|---|
| Quantidade | 5 unid. **por design** (3 designs = 15 placas no total) |
| Camadas | 2L, FR-4, cobre 1 oz |
| Espessura | 1,6 mm (gateway) · 0,8 mm (pulseiras) |
| Acabamento | ENIG (1U", padrão de protótipo) |
| Cor / máscara | Verde padrão, silk branco (opção mais barata) |
| Trilha/espaço | ≥ 5/5 mil; furo mín. ≥ 0,3 mm (evita taxa de feature fina) |
| Contorno | Circular Ø32 (2 designs) + retangular 62×36 (1 design); contorno fresado incluso no preço base |
| Stencil | 1 stencil frameless por design que for montar em bancada (topo); espessura padrão 0,10–0,12 mm |
| Frete | Estimativa para Brasil, cotada no checkout (calculadora oficial); DHL/FedEx expresso vs. correio econômico |
| Câmbio | Valores em USD (moeda de cobrança das duas fábricas); conversão BRL só no fechamento (câmbio + IOF + impostos de importação variam) |

**O que NÃO está incluído:** montagem SMT, componentes (BOM), painelização especial, impedância controlada, testes além do e-test padrão, taxas alfandegárias brasileiras (II + ICMS + despacho — responsabilidade do importador).

---

## 2. Fontes oficiais consultadas (2026-09-10, sem login, sem pedido)

- JLCPCB homepage — "From $2.00 / 5 pcs", 2 camadas, build 24 h: https://jlcpcb.com/
- JLCPCB SMT Stencil — "from $3 (100×100 mm)", build 12 h, aço 304 HTA, ±0,003 mm: https://jlcpcb.com/pcb-stencil
- JLCPCB blog "Breaking Down PCB Pricing" — ENIG custa 20–40 % a mais que HASL: https://jlcpcb.com/blog/pcb-pricing-breakdown
- JLCPCB Help "How much does shipping cost?" — frete calculado por peso/país/método no checkout: https://jlcpcb.com/help/article/how-much-does-shipping-cost
- JLCPCB Help "Shipping Methods and Delivery Time": https://jlcpcb.com/help/article/shipping-methods-and-delivery-time
- JLCPCB News 2026-06-13 — ajuste dinâmico de preço por custo de laminado/cobre (preço final pode variar na calculadora): https://jlcpcb.com/news/jlcpcb-pcb-pricing-notice
- PCBWay homepage — instant quote "US $5.00, 10 pcs 1–2 layer, build 24 h": https://www.pcbway.com/
- PCBWay 2-layer 100×100 mm prototype — "Price: US $5.00": https://www.pcbway.com/pcb_prototype/2_Layer_pcb/100x100mm.html
- PCBWay 2-layer 150×100 mm prototype — "Price: US $41.00" (mostra que preço sobe com área fora da faixa promo): https://www.pcbway.com/pcb_prototype/2_Layer_pcb/150x100mm.html
- PCBWay stencil (cotação online por tamanho/espessura): https://www.pcbway.com/stencil.aspx
- PCBWay Shipping Method Guide — DHL 3–7 dias úteis, UPS/TNT/FedEx/EMS/correio econômico: https://www.pcbway.com/shipping_method_guide.aspx

> Preços "a partir de" são promocionais para placas pequenas (≤100×100 mm) em spec padrão.
> ENIG, espessura 0,8 mm e contorno circular somam adicional sobre a base — o valor exato
> só sai na calculadora oficial com o Gerber anexado. Nenhuma cotação foi submetida.

---

## 3. Tabela comparativa (estimativa, 5 peças por design, ENIG)

| Item | **JLCPCB** (estimado) | **PCBWay** (estimado) |
|---|---|---|
| PCB — pulseira discreta Ø32, 0,8 mm, 2L, ENIG, 5 unid. | ~US$ 4–8 | ~US$ 8–15 |
| PCB — pulseira módulo Ø32, 0,8 mm, 2L, ENIG, 5 unid. | ~US$ 4–8 | ~US$ 8–15 |
| PCB — gateway 62×36, 1,6 mm, 2L, ENIG, 5 unid. | ~US$ 2–6 (base promo US$ 2 + adicional ENIG) | ~US$ 5–12 (base US$ 5 faixa 100×100) |
| **Subtotal PCBs (3 designs × 5 unid.)** | **~US$ 10–22** | **~US$ 21–42** |
| Stencil frameless (por design, 0,10–0,12 mm, sem eletropolimento) | a partir de ~US$ 3 cada (fonte oficial) → 1–3 unid.: ~US$ 3–15 | ~US$ 8–20 cada (via calculadora; combinar designs num stencil só quando possível) → 1–3 unid.: ~US$ 8–30 |
| Frete estimado p/ Brasil (pacote leve < 0,5 kg) | Econômico/postal: ~US$ 5–12 (7–20 dias) · DHL/FedEx: ~US$ 18–32 (3–7 dias) | Econômico: ~US$ 8–15 (7–20 dias) · DHL/UPS/FedEx: ~US$ 25–40 (3–7 dias) |
| **Total estimado (PCBs + 1 stencil + frete DHL)** | **~US$ 31–69** | **~US$ 54–112** |
| **Total estimado (PCBs + 1 stencil + frete econômico)** | **~US$ 18–49** | **~US$ 37–87** |
| Prazo fabril (protótipo 2L padrão) | 24 h–3 dias (ENIG soma ~1 dia) | 24 h–3 dias (ENIG soma ~1–2 dias) |
| Prazo porta a porta (fab + frete) | ~5–10 dias (DHL) · ~10–25 dias (econômico) | ~5–10 dias (DHL) · ~10–25 dias (econômico) |

**Leitura direta:**
- Placas pequenas (Ø32 e 62×36) ficam dentro da faixa promocional das duas fábricas; o custo dominante é **ENIG + frete**, não a placa nua.
- JLCPCB tende a ~40–50 % mais barato no total para este perfil (base US$ 2 vs. US$ 5 + stencil mais barato).
- PCBWay compensa se for preciso engenharia de revisão/ajuda em inglês ou combinar stencil+montagem no mesmo pedido.
- Valores são **faixas estimadas**, não cotação fechada: confirmar na calculadora oficial antes de qualquer decisão de compra.

---

## 4. GATE de envio — estado por placa (base: DRC `--severity-error`, sem físicos pendentes)

**Regra do GATE:** status **"PRONTO PARA ENVIAR"** somente se DRC = 0 error **e** nenhum problema físico/roteamento pendente. Caso contrário, a placa **NÃO** vai no pacote.

| Placa | DRC errors | Unconnected | Físicos pendentes | GATE |
|---|---|---|---|---|
| Gateway (62×36→board atual 60×32, 1,6 mm) | 0 | 0 | 0 | ✅ **PRONTO PARA ENVIAR** (isoladamente) |
| Pulseira discreta (Ø32, 0,8 mm) | — | 16 | 2 | ❌ **NÃO ENVIAR** — faltam: 2 problemas físicos + 16 nets unconnected (re-placement dos passivos + vias de stitch GND; ver `docs/layout_status.md` §4a) |
| Pulseira módulo (Ø32, 0,8 mm) | 28 | — | decisões abertas | ❌ **NÃO ENVIAR** — faltam: 28 errors de física (módulo E73 17,5×28,7 + holder CR2032 não cabem lado a lado no Ø32) + decisão de projeto pendente: (1) cápsula maior que Ø32, (2) módulo menor da família E73, ou (3) aceitar overhang (ver `docs/layout_status.md` §4b) |

**Veredito do lote:** ❌ **LOTE NÃO PRONTO — "PRONTO PARA ENVIAR" NEGADO para o pacote completo.** Somente o gateway atende ao GATE; as duas pulseiras têm pendências bloqueantes. Opção: fabricar **só o gateway** (pedido isolado, 5 unid., 1,6 mm, ENIG) enquanto as pulseiras fecham layout — decisão do responsável.

**Antes de qualquer upload, ainda exigido (vale para o gateway inclusive):**
1. Re-rodar DRC `--severity-error` no board final e confirmar 0 error (JSON commitado em `exports/`).
2. Conferir footprint do soquete do DevKitC (fileiras a 27,94 mm — ver pendência registrada em `docs/layout_status.md` §4c) e dimensão final do board (60×32 vs. 62×36).
3. Revisão visual dos Gerbers (camadas, máscara, silk, Edge.Cuts) antes de anexar.

---

## 5. Checklist do pacote de fabricação (por design PRONTO)

Gerar via `kicad-cli` (nunca GUI para gerar), um diretório por design em `exports/<placa>/fab/`:

- [ ] Gerbers RS-274X: `F.Cu`, `B.Cu`, `F.Mask`, `B.Mask`, `F.SilkS`, `B.SilkS`, `Edge.Cuts`
- [ ] Drill: Excellon (`*.drl`) + mapa de furos
- [ ] `BOM.csv` (designators, footprint, valor, fabricante/PN, DNP marcados)
- [ ] `P&P.csv` (centroide + rotação + lado, origem comum ao Gerber; só se for montar fora)
- [ ] Paste: `F.Paste` (e `B.Paste` se dupla face) p/ stencil
- [ ] `README_fab.txt`: stackup (2L, espessura, cobre 1 oz), acabamento ENIG, cor máscara/silk, quantidade, contorno especial (circular Ø32 / retangular), observações (keepout antena, ISOLAR BT1 se aplicável)
- [ ] PDF de conferência (layers Cu+Mask+Silk+Edge.Cuts) + STEP para checagem mecânica da cápsula
- [ ] DRC JSON 0-error anexado como evidência do GATE

Comandos de referência (KiCad 10.0.6, ver `docs/kicad10_recipe.md` e `docs/layout_approach.md`):
`kicad-cli pcb drc`, `kicad-cli pcb export gerbers`, `kicad-cli pcb export drill`,
`kicad-cli pcb export pdf --layers F.Cu,B.Cu,Edge.Cuts,F.SilkS,B.SilkS,F.Mask,B.Mask`,
`kicad-cli pcb export step`, `kicad-cli sch export bom`.

---

## 6. Próximo passo (sem compromisso)

1. Decidir: pedido isolado do gateway agora vs. aguardar as pulseiras.
2. Fechar pendências das pulseiras (§4) e re-rodar DRC até 0 error.
3. Só então: gerar pacote (§5) → cotar na calculadora oficial (JLCPCB e PCBWay) → comparar total com frete real → submeter mediante aprovação explícita.

*Nenhum pedido, conta ou upload foi realizado nesta etapa — apenas pesquisa web + este documento.*
