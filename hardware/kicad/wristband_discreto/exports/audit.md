# Auditoria independente — `wristband_discreto` (Variante B, nRF52810 QFN32)

**Data:** 2026-09-09 · **Auditor:** sessão fresh (3.1), read-only exceto este relatório
**Escopo:** `wristband_discreto.kicad_pcb` (mtime 17:01) — re-execução independente do done comum 2.1 + checklist físico + ratsnest.

## 1. Re-execução DRC (fresh, nesta sessão)

Comandos da fase 2 re-executados **sem `--save-board`** (auditoria read-only; o `--save-board` da fase 2 só re-gravou o board após refill — ver §1.2):

| Comando | Resultado fresh | Committed (fase 2) | Bate? |
|---|---|---|---|
| `kicad-cli pcb drc … --schematic-parity --refill-zones --severity-error --format json` | **284 violações (284× error)**, 22 desconectados, 0 parity | 284 / 22 / 0 | ✅ contagens idênticas |
| `kicad-cli pcb drc … --all-track-errors --format json` | **401 violações (353 error + 48 warning)**, 22 desconectados | 401 / 22 | ✅ contagens idênticas |

### 1.1 Composição das 284 violações error (drc1)
`shorting_items` 83 · `solder_mask_bridge` 116 · `clearance` 71 · `courtyards_overlap` 12 · `starved_thermal` 1 · `hole_clearance` 1.

Exemplo real de curto: `Trilha [VDD_BAT] F.Cu 0,5mm` × `Ilha [NET_DEC4] de L3`, × `Ilha [NET_RESET] de R1`, × `Ilha [<no net>] de U1` — o roteador A* deixou cobre de VDD_BAT colidindo com ilhas de outras nets. **O critério do done ("0 violações error") NÃO foi atendido.**

### 1.2 JSONs commitados vs board atual
Contagens e tipos idênticos aos JSONs de `exports/` (284/401, 22 unconn). Diff normalizado mostra apenas renumeração de ilhas GND e troca `Trilha [GND] 0,8mm`↔`Ilha [GND] de U1` — efeito do `--refill-zones --save-board` da fase 2 (renumera ilhas do refill). **Os JSONs refletem o board atual.**

## 2. Asserts de geometria (pcbnew 10.0.6, executados nesta sessão)

| Assert | Esperado | Encontrado | Veredito |
|---|---|---|---|
| Edge.Cuts | círculo r=16 (Ø32) em (100,100) | `gr_circle center (100,100) end (16,0)` → **raio real = √(84²+100²) = 130,60 mm (Ø261,2 mm)** | **FALHA** |
| `validate_pads_inside_edges` | [] | [] (trivialmente — o círculo de 130,6 mm contém tudo; o assert da fase 2 ficou cego para este bug) | ⚠️ passou por causa da FALHA acima |
| Footprints | 24 (sem TAG1) | 24, TAG1 ausente | OK |
| Tracks / vias / zones | — | 338 / 8 / 1 (zona GND B.Cu) | OK |

**Causa raiz (localizada):** `gen_board_v2.py` linhas ~883–888 move o círculo só com `SetCenter()`; o ponto `end` fica em (16,0) absoluto e o raio vira 130,6 mm. O `gen_board_modulo.py` (linhas 426–431) já documenta exatamente esta armadilha e corrime com `SetEnd(CENTER+16,0)` — a correção não foi portada para a variante B. Consequências: DRC sem `copper_edge_clearance` (borda longe), STEP/PDF com disco gigante, assert de pads dentro do disco sem valor.

## 3. Checklist físico — item a item

