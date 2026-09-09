# Auditoria independente — `wristband_modulo` (Variante A, E73-2G4M04S)

**Data:** 2026-09-09 · **Auditor:** sessão fresh (3.2), read-only exceto este relatório
**Escopo:** `wristband_modulo.kicad_pcb` (mtime 17:23) — re-execução independente do done comum 2.2 + checklist físico + ratsnest.

## 1. Re-execução DRC (fresh, nesta sessão)

Comandos da fase 2 re-executados **sem `--save-board`** (read-only):

| Comando | Resultado fresh | Committed (fase 2) | Bate? |
|---|---|---|---|
| `kicad-cli pcb drc … --schematic-parity --refill-zones --severity-error --format json` | **30 violações (30× error)**, 2 desconectados, 0 parity | 30 / 2 / 0 | ✅ |
| `kicad-cli pcb drc … --all-track-errors --format json` | **67 violações (30 error + 37 warning)**, 2 desconectados | 67 / 2 | ✅ |

### 1.1 Composição das 30 violações error
`copper_edge_clearance` 15 · `clearance` 6 · `solder_mask_bridge` 4 · `courtyards_overlap` 5.

- `courtyards_overlap` (5): U1×BT1, U1×TP1, U1×TP3, U1×TP4, BT1×C2 — consequência direta da **sobreposição BT1×U1 documentada** (impossibilidade física do Ø32; docstring de `gen_board_modulo.py` linhas 17–22).
- `clearance`/`solder_mask_bridge` (10): ilha VDD_BAT de BT1 contra pads `<no net>` do U1 (4/5/6/7/29/30) e TP3 — mesma causa (BT1 sob o módulo).
- `copper_edge_clearance` (15): trilhas a menos da folga do círculo r=16 (ex.: `Trilha [VDD_BAT] F.Cu 3,175 mm` × `Círculo no Edge.Cuts`).

**O critério do done ("0 violações error") NÃO foi atendido** — mas 10 das 30 derivam da pendência física documentada; as 15 de borda são qualidade de rota.

### 1.2 JSONs commitados vs board atual
Contagens/tipos idênticos; diff normalizado só renumera ilhas (efeito do `--save-board` da fase 2). **JSONs refletem o board atual.**

## 2. Asserts de geometria (pcbnew 10.0.6)

| Assert | Esperado | Encontrado | Veredito |
|---|---|---|---|
| Edge.Cuts | círculo r=16 em (100,100) | `gr_circle center (100,100) end (116,100)` → **r = 16,000 mm exato** | OK |
| `validate_pads_inside_edges` | [] | [] | OK |
| Footprints | 10 (sem TAG1) | 10, TAG1 ausente | OK |
| Tracks / vias / zones | — | 20 / 8 / 2 (zona GND B.Cu + zona keepout F&B) | OK |

## 3. Checklist físico — item a item

| # | Item | Veredito | Evidência |
|---|---|---|---|
| 1 | Ø32 mm | OK | r=16,000 exato (o gerador desta variante fez `SetCenter`+`SetEnd` corretamente) |
| 2 | Keepout NOTA 4 x∈[-15.5,-8.85] y∈[-9,9] (rel. centro) | OK c/ observação | varredura de cobre em [84.5,91.15]×[91,109] abs: **0 cobre** (nem pads do U1). Zona keepout nativa presente (F.Cu+B.Cu, tracks/vias/pads/copperpour/footprints not_allowed). **Observação:** a zona desenhada é x∈[85.65,91.15] y∈[91.25,108.75] — ~1,15 mm mais estreita a oeste e 0,25 mm nos topos que o retângulo da NOTA 4; o cobre real respeita o retângulo completo, mas a zona nativa não cobre tudo |
| 3 | Rotas VDD_BAT / SWD | OK | VDD_BAT 39,25 mm; SWDCLK 10,58 mm; SWDIO 12,35 mm; 0 pendências de sinal |
| 4 | TAG1 fora do board | OK | 10 footprints, nenhum TAG1 (inlay na cápsula) |
| 5 | Resíduos BT1×U1 documentados | OK | docstring `gen_board_modulo.py` linhas 17–22 ("SOBREPÕE o módulo U1: impossibilidade física do Ø32… Documentado"); DRC registra as 5 courtyards_overlap |
| 6 | Pads U1.15/16/27/28 fora do disco (física) | OK confirmado | dist+raio do pad: 15→16,24 · 16→16,31 · 27→16,31 · 28→16,24 mm (> 16). Fisicamente fora do disco, como previsto; documentado no gerador (comentário linhas ~379: "pads na periferia (C1.2, C2.2, U1.15)") |
| 7 | J1 no verso | OK | J1 em B.Cu (100,89) |
| 8 | SHLD1 B.Cu | OK | SHLD1 B.Cu (100,100) |

