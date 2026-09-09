# Mapa Canônico de Designators e Pinos — Smart Badge Pub

**Versão:** 1.0 (resolução das 9 divergências do plano .bob/plans/kicad-esquematicos-verificacao.md passo 1.1)  
**Fontes:** `netlist_conexoes.md`, `BOM_smartbadge_v2.csv` (variante A), `BOM_discreta_corrigida_nRF52810_QFN32.csv` (variante B), `RELATORIO_REVISAO_TECNICA.md` §2.1–2.2

---

## Variante A — Módulo BLE Certificado (rota recomendada)

| Designator | Valor | Footprint | Pin (módulo) | Rede (net) | Justificativa (1 linha) |
|---|---|---|---|---|---|
| U1 | BLE Module (nRF52810/832-based) | Module footprint per vendor datasheet | — | — | Placeholder para módulo certificado ANATEL (Fanstel/Raytac/u-blox); passo 2.1 define PN final |
| TAG1 | NTAG213 Inlay | Adesivo ~25mm diâmetro | — | — | Inlay pronto (chip+antena), não die nu; posicionado na borda do disco Ø32mm longe da bateria |
| SHLD1 | Ferrite Shielding Sheet | Disco ~20-22mm | — | GND | Blindagem de ferrite entre bateria e bobina NFC (item novo, ausente no doc original) |
| BT1 | Coin Cell Holder CR2032 | Keystone 1059 (SMT) | + | VDD_BAT | Suporte metálico polo positivo; polo negativo via J1 |
| J1 | Battery clip contact (verso) | SMT pad ENIG | – | GND | Contato negativo da bateria; Keystone 1059 só tem polo +, J1 obrigatório nas duas variantes |
| C1 | 10µF X5R 6.3V | 0603 | — | VDD_BAT | Desacoplo principal VDD (bulk) próximo ao módulo |
| C2 | 100nF X7R 16V | 0402 | — | VDD_BAT | Filtro alta frequência VDD próximo ao módulo |
| TP1 | Test Pad VDD | 1.0mm pad ENIG | — | VDD_BAT | Ponto de gravação/debug SWD |
| TP2 | Test Pad SWDIO | 1.0mm pad ENIG | SWDIO módulo | NET_SWDIO | Ponto de gravação SWD |
| TP3 | Test Pad SWDCLK | 1.0mm pad ENIG | SWDCLK módulo | NET_SWDCLK | Ponto de gravação SWD |
| TP4 | Test Pad GND | 1.0mm pad ENIG | — | GND | Ponto de referência GND para debug |

**Notas Variante A:**  
- Módulo BLE certificado elimina circuito discreto de RF (L1/L2/L3/C3/C7/X1/C1_xtal/C2_xtal/C5/C8/C10/ANT1) e ajuste de VNA.  
- Pinagem do módulo segue datasheet do vendor escolhido; mapear VDD/GND/SWDIO/SWDCLK/RESET/ANT conforme pinout do módulo.  
- R1 (pull-up nRESET 10k) **não incluído** — módulos costumam ter pull-up interno; se necessário, adicionar como DNP (ver variante B).  
- GPIOs não usados do módulo: deixar NC conforme pinout do vendor.

---

## Variante B — Rota Discreta nRF52810-QCAA QFN32

