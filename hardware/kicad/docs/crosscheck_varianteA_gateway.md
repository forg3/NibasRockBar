# Cross-check Variante A (módulo E73) + Gateway ESP32 — passo 5.3

**Data:** 2026-09-09 · **Verificador:** build (sessão fresh, ≠ autores de 4.2/4.3) · **Plano:** `.bob/plans/kicad-esquematicos-verificacao.md` [5.3]

**Entradas lidas (read-only):** `wristband_modulo.kicad_sch` + `exports/wristband_modulo.net` + `exports/erc_report.json` · `gateway_esp32.kicad_sch` + `exports/gateway_esp32.net` + `exports/erc_report.json` · `BOM_smartbadge_v2.csv` · `docs/pesquisa_modulo_ble.md` · `docs/pesquisa_gateway_esp32.md` · `docs/gateway_lib_status.md` · `docs/designator_map.md` · `docs/verificacao_matematica.md` (E2–E4) · `firmware/main.c` · `gateway_esp32/gateway_esp32.ino`.

**Fontes primárias RE-VERIFICADAS hoje (não herdadas de 2.1/2.2):**

| Fonte | URL | Uso |
|---|---|---|
| Página oficial Ebyte E73-2G4M04S1A — Pin Definition | https://www.cdebyte.com/products/E73-2G4M04S1A/2 | pinout pads 0–43 (acessada 2026-09-09) |
| **E73-2G4M04S1A User Manual rev 1.8 (2025-01-13)** — PDF oficial | https://www.cdebyte.com/pdf-down.aspx?id=3536 | pin definition + seção 4.1 "Hardware Design" |
| FAQ oficial do fabricante (loja Ebyte) — DC/DC | https://ebyteiot.com/products/ebyte-e73-2g4m04s1b-nrf52832-wireless-module-ble-4-2-iot-ble5-0-bluetooth-module-2-4ghz-wireless-transceiver-modules-soc | suporte a DC/DC no módulo (ver §3) |
| ESP32-DevKitC V4 User Guide — fonte RST oficial | https://github.com/espressif/esp-dev-kits → `docs/en/esp32-devkitc/user_guide.rst` (renderiza em docs.espressif.com) | tabelas J2/J3 + nota [2] dos pinos de flash |
| Adafruit Feather nRF52832 (MDBT42Q) — esquemático público | https://github.com/adafruit/Adafruit-nRF52-Bluefruit-Feather-PCB (`Adafruit nRF52 Bluefruit Feather.sch`) | contraprova: indutor DC/DC externo em módulo concorrente |

---

## 1. CROSS-CHECK VARIANTE A — `wristband_modulo`

### 1a. Netlist ↔ `BOM_smartbadge_v2.csv` — **OK**

BOM tem 11 itens; netlist tem 11 componentes — correspondência 1:1, bidirecional, sem órfão dos dois lados.

| Item BOM | Valor/footprint BOM | No netlist? | Valor/footprint no netlist | Veredito |
|---|---|---|---|---|
| U1 | BLE Module nRF52810/832, footprint per vendor, PN "a definir" | sim | `E73-2G4M04S-52810`, `RF_Module:E73-2G4M04S` | OK — PN resolvido pelo passo 2.1 (nRF52810, S112 direto); campo PN do BOM ficou stale ("a definir") — nota no §4 |
| TAG1 | NTAG213 Inlay, adesivo ~25 mm | sim | `NTAG213_Inlay`, `nibas_wristband:NTAG213_Inlay_25mm` | OK |
| SHLD1 | Ferrite Shielding Sheet, disco ~20–22 mm | sim | `Ferrite_Shield`, `nibas_wristband:SHLD1_Ferrite_Shield_22mm` | OK |
| BT1 | Coin Cell Holder CR2032, Keystone 1059 | sim | `Keystone_1059`, `nibas_wristband:Keystone_1059_CR2032_SMT` | OK |
| C1 | 10 µF, 0603 | sim | `10uF`, `Capacitor_SMD:C_0603_1608Metric` | OK |
| C2 | 100 nF, 0402 | sim | `100nF`, `Capacitor_SMD:C_0402_1005Metric` | OK |
| TP1 | Test Pad VDD, 1.0 mm | sim | `TestPad_VDD`, `TestPoint:TestPoint_Pad_D1.0mm` | OK |
| TP2 | Test Pad SWDIO, 1.0 mm | sim | `TestPad_SWDIO`, idem | OK |
| TP3 | Test Pad SWDCLK, 1.0 mm | sim | `TestPad_SWDCLK`, idem | OK |
| TP4 | Test Pad GND, 1.0 mm | sim | `TestPad_GND`, idem | OK |
| J1 | Battery clip contact (verso), SMT pad | sim | `Battery_Negative_Contact`, `nibas_wristband:J1_Battery_Negative_Contact` | OK |

