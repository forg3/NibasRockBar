---
title: "Relatório Completo da Sessão de Trabalho"
subtitle: "NibasRockBar — Smart Badge Pub (pulseira NFC+BLE + gateway ESP32)"
date: "09 de setembro de 2026"
lang: pt-BR
---

# 1. Contexto do projeto

O NibasRockBar é uma pulseira eletrônica (NFC + BLE) para identificação de clientes e localização indoor no salão do pub, integrada ao sistema de caixa **Deli** (plataforma Fudo, API pública em `api.fu.do`).

**Decisões de negócio já fechadas (não reabrir sem motivo novo):**

- **Sem self-service**: o garçom tira o pedido e a equipe serve tudo. A pulseira só identifica e localiza — não aciona nada fisicamente (sem torneira automática, sem válvula).
- **Forma física**: disco Ø32 mm, cápsula IP67, pulseira esportiva de silicone; bateria CR2032.
- **Rádio**: módulo BLE certificado (nRF52810), não SoC discreto com antena própria — simplifica homologação ANATEL.
- **Identificação**: NXP NTAG213 (inlay pronto), com blindagem de ferrite entre a bobina NFC e a bateria.
- **Fluxo**: check-in (abre comanda no Deli) → pedido (garçom lança no Deli; pulseira só identifica) → localização (BLE, assistência ao garçom) → checkout automático quando o caixa fecha a comanda no Deli (polling de `saleState`; o projeto nunca fecha a comanda por conta própria).
- **Divisão de responsabilidade**: Deli é o sistema de registro de pedido/pagamento/fiscal; este projeto nunca duplica cardápio nem processa pagamento.

A sessão de 2026-09-09 executou dois planos encadeados: **`kicad-esquematicos-verificacao`** (SESSÃO 1 — esquemáticos KiCad + verificação independente) e **`plano_frentes_A_B_C`** (SESSÃO 2 — layouts PCB, correções de firmware e preparação do GitHub).

---

# 2. SESSÃO 1 — Esquemáticos KiCad (plano `kicad-esquematicos-verificacao`, 6 ondas)

## 2.1 O que foi entregue

Três esquemáticos KiCad 10.0.6 gerados por código (S-expression via `kicad-cli`, sem GUI), cada um com **ERC com 0 violações** (error+warning+exclusion), netlist exportada e PDF vetorial:

| Placa | Conteúdo | ERC |
|---|---|---|
| `wristband_modulo` (Variante A) | Módulo BLE **Ebyte E73-2G4M04S-52810** (nRF52810, SoftDevice S112 direto), NTAG213 inlay, Keystone 1059, J1, ferrite SHLD1, C1/C2, TP1–TP4 | 0 violações |
| `wristband_discreto` (Variante B) | **nRF52810-QCAA QFN32** com topologia de referência Nordic Fig. 146: rede RF de 2 elementos (C3 0,8 pF shunt + L1 3,9 nH série), ladder DC/DC (DCC→L2 10 µH→L3 15 nH→DEC4 + C10 1,0 µF), cristal 32 MHz CL=8 pF com 2×12 pF, desacoplos completos | 0 violações |
| `gateway_esp32` | Carrier para **ESP32-DevKitC-32E** (soquete 2×19, entrada 5 V, EN com pull-up 10 k + botão) | 0 violações |

Libs customizadas em `hardware/kicad/libs/` (`nibas_wristband`, `nibas_gateway`): símbolo NTAG213 inlay, footprint Keystone 1059 (SMT, dims UNVERIFIED — ver pendências), SHLD1 ferrite, J1 contato negativo, símbolo ESP32-DevKitC-32E. Receita completa de geração documentada em `docs/kicad10_recipe.md` (8 regras do parser descobertas empiricamente).

## 2.2 Correções da revisão cruzada (o anti-slop funcionando)

A verificação independente (sessões fresh, sem herdar artefatos anteriores como fonte de verdade) pegou erros reais antes que virassem hardware:

