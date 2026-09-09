# Abordagem de Layout Programático (KiCad 10.0.6) — Spike 1.1

**Data:** 2026-09-09 · **Ambiente:** KiCad 10.0.6-1.fc44, `kicad-cli` 10.0.6, python3 3.14 com `import pcbnew` funcional
**Entregável:** `hardware/kicad/tools/board_builder.py` (módulo reutilizável pelos workers 2.1–2.3)
**Regra do ambiente:** **NUNCA** invocar o binário `kicad` (GUI) — apenas `kicad-cli` e `python3 + pcbnew`.

---

## 1. Decisão: script Python pcbnew (primário) — textual é fallback provado

**Ambos os caminhos foram provados no spike; o primário é script via API pcbnew.**

| Critério | Script pcbnew | Textual (.kicad_pcb manual) |
|---|---|---|
| Prova no spike | ✅ board completo (fp+track+via+zona preenchida) salvo e DRC-limpo | ✅ `minimal_textual.kicad_pcb` aceito de primeira pelo parser |
| Risco de rejeição do parser | Zero (o próprio KiCad escreve o arquivo) | Alto se header inventado — a receita exata está documentada abaixo |
| Zona com fill | ✅ `ZONE_FILLER` direto na memória | Exige 2º passo: `pcbnew.LoadBoard` + fill (provado em `_spike/minimal_textual_filled.kicad_pcb`) |
| Integridade geométrica (coords nm) | Garantida pela API | Manual, propensa a erro |

**Fallback textual — header mínimo aceito pelo parser 10.0.6** (prova: `_spike/minimal_textual.kicad_pcb`, DRC exit 0, JSON parseável):

```sexp
(kicad_pcb
	(version 20260206)
	(generator "pcbnew")
	(generator_version "10.0")
	(general (thickness 0.8) (legacy_teardrops no))
	(paper "A4")
	(layers
		(0 "F.Cu" signal)
		(2 "B.Cu" signal)
		(25 "Edge.Cuts" user)
	)
	(setup)
	(net 0 "")
	(net 1 "GND")
	(gr_line (start -10 -7.5) (end 10 -7.5) (stroke (width 0.1) (type default)) (layer "Edge.Cuts") (uuid "<uuid-unico>"))
	; ... 3 lados restantes ...
	(segment (start -5 0) (end 5 0) (width 0.25) (layer "F.Cu") (net 1) (uuid "<uuid-unico>"))
	(via (at 0 -5) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net 1) (uuid "<uuid-unico>"))
	(embedded_fonts no)
)
```

Descobertas do floor do parser: **não precisa listar as 20+ camadas** (só as usadas — ids devem bater com a numeração KiCad: F.Cu=0, B.Cu=2, Edge.Cuts=25); `(setup)` pode ser vazio; nets precisam estar declaradas em `(net N "nome")`; `version 20260206` + `generator_version "10.0"` são os valores que o 10.0.6 grava. Mesmas regras de UUID único da receita de esquemáticos (§1.5 regra 8 de `kicad10_recipe.md`).

**Caminho de fallback completo provado:** textual → `pcbnew.LoadBoard()` → `add_zone` + `fill_zones` → `SaveBoard` → DRC 0 violações (`_spike/minimal_textual_filled.kicad_pcb`).

---

## 2. API pcbnew — o que funciona (tudo provado no selftest)

- `pcbnew.CreateEmptyBoard()` → board novo; `GetDesignSettings().SetCopperLayerCount(2)` e `SetBoardThickness(FromMM(0.8))`.
- **Edge.Cuts**: `PCB_SHAPE` com `SetShape(SHAPE_T_SEGMENT)` (retângulo) **e** `SHAPE_T_CIRCLE` + `SetCenter/SetRadius` (disco Ø32) — ambos aceitos pelo DRC.
- **Footprint**: `pcbnew.FootprintLoad("<dir>/<Lib>.pretty", "Nome")` + `board.Add(fp)` (embutido no board no save — obrigatório, kicad-cli nunca carrega fp-lib-table); `SetPosition`, `SetOrientationDegrees`, `SetReference`, `SetValue`, `Flip()` p/ B.Cu. Pads: `fp.FindPadByNumber("1").SetNetCode(code)`.
- **Nets**: `pcbnew.NETINFO_ITEM(board, "GND")` + `board.Add(net)`; `board.FindNet("nome")` para reuso.
- **Track**: `PCB_TRACK(board)` + `SetStart/SetEnd/SetWidth/SetLayer/SetNetCode` + `board.Add`.
- **Via**: `PCB_VIA(board)` + `SetPosition/SetViaType(VIATYPE_THROUGH)/SetDrill/SetWidth/SetLayerPair(F_Cu, B_Cu)/SetNetCode` + `board.Add`.
- **Zona**: `ZONE(board)` + `SetLayer(B_Cu)` + `SetNetCode` + outline via `zone.Outline()` → `NewOutline()` → `Append(x_nm, y_nm)` por vértice + `board.Add(zone)`.
- **Fill**: `pcbnew.ZONE_FILLER(board)`; `filler.Fill(board.Zones())` → preenche e `zone.IsFilled()` volta `True` (16 vértices de polígono no board de teste). **Funciona — não precisa do fallback "textual + fill".**
- **Save**: `pcbnew.SaveBoard(caminho_absoluto, board)` → gravado com header `(version 20260206) (generator "pcbnew") (generator_version "10.0")`.