Componentes no netlist que não estão no BOM: **nenhum** (11 = 11).

### 1b. Netlist ↔ pinout oficial E73-2G4M04S1A — **OK**

Pinout re-verificado hoje na página oficial (cdebyte.com/products/E73-2G4M04S1A/2) e no User Manual rev 1.8 (pdf-down id=3536): pad 33=P0.18, 36=P0.21/RST, 37=SWDCLK, 38=SWDIO, 40=P0.23, 41=P0.24, VCC=16 (1.8–3.6 V), GND=0/1/2/15/42/43. **A correção de 2026-09-09 da tabela §5 de `pesquisa_modulo_ble.md` está correta** — e agora também confirmada pelo manual rev 1.8 (cuja revisão "1.8 · 2025/01/13 · Modify the pin sequence number description" é exatamente essa correção de sequência).

| Rede (netlist) | Nós no netlist | Pad oficial Ebyte | Veredito |
|---|---|---|---|
| `/VDD_BAT` (code 3) | BT1.1 + C1.1 + C2.1 + TP1.1 + **U1.16 (VCC)** | 16 = VCC, "Power supply 1.8~3.6 V DC" | OK |
| `/NET_SWDCLK` (code 1) | TP3.1 + **U1.37** | 37 = SWDCLK (Input) | OK |
| `/NET_SWDIO` (code 2) | TP2.1 + **U1.38** | 38 = SWDIO | OK |
| `GND` (code 4) | C1.2 + C2.2 + J1.1 + SHLD1.1 + TP4.1 + **U1.0/1/2/15/42/43** | 0,1,2,15,42,43 = GND | OK — todos os 6 pads de terra conectados |
| nRESET | U1.36 = **NC explícito** | 36 = P0.21 (Input/Output/RST) | OK c/ nota — decisão registrada (`designator_map.md` linha 27: R1 não incluído na variante A; função RESET tem pull-up interno no nRF52 via UICR PSELRESET; NC inofensivo também com chip virgem) |
| DEC1(14)/DEC2(3)/DEC3(4)/DEC4(12)/DCC(13) | **NC explícito** | pads expostos | ver seção 3 (veredito DC/DC) |
| GPIOs P0.02–P0.31 (pads 5–11, 17–35, 39–41) | NC explícito (35 pins com flag `no_connect`) | GPIO livres | OK — firmware não usa GPIO; contagem confere: 44 pads − 9 conectados (6 GND + VCC + SWDCLK + SWDIO) = 35 NC |
| Antena | nenhuma rede externa | PCB trace integrada + keep-out no footprint | OK — coerente com NOTA 4 do esquemático |

TAG1 (ANT1/ANT2) NC: OK — inlay NFC é adesivo autônomo (chip+antena internos); pads são representação para BOM/posição (mesma conclusão do 5.1, Extra E3).

### 1c. ERC `wristband_modulo` — **OK (0 violações)**

`exports/erc_report.json`: `"violations": []` com severidades error+warning+exclusion incluídas. KiCad 10.0.6, data 2026-09-09T09:06:45 (mesma timestamp da netlist — relatório não está stale).

Checks ignorados no nível global (5) — justificativa um a um:

| Check ignorado | Justificativa | Aceito? |
|---|---|---|
| `pin_not_driven` | Necessário: U1.37 (SWDCLK, tipo input) é dirigido por TP3 (passive), que o ERC não conta como driver → falso-positivo garantido. `/VDD_BAT` também não tem símbolo de power (só passives + power_in) — ver observação O3. | Sim |
| `single_global_label` | Esquema não usa global labels (nets por labels locais) — preventivo. | Sim |
| `four_way_junction` | Estilo de desenho (junções de 4 fios) — preventivo. | Sim |
| `footprint_link_issues` | Preventivo; todos os 11 componentes têm footprint atribuído no netlist. | Sim |
| `footprint_filter` | Preventivo; conferência manual: todos os footprints casam com os filtros dos símbolos (ex.: `TestPoint_Pad_D1.0mm` ↔ `Pin* Test*`; `E73-2G4M04S` ↔ `E73*2G4M04S*`). | Sim |

### 1d. Decoupling VDD_BAT (C1 10 µF + C2 100 nF) — **OK**

Netlist: C1.1 e C2.1 em `/VDD_BAT`; C1.2 e C2.2 em `GND`. Valores/footprints batem com o BOM (C1=10 µF 0603, C2=100 nF 0402). Atende também a exigência do FAQ Ebyte de "decoupling capacitance suficiente" para os transientes do DC/DC (ver §3).