- **Pinout E73 errado na pesquisa**: a tabela original citava SWD nos pads 40/41 e nRESET no pad 33. Correto, confirmado em 4 fontes (datasheet oficial E73-2G4M04S1A, símbolo KiCad padrão, esquemático aprovado, manual rev 1.8): **SWDCLK=37, SWDIO=38, nRESET/P0.21=36, P0.18=33**.
- **Alucinação "VDD = pino 25 único" refutada**: o `datasheet_facts_nordic.md` §1.1 afirmava VDD=25 único, DEC4=31, DCC=32 e um "P0.29" que não existe no QFN32 — e ainda invertia o veredito ("pinagem do projeto é INCORRETA"). Refutado por 3 fontes independentes (PS v1.3 Tabela 114, DevZone #53125, símbolo KiCad `MCU_Nordic:nRF52810-QCxx`): **correto é VDD = 9/25/32; DEC4=30; DCC=31**. A pinagem do projeto estava certa; o facts file é que estava errado.
- **Topologia RF: Π de 4 elementos → 2 elementos**: a Fig. 146 do PS v1.3 (extraída vetor a vetor via PyMuPDF) mostra o casamento de referência como **ANT(19) → C3 0,8 pF shunt → L1 3,9 nH série → antena**. L3 15 nH pertence ao ladder DC/DC e C7 100 pF é desacoplo de DEC3 — nenhum dos dois está no caminho de RF. Esquema corrigido e confirmado na netlist as-built.
- **C8/DEC2/DEC3**: o projeto antigo amarrava DEC2+DEC3 com C8 100 nF único ("crítico"). A referência Nordic mostra **DEC3→100 pF, DEC2→posição N.C. (DNP), C8 100 nF no VDD**. Corrigido no esquema e no `designator_map.md`.
- **F1 (doc DEC/DCC da variante A)**: a pesquisa mandava conectar caps DEC e indutor de 10 µH externos ao módulo E73 — o manual oficial rev 1.8 §4.1 e o FAQ Ebyte confirmam que desacoplos e DC/DC são **internos ao módulo**; pads DEC/DCC ficam NC. Corrigido no doc.
- **24 correções visuais** aplicadas ao esquemático da variante B pela conferência do critic/vision (fios, labels, alinhamentos, anotações).

## 2.3 Verificação matemática independente: 27/27 vereditos

Recontagem do zero contra fontes primárias (PS v1.3 lido pino a pino, Energizer CR2032, Johanson, Ebyte, arduino-esp32):

- **21 CONFIRMADOS** (6 com ressalva): I_s 1,5 µA; t_a 3 ms conservador; CR2032 235 mAh nominal/180–200 úteis; TX default 0 dBm; FSPL(10 m)=60 dB; sensibilidade −96 dBm; margem de link ~10–11 dB (apertada); expoente n=2,5–4 + corpo 10–20 dB; assimetria ±6 dB (+58,5 %/−36,9 %); pinagem QFN32 completa; cristal CL=8 pF→2×12 pF; ladder DC/DC; ferrite NFC; EWMA α=0,2; unidades de scan ESP32; MDBT42Q=nRF52832 (incompatível com S112 — resolvido pelo E73); ANATEL por módulo (princípio); aritmética do orçamento (R$ 2.514,00 fecha).
- **4 DIVERGENTES — todos tratados**:
  1. **I_a 5,0 mA → 5,8 mA** (sistema com DC/DC, PS §5.2.1.2; 4,6 mA é pico do rádio): autonomia real = **1,66 anos com DC/DC** vs **0,96 ano em modo LDO** (perde a meta de 12 meses — o DC/DC é condição do resultado).
  2. **Topologia Π** não é a referência Nordic (corrigida para 2 elementos, ver §2.2).
  3. **C8/DEC2/DEC3** — corrigido conforme Fig. 146.
  4. **Mapeamento linear de bateria 3,0→2,0 V** — a curva da CR2032 é plana; o mapa linear lê ~80–90 % durante quase toda a vida. Aceitável só como limiar "ok/fraca"; recomendação: limiar (<2,5 V) + tendência.

## 2.4 Critic final

**ACCEPT**, com 13 resíduos classificados como **documental-cosméticos** (descriptions desatualizadas, citação de tabela divergente entre docs, gap de anotação #PWR0111, fios/labels duplicados sobrepostos, BOM raiz stale) — nenhum elétrico, nenhum bloqueia as fases seguintes. Cross-checks: variante B **10/10 tarefas OK** (~60 itens verificados); variante A + gateway **9/9 OK** (veredito DC/DC do E73: OK condicional, com fonte do fabricante).

---

# 3. SESSÃO 2 — Frentes A/B/C (plano `plano_frentes_A_B_C`)

## 3.A) Layouts PCB ×3

**Abordagem**: script Python via API `pcbnew` (primário) com `tools/board_builder.py` como módulo compartilhado; fallback textual provado no spike. Regra do ambiente: nunca invocar o binário GUI — só `kicad-cli` + `python3+pcbnew`. Comandos DRC/export validados e documentados em `docs/layout_approach.md` (nota: no KiCad 10, `pcb export pdf` exige `--layers`).

**Estado por placa:**

| Item | Discreta (Var. B, QFN32) | Módulo (Var. A, E73) | Gateway (carrier DevKitC) |
|---|---|---|---|
| Edge.Cuts | círculo r=16,000 exato | círculo r=16,000 exato | retângulo 60,00×32,00 exato |
| DRC error | 27 | 26 | **0** |
| Composição | 12 courtyards_overlap (7 envolvem BT1/Keystone 1059 UNVERIFIED) · 8 copper_edge_clearance · 6 clearance · 1 mask | 11 copper_edge_clearance (10 pads físicos do E73 na periferia + 1 resíduo ~0,02 mm) · 6 clearance · 5 courtyards (BT1×U1 — física do Ø32) · 4 mask | — |
| Unconnected | 22 (13 rotas de sinal + 9 GND sem stitch) | **0** (punch list fechada) | **0** |
| Parity | 0 | 0 | 0 |
| Curtos | 0 | 0 | 0 |
| Veredito da auditoria | REPROVADO (estado da auditoria; board regenerado depois) | REPROVADO → punch list FECHADA (restam só erros de física documentada) | APROVADO COM PENDÊNCIAS |

**Keepouts de antena** (valor + fonte): Discreta — canto NE do disco, ~3 mm de margem da Johanson (regra no gerador, sem zona nativa); Módulo — extremidade oeste (NOTA 4 do esquemático, y_local < −8,85 mm), zona nativa presente e confirmada com 0 cobre; Gateway — extremidade leste (antena PCB do DevKitC), 0 cobre verificado nas duas camadas.

**Bugs pegos pelas auditorias (e corrigidos):**

- **Círculo r=130,6 mm ×2**: `SetCenter()` sem `SetEnd()` fazia o raio virar ~130,6 mm em vez de 16 mm (detectado na auditoria da variante B; o mesmo bug existia em potencial no gerador da variante B — padrão de correção `SetCenter`+`SetEnd` portado do `gen_board_modulo.py`). As 3 placas ativas têm Edge.Cuts verificado.
- **Duplo-flip J1**: na variante B, `FLIP_REFS` aplicou ao SHLD1 mas não ao J1 (contato negativo ficou em F.Cu em vez do verso).
- **Pads `<no net>`**: na variante A, ilha VDD_BAT do BT1 colidia com pads sem-net do U1 (mesma causa: sobreposição física BT1×U1).
- **Obstáculos de via**: stitches GND bloqueados por pads/vias vizinhos — resolvido na variante A com offsets 0,6–0,9 mm × 8 direções; na variante B, 9 pads GND seguem sem via.

## 3.B) Firmware

**6 bugs corrigidos** (arquivos permitidos: `firmware/main.c` e `gateway_esp32/gateway_esp32.ino`):

| Bug | Correção |
|---|---|
| B1 | Leitura de bateria real via SAADC (canal 0 = VDD, gain 1/6, ref 0,6 V, oversample 4×, burst) — fim do placeholder `vbat=3.0f` |
| B2 | Símbolos não declarados: `ram_start`, `m_adv_handle`, `APP_BLE_CONN_CFG_TAG` |
| B3 | Bloco CONFIG separado no `.ino` com TODO de provisioning via Preferences/NVS |
| B4 | `connectWiFi()`/`connectMQTT()` com timeout de 15 s (`millis()`) — não travam mais o boot |
| B5 | Filtro de Company ID implementado de verdade (`EXPECTED_COMPANY_ID = 0xFFFF`, little-endian, descarta advertiser desconhecido) |
| B6 | Rate-limit por tag usando `PUBLISH_PERIOD_MS` (antes: publish imediato por pacote) |

Mais 2 fixes de build: cast explícito no `mqttClient.publish` (evita overload com flag retained) e correção do índice mínimo do manufacturer data (6 bytes, não 5).

**Registro honesto de compilação**: ESP32 **compila** (arduino-cli, core esp32, partition scheme huge_app); nRF52810 **não compilável localmente** (sem `arm-none-eabi-gcc`, sem nRF5 SDK 17, sem Makefile/sdk_config — `main.c` é esqueleto de referência por declaração própria).

**Punch list pré-integração (nRF)**: a chamada `sd_ble_gap_adv_data_set` (main.c:128) é da API antiga do SoftDevice — no SDK 17 o correto é `sd_ble_gap_adv_set_configure`; demais itens menores listados na seção 4.

## 3.C) GitHub

- Remote `origin` = `https://github.com/forg3/NibasRockBar.git`; `gh` autenticado como `forg3` (keyring, escopo repo+workflow) → push funcionará.
- `main` sincronizada com origin em `6ff2dfc` (0/0).
- Trabalho pendente de commit: dirty = `.bob/`, `.opencode/`, `hardware/` + modificações em `firmware/main.c` e `gateway_esp32/gateway_esp32.ino`. `.gitignore` já cobre `.env`/`*.env` (sem risco de credenciais Deli). Convenção: commits em inglês, 2 commits (hardware; firmware).

---

# 4. Pendências consolidadas

| # | Item | Impacto | O que precisa para resolver |
|---|---|---|---|
| 1 | **Keystone 1059 UNVERIFIED** | 7 dos 12 courtyards_overlap da variante B podem ser falsos positivos (footprint custom com dims não conferidas) | Baixar o drawing oficial do site Keystone → conferir/corrigir o footprint `nibas_wristband:Keystone_1059_CR2032_SMT` |
| 2 | **DC/DC no E73-2G4M04S1A** | Se não houver indutor interno, habilitar DC/DC degrada o rail de 1,3 V; sem DC/DC a autonomia cai de 1,66 a → 0,96 a | Confirmar em 1 linha com o suporte Ebyte (service@cdebyte.com) que o 1A tem o indutor DC/DC interno (a confirmação atual é por família, via FAQ do 1B) |
| 3 | **ANATEL do módulo** | Bloqueia operação comercial com público (não bloqueia bancada/laboratório) | Consulta na base pública ANATEL / suporte Ebyte — certificado do E73 não localizado online |
| 4 | **nRF não compilável** | Impossível validar firmware da pulseira antes da bancada | Instalar `arm-none-eabi-gcc` + nRF5 SDK 17 + Makefile/sdk_config (ou portar); corrigir `sd_ble_gap_adv_data_set` → `sd_ble_gap_adv_set_configure` |
| 5 | **Discreta: 13 rotas de sinal pendentes** + 9 GND sem stitch | Placa não fabricável no estado atual | Re-placement dos passivos (afastar caps do muro de pads do U1) e regenerar, ou acabamento manual no GUI KiCad 10 com o roteador interativo |
| 6 | **Módulo: E73 não cabe no Ø32** | Pads U1.15/16/27/28 ficam a r=16,24–16,86 mm (fora do disco); BT1×U1 sobrepostos | Decisão de projeto: cápsula maior / módulo menor (checar variantes da família E73) / aceitar overhang na borda |
| 7 | **Gateway: soquete errado** | Fileiras a 2,54 mm vs 27,94 mm reais do DevKitC-32E — o DevKit físico NÃO encaixa | Trocar para footprint custom `ESP32-DevKitC-32E_Carrier` (2× soquete fêmea 1x19 a 27,94 mm) e regenerar antes de fabricar |
| 8 | **RF: tuning em bancada** | Matching final (C3/L1) só se fecha com medição real na placa física | VNA na variante B; ajustar S11 da rede de casamento |
| 9 | **STEP sem corpos 3D** | Conferência visual 3D não mostra componentes | Instalar `kicad-packages3d` (o export STEP funciona, mas só com cobre/board/pads) |
| 10 | **Firmware menor** | Qualidade/compatibilidade | `StaticJsonDocument` deprecated (usar `JsonDocument`); `APP_ERROR_CHECK` faltantes em `app_timer_create/start` |

---

# 5. Próxima sessão (checklist ordenado por prioridade)

1. **Acabamento manual dos layouts no GUI KiCad 10** — variante B: re-placement dos passivos + 13 rotas + 9 stitches GND; variante A: rerotear os 11 copper_edge_clearance (ou aceitar os físicos); gateway: afastar vias de stitch dos PTHs (13 warnings hole_to_hole).
2. **Decisão física Ø32 da variante A** — cápsula maior / módulo menor / overhang (pads fora do disco hoje).
3. **Footprints**: conferir/corrigir Keystone 1059 (drawing oficial) + trocar soquete do gateway para `ESP32-DevKitC-32E_Carrier` (27,94 mm).
4. **Toolchain nRF** — instalar `arm-none-eabi-gcc` + SDK 17 + Makefile/sdk_config; corrigir `sd_ble_gap_adv_set_configure`; integrar `main.c` a projeto real (pca10040e/blank + S112).
5. **Pedidos de fabricação (JLCPCB/PCBWay)** — só após DRC 0 violações error nas 3 placas; incluir cotação formal.
6. **Bancada** — VNA para tuning RF da variante B; confirmar DC/DC do E73 com suporte Ebyte; consulta ANATEL.

---

# 6. Como verificar tudo

**Artefatos por placa** (padrão: `hardware/kicad/<placa>/`):

- Esquemático: `<placa>.kicad_sch` + `<placa>.kicad_pro`; exports em `exports/`: `<placa>.net` (netlist), `<placa>.pdf` (esquemático), `erc_report.json`, `<placa>_layout.pdf`, `<placa>_layout.step`, `drc_<placa>.json`, `drc_tracks_<placa>.json`, `audit.md` (auditoria independente).
- Boards: `wristband_discreto.kicad_pcb`, `wristband_modulo.kicad_pcb`, `gateway_esp32.kicad_pcb` (autocontidos — footprints embutidos; abrem direto no GUI KiCad 10).

**Comandos de re-verificação (KiCad 10.0.6):**

```bash
# ERC do esquemático
kicad-cli sch erc --format json --severity-all \
  -o <placa>/exports/erc_recheck.json <placa>/<placa>.kicad_sch

# Netlist
kicad-cli sch export netlist -o <placa>/exports/<placa>.net <placa>/<placa>.kicad_sch

# DRC do layout (0 violações error = alvo)
kicad-cli pcb drc <placa>/<placa>.kicad_pcb --schematic-parity --refill-zones \
  --severity-error --format json --output <placa>/exports/drc_<placa>.json
kicad-cli pcb drc <placa>/<placa>.kicad_pcb --all-track-errors \
  --format json --output <placa>/exports/drc_tracks_<placa>.json

# Exports
kicad-cli pcb export pdf --layers F.Cu,B.Cu,Edge.Cuts,F.SilkS,B.SilkS,F.Mask,B.Mask \
  --output <placa>/exports/<placa>_layout.pdf <placa>/<placa>.kicad_pcb
kicad-cli pcb export step --output <placa>/exports/<placa>_layout.step <placa>/<placa>.kicad_pcb
```

**Regenerar boards do zero (idempotente):**

```bash
python3 hardware/kicad/wristband_discreto/gen_board_v2.py
python3 hardware/kicad/wristband_modulo/gen_board_modulo.py
python3 hardware/kicad/gateway_esp32/gen_board_gateway.py
python3 hardware/kicad/tools/board_builder.py --selftest   # sanity da API pcbnew
```

**Documentação de referência** (`hardware/kicad/docs/`): `designator_map.md` (ground truth de designators/pinos), `kicad10_recipe.md` (receita de geração de esquemáticos), `layout_approach.md` (API pcbnew + comandos validados), `layout_status.md` (estado dos layouts), `pesquisa_modulo_ble.md`, `pesquisa_gateway_esp32.md`, `datasheet_facts_nordic.md`, `verificacao_matematica.md`, `crosscheck_varianteB.md`, `crosscheck_varianteA_gateway.md`.

**Firmware:** `firmware/main.c` (nRF52810/S112 — esqueleto de referência), `gateway_esp32/gateway_esp32.ino` (compila com arduino-cli + core esp32, huge_app).

---

*Relatório gerado em 2026-09-09 a partir dos artefatos commitados em `hardware/kicad/docs/`, `exports/audit.md` ×3, `.bob/plans/*.md`, código de firmware e histórico git.*