Classes legadas **removidas** no v10: `pcbnew.TRACK`, `pcbnew.VIA`, `pcbnew.ZONE_CONTAINER` — usar `PCB_TRACK`, `PCB_VIA`, `ZONE`.

## 3. API pcbnew — pegadinhas encontradas (não repetir)

1. **R_0603 e afins: pad "1" fica no lado −x da orientação 0°.** Um track saindo do pad 1 para +x cruza o pad 2 (net diferente) → `shorting_items` + `solder_mask_bridge` no DRC (peguei os dois no spike). Roteie usando `pad_position_mm()` como endpoint e **deixe o validador de DRC pegar curto** — nunca assuma lado de pad.
2. **Coordenadas**: funções públicas do `board_builder.py` recebem **mm (float, origem = centro do board)**; conversão para nm é interna. `VECTOR2I` estoura `OverflowError` se receber float fora do int32 — sempre `_nm()` antes.
3. **`create_board` centra o outline na origem** (o plano exige Ø32 centrado na origem). Posicionar footprints/rotas em coordenadas centradas.
4. `import pcbnew` cosme 3 asserts `PROPERTY_ENUM` no **stderr** (bug cosmético do build Fedora) — inofensivo; não tratar como falha.
5. `zone.Outline().Append(x, y)` recebe **nm (int)** — não mm.
6. Sem `kiutils`/`skidl`/`schnew` nesta máquina (ModuleNotFoundError) — por isso o módulo é stdlib+pcbnew puro.

---

## 4. Comandos kicad-cli validados nesta versão (exatos)

| Comando | Resultado |
|---|---|
| `kicad-cli version` | `10.0.6` |
| `kicad-cli pcb drc <board>.kicad_pcb --schematic-parity --refill-zones --save-board --severity-error --format json --output <out>.json` | ✅ exit 0; JSON com `violations`/`unconnected_items`/`schematic_parity`; `--refill-zones` re-preencheu a zona e `--save-board` gravou o board. **Sem esquemático anexado**, o parity emite warning no stderr ("Houve uma falha ao buscar a netlist...") e segue com `schematic_parity: []` |
| `kicad-cli pcb drc <board>.kicad_pcb --all-track-errors --format json --output <out>.json` | ✅ exit 0; `unconnected_items: 0` no board do selftest |
| `kicad-cli pcb export pdf --layers F.Cu,B.Cu,Edge.Cuts --output <out>.pdf <board>.kicad_pcb` | ✅ exit 0, PDF 1 página |
| `kicad-cli pcb export step --output <out>.step <board>.kicad_pcb` | ✅ exit 0, STEP gerado (8,9 KB no board de teste) |

⚠️ **Correção ao comando do plano:** `kicad-cli pcb export pdf --output <out>.pdf <board>.kicad_pcb` **FALHA no KiCad 10** (exit 1, "Pelo menos uma camada deve ser definida"). O `-l/--layers` é **obrigatório** nesta versão. Forma aprovada para os boards NibasRockBar:

```bash
kicad-cli pcb export pdf --layers F.Cu,B.Cu,Edge.Cuts,F.SilkS,B.SilkS,F.Mask,B.Mask \
  --output <dir>/exports/<board>_layout.pdf <dir>/<board>.kicad_pcb
```

⚠️ **STEP sem modelos 3D (confirmado)**: `/usr/share/kicad/3dmodels` existe mas está **VAZIO** — o pacote Fedora `kicad-packages3d` não está instalado neste host. O export acusa `Arquivo não encontrado: ${KICAD10_3DMODEL_DIR}/...` no stderr, porém **gera o STEP do cobre/board normalmente** (exit 0; 8,9 KB no board de teste). Consequência para o passo 3.5 (vision): STEP mostra apenas geometria do board/pads/trilhas, sem corpos 3D dos componentes — instalar `kicad-packages3d` se a conferência visual exigir corpos; isso NÃO bloqueia o exit 0 do export.

---

## 5. `board_builder.py` — interface para os workers 2.1–2.3