---

## 2. CROSS-CHECK GATEWAY — `gateway_esp32`

### 2a. Netlist ↔ pinout oficial ESP32-DevKitC V4 — **OK (38/38 pinos)**

Conferência pino-a-pino do símbolo `nibas_gateway:ESP32-DevKitC-32E` (via libpart do netlist) contra as tabelas J2/J3 do User Guide oficial (RST fonte `docs/en/esp32-devkitc/user_guide.rst` do repo `espressif/esp-dev-kits`). **Os 38 pinos batem 1:1 em nome e posição**, incluindo os mandatórios desta tarefa:

| Pino | User Guide oficial | Netlist/símbolo | Conexão no esquema | Veredito |
|---|---|---|---|---|
| J2-19 | 5V (P) | `5V_J2-19` (power_in) | `+5V` ← J1.1 (entrada 5 V) | OK |
| J2-1 | 3V3 (P) | `3V3_J2-1` (power_out) | `+3V3` → R1.1 | OK |
| J2-2 | EN (I, CHIP_PU/Reset) | `EN_J2-2` (input) | `/EN` (R1.2 + SW1.1) | OK |
| J2-14 | GND (G) | `GND_J2-14` | `GND` | OK |
| J3-1 | GND (G) | `GND_J3-1` | `GND` | OK |
| J3-7 | GND (G) | `GND_J3-7` | `GND` | OK |

Demais 32 pinos (VP, VN, IO34/35/32/33/25/26/27/14/12/13, IO23/22/TX/RX/21/19/18/5/17/16/4/0/2/15): todos NC explícito — coerente com firmware sem GPIO (`gateway_esp32.ino` não toca nenhum pino; só BLE scan + WiFi/MQTT). Strapping (IO0/IO2/IO12/IO15) resolvido no próprio DevKitC — nota de texto no esquemático documenta isso.

### 2b. Circuito de EN — **OK**

Netlist `/EN` (code 3): R1.2 + SW1.1 + U1.J2-2; R1.1 em `+3V3` (J2-1); SW1.2 em `GND`. R1 = 10 kΩ 0603. Ou seja: **pull-up 10 k→3V3 + botão NA→GND, ambos presentes**. Notas: (i) o DevKitC já tem RC 10k/1µF + botão EN onboard — R1 externo fica em paralelo com o pull-up onboard (5 k efetivo, inofensivo) e SW1 replica o botão EN do DevKit, que fica inacessível quando o DevKit está em soquete — justificativa explícita na descrição do símbolo SW1; (ii) sem capacitor externo no EN da carrier — correto, o RC já existe no DevKit (adicionar outro C em paralelo alteraria o RC de reset).

### 2c. Pinos de flash D0–D3/CMD/CLK — **OK (todos NC)**

User Guide oficial, nota [2]: *"The pins D0, D1, D2, D3, CMD and CLK are used internally for communication between ESP32 and SPI flash memory... Avoid using these pins."*

| Pino | GPIO | No netlist |
|---|---|---|
| J3-18 (D0) | GPIO7 | `unconnected-(U1-D0-PadJ3-18)` ✓ |
| J3-17 (D1) | GPIO8 | `unconnected-(U1-D1-PadJ3-17)` ✓ |
| J2-16 (D2) | GPIO9 | `unconnected-(U1-D2-PadJ2-16)` ✓ |
| J2-17 (D3) | GPIO10 | `unconnected-(U1-D3-PadJ2-17)` ✓ |
| J2-18 (CMD) | GPIO11 | `unconnected-(U1-CMD-PadJ2-18)` ✓ |
| J3-19 (CLK) | GPIO6 | `unconnected-(U1-CLK-PadJ3-19)` ✓ |

Nenhuma conexão nos 6 pinos; nota de texto no esquemático (`gateway_esp32.kicad_sch`, linha ~616) documenta a regra.

### 2d. ERC `gateway_esp32` — **OK (0 violações)**

`exports/erc_report.json`: `"violations": []` (error+warning+exclusion incluídos), mesma timestamp da netlist. Ignores globais (4): `single_global_label` (sem global labels — preventivo), `four_way_junction` (estilo), `simulation_model_issue` (símbolos custom sem modelo SPICE; projeto não simula), `footprint_filter` (símbolos custom `nibas_gateway` sem filtros definidos) — todos justificados.

---

## 3. CHECK DC/DC NO MÓDULO E73 × FIRMWARE — **OK (condicional, com fonte)**

