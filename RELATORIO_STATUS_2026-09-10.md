---
title: "2º Relatório de Status do Projeto"
subtitle: "NibasRockBar — Smart Badge Pub (pulseira NFC+BLE + gateway ESP32)"
date: "10 de setembro de 2026"
lang: pt-BR
---

# 1. Contexto e base deste relatório

Este é o 2º relatório de status. Cobre o delta desde o `RELATORIO_TRABALHO_2026-09-09`
(sessões de esquemáticos + layouts + firmware + GitHub).

**Fontes lidas para este relatório:**

- `hardware/kicad/docs/layout_status.md`
- `hardware/kicad/docs/decisao_forma_fisica.md`
- `hardware/kicad/docs/cotacao_fabricacao.md`
- `hardware/kicad/docs/procedimento_vna.md`
- `hardware/kicad/wristband_discreto/exports/audit.md`
- `hardware/kicad/wristband_modulo/exports/audit.md`
- `hardware/kicad/gateway_esp32/exports/audit.md`
- `git log` (HEAD = `d4b8bd6`, sincronizado com `origin/main`; ~50 arquivos modificados/novos no working tree, ainda não commitados)
- JSONs de DRC atuais no working tree (`exports/drc_*.json`), footprints em `hardware/kicad/libs/`, `firmware/nrf/armgcc/_build/`, pacotes `exports/fab/`

**Decisões de negócio seguem fechadas:** sem self-service (garçom tira o pedido, equipe serve tudo);
pulseira só identifica e localiza; Deli é o sistema de registro/pagamento/fiscal; checkout automático
apenas por polling de `saleState` (o projeto nunca fecha comanda por conta própria).

---

# 2. Decisão física: E73 → Fanstel BM832A

**Decidido** (`docs/decisao_forma_fisica.md`, 2026-09-09). A variante A troca o módulo
Ebyte E73-2G4M04S-52810 (17,5 × 28,7 mm, diagonal ≈ 33,5 mm) pelo **Fanstel BM832A**
(nRF52810, **10,2 × 15 × 1,9 mm**, diagonal ≈ 18,2 mm, US$ 3,61 vs US$ 3,59 — paridade de preço).

Por que:

1. **Sem cápsula Ø34–38 no mercado.** Não existe cápsula vazia IP67 redonda Ø34–38 mm à venda.
   O que existe são beacons prontos (Trax10214 Ø35,9 mm; Minew B10 Ø38 mm; Minew E7 Ø39 × 15,5 mm
   IP67 — menor cápsula comprovada, para CR2477). Aumentar a cápsula além de Ø32 mm exigiria
   moldagem custom (ferramental + NRE), inviável para protótipo de 5 unidades.
   Fontes: beacontrax.com, minew.com, takachi-enclosure.com.
2. **Overhang castelado refutado.** JLCPCB e PCBWay exigem furo PTH bissecado pelo contorno +
   pad com extensão ≥ 0,5 mm para dentro do contorno. Os pads das pontas do E73 ficariam fora do
   arco do disco (sagitta ≈ 1,65 mm) — viola a regra nas duas casas. Manter o E73 com overhang
   **não é fabricável**.
3. **BM832A encaixa, custa igual, zero migração de firmware.** Mesmo SoC nRF52810 → SoftDevice S112
   funciona direto. VDD 1,7–3,6 V (CR2032 ok). Antena integrada + certificações FCC/CE/TELEC.
   **Indutores do DC/DC integrados ao módulo** (página oficial Fanstel) — fecha o item aberto #2
   do relatório anterior (dúvida do indutor interno do E73-2G4M04S1A).

**Ressalva honesta (registrada no doc):** diagonal caber no disco não significa layout fechado.
O keepout de antena do BM832A (antena estendida fora do ground plane — verificar dimensões exatas
no manual Fanstel) e a coexistência com BT1 (porta-pilha CR2032) e TAG1 (NTAG213) precisam de
validação geométrica no KiCad antes de considerar a placa resolvida. Impacto previsto: novo
símbolo + footprint do BM832A (transcritos do datasheet Fanstel), troca de U1 no `.kicad_sch`
da variante A, re-layout da placa.

---

# 3. Footprints corrigidos

## 3.1 Porta-pilha: Keystone 1060 (não 1059)