| Designator | Valor | Footprint | Pin nRF52810 | Rede (net) | Justificativa (1 linha) |
|---|---|---|---|---|---|
| U1 | nRF52810-QCAA | QFN32 5x5mm | — | — | Part number correto confirmado no datasheet Nordic (QFN32 5x5, variante QCAA) |
| ANT1 | Johanson 2450AT18A100E | SMD1206 | — | NET_RF (feed) + GND | Antena chip 2.4GHz; requer ajuste de rede com VNA na placa física |
| X1 | 32MHz ±10ppm CL=8pF | XTAL SMD2016 | 23 (XC1), 24 (XC2) | NET_XC1, NET_XC2 | Cristal principal; pinos corrigidos (doc original citava 2/3 errado) |
| C1 | 12pF NP0 ±2% | 0402 | 23 → GND | NET_XC1 | Capacitor de carga do cristal X1 (pino XC1) |
| C2 | 12pF NP0 ±2% | 0402 | 24 → GND | NET_XC2 | Capacitor de carga do cristal X1 (pino XC2) |
| C3 | 0.8pF NP0 ±5% | 0402 | — | NET_ANT (19) → GND | Shunt no nó ANT conforme nRF52810 PS Fig. 146 (ANT→C3 shunt→L1 série→antena, 2 elementos); AJUSTAR EM BANCADA com VNA |
| C4 | 100nF X7R ±10% | 0402 | 9, 25, 32 → GND | VDD_BAT | Desacoplo VDD (pinos 9/25/32); ausente na netlist original, adicionado aqui |
| C5 | 100nF X7R ±10% | 0402 | 1 (DEC1) → GND | NET_DEC1 | Desacoplo DEC1 (regulador 0.9V digital) |
| C6 | 100pF NP0 ±5% | 0402 | 22 (DEC3) → GND | NET_DEC3 | Desacoplo DEC3 conforme Fig. 146/Tabela 123 (era o antigo C7 na rede RF — RF reduzida a 2 elementos em 2026-09-09) |
| C7 | 100nF X7R ±10% | 0402 (DNP) | 21 (DEC2) → GND | NET_DEC2 | Posição DEC2 NÃO MONTADA na referência Nordic (C6 N.C., Tabela 123) — mantida como DNP para eventuais ajustes |
| C8 | 100nF X7R ±10% | 0402 | 9, 25, 32 → GND | VDD_BAT | Desacoplo VDD conforme Fig. 146 (antes amarrado a DEC2+DEC3 — tie não documentado no PS; corrigido em 2026-09-09, ver verificacao_matematica.md claim 20) |
| C9 | 4.7µF X5R ±10% | 0603 | 9, 25, 32 → GND | VDD_BAT | Desacoplo bulk VDD próximo do IC; corrigido de 10µF (fora da ref Nordic) para 4.7µF |
| C10 | 1.0µF X7R ±10% | 0603 | 30 (DEC4) → GND | NET_DEC4 | Estabilização saída DC/DC; também alimenta L2 (footprint 0603 conforme Tabela 123) |
| L1 | 3.9nH ±5% | 0402 | 19 (ANT) → NET_RF | NET_ANT–NET_RF | Série entre ANT(19) e ANT1 conforme Fig. 146 (casamento de 2 elementos); valor OK confirmado com ref Nordic |
| L2 | 10µH Isat>50mA ±20% | 0603 | 31 (DCC) – NET_L2_L3 | NET_DCC – NET_L2_L3 | Indutor do DC/DC; valor OK confirmado com ref Nordic |
| L3 | 15nH ±10% | 0402 | NET_L2_L3 – 30 (DEC4) | NET_L2_L3 – NET_DEC4 | Série no ladder DC/DC (DCC→L2→L3→DEC4) conforme Fig. 146; saiu da rede RF na correção de 2026-09-09 |
| TAG1 | NTAG213 Inlay adesivo ~25mm | Adesivo | — | — | Tag NFC passiva; usar inlay pronto, não die nu; manter longe da bateria/blindado por SHLD1 |
| TP1 | Test Pad VDD | 1.0mm pad ENIG | — | VDD_BAT | Ponto de gravação SWD (corrigido: doc original citava pinos 24/25 invertidos) |
| TP2 | Test Pad SWDIO | 1.0mm pad ENIG | 18 (SWDIO) | NET_SWDIO | Ponto de gravação SWD |
| TP3 | Test Pad SWDCLK | 1.0mm pad ENIG | 17 (SWDCLK) | NET_SWDCLK | Ponto de gravação SWD |
| TP4 | Test Pad GND | 1.0mm pad ENIG | — | GND | Ponto de referência GND para debug |
| BT1 | Suporte CR2032 | Keystone 1059 | + | VDD_BAT | Retentor bateria; adicionar folha de ferrite SHLD1 entre bateria e TAG1 |
| J1 | Battery clip contact (verso) | SMT pad ENIG | – | GND | Contato negativo da bateria; Keystone 1059 só tem polo +, J1 obrigatório nas duas variantes |
| SHLD1 | Ferrite Shielding Sheet | Disco ~20-22mm | — | GND | Blindagem de ferrite entre bateria e bobina NFC; conectada a GND (item novo) |
| R1 | 10kΩ (DNP/optional) | 0402 | 16 (nRESET/P0.21) → VDD_BAT | NET_RESET | Pull-up nRESET recomendado DNP: nRF52810 tem pull-up interno; popular só se ruído externo exigir |
| — | NC (No Connect) | — | 2, 3, 4, 5, 6, 7, 8 | — | 16 GPIOs não usados: pinos 2–8, 10–15, 26–28 deixados NC explicitamente |
| — | NC (No Connect) | — | 10, 11, 12, 13, 14, 15 | — | 16 GPIOs não usados: pinos 2–8, 10–15, 26–28 deixados NC explicitamente |
| — | NC (No Connect) | — | 26, 27, 28 | — | 16 GPIOs não usados: pinos 2–8, 10–15, 26–28 deixados NC explicitamente |

