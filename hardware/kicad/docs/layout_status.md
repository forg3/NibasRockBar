# Status dos layouts PCB — KiCad 10.0.6

**Data:** 2026-09-09 · **Fontes:** `exports/audit.md` das 3 placas, JSONs de DRC commitados (`drc_*.json`, `drc_tracks_*.json`), geradores (`gen_board_v2.py`, `gen_board_modulo.py`, `gen_board_gateway.py`), `docs/layout_approach.md`.

---

## 1. Decisão de abordagem

**Script Python via API `pcbnew` (primário), com `tools/board_builder.py` como módulo compartilhado.** O fallback textual (`.kicad_pcb` escrito à mão) também foi provado no spike (`_spike/minimal_textual_filled.kicad_pcb`, DRC 0 violações), mas o caminho primário elimina o risco de rejeição do parser e garante integridade geométrica (coords em nm pela API). Regra do ambiente: **nunca** invocar o binário `kicad` (GUI) para gerar — só `kicad-cli` e `python3 + pcbnew`.

Comandos `kicad-cli` validados no 10.0.6 (detalhes em `layout_approach.md` §4):

- `kicad-cli pcb drc <board>.kicad_pcb --schematic-parity --refill-zones --severity-error --format json --output <out>.json` (com `--save-board` quando se quer gravar o refill)
- `kicad-cli pcb drc <board>.kicad_pcb --all-track-errors --format json --output <out>.json`
- `kicad-cli pcb export pdf --layers F.Cu,B.Cu,Edge.Cuts,F.SilkS,B.SilkS,F.Mask,B.Mask --output <out>.pdf <board>.kicad_pcb`
- `kicad-cli pcb export step --output <out>.step <board>.kicad_pcb`

**Correção ao comando do plano:** no KiCad 10, `kicad-cli pcb export pdf` **exige** `--layers` — sem ele falha com exit 1 ("Pelo menos uma camada deve ser definida"). A forma aprovada é a do bloco acima.

**Bug corrigido nos geradores (Edge.Cuts):** `SetCenter()` sozinho no círculo de borda deixa o ponto `end` em (16,0) absoluto e o raio vira ~130,6 mm em vez de 16 mm (detectado na auditoria da variante B). Correção: `SetCenter` + `SetEnd(CENTER+16,0)` na mesma escala (`bb._nm`) — padrão portado do `gen_board_modulo.py` para o `gen_board_v2.py`. As 3 placas ativas hoje têm Edge.Cuts verificado (raio 16,000 / retângulo 60×32 exatos).

---

## 2. Estado por placa

| Item | **Discreta** (Variante B, nRF52810 QFN32) | **Módulo** (Variante A, E73-2G4M04S) | **Gateway** (carrier DevKitC-32E) |
|---|---|---|---|
| Edge.Cuts | ✅ círculo r=16,000 em (100,100) | ✅ círculo r=16,000 em (100,100) | ✅ retângulo 60,00×32,00 em (100,100) |
| DRC error (`--severity-error`) | **27** | **26** | **0** |
| Composição dos errors | 12 courtyards_overlap (7 envolvem BT1 — footprint Keystone 1059 com dims UNVERIFIED; 5 outros pares: ANT1×C3, C10×C6, C8×X1, L2×L3, L2×U1) · 8 copper_edge_clearance (pads/trilhas na borda) · 6 clearance · 1 solder_mask_bridge | 11 copper_edge_clearance (10 pads físicos do E73 na periferia + 1 resíduo ~0,02 mm no stub VDD_BAT→U1.16) · 6 clearance · 5 courtyards_overlap (BT1×U1 — física do Ø32) · 4 solder_mask_bridge | — |
| Unconnected | **22** | **0** | **0** |
| — rotas de sinal pendentes | **7** (com 4L, GND e VDD_BAT saíram dos corredores F.Cu/B.Cu — ver §4a) | 0 | 0 |
| — GND sem stitch livre | **9** (pads GND em F.Cu sem via para a zona B.Cu; gerador registra 8 pads sem direção livre: C2.2/C4.2/C5.2/C6.2/C7.2/C8.2/U1.20/U1.29) | 0 (punch list fechada: C1.2/C2.2 com via de costura) | 0 |
| Parity (`--schematic-parity`) | 0 | 0 | 0 |
| Curtos | 0 (0 `shorting_items` no estado atual) | 0 | 0 |
| Warnings (all-track-errors) | 54 warning (silk sobre cobre/sobreposição, texto, 2 track_dangling) — não bloqueiam | 36 warning (silk/texto, 1 padstack) — não bloqueiam | **0** (fechado: os 13 warning de furo — 12× `hole_to_hole` + 1× `holes_co_located` — foram eliminados ao afastar as vias GND de stitch dos PTHs; offset inicial 1,6 mm validado furo-a-furo ≥0,6 mm contra todos os PTHs) |
| Veredito da auditoria | REPROVADO (estado da auditoria; desde então o Edge.Cuts foi corrigido e o board regenerado — ver JSONs atuais) | REPROVADO → punch list FECHADA (restam só os 11 errors de física documentada) | APROVADO COM PENDÊNCIAS |