O footprint antigo `Keystone_1059_CR2032_SMT` foi **removido** — e com motivo: **Keystone 1059 é a
variante THM**; a variante SMT correta é a **Keystone 1060** (série Vibra-Fit, low-profile para
CR2032/CR2025). Novo footprint `Keystone_1060_CR2032_SMT` com dimensões do **drawing oficial
Keystone 1060 rev C** (`https://www.keyelco.com/product-pdf.cfm?p=726`, registrado no campo
Datasheet do footprint): pads de montagem 11,00 × 7,01 mm no centro + abas de 2,59 × 3,61 mm,
centros das abas a ±14,655 mm (29,31 mm centro a centro); corpo 28,40 × 22,00 mm, altura 5,51 mm.
Fecha a pendência #1 do relatório anterior (footprint UNVERIFIED causador de 7 dos 12
`courtyards_overlap` da variante B).

## 3.2 Carrier do gateway: ESP32-DevKitC-32E a 27,94 mm

Novo footprint `ESP32-DevKitC-32E_Carrier` em `nibas_gateway.pretty`: dois soquetes fêmea 1×19
para os headers J2/J3, com **27,94 mm entre fileiras** (largura real do módulo DevKitC-32E,
conforme esquemático oficial Espressif DevKitC V4). Fecha a pendência #7 do relatório anterior
(o board antigo usava `PinHeader_2x19` com 2,54 mm entre fileiras — o DevKitC físico não encaixava).
Nota: o esquemático e a lib já apontam para a carrier (módulo 55 × 28); a migração do board
exigiu redimensionamento (ver §4).

---

# 4. Layouts: estado final

Comandos de re-verificação (KiCad 10.0.6): `kicad-cli pcb drc <board>.kicad_pcb
--schematic-parity --refill-zones --severity-error --format json` e `--all-track-errors`.
Números abaixo lidos dos JSONs atuais no working tree.

| Item | Discreta (Var. B, QFN32) | Módulo (Var. A, BM832A) | Gateway (carrier DevKitC) |
|---|---|---|---|
| Edge.Cuts | círculo r=16,000 exato | círculo r=16,000 exato | retângulo **62×36** exato (era 60×32) |
| DRC `--severity-error` | **2 físicos** (`copper_edge_clearance`) — restante do JSON é silk cosmético (16 `silk_overlap` + 16 `silk_over_copper` + 5 `silk_edge_clearance`); era 27 | **28 físicos** (13 `clearance` + 12 `solder_mask_bridge` + 2 `copper_edge_clearance` + 1 `courtyards_overlap`) | **0** |
| Unconnected | **16** (rotas de sinal + stitches GND pendentes) | **0** | **0** |
| Shorting / parity | 0 / 0 | 0 / 0 | 0 / 0 |
| Veredito | Não fabricável — acabamento manual pendente | Não fabricável isolado — física do Ø32 em decisão (ver §2 ressalva) | **Pronto isolado** (ver GATE §6) |

Leitura:

- **Discreta:** caiu de 27 errors/22 unconnected para **2 físicos/16 unconnected**. Os 9 GND sem
  stitch e as 13 rotas de sinal seguem exigindo re-placement dos passivos (afastar caps de
  decoupling/cristal do muro de pads do U1) ou acabamento manual no roteador interativo do
  KiCad 10. Keepout de antena (canto NE, margem ~3 mm da Johanson) segue como regra do gerador,
  sem zona nativa — edit manual não seria bloqueado.
- **Módulo:** 0 unconnected, 0 shorting, punch list de rotas fechada; os 28 errors são a física
  documentada do Ø32 + resíduos de solda/máscara a tratar no re-layout para o BM832A (footprint
  10,2 × 15 mm, bem menor que o E73 — a troca tende a reduzir esses errors, a confirmar no DRC
  do novo board).
- **Gateway:** 0 errors, 0 unconnected, 0 parity; warnings de furo (`hole_to_hole`/
  `holes_co_located`, 13 no estado auditado) fechados ao afastar as vias de stitch GND dos PTHs
  (offsets ≥ 1,6 mm, validação furo-a-furo ≥ 0,6 mm). Board redimensionado de 60×32 para **62×36**
  para acomodar a carrier 55×28 + J1/SW1/R1 sem sobreposição de courtyard.

---

# 5. Firmware e segurança