**Firmware:** `firmware/main.c:52` — `sd_power_dcdc_mode_set(NRF_POWER_DCDC_ENABLE);` (SoftDevice S112, chamada em runtime no boot; comentário da linha 51 remete a L2/C10 que só existem na variante B). Não há `sdk_config.h` no repo (o `main.c` é esqueleto de referência) — a chamada runtime é a evidência definitiva de que o firmware liga DC/DC.

**O módulo expõe pads DCC (13) e DEC4 (12)?** Sim — mas isso não implica componente externo: o datasheet E73 afirma "All IO ports are led out" (o módulo expõe TODOS os pinos do chip nRF52810, incluindo DEC1–4/DCC, como pontos de acesso/prova).

**Evidência coletada hoje:**

| # | Evidência | Fonte |
|---|---|---|
| E-1 | FAQ oficial do fabricante: *"Q: Can the E73-2G4M04S1B operate using the internal DC-DC converter of the nRF52832? A: **Yes, the module hardware supports the nRF52832's internal DC-DC regulator mode.** When enabled via software, this significantly improves power efficiency... To ensure stability, the supply voltage must remain within the 1.8V to 3.6V range with sufficient decoupling capacitance..."* — sem MENÇÃO a indutor/capacitor externo em DCC/DEC4 | https://ebyteiot.com/products/ebyte-e73-2g4m04s1b-nrf52832-wireless-module-ble-4-2-iot-ble5-0-bluetooth-module-2-4ghz-wireless-transceiver-modules-soc (JSON-LD da página, verbatim) |
| E-2 | **User Manual oficial do E73-2G4M04S1A rev 1.8 (2025-01-13)**, seção 4.1 "Hardware Design": instruções apenas de qualidade de alimentação, GND, layout e antena — **nenhum componente externo exigido** (nem caps DEC, nem indutor); o manual não tem circuito de aplicação típica e remete ao PS Nordic para detalhes do chip | https://www.cdebyte.com/pdf-down.aspx?id=3536 |
| E-3 | Placa de teste oficial Ebyte (E73-TBA/TBB, manual id=2520): alimentação = USB 5 V → fusível → LDO ME6211 → 3,3 V direto no módulo; sem indutor/caps DEC descritos no circuito de potência | https://www.cdebyte.com/products/E73-TBB/4 → pdf-down id=2520 |
| E-4 | **Contraprova (módulo concorrente):** a Adafruit Feather nRF52832 (Raytac MDBT42Q) usa **L2 = 10 µH 0805 EXTERNO entre DCC e DEC4** + C4 em DEC4 (nets N$3/N$8 do esquemático público); o símbolo MDBT42Q nem expõe DEC1/2/3 (internos). Prova que "módulo nRF52" NÃO implica indutor interno em geral — e que a pergunta desta seção era legítima | https://github.com/adafruit/Adafruit-nRF52-Bluefruit-Feather-PCB |
| E-5 | Designs open-source com família E73 (nrfmicro c/ E73-2G4M08S1C; b-parasite c/ E73-2G4M08S1C): **nenhum indutor no projeto**, pino DCCH/DCC pendente — coerentes com operação em modo LDO (core Arduino nRF52 não liga DCDCEN por default) | github.com/joric/nrfmicro (`hardware/nrfmicro.kicad_sch`), github.com/rbaron/b-parasite |

**Veredito: OK (condicional).** O fabricante afirma explicitamente (E-1) que o hardware do módulo suporta o modo DC/DC interno ativado por software — eletricamente impossível sem o indutor DCC↔DEC4 a bordo do módulo — e o manual oficial da variante 1A (E-2) não exige componente externo algum. O as-built da variante A (DEC/DCC NC + C1/C2 em VDD_BAT + `DCDCEN=1` no firmware) é, portanto, **suportado pela documentação do fabricante**. O esquemático está correto e a NOTA 2 (`wristband_modulo.kicad_sch:2651–2657`) tem base em fonte.

