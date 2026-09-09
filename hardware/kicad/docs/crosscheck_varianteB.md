# Cross-check Variante B — nRF52810-QCAA QFN32 (passo 5.2)

**Data:** 2026-09-09 · **Verificador:** sessão fresh (independente, sem acesso aos artefatos das waves anteriores como fonte de verdade)
**Escopo:** `hardware/kicad/wristband_discreto/` (esquema + exports) vs `docs/designator_map.md` (ground truth da Variante B) vs `BOM_discreta_corrigida_nRF52810_QFN32.csv` (raiz — **apenas valores**) vs `docs/verificacao_matematica.md` (claims 13–18/20).

**Fontes NÃO usadas como referência (registrado por decisão do despacho):**
- `netlist_conexoes.md` (raiz) — topologia anterior à correção de 2026-09-09 (Π de 4 elementos, C8 em DEC2+DEC3). Não usada para topologia.
- `docs/datasheet_facts_nordic.md` §1.1 — pinagem alucinada (afirma VDD=25 único, DEC4=31, DCC=32, "P0.29"); refutada por 3 fontes independentes (PS v1.3 Tabela 114, DevZone #53125, símbolo KiCad `MCU_Nordic:nRF52810-QCxx`) — ver `verificacao_matematica.md` claim 13. Não usada para pinagem; o restante do arquivo (Tabela 123, cristal, correntes) foi citado apenas via claims 17/19/20 já verificados no passo 5.1.

**Método (tudo executado nesta sessão):**
1. Leitura do `lib_symbols` embutido no `.kicad_sch` (pinNumber pino a pino, linhas 17–712).
2. Leitura integral da netlist exportada `exports/wristband_discreto.net` (2598 linhas, 33 nets).
3. Leitura de `exports/erc_report.json` + re-execução fresh do ERC e da export de netlist em `/tmp` (comparação byte a byte com os exports commitados).
4. Conferência de fios/labels por coordenada no `.kicad_sch` (prova dos PWR_FLAG, que não aparecem na netlist).
5. Varredura de higiene: unicidade de UUIDs, flags `no_connect`/`dnp`, title block, valores vs `designator_map.md` linha a linha.

**Sincronia exports ↔ esquema:** `.kicad_sch` (mtime 10:30) é anterior aos exports (10:36). Re-execução fresh nesta sessão: ERC exit 0 ("0 violações") e netlist re-exportada **idênticas** aos arquivos commitados (diff vazio, exceto timestamp). Os exports refletem o esquema atual.

---

## Tarefa 1 — Pinagem U1 (QFN32) — **OK**

Fontes confrontadas: (a) embed `MCU_Nordic:nRF52810-QCxx` no `.kicad_sch` linhas 17–712; (b) `pinfunction` da netlist; (c) `designator_map.md` linha 66. Resultado: 33/33 pinos do embed casam com as três fontes.

| Pino | Nome no embed (.kicad_sch) | `pinfunction` na netlist | designator_map | Veredito |
|---|---|---|---|---|
| 1 | DEC1 | `DEC1_1` | DEC1=1 | OK |
| 9 | VDD | `VDD_9` | VDD=9/25/32 | OK |
| 25 | VDD | `VDD_25` | VDD=9/25/32 | OK |
| 32 | VDD | `VDD_32` | VDD=9/25/32 | OK |
| 16 | P0.21/~{RESET} | `P0.21/~{RESET}_16` | nRESET=16 | OK |
| 17 | SWDCLK | `SWDCLK_17` | SWDCLK=17 | OK |
| 18 | SWDIO | `SWDIO_18` | SWDIO=18 | OK |
| 19 | ANT | `ANT_19` | ANT=19 | OK |
| 20 | VSS | `VSS_20` | VSS=20/29+die pad | OK |
| 29 | VSS | `VSS_29` | VSS=20/29+die pad | OK |
| 33 | VSS (die pad, QFN-32-1EP) | `VSS_33` | die pad → GND | OK |
| 21 | DEC2 | `DEC2_21` | DEC2=21 | OK |
| 22 | DEC3 | `DEC3_22` | DEC3=22 | OK |
| 23 | XC1 | `XC1_23` | XC1=23 | OK |
| 24 | XC2 | `XC2_24` | XC2=24 | OK |
| 30 | DEC4 | `DEC4_30` | DEC4=30 | OK |
| 31 | DCC | `DCC_31` | DCC=31 | OK |
| 2–8, 10–15, 26–28 | P0.00…P0.30 (16 GPIOs, nomes = Tabela 114 PS v1.3) | todos em nets `unconnected-(U1-…)` | NC explícito | OK |

Conferência adicional: os 3 pinos VDD (9/25/32) estão todos na net `VDD_BAT` (netlist código 15) e os 3 VSS (20/29/33) na net `GND` (netlist código 14) — coincide com o `designator_map.md` e com o claim 13/15 do `verificacao_matematica.md` (CONFIRMADOS). O §1.1 alucinado do facts file não foi usado.

## Tarefa 2 — No-connect e DNP — **OK**

| Item | Esperado | Encontrado | Evidência | Veredito |
|---|---|---|---|---|
| NC pinos 2–8 (7) | flag no_connect | 7 nets `unconnected-(U1-P0.xx-PadN)` com pintype `+no_connect` | netlist códigos 18–24; marcadores `.kicad_sch` 4580–4586 | OK |
| NC pinos 10–15 (6) | flag no_connect | 6 nets idem | netlist códigos 25–30; marcadores 4587–4592 | OK |
| NC pinos 26–28 (3) | flag no_connect | 3 nets idem | netlist códigos 31–33; marcadores 4593–4595 | OK |
| Total U1 NC | 16 | 16 (18 marcadores no total: 16 U1 + 2 TAG1) | `grep -c no_connect` = 18 | OK |
| TAG1 ANT1/ANT2 | sem conexão elétrica (inlay adesivo) | 2 nets `unconnected-(TAG1-…)` com `+no_connect` | netlist códigos 16–17; marcadores 4596–4597 | OK |
| C7 | DNP | `(dnp yes)` — único cap DNP | `.kicad_sch` 3728; prop `dnp` na netlist 510 | OK |
| R1 | DNP | `(dnp yes)` — único resistor DNP | `.kicad_sch` 3230; prop `dnp` na netlist 941 | OK |
| Outros DNP | nenhum | contagem global `(dnp yes)` = 2 (C7, R1) | varredura do arquivo | OK |

## Tarefa 3 — Topologia RF de 2 elementos (PS v1.3 Fig. 146) — **OK**

| Item | Esperado (Fig. 146 / designator_map linha 41/49/67) | Encontrado na netlist | Veredito |
|---|---|---|---|
| Nó no pino ANT | `NET_ANT` = {U1.19, C3.1, L1.1} | código 1: exatamente {C3.1, L1.1, U1.19 `ANT_19`} | OK |
| C3 shunt | 0.8pF, C3.2 → GND | valor 0.8pF; C3.2 ∈ GND (código 14) | OK |
| L1 série | 3.9nH entre NET_ANT e antena | valor 3.9nH; L1.1 ∈ NET_ANT, L1.2 ∈ NET_RF | OK |
| Feed da antena | `NET_RF` = {L1.2, ANT1.1} | código 9: {ANT1.1 `FEED_1`, L1.2} | OK |
| GND da antena | ANT1.2 → GND | ANT1.2 `PCB_Trace_2` ∈ GND | OK |
| Sem L3 no caminho RF | L3 isolado no ladder DC/DC | L3 aparece apenas em NET_L2_L3/NET_DEC4 | OK |
| Sem C7 no caminho RF | C7 = desacoplo DEC2 | C7 aparece apenas em NET_DEC2 | OK |

Topologia como-construída = ANT(19) → [C3 0.8pF shunt→GND] → [L1 3.9nH série] → ANT1 (2 elementos), exatamente a referência Nordic registrada no `designator_map.md` (linha 67) e no claim 18 do passo 5.1.

## Tarefa 4 — Ladder DC/DC (Fig. 146) — **OK**

| Item | Esperado | Encontrado na netlist | Veredito |
|---|---|---|---|
| NET_DCC | {U1.31, L2.2} | código 2: {L2.2, U1.31 `DCC_31` (power_out)} | OK |
| L2 | 10µH | valor 10uH, footprint L_0603 | OK |
| NET_L2_L3 | {L2.1, L3.1} | código 7: exatamente {L2.1, L3.1} | OK |
| L3 | 15nH no ladder | valor 15nH, footprint L_0402 | OK |
| NET_DEC4 | {L3.2, C10.1, U1.30} | código 6: {C10.1, L3.2, U1.30 `DEC4_30`} | OK |
| C10 | 1.0µF → GND | valor 1.0uF; C10.2 ∈ GND; footprint C_0603 | OK |

Ladder como-construído = DCC(31) – L2 10µH – L3 15nH – DEC4(30) + C10 1.0µF→GND: igual ao `designator_map.md` (linha 51/68) e ao claim 17 (DIVERGÊNCIA da versão antiga resolvida — o esquema já incorpora o L3 do ladder).

## Tarefa 5 — Desacoplos — **OK**

| Item | Esperado (designator_map linhas 43–47) | Encontrado | Veredito |
|---|---|---|---|
| C5 | 100nF, DEC1(1)→GND | NET_DEC1 = {C5.1, U1.1}; C5.2 ∈ GND; 100nF 0402 | OK |
| C7 | 100nF **DNP**, DEC2(21)→GND | NET_DEC2 = {C7.1, U1.21}; C7.2 ∈ GND; 100nF 0402; `dnp yes` | OK |
| C6 | 100pF, DEC3(22)→GND | NET_DEC3 = {C6.1, U1.22}; C6.2 ∈ GND; 100pF 0402 | OK |
| C4 | 100nF, VDD(9/25/32)→GND | C4.1 ∈ VDD_BAT, C4.2 ∈ GND | OK |
| C8 | 100nF, VDD(9/25/32)→GND | C8.1 ∈ VDD_BAT, C8.2 ∈ GND | OK |
| C9 | 4.7µF, VDD(9/25/32)→GND | C9.1 ∈ VDD_BAT, C9.2 ∈ GND; 4.7uF 0603 | OK |

VDD_BAT (netlist código 15) contém exatamente {BT1.1, C4.1, C8.1, C9.1, R1.2, TP1.1, U1.9, U1.25, U1.32} — sem nó estranho. C6/C7/C8 com nets e valores corretos conforme a correção de 2026-09-09 (claim 20: DEC3→100pF, DEC2 posição DNP, C8 no VDD).

## Tarefa 6 — Cristal 32 MHz — **OK**

| Item | Esperado | Encontrado | Veredito |
|---|---|---|---|
| X1 | 32MHz, CL=8pF, em XC1(23)/XC2(24) | valor "32MHz CL=8pF"; X1.1 ∈ NET_XC1 (com U1.23), X1.2 ∈ NET_XC2 (com U1.24); footprint Crystal_SMD_2016-2Pin | OK |
| C1/C2 | 12pF NP0 → GND | C1 12pF: C1.1 ∈ NET_XC1, C1.2 ∈ GND; C2 12pF: C2.1 ∈ NET_XC2, C2.2 ∈ GND | OK |
| Matemática CL | CL = (C1·C2)/(C1+C2) + Cstray = 6pF + Cstray | com C1=C2=12pF ⇒ CL=8pF se Cstray=2pF — equivalente à fórmula do claim 19: C = 2·(CL−Cstray) = 2·(8−2) = 12pF (CONFIRMADO no passo 5.1, Tabelas 122/123 PS v1.3) | OK |

## Tarefa 7 — Alimentação, TPs, mecânica — **OK**

| Item | Esperado | Encontrado | Veredito |
|---|---|---|---|
| BT1 | Keystone 1059, + → VDD_BAT | valor Keystone_1059; BT1.1 ∈ VDD_BAT; footprint `nibas_wristband:Keystone_1059_CR2032_SMT` | OK |
| J1 | contato negativo → GND | J1.1 ∈ GND (código 14); label GND via símbolo #PWR0102 (fio `.kicad_sch` 4152) | OK |
| PWR_FLAG em VDD_BAT | presente | #FLG0101 ligado por fio direto ao símbolo de alimentação VDD_BAT #PWR0101 (fio `.kicad_sch` 4148: (76.2,45.72)→(76.2,50.8)) | OK |
| PWR_FLAG em GND | presente | #FLG0102 ligado por fio direto ao símbolo GND #PWR0103 (fio `.kicad_sch` 4156: (76.2,109.22)→(76.2,114.3)) | OK |
| SHLD1 | ferrite → GND | SHLD1.1 ∈ GND; label GND em (63.5,177.8) | OK |
| TAG1 | inlay passivo, pads representados | 2 pads NC (ver Tarefa 2) — coerente com designator_map linha 52 | OK |
| TP1 | VDD_BAT | TP1.1 ∈ VDD_BAT | OK |
| TP2 | SWDIO(18) | TP2.1 ∈ NET_SWDIO = {TP2.1, U1.18} | OK |
| TP3 | SWDCLK(17) | TP3.1 ∈ NET_SWDCLK = {TP3.1, U1.17} | OK |
| TP4 | GND | TP4.1 ∈ GND | OK |
| R1 | 10k, nRESET(16)→VDD_BAT, DNP | R1.1 ∈ NET_RESET = {R1.1, U1.16}; R1.2 ∈ VDD_BAT; `dnp yes` | OK |

Nota: `power_pin_not_driven` permanece **error** no `.kicad_pro` e o ERC passou — os dois PWR_FLAG são eficazes (sem eles, U1.9 e BT1.1 violariam). Prova por coordenadas foi necessária porque power symbols/PWR_FLAG não aparecem na netlist exportada.

## Tarefa 8 — ERC — **OK**

| Item | Esperado | Encontrado | Veredito |
|---|---|---|---|
| Violações | 0 de qualquer severidade | `"violations": []` com `included_severities = [error, warning, exclusion]` (`erc_report.json` 27–37) | OK |
| Re-execução fresh | exit 0, mesmo resultado | `kicad-cli sch erc --exit-code-violations --severity-all` → exit 0, "0 violações", JSON idêntico (diff vazio) | OK |
| Exclusões pontuais | nenhuma sem justificativa | `erc_exclusions: []` no `.kicad_pro` — nada excluído item a item | OK |
| Checks em ignore (5) | justificados | ver tabela abaixo | OK |

Justificativa dos 5 checks em `ignore` no `.kicad_pro` (duplicados em `erc_report.json` 5–26):

| Check | Julgamento |
|---|---|
| `pin_not_driven` | **Justificado e necessário** — XC1/XC2/SWDCLK são entradas sem driver no esquemático (cristal e TP de debug); DEC*/DCC são passivos por design (ref. Nordic). Documentado no próprio esquema (NOTA 7, linhas 4694–4707). `power_pin_not_driven` continua error, cobrindo o risco real. |
| `footprint_link_issues` | **Justificado** — NOTA 7 registra: kicad-cli 10.0.6 não carrega fp-lib-table do projeto; links validados por nome. |
| `footprint_filter` | Aceitável — falso positivo esperado em ANT1 (símbolo `Device:Antenna_Chip` com footprint Johanson fora do filtro do símbolo) e nos símbolos custom `nibas_wristband`. |
| `four_way_junction` | Aceitável — severidade cosmética; sem impacto elétrico. |
| `single_global_label` | Inócuo — o esquemático não tem nenhum global label (varredura). Ignore desnecessário, porém sem risco. |

## Tarefa 9 — Higiene — **OK**

| Item | Critério | Encontrado | Veredito |
|---|---|---|---|
| UUIDs únicos | duplicatas = 0; `grep -c "dddd"` = 0 | 270 ocorrências de uuid, 270 valores distintos; `dddd` = 0 | OK |
| Title block numerado | comments 1..3 preenchidos | comment 1 (variante), 2 (pinagem), 3 (BOM) — `.kicad_sch` 12–14; rev "A", data 2026-09-09, company NibasRockBar | OK |
| Valores linha a linha vs designator_map | 25/25 designators | tabela abaixo | OK |

Cobertura de valores/footprints (25 componentes: U1, ANT1, X1, C1–C10, L1–L3, TAG1, TP1–TP4, BT1, J1, SHLD1, R1) — todos casam com a tabela da Variante B do `designator_map.md` (linhas 36–63), incluindo footprints 0402/0603/2016/QFN-32-1EP e os custom `nibas_wristband:*`. Notas de layout presentes no esquema (NOTA 1–7, linhas 4598–4707: keep-out de antena, ferrite, 2 camadas 0.8mm, justificativas de ERC).

**BOM raiz (`BOM_discreta_corrigida_nRF52810_QFN32.csv`) — uso apenas para valores, conforme despacho:**
- Valores que constam na BOM e no esquema: U1 nRF52810-QCAA; ANT1 2450AT18A100E; X1 32MHz CL=8pF; C1/C2 12pF; C3 0.8pF; L1 3.9nH; L2 10uH; L3 15nH; C4/C5/C8 100nF; C9 4.7uF; C10 1.0uF; BT1 Keystone 1059; TAG1 NTAG213; TP1–TP4 — **todos OK**.
- Divergências BOM↔esquema **esperadas** (a BOM raiz preserva a topologia anterior à correção de 2026-09-09; o ground truth é o `designator_map.md`): BOM diz C7=100pF no caminho RF (esquema: C7=100nF DNP em DEC2, e o 100pF virou C6 em DEC3); BOM diz C8 em DEC2+DEC3 (esquema: C8 em VDD_BAT); BOM diz L3 na rede RF (esquema: L3 no ladder DC/DC). O esquema segue o `designator_map.md` em todos os casos — correto.
- Componentes no esquema **ausentes da BOM raiz**: C6, J1, SHLD1, R1 — todos previstos no `designator_map.md` (C6 nasce da correção Fig. 146; J1/SHLD1/R1 das divergências 4/5/6 do plano). Recomendação (fora do escopo deste passo): regenerar a BOM da variante B para refletir o esquema atual.

## Observações (desvios menores — nenhum elétrico; nenhum entra na contagem de itens reprovados)

Todas com arquivo+linha e correção sugerida, para eventuais wave de correção/limpeza:

1. **Fios e labels duplicados sobrepostos no U1 (higiene visual).** 3 fios idênticos (297.18,119.38)→(297.18,116.84) [`.kicad_sch` 4080, 4120, 4136] com 3 labels "VDD_BAT" empilhados em (297.18,116.84) [4316, 4376, 4400]; e 3 fios idênticos (297.18,170.18)→(297.18,172.72) [4100, 4124, 4140] com 3 labels "GND" em (297.18,172.72) [4346, 4382, 4406]. Eletricamente inócuo (mesma net; netlist confirma U1.25∈VDD_BAT e U1.33∈GND; ERC não sinaliza). Correção: apagar 2 cópias de cada fio e 2 cópias de cada label (pino 25 e pino 33 do U1).
2. **Description desatualizada do C8:** "DEC2+DEC3 unidos (critico)" [`.kicad_sch` 3174; eco na netlist 543–551] — contradiz a conexão real (C8.1 ∈ VDD_BAT) e o `designator_map.md` linha 46. Correção: trocar para "Desacoplo VDD (PS Fig. 146)".
3. **Description do L2 omissa:** "DC/DC DCC->L3->DEC4" [`.kicad_sch` 3602] — omite o próprio L2 do texto. Correção: "DC/DC DCC->L2->L3->DEC4 (PS Fig. 146)".
4. **comment 3 do title block incompleto:** lista "C1-C5 C7-C10" [`.kicad_sch` 14; netlist 27] — omite C6. Correção: "C1-C10".
5. **Citação de tabela no texto do esquema:** NOTA 1 e comment 2 citam "Table 99" [`.kicad_sch` 10, 4604; netlist 23]; o passo 5.1 cita "Tabela 114 (PS v1.3, p. 390–391)" para a mesma tabela de pinos. Os **números de pino** estão corretos (3 fontes); apenas a numeração da tabela citada difere entre documentos. Correção: uniformizar a citação (conferir contra o PDF v1.3 antes de editar).
6. **Gap de anotação #PWR0111** (sequência pula de #PWR0110 para #PWR0112) — resíduo de edição, sem efeito. Correção: re-anotar símbolos de power no KiCad (opcional).

---

## Resumo final (Tarefa 10)

- **10/10 tarefas verificadas item a item: todas OK.** Total de ~60 itens de verificação nas tabelas acima, nenhum reprovado.
- Topologia RF de 2 elementos e ladder DC/DC com L3 **confirmados na netlist como-construída** — a correção de 2026-09-09 (PS v1.3 Fig. 146/Tabela 123) está efetivamente aplicada no esquema, na netlist e nas notas do próprio arquivo.
- Pinagem QFN32 33/33 pinos correta (embed + netlist + designator_map); §1.1 alucinado do facts file e a `netlist_conexoes.md` da raiz não foram usados como referência, conforme despacho.
- ERC: 0 violações de qualquer severidade, re-execução fresh confirma; 5 ignores justificados (2 deles documentados no próprio esquema), zero exclusões pontuais.
- 6 observações de higiene listadas (nenhuma elétrica; todas com localização e correção sugerida).
- Palavra-chave de status negativo do plano (F-A-L-H-A, sem hífens): **0 ocorrências neste arquivo** — conferido com `grep -c` antes do fechamento (requisito do passo 5.2).

**Veredito do passo 5.2:** variante B aprovada no cross-check; observações 1–6 encaminhadas ao Bob como candidatos a limpeza opcional (não bloqueiam 6.1/6.2).