| # | Item | Veredito | Evidência |
|---|---|---|---|
| 1 | Ø32 mm | **FALHA** | Edge.Cuts r=130,6 mm (§2) |
| 2 | BT1 no centro | OK | BT1 (100,00,100,00) |
| 3 | TAG1 fora do board (inlay na cápsula) | OK | 24 footprints, nenhum TAG1 |
| 4 | SHLD1 em B.Cu sob BT1 | OK | SHLD1 B.Cu (100,00,100,00), pad GND funde com zona |
| 5 | J1 no verso | **FALHA** | footprint J1 em `layer "F.Cu"`, pad 8×8 em `layers "F.Cu" "F.Mask" "F.Paste"` — `FLIP_REFS={"J1","SHLD1"}` não aplicou ao J1 (SHLD1 virou, J1 não) |
| 6 | Keepout antena x∈[8,14] y∈[8,14] (rel. centro) | OK c/ observação | varredura de cobre em [108,114]×[108,114]: só NET_RF (isento) + GND (retorno de C3.2/ANT1.2 — isento pela regra do gerador, que inclui GND em `rf_nets` via C3/ANT1). Nenhuma rede não-RF. **Observação:** não existe zona keepout no board — a regra vive só no gerador; um edit manual no KiCad não seria bloqueado |
| 7 | Rota RF | OK | NET_ANT 6,87 mm + NET_RF 2,56 mm em F.Cu (C3→L1→ANT1) |
| 8 | Rota cristal | OK | NET_XC1 23,05 mm; NET_XC2 16,28 mm (resta 1 trecho C2.1↔U1.24 — ver §4) |
| 9 | Rota DC/DC | **PENDÊNCIA** | NET_DCC, NET_DEC4, NET_L2_L3: **0 mm de trilha** — ladder inteiro pendente |
| 10 | Rota SWD | **PENDÊNCIA** | SWDCLK 27,07 mm OK; **SWDIO 0 mm** (TP2.1↔U1.18 pendente) |
| 11 | Die pad U1.33 com vias GND | **FALHA** | nenhum via GND num raio de 4 mm do centro do U1 (único via próximo é NET_SWDCLK); U1.33 flutuante (aparece 2× em unconnected) |
| 12 | DNP C7/R1 presentes | OK c/ observação | ambos posicionados (C7 98,5/114,5; R1 90/90); flag DNP do footprint no board não setado (`dnp=False`) — atributo ficou só no esquemático |

## 4. Ratsnest / unconnected (22 itens — lista exata e classificação)

**Rotas de sinal pendentes (10):**
1. `NET_DEC1`: C5.1 ↔ U1.1
2. `VDD_BAT`: trilha 0,5 mm ↔ U1.9 (trecho final)
3. `NET_RESET`: R1.1 ↔ U1.16 (R1 é DNP — rota dispensável na população mínima, mas o cobre existe)
4. `NET_SWDIO`: TP2.1 ↔ U1.18
5. `NET_DEC3`: C6.1 ↔ U1.22
6. `NET_XC2`: C2.1 ↔ trilha 0,5 mm (trecho final)
7. `NET_DEC4`: U1.30 ↔ L3.2
8. `NET_DEC4`: C10.1 ↔ U1.30
9. `NET_DCC`: L2.2 ↔ U1.31
10. `NET_L2_L3`: L3.1 ↔ L2.1

**Ilhas GND flutuantes em F.Cu (12)** — pads GND sem via para a zona B.Cu (o gerador adicionou 6 vias GND; 9 pads ficaram sem direção livre, e o ratsnest confirma que continuam desconectados):
11–12. C4.2 ↔ C8.2 · 13. C9.2 ↔ C8.2 · 14. C9.2 ↔ C2.2 · 15. C9.2 ↔ TP4.1 · 16–17. C2.2 ↔ C1.2 · 18–19. U1.29 ↔ U1.33 · 20–21. U1.33 ↔ U1.20 · 22. ANT1.2 ↔ via GND órfã.

**Falso-positivo: nenhum.** Todos os 22 são cobre real desconectado. Nota: os 12 itens GND são *eletricamente críticos* (desacoplos C4/C8/C9 e die pad sem retorno GND).

## 5. Veredito: **REPROVADO**

Punch list (bloqueia):
1. Edge.Cuts com raio 130,6 mm em vez de 16 mm — corrigir `gen_board_v2.py` (portar o `SetEnd` do `gen_board_modulo.py`) e regenerar.
2. 284 violações error (83 curtos reais de VDD_BAT contra ilhas de outras nets + 71 clearance + 116 solder_mask_bridge) — roteador precisa de re-checagem de colisão.
3. 10 rotas de sinal pendentes (DC/DC completo, SWDIO, DEC1/DEC3, XC2, VDD_BAT).
4. 12 pads GND flutuantes em F.Cu (sem via para a zona) — inclui die pad U1.33 sem array de vias.
5. J1 não flipado (deveria estar em B.Cu).

Não bloqueia, mas registrar: flag DNP ausente nos footprints do board; keepout de antena sem zona keepout nativa.