**Notas Variante B:**  
- Pinagem verificada no datasheet Nordic (nRF52810 Product Specification, QFN32 QCAA): DEC1=1, VDD=9/25/32, nRESET/P0.21=16, SWDCLK=17, SWDIO=18, ANT=19, VSS=20/29+die pad, DEC2=21, DEC3=22, XC1=23, XC2=24, DEC4=30, DCC=31.  
- Casamento RF conforme nRF52810 PS Fig. 146/Tabela 123 (corrigido vs netlist_conexoes.md em 2026-09-09; ver docs/verificacao_matematica.md claims 18/20): ANT(19)–nó NET_ANT–C3(0.8pF)→GND–L1(3.9nH) série–ANT1. Footprint 0402 em C3 para iteração VNA.  
- Desacoplos conforme Fig. 146: DEC1→C5 100nF; DEC3→C6 100pF; DEC2→C7 100nF DNP (posição N.C. da referência); VDD(9/25/32)→C4 100nF + C8 100nF + C9 4.7µF; ladder DCC(31)–L2 10µH–L3 15nH–DEC4(30) + C10 1.0µF→GND.  
- Keep-out de cobre sob ANT1 e rede de casamento; plano de terra na camada inferior; die pad (VSS) com múltiplas vias para GND.  
- L1/L2/L3 canônicos: L1=3.9nH (RF série), L2=10µH (DC/DC), L3=15nH (DC/DC série com L2, Fig. 146) — RELATORIO §2.2 linha ~44 cita ordem diferente; topologia corrigida contra Fig. 146 em 2026-09-09.  
- R1 DNP justificativa: nRF52810 tem pull-up interno no nRESET (~13kΩ típico); resistor externo só necessário em ambientes com ruído forte no reset ou para debug hardware forçado.

---

## Resolução das 9 Divergências (Resumo)

| # | Divergência | Resolução |
|---|---|---|
| 1 | Colisão C1/C2 entre variantes | **Mantidos separados por função**: Variante A (C1=10µF bulk, C2=100nF HF VDD); Variante B (C1/C2=12pF cristal, C4=100nF VDD, C9=4.7µF bulk). Sem colisão — funções distintas. |
| 2 | C4/C9 na BOM discreta mas não na netlist | **Adicionados à net VDD_BAT** na Variante B: C4 (100nF pinos 9/25/32→GND) e C9 (4.7µF bulk próximo IC→GND). |
| 3 | Part number nRF52810 | **nRF52810-QCAA (QFN32 5x5)** confirmado no datasheet Nordic e BOM_discreta. |
| 4 | J1 contato negativo bateria | **Incluído nas DUAS variantes** (Keystone 1059 só tem polo +; J1 = polo – em SMT pad ENIG no verso). |
| 5 | SHLD1 (ferrite, GND) | **Incluído nas DUAS variantes** (disco ~20-22mm, conectado a GND, entre bateria e TAG1). |
| 6 | R1 10k pull-up nRESET (pino 16) | **DNP/optional na Variante B** com footprint 0402; justificativa: pull-up interno do nRF52810 suficiente, externo só se ruído exigir. Variante A: módulo define. |
| 7 | 16 GPIOs não usados | **Lista explícita NC**: pinos 2–8, 10–15, 26–28 (total 16 pinos) marcados No Connect na Variante B. |
| 8 | L1/L2/L3 canônicos | **Confirmados**: L1=3.9nH RF, L2=10µH DC/DC, L3=15nH RF. RELATORIO §2.2 linha ~44 diverge na ordem mas valores batem com ref Nordic. |
| 9 | U1 Variante A placeholder | **Mantido como placeholder** "BLE Module (nRF52810/832-based), Module footprint per vendor datasheet" — passo 2.1 (pesquisa_modulo_ble.md) fecha PN final em paralelo. |

---

## Checklist de Cobertura

- [x] Todos os designators do `BOM_smartbadge_v2.csv` (Variante A) mapeados
- [x] Todos os designators do `BOM_discreta_corrigida_nRF52810_QFN32.csv` (Variante B) mapeados
- [x] Todas as redes do `netlist_conexoes.md` refletidas na Variante B
- [x] Zero valor sem fonte nos documentos de entrada
- [x] Nenhuma colisão de designator entre variantes (funções distintas por variante)
- [x] 9 divergências resolvidas com justificativa de 1 linha cada