Nota de rastreabilidade: a auditoria da Discreta registrou 284 errors no board com o bug de raio (83 curtos reais de VDD_BAT, 116 mask, 71 clearance, J1 não flipado). O board atual (regenerado em `gen_run_4`, 18:21) tem 27 errors / 22 unconnected / 0 curtos — os JSONs commitados refletem o board atual (verificado por re-execução DRC nas auditorias).

---

## 3. Keepouts de antena (valor + fonte)

| Placa | Keepout (frame do board) | Fonte |
|---|---|---|
| Discreta | x∈[8,14], y∈[8,14] mm rel. ao centro (canto NE do disco) — ~3 mm de margem da antena chip Johanson | Regra do gerador `gen_board_v2.py` (`rf_nets` isentos: NET_RF/NET_ANT + GND de retorno C3/ANT1). **Observação:** a regra vive só no gerador — não há zona keepout nativa no board; um edit manual no KiCad não seria bloqueado |
| Módulo | x∈[-15,5,-8,85], y∈[-9,9] mm rel. ao centro (extremidade oeste) | NOTA 4 do esquemático (y_local < -8,85 do footprint E73), rotacionada 90° — mapeamento verificado pelos pads reais (U1.16/U1.37). **Keepout nativo do footprint E73 confirmado no pour:** varredura de cobre na faixa = 0 cobre (zona keepout F.Cu+B.Cu presente no board; zona desenhada ~1,15 mm mais estreita a oeste que o retângulo da NOTA 4 — cobre real respeita o retângulo completo) |
| Gateway | x∈[124,130], y∈[84,116] (extremidade leste, antena PCB do DevKitC) | NOTA do gerador `gen_board_gateway.py`; isenção de 1,0 mm para pads do próprio U1 (J2-19/J3-19 em x≈122,86). Verificado: 0 cobre de rota na faixa, ambas as camadas |

---

## 4. Pendências honestas (e o que é preciso para resolver)

### a) Discreta — 7 rotas de sinal pendentes + courtyards BT1
Após a migração para 4 camadas (§6), GND e VDD_BAT saíram dos corredores F.Cu/B.Cu para planos internos, liberando espaço para o A* router. As 7 rotas restantes (NET_XC2, NET_DCC, NET_DEC4, NET_DEC3, NET_SWDCLK, NET_SWDIO, NET_RESET) ainda dependem de **re-placement dos passivos** (afastar caps de decoupling/cristal do muro de pads do U1) e regenerar, **ou** acabamento manual no GUI KiCad 10 com o roteador interativo. Os 9 GND sem stitch precisam de vias em direções hoje bloqueadas — mesmo tratamento. Os 12 courtyards_overlap: conferir o drawing oficial da **Keystone 1059** (footprint custom `nibas_wristband:Keystone_1059_CR2032_SMT` está marcado **UNVERIFIED** no símbolo) antes de tratar como erro real de placement.