- **nRF52810 compila.** Toolchain instalada (`arm-none-eabi-gcc` + nRF5 SDK-style em `firmware/nrf/`):
  `firmware/nrf/armgcc/_build/nrf52810_xxaa.hex` gerado (≈ 105 KB, **~37 KB de aplicação**),
  SoftDevice **S112 7.2.0** (`firmware/nrf/softdevice/s112_nrf52_7.2.0_softdevice.hex`).
  Fecha a pendência #4 do relatório anterior ("nRF não compilável localmente"). Correções aplicadas:
  leitura real de bateria via SAADC (fim do placeholder `vbat=3.0f`), símbolos pendentes,
  filtro de Company ID (`0xFFFF`, little-endian), rate-limit por tag, timeouts de 15 s no Wi-Fi/MQTT
  do gateway, bloco CONFIG com TODO de provisioning via Preferences/NVS.
- **ESP32 compila** (arduino-cli + core esp32, partition scheme huge_app), incluindo as mudanças
  de segurança abaixo.
- **Segurança corrigida e pusheada (commit `d4b8bd6`, sincronizado com `origin/main`):**
  autenticação por API key no backend, suporte a credenciais MQTT (antes anônimo/aberto),
  validação de entradas, fim do eco de erro de upstream, cobertura de `.gitignore` (sem risco de
  credenciais Deli — `DELI_API_KEY`/`DELI_API_SECRET` seguem em variáveis de ambiente),
  higiene de dependências (`backend/requirements.txt`). Detalhes em `docs/security-audit/`
  (`relatorio-auditoria-seguranca.pdf` + `gerar_relatorio.py`).

---

# 6. Fabricação: pacotes prontos + cotação com GATE

- **Pacotes fab gerados** via `kicad-cli` (nunca GUI) em `exports/fab/` das 3 placas:
  Gerbers RS-274X (F.Cu, B.Cu, F.Mask, B.Mask, F.SilkS, B.SilkS, Edge.Cuts), Excellon + mapa de
  furos, `bom.csv`, `pos_jlc.csv` (centroide), `*-job.gbrjob`.
- **Cotação** (`docs/cotacao_fabricacao.md`, 2026-09-10, pesquisa web sem login, **nenhum pedido
  submetido**): 3 designs, 2L, ENIG, 5 peças por design. Pulseiras Ø32 0,8 mm; gateway 62×36
  1,6 mm. Estimativas: JLCPCB ~US$ 10–22 (PCBs) / total com 1 stencil + DHL ~US$ 31–69;
  PCBWay ~US$ 21–42 / total ~US$ 54–112. Custo dominante: ENIG + frete, não a placa nua.
  Valores são faixas — o número exato só sai na calculadora oficial com o Gerber anexado.
- **GATE de envio (regra: DRC 0 error E sem pendência física/roteamento):**

| Placa | GATE |
|---|---|
| Gateway 62×36 | [OK] **PRONTO PARA ENVIAR isoladamente** |
| Pulseira discreta | [NAO] NÃO ENVIAR — 2 físicos + 16 unconnected |
| Pulseira módulo | [NAO] NÃO ENVIAR — 28 errors de física + re-layout BM832A pendente |

  **Veredito do lote: LOTE NÃO PRONTO.** Opção: fabricar só o gateway (pedido isolado, 5 unid.)
  enquanto as pulseiras fecham layout — decisão do responsável. **Nada foi enviado**: sem conta,
  sem upload, sem checkout. Antes de qualquer upload: re-rodar DRC 0-error no board final,
  conferir soquete 27,94 mm e dimensão 62×36, revisão visual dos Gerbers.

---

# 7. Verificações

- **DC/DC do BM832A: OK.** Indutores do DC/DC integrados ao módulo (fonte: página oficial
  Fanstel). Sem o DC/DC a autonomia cairia de 1,66 ano para 0,96 ano (cálculo verificado no
  relatório anterior, PS §5.2.1.2) — com o BM832A o DC/DC é condição atendida, não aposta.
- **ANATEL: sem certificado localizado.** A base de consulta pública estava indisponível no dia
  (fora do ar); alternativa registrada: base Qlik / laboratório de homologação no Brasil.
  Status inalterado e honesto: bloqueia operação comercial com público, **não bloqueia
  bancada/laboratório**. Usar módulo certificado mantém o enquadramento como equipamento derivado
  (processo mais simples que homologar design discreto próprio).