## 4. Ratsnest / unconnected (2 itens — lista exata e classificação)

1. `Ilha 2 [GND] de C2 (F.Cu)` ↔ `Ilha 2 [GND] de C1 (F.Cu)` — **ilha GND**: pads de retorno dos caps do cristal sem via para a zona B.Cu (stitch GND pendente; o gerador tenta 8 direções e registra bloqueio por colisão).
2. `Ilha 2 [GND] de C1 (F.Cu)` ↔ `Ilha 15 [GND] de U1 / trilha GND 0,8 mm (F.Cu)` — **ilha GND**, mesma causa (C1.2 sem stitch para B.Cu).

**Falso-positivo: nenhum.** Nenhuma rota de sinal pendente — VDD_BAT, SWDCLK, SWDIO 100% roteadas.

## 5. Veredito: **REPROVADO** (critério "0 violações error" não atendido) — punch list curta

Bloqueia:
1. 15× `copper_edge_clearance` — trilhas de rota colidindo com a margem do círculo r=16 (qualidade de rota, não é a pendência física).
2. 2 stitches GND pendentes (C1.2/C2.2 sem via para a zona B.Cu).

Pendências físicas já documentadas (não reprovam por si, mas impedem fabricação): sobreposição BT1×U1 (impossibilidade Ø32) e pads U1.15/16/27/28 fora do disco — ambas registradas no gerador e visíveis no DRC.

Observação menor: zona keepout nativa menor que o retângulo da NOTA 4 (cobre real OK; alinhar a zona ao spec na próxima regeneração).

## 6. Punch list — FECHADA (2026-09-09, 3 iterações, `gen_board_modulo.py`)

| Item | Antes | Depois | Como |
|---|---|---|---|
| `copper_edge_clearance` | 15 | **11** | C1→(9.5,10.7), C2→(7.0,11.7), J1→y=-10.9 (cantos a r≤15,48, folga ≥0,52); checagem de borda (0,5 mm) em todo roteamento; trilha VDD_BAT→U1.16 reroteada **por B.Cu** (via 108,110.16 → B.Cu → via 108,106.985 → stub F.Cu 0,2 mm) — elimina o cobre a r=17,58 (1,58 mm FORA do disco) |
| Stitches GND (C1.2/C2.2) | 2 pendentes | **0** | Via de costura com offsets 0,8/0,7/0,6/0,9 × 8 direções; skip só para pads exclusivamente em B.Cu (SHLD1 é F+B e precisava de via) |
| unconnected | 2 | **0** | C1.2/C2.2 com via; SHLD1 religada |
| Parity | 0 | 0 | ✅ |

**11 restantes = física documentada**: 10 pads do U1 na periferia (Ilhas 15–19/24–28, cantos a r=16,24–16,68 — módulo 28,7 mm não cabe no Ø32) + 1 resíduo de ~0,02 mm na ponta do stub VDD_BAT→U1.16 (mesma causa: o pad U1.16, centro r=15,96, só é alcançável invadindo a margem). Nenhuma rota de sinal pendente.

Asserts: raio 16,000000 exato · DRC error 26 (11 edge + 10 BT1×U1 físicos + 6 clearance + 4 mask) · DRC all-track-errors 62 (mesmos + silk/texto, não bloqueiam) · exports pdf/step regenerados.