### b) Módulo — E73 não cabe no Ø32
Os pads U1.15/16/27/28 ficam a r=16,24–16,86 mm do centro — **fisicamente fora do disco Ø32** (módulo 17,5×28,7 mm + holder CR2032 15,24×30,48 mm não cabem lado a lado). É decisão de projeto, não de rota: (1) cápsula maior que Ø32; (2) módulo menor — verificar variante do E73 (ex. E73-2G4M04S é 17,5×28,7; checar se existe variante menor da família E73 que atenda); ou (3) aceitar overhang do módulo na borda. A sobreposição BT1×U1 (5 courtyards + 6 clearance + 4 mask) tem a mesma causa raiz. Os 11 `copper_edge_clearance` restantes são todos essa física documentada.

### c) Gateway — footprint do soquete errado + hole-to-hole
O U1 usa `PinHeader_2x19_P2.54mm_Vertical` com **2,54 mm entre fileiras**, mas o DevKitC-32E real tem as fileiras de header a **27,94 mm** (largura do módulo). O board atual NÃO encaixa o DevKitC físico. Antes de fabricar: trocar por footprint custom `ESP32-DevKitC-32E_Carrier` (27,94 mm entre fileiras, soquete fêmea 1x19) e regenerar placement/rotas. **PENDÊNCIA ATIVA:** o esquemático e a lib já apontam para a carrier (módulo 55×28), mas o board 60×32 não acomoda o módulo físico + J1/SW1/R1 sem sobreposição de courtyard — a migração exige redimensionar o board (decisão de projeto). O gerador (`gen_board_gateway.py`) fixa U1 no PinHeader_2x19 enquanto isso. Os 13 warnings `hole_to_hole`/`holes_co_located` **FECHADOS**: vias de stitch GND agora em offsets ≥1,6 mm do pad, validadas furo-a-furo (borda a borda ≥0,6 mm) contra todos os PTHs + clearance de cobre, com fallback de busca em grade até r 14,5 mm (DRC all-track-errors: 0 violações).

### d) Geral
- **Tuning RF em bancada com VNA** (variante B — antena chip Johanson): o layout garante a rota, mas o matching (L1/L2/C3) só se fecha com medição real.
- **Modelos 3D ausentes:** `kicad-packages3d` não instalado neste host (`/usr/share/kicad/3dmodels` vazio) — o STEP sai só com cobre/board/pads, sem corpos dos componentes. Instalar o pacote se a conferência visual (passo vision) exigir; o export não falha por isso.

---

## 5. Como abrir / continuar

- **Abrir no KiCad 10 GUI:** os `.kicad_pcb` são autocontidos (footprints embutidos no board — não dependem de fp-lib-table):
  - `hardware/kicad/wristband_discreto/wristband_discreto.kicad_pcb`
  - `hardware/kicad/wristband_modulo/wristband_modulo.kicad_pcb`
  - `hardware/kicad/gateway_esp32/gateway_esp32.kicad_pcb`
- **Regenerar do zero** (idempotente, cada gerador recria o board completo):
  - `python3 hardware/kicad/wristband_discreto/gen_board_v2.py`
  - `python3 hardware/kicad/wristband_modulo/gen_board_modulo.py`
  - `python3 hardware/kicad/gateway_esp32/gen_board_gateway.py`
- **Re-checar DRC:** comandos do §1 (JSONs vão para `exports/`).
- Regra do ambiente segue valendo: geração/validação por `kicad-cli` + `pcbnew`; o GUI KiCad 10 só para acabamento manual (roteador interativo da Discreta).

---

## 6. Migração 4 camadas (variante discreta)

A variante discreta foi migrada de 2 para 4 camadas (F.Cu/In1.Cu/In2.Cu/B.Cu)
para resolver o bloqueio de roteamento causado pelas autostradas de potência
(GND e VDD_BAT) nos corredores de sinal.

**Stackup:** F.Cu (sinal) / In1.Cu (plano GND) / In2.Cu (plano VDD_BAT) / B.Cu (sinal+GND)
**Espessura:** 0,8 mm
**Mudanças:** GND e VDD_BAT removidos do roteamento por trilha; vias blind F.Cu→In1/In2
conectam pads de potência aos planos internos. Sinais (RF, cristal, DEC, SWD, DCC, RESET)
roteados em F.Cu/B.Cu com mais espaço disponível.

**Status:** Script gen_board_v2.py atualizado para 4L; board_builder.py estendido com
suporte a camadas internas, planos e vias blind/buried.