- **Procedimento VNA** (`docs/procedimento_vna.md`, rev A): tuning da rede de 2 elementos da
  variante B (C3 0,8 pF shunt + L1 3,9 nH série, ref. Nordic PS v1.3 Fig. 146) com placa de
  sacrifício, bateria + ferrite presentes, critério S11 < −9,5 dB (VSWR < 2) em 2400–2480 MHz,
  tabela de registro + print do VNA no dossiê. L3 (15 nH) é do ladder DC/DC — não mexer.

---

# 8. O que falta (tabela honesta)

| # | Item | Estado | Próximo passo |
|---|---|---|---|
| 1 | Acabamento manual das rotas (discreta: 2 físicos + 16 unconn) | Aberto | Re-placement dos passivos + regenerar, ou roteador interativo no GUI KiCad 10; stitches GND C1/C2/C4–C9, U1.20/29, ANT1.2; rotas XC1/XC2, DEC1/3/4, DCC, SWDCLK/SWDIO, RESET |
| 2 | Re-layout da variante A para o BM832A no Ø32 | Aberto | Novo símbolo + footprint (datasheet Fanstel), troca de U1, re-layout; validar keepout de antena + coexistência BT1/TAG1 geometricamente; DRC até 0 error |
| 3 | Decisão Ø32 documentada | Feita (E73→BM832A) | Registrar no `designator_map.md`/BOM a troca de PN; manter alternativa descartada (cápsula Ø39 custom) fora do plano |
| 4 | Toolchain nRF | **Pronto** (compila, S112 7.2.0) | Integrar `main.c` ao projeto real (pca10040e/blank + S112); corrigir `sd_ble_gap_adv_data_set` → `sd_ble_gap_adv_set_configure`; `JsonDocument` no gateway; `APP_ERROR_CHECK` em `app_timer_create/start` |
| 5 | Gateway 62×36 | Pronto isolado | Decisão: pedido isolado agora vs. aguardar pulseiras; gerar pacote final + cotar na calculadora oficial |
| 6 | ANATEL | Aberto (sem certificado) | Re-tentar consulta pública; alternativa Qlik/laboratório; confirmar com Fanstel antes de operação com público |
| 7 | Bancada RF | Procedimento pronto, não executado | VNA na variante B após fabricação; ajustar S11 da rede C3/L1 |
| 8 | STEP sem corpos 3D | Aberto (cosmético) | Instalar `kicad-packages3d` se a conferência visual exigir |

---

# 9. Histórico git (evidência)

- `d4b8bd6` (2026-09-10) — segurança backend/gateway, **pusheado** (`origin/main` sincronizada)
- `77ed5e1` (2026-09-09) — bugs de firmware (SAADC, timeouts, Company ID, rate-limit)
- `beab01e` (2026-09-09) — esquemáticos, layouts, docs de verificação + 1º relatório
- Working tree atual: ~50 arquivos modificados/novos (footprints Keystone 1060 + BM832A + carrier,
  re-layouts, DRC JSONs, pacotes `fab/`, docs de decisão/cotação/VNA, `firmware/nrf/`,
  `docs/security-audit/`) — **ainda não commitados** no momento deste relatório.

---

# 10. Como verificar tudo

```bash
# DRC (0 error = alvo)
kicad-cli pcb drc <placa>/<placa>.kicad_pcb --schematic-parity --refill-zones \
  --severity-error --format json --output <placa>/exports/drc_<placa>.json
kicad-cli pcb drc <placa>/<placa>.kicad_pcb --all-track-errors \
  --format json --output <placa>/exports/drc_tracks_<placa>.json

# Regenerar boards (idempotente)
python3 hardware/kicad/wristband_discreto/gen_board_v2.py
python3 hardware/kicad/wristband_modulo/gen_board_modulo.py
python3 hardware/kicad/gateway_esp32/gen_board_gateway.py

# Firmware nRF
ls firmware/nrf/armgcc/_build/nrf52810_xxaa.hex firmware/nrf/softdevice/s112_nrf52_7.2.0_softdevice.hex
```

*Relatório gerado em 2026-09-10 a partir de `hardware/kicad/docs/`, `exports/audit.md` ×3,
DRC JSONs atuais, footprints, `firmware/nrf/`, `docs/security-audit/` e histórico git.*