**Ressalva (condição do OK):** a frase explícita E-1 está na página do **E73-2G4M04S1B (nRF52832)**; para o **1A (nRF52810)** a confirmação é por família (mesmo PCB 17,5×28,7 mm, mesmo pinout de 44 pads, mesmo manual-irmão). A página do 1A não tem FAQ equivalente. **Ação:** confirmar em 1 linha com o suporte Ebyte (service@cdebyte.com) que o E73-2G4M04S1A tem o indutor DC/DC interno — pendência já registrada em `pesquisa_modulo_ble.md` §4 (Itens Abertos #2). Este veredito **fecha o Extra E2 do `verificacao_matematica.md`** (que estava "não verificado online").

**Plano B se o suporte Ebyte disser que NÃO há indutor interno** (não aplicar agora; decisão do Bob):
1. Preferível: adicionar na carrier da variante A `L 10 µH` entre pads 12–13 + `C 1,0 µF` de DEC4→GND (pads existem no footprint `RF_Module:E73-2G4M04S`) — replicando a topologia da variante B; ou
2. Alternativa: remover a chamada em `firmware/main.c:52` (fica em modo LDO) — custo: I_a sobe de ~5,8 mA p/ ~10,5 mA (PS Nordic, cenário TX 0 dBm) e a autonomia cai de ~1,66 a p/ ~0,96 a (matemática do 5.1, afirmação 1/Extra E2) — **perde a meta de 12 meses**; usar só se a opção 1 for inviável.

---

## 4. RESUMO FINAL

### Contagem por seção

| Seção | Itens | OK | FALHA |
|---|---|---|---|
| 1. Variante A | 1a, 1b, 1c, 1d | 4 | 0 |
| 2. Gateway | 2a, 2b, 2c, 2d | 4 | 0 |
| 3. DC/DC E73 | 1 veredito | 1 (condicional) | 0 |
| **Total** | **9** | **9** | **0** |

### Desvios encaminhados ao Bob (decisão de correção)

**F1 — FALHA de documentação (não de circuito): `hardware/kicad/docs/pesquisa_modulo_ble.md` linhas 321–332 e 366–367.** A coluna "Conexão no Esquemático (Variante A)" da tabela §5 e as notas de conexão mandam conectar `C_DEC1..C_DEC4` (100 nF cada) e `L_DCC` (10 µH entre pads 12–13) — o esquemático as-built deixa esses pads NC (corretamente, ver §3), o BOM não lista esses componentes, e o manual oficial rev 1.8 + FAQ Ebyte não exigem nada externo. A tabela §5 foi corrigida em 2026-09-09 para os pads 33/36–41, mas as linhas DEC/DCC ficaram stale (refletem a referência Nordic do chip nu, não o módulo). **Correção sugerida:** atualizar as 5 linhas (pads 3, 4, 12, 13, 14) e as 2 notas de conexão para "NC — desacoplo e DC/DC internos ao módulo (manual E73-2G4M04S1A rev 1.8 §4.1; FAQ Ebyte; confirmar 1A c/ suporte — ver crosscheck_varianteA_gateway.md §3)".

### Observações (não-FALHA; registro para decisão/next steps)

- **O1 (gateway):** U1, J1 e SW1 estão **sem footprint** atribuído (`gateway_esp32.net`, campos Footprint vazios). `gateway_lib_status.md` manda usar `Espressif:ESP32-DevKitC` (lib oficial) para o footprint. Inofensivo no escopo atual (só esquemático, sem layout — premissa do plano), mas é pré-requisito da fase de layout; os soquetes fêmea 2×19 também não aparecem como componentes (estão implícitos no footprint do U1).
- **O2 (gateway):** `pesquisa_gateway_esp32.md` §6 (BOM do caminho escolhido) inclui LED de status + R 1k + caps 0,1 µF/10 µF nos headers; o esquemático tem apenas J1/R1/SW1/U1. Impacto baixo (DevKit já tem LDO+caps onboard), mas é divergência doc↔esquemático — adicionar ao esquema ou atualizar a doc.
- **O3 (variante A):** `/VDD_BAT` não tem símbolo de power (driver `power_out`) — o ERC só passa porque `pin_not_driven` foi ignorado globalmente. Cosmético; se os ignores forem revistos, adicionar power symbol (ex.: `+BATT`) na rede.
- **O4 (BOM):** `BOM_smartbadge_v2.csv` linha 2 ainda tem PN "A definir (Fanstel/Raytac/u-blox)" — o passo 2.1 fechou o E73-2G4M04S1A; atualizar o campo PN (e o preço: E73 ~US$ 3,59 vs US$ 6,50 orçados — folga registrada no 5.1, afirmação 25).
- **O5 (firmware, fora do escopo hardware):** `main.c` usa `ram_start` (linha 48) e `m_adv_handle` (linhas 97/128) sem declaração no arquivo — coerente com o cabeçalho ("não é compilável standalone"), sem ação nesta onda.

### Verificação de contagem

`grep -c "FALHA" hardware/kicad/docs/crosscheck_varianteA_gateway.md` → **4** (linhas 150, 159, 161 e 171: cabeçalho da coluna da tabela, corpo do item F1, título "não-FALHA" das observações, e esta linha auto-referente). As 9 verificações mandatórias têm **0 FALHA** — o único desvio (F1) é de documentação de apoio, encaminhado para wave de correção.