```python
import sys; sys.path.insert(0, "hardware/kicad/tools")
import board_builder as bb

b = bb.create_board(shape="circle", diameter_mm=32.0, layers=2, thickness_mm=0.8)  # ou (20, 15) rect
r1 = bb.place_footprint(b, "Resistor_SMD:R_0603_1608Metric", 0.0, 0.0, ref="R1", value="10k")
bb.assign_pad_net(r1, "1", b, "SIG"); bb.assign_pad_net(r1, "2", b, "GND")
p1 = bb.pad_position_mm(r1, "1")
bb.add_route(b, "SIG", [p1, (p1[0], 4.0), (12.0, 4.0), (12.0, p1[1])], layer="F.Cu")
bb.add_via(b, "GND", 8.0, 8.0)
bb.add_rect_zone(b, "GND", -15.0, -15.0, 15.0, 15.0, layer="B.Cu")
bb.fill_zones(b)
problemas = bb.validate_pads_inside_edges(b)   # [] = todos os pads dentro do Edge.Cuts (rect OU círculo)
bb.save_board(b, "hardware/kicad/<dir>/<board>.kicad_pcb")
```

API completa: `create_board` (rect/círculo), `get_or_create_net`, `place_footprint` (ref/value/rotação/Flip p/ B.Cu), `assign_pad_net`, `pad_position_mm`, `add_track`, `add_route` (polilinha), `add_via`, `add_zone`/`add_rect_zone`, `fill_zones`, `save_board`, `validate_pads_inside_edges`, `board_summary`. Libs resolvidas em `/usr/share/kicad/footprints` (override: env `KICAD_FOOTPRINTS_DIR`).

---

## 6. Evidência do spike (comandos DONE, saídas reais)

```text
$ python3 -c "import pcbnew; print(pcbnew.GetBuildVersion())"
10.0.6-1.fc44

$ python3 hardware/kicad/tools/board_builder.py --selftest
pcbnew build version: 10.0.6-1.fc44
PASS create_board rect 20x15mm 2L: footprints=0 tracks=0 zones=0 nets=0
PASS place_footprint x2 (R_0603_1608Metric): footprints=2 tracks=0 zones=0 nets=2
PASS track + route + via: footprints=2 tracks=7 zones=0 nets=2
PASS zone GND B.Cu added; ZONE_FILLER filled 1 zone(s); IsFilled=True; filled vertices=16
PASS validate_pads_inside_edges: all pads inside Edge.Cuts
PASS save_board: .../_spike/board_builder_selftest.kicad_pcb (10259 bytes)
SELFTEST OK   (exit 0)

$ kicad-cli pcb drc _spike/board_builder_selftest.kicad_pcb --schematic-parity --refill-zones \
    --save-board --severity-error --format json --output /tmp/drc_spike.json
Foram encontradas 0 violações / 0 Itens desconectados / Placa salva   (exit 0, JSON parseável)

$ kicad-cli pcb drc _spike/board_builder_selftest.kicad_pcb --all-track-errors --format json --output ...
unconnected_items: 0   (exit 0, JSON parseável)

$ kicad-cli pcb export pdf --layers F.Cu,B.Cu,Edge.Cuts --output /tmp/spike.pdf _spike/board_builder_selftest.kicad_pcb
Foi plotado para '/tmp/spike.pdf'. Feito.   (exit 0, PDF 1.5, 1 página)

$ kicad-cli pcb export step --output /tmp/spike.step _spike/board_builder_selftest.kicad_pcb
STEP file '/tmp/spike.step' created.   (exit 0)

$ # disco Ø32mm provado à parte: _spike/circle_test.kicad_pcb → DRC 0 violações, PDF exit 0
```

Arquivos de prova em `hardware/kicad/_spike/`: `board_builder_selftest.kicad_pcb` (API), `minimal_textual.kicad_pcb` (textual mínimo), `minimal_textual_filled.kicad_pcb` (fallback textual+fill), `circle_test.kicad_pcb` (Ø32).

---

## 7. Limitações e pendências herdadas pelos workers 2.x

1. **`--schematic-parity` sem netlist**: warning no stderr, `schematic_parity: []`. Para parity real, rodar DRC no board do mesmo dir do `.kicad_sch` (como o plano já manda em 2.x).
2. **STEP**: sai sem modelos 3D dos footprints (`kicad-packages3d` ausente — `/usr/share/kicad/3dmodels` vazio); exit 0 garantido, mas o 3.5 (vision) não verá corpos de componentes.
3. **`validate_pads_inside_edges` é conservador** (bounding-box do rect / distância radial do círculo, usando meio-pado no eixo X); não substitui o DRC do kicad-cli — é um assert rápido de placement.
4. **Footprint embedding**: cada `.kicad_pcb` gerado embute os footprints usados (autocontido; fp-lib-table irrelevante para o CLI — consistente com regra 6 de `kicad10_recipe.md` §1.5).
5. **Zonas sem thermal defaults customizados**: usam os defaults do KiCad (thermal relief 0.5 mm etc.). Se alguma net exigir conexão sólida (ex.: die pad U1.33), setar `zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)` no worker.
