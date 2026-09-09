# Auditoria independente — `gateway_esp32` (carrier DevKitC-32E)

**Data:** 2026-09-09 · **Auditor:** sessão fresh (3.3), read-only exceto este relatório
**Escopo:** `gateway_esp32.kicad_pcb` (mtime 17:35) — re-execução independente do done comum 2.3 + checklist físico + ratsnest.

## 1. Re-execução DRC (fresh, nesta sessão)

Comandos da fase 2 re-executados **sem `--save-board`** (read-only):

| Comando | Resultado fresh | Committed (fase 2) | Bate? |
|---|---|---|---|
| `kicad-cli pcb drc … --schematic-parity --refill-zones --severity-error --format json` | **0 violações**, 0 desconectados, 0 parity | 0 / 0 / 0 | ✅ JSON idêntico |
| `kicad-cli pcb drc … --all-track-errors --format json` | **13 violações (13× warning)**, 0 desconectados | 13 / 0 | ✅ JSON idêntico |

**Critério do done ("0 violações error", unconnected = 0): ATENDIDO.** As 13 violações do segundo comando são todas **warning** de furo: 12× `hole_to_hole` (vias GND de stitch a menos da folga de PTHs do PinHeader U1, J1 e SW1) + 1× `holes_co_located` (2 vias GND coincidentes). Pendência de fabricação (folga de furo), não elétrica.

## 2. Asserts de geometria (pcbnew 10.0.6)

| Assert | Esperado | Encontrado | Veredito |
|---|---|---|---|
| Edge.Cuts | retângulo 60×32 em (100,100) | 4 segmentos: (70,84)→(130,84)→(130,116)→(70,116) = **60,00 × 32,00 mm exato** | OK |
| `validate_pads_inside_edges` | [] | [] (todos os 46 pads dentro de [70,130]×[84,116]) | OK |
| Footprints | 4 | U1 (PinHeader 2x19, 38 pads), J1 (1x02), SW1 (6 mm), R1 (0603) | OK |
| Tracks / vias / zones | — | 14 / 6 / 1 (zona GND B.Cu) | OK |

## 3. Checklist físico — item a item

| # | Item | Veredito | Evidência |
|---|---|---|---|
| 1 | Board 60×32 mm | OK | §2 |
| 2 | Rota +5V | OK | 58,59 mm (J1.1 → U1/J2-19) |
| 3 | Rota +3V3 | OK | 7,62 mm (U1/J2-1 → R1) |
| 4 | Rota EN | OK | 19,05 mm (U1/J2-2 → R1.1/SW1) |
| 5 | Zona GND | OK | B.Cu, bbox (70.5,84.5)–(129.5,115.5) = inset 0,5 mm do Edge.Cuts, preenchida |
| 6 | Keepout antena x∈[124,130] | OK | varredura de cobre na faixa (ambas camadas): **0 cobre** — nem trilhas, nem vias, nem pads (a isenção de 1,0 mm dos pads J2-19/J3-19 nem chegou a ser necessária: pads terminam em x=122,86) |
| 7 | Espaçamento de fileiras do DevKitC | **PENDÊNCIA DE FABRICAÇÃO (registrada nesta auditoria)** | U1 = `PinHeader_2x19_P2.54mm_Vertical`: fileiras em y=98,73 e y=101,27 → **2,54 mm entre fileiras**. O DevKitC-32E real tem as duas fileiras de header a **27,94 mm** (largura do módulo). O footprint do board NÃO encaixa o DevKitC físico. O esquemático (NOTA de pinout) já previa "2 soquetes fêmea 1x19 P2.54 ou footprint oficial Espressif — definir na fase de layout"; a definição final usou um 2x19 combinado com passo de fileira errado e a divergência não foi registrada em nenhum doc do projeto antes desta auditoria |

## 4. Ratsnest / unconnected

**0 itens desconectados** (confirmado pelos 2 comandos DRC e por `GetConnectivity().GetUnconnectedCount() = 0`). +5V, +3V3, EN e GND 100% roteadas. Nada a classificar.

## 5. Veredito: **APROVADO COM PENDÊNCIAS**

Pendências (não bloqueiam o DRC, bloqueiam fabricação):
1. **Footprint do U1 não encaixa o DevKitC físico**: fileiras a 2,54 mm vs 27,94 mm reais. Ação: trocar por 2× `PinSocket_1x19_P2.54mm` posicionados a 27,94 mm (ou footprint oficial `Espressif:ESP32-DevKitC`) e regenerar placement/rotas.
2. 13 warnings de folga entre furos (vias GND vs PTHs de U1/J1/SW1; 1 par de vias coincidente) — afastar vias de stitch dos PTHs na regeneração.
3. Footprint é header macho enquanto o esquemático especifica soquete fêmea — resolver junto com o item 1.
