# Decisão de forma física — Variante A (pulseira, disco Ø32 mm)

**Data:** 2026-09-09
**Status:** Decidido
**Escopo:** Variante A (pulseira esportiva de silicone, cápsula IP67, disco Ø32 mm)

## Decisão

Substituir o módulo Ebyte E73-2G4M04S-52810 (17,5 × 28,7 mm) pelo **Fanstel BM832A**
(nRF52810, 10,2 × 15 × 1,9 mm, US$ 3,61) na variante A.

## Justificativa (com fontes)

### 1. Cápsula: não existe cápsula vazia IP67 redonda Ø34–38 mm no mercado

Não existe cápsula vazia IP67 redonda Ø34–38 mm no mercado. O que existe são
**beacons prontos** (não cápsulas vazias):

- Trax10214 — Ø35,9 mm (beacontrax.com)
- Minew B10 — Ø38 mm (minew.com)
- Minew E7 — Ø39 × 15,5 mm, IP67, rosca — menor cápsula **comprovada** que aceita
  pilha CR2477 (minew.com)

Aumentar a cápsula além de Ø32 mm exigiria **moldagem custom** (ferramental +
NRE), custo inviável para protótipo de 5 unidades. Fontes: beacontrax.com,
minew.com, takachi-enclosure.com.

### 2. Overhang castelado fora do círculo: NÃO viável

Regras oficiais de fabricação eliminam a opção de manter o E73 com os pads das
pontas em overhang (fora do arco do disco):

- JLCPCB e PCBWay exigem furo PTH bissecado pelo contorno da placa + pad com
  extensão ≥ 0,5 mm para dentro do contorno (links oficiais das regras de
  fabricação de ambos).
- Os pads das pontas do E73 ficariam fora do arco (sagitta ≈ 1,65 mm) — violam
  a regra de fabricação em ambas as casas.

### 3. Fanstel BM832A: encaixa, custa igual, zero migração de firmware

- **Mesmo SoC** nRF52810 → SoftDevice S112 funciona direto, **zero migração**.
- **Dimensões:** 10,2 × 15 mm → diagonal ≈ 18,2 mm, cabe folgado no Ø32 mm.
  (E73: diagonal ≈ 33,5 mm — não cabe.)
- **Preço:** paridade — US$ 3,61 vs US$ 3,59.
- **Alimentação:** VDD 1,7–3,6 V → CR2032 ok.
- **Antena integrada** + certificações FCC/CE/TELEC.
- **Indutores do DC/DC integrados ao módulo** ([página oficial Fanstel BM832A](https://www.fanstel.com/bm832a-bluetooth-5-module)) —
  **fecha o item aberto #2** do projeto.
- **ANATEL:** segue como item aberto (mesmo status do E73 — módulo BLE
  certificado, homologação a confirmar).

### 4. Alternativa registrada (não escolhida)

Manter o E73 e usar cápsula Ø39 custom (moldagem). Descartada: custo de
ferramental inviável para protótipo de 5 unidades.

### 5. Impacto no projeto

- Novo símbolo + footprint do BM832A (transcritos do datasheet Fanstel).
- Troca de U1 no `.kicad_sch` da variante A.
- Re-layout da placa.
- Keepout de antena do BM832A conforme manual Fanstel (antena estendida fora
  do ground plane — **verificar dimensões exatas no manual**).

### 6. Ressalva honesta

Diagonal caber no disco **não significa layout fechado**. O keepout de antena
do BM832A e a coexistência com BT1 (porta-pilha CR2032) e TAG1 (NTAG213)
precisam ser validados geometricamente no KiCad antes de considerar a placa
resolvida.

## Referências

- beacontrax.com — Trax10214 (Ø35,9 mm)
- minew.com — B10 (Ø38 mm), E7 (Ø39 × 15,5 mm, IP67, CR2477)
- takachi-enclosure.com — busca de cápsulas IP67
- JLCPCB — regras de fabricação (furo PTH bissecado + pad ≥ 0,5 mm)
- PCBWay — regras de fabricação (idem)
- Fanstel — [página oficial BM832A](https://www.fanstel.com/bm832a-bluetooth-5-module) (dimensões, preço, indutores DC/DC
  integrados, certificações)
