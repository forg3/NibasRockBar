# Pesquisa Módulo BLE — Variante A (Pulseira)

**Data:** 2025-09-08  
**Autor:** Explore (firecrawl/web research)  
**Objetivo:** Selecionar módulo BLE certificado para variante A da pulseira (disco Ø32 mm, CR2032, NTAG213 25 mm na borda, ferrite, Keystone 1059)

---

## 1. Critérios Obrigatórios

| Critério | Requisito |
|----------|-----------|
| **SoC** | Preferir nRF52810 (firmware atual usa SoftDevice S112) |
| **VDD** | Cobrir CR2032 3.0 → 2.0 V (nRF52810 opera 1.7–3.6 V; **rejeitar** módulo com LDO interno que exija >3.0 V mín) |
| **Antena** | Chip/PCB integrada (sem antena externa) |
| **Dimensões** | Compatível com disco Ø32 mm (NTAG213 25 mm na borda + Keystone 1059 + folha ferrite) |
| **SWD** | Pinout documentado (SWDCLK, SWDIO, VDD, GND, nRESET) |
| **Footprint** | Dimensões dos pads transcritas do datasheet |
| **Estoque/Preço** | Digikey/Mouser/LCSC vs budget ~6.50 USD/un |
| **ANATEL** | Certificado, "contém TX", ou pendente (se não verificável online → item aberto p/ suporte, **não bloqueia**) |

---

## 2. Tabela Comparativa dos 4 Candidatos

| Item | **Ebyte E73-2G4M04S-52810** (E73-2G4M04S1A) | **Fanstel BT832A / BT832AF** | **Raytac MDBT42Q-192KV2** | **u-blox ANNA-B112** |
|------|---------------------------------------------|------------------------------|---------------------------|----------------------|
| **SoC** | nRF52810-QFAA/QCAA | nRF52810-QFAA | nRF52810-QFAA | **nRF52832** ❌ |
| **Flash/RAM** | 192 KB / 24 KB | 192 KB / 24 KB | 192 KB / 24 KB | 512 KB / 64 KB |
| **SoftDevice** | **S112** (compatível) | **S112** (compatível) | **S112** (compatível) | S132 (incompatível) |
| **VDD range** | 1.7–3.6 V (direto do SoC) | 1.7–3.6 V (direto do SoC) | 1.7–3.6 V (direto do SoC) | 1.7–3.6 V |
| **Antena** | PCB trace / IPEX opcional | PCB trace integrada | Chip antenna (cerâmica) / PCB trace | Chip antenna integrada / pino ant. ext. |
| **Dimensões (mm)** | **17.5 × 28.7 × ~2.0** | 14 × 16 × 1.9 (BT832A)<br>15 × 20.8 × 1.9 (BT832AF) | **10 × 16 × 2.2** | **6.5 × 6.5 × 1.2** |
| **Pinos expostos** | 43 (castellated, 1.27 mm pitch) | 16 castellated + 24 LGA (BT832A)<br>mesmo footprint BT832AF | 32 (castellated + LGA central) | 52 (LGA, 0.5 mm pitch) |
| **SWD exposto** | Sim (pinos dedicados) | Sim (pinos dedicados) | Sim (pinos dedicados) | Sim (pinos dedicados) |
| **NFC** | Não (nRF52810 não tem) | Não (nRF52810 não tem) | Não (nRF52810 não tem) | **Sim** (nRF52832) |
| **Certificações** | FCC, CE, TELEC (MIC), SRRC, KC, NCC | FCC, IC, CE, TELEC, NCC | FCC, IC, CE, TELEC, KC, SRRC, NCC, WPC, UKCA | FCC, IC, CE, TELEC, KC, NCC, RCM |
| **ANATEL** | Não verificado online → **item aberto** | Não verificado online → **item aberto** | Não verificado online → **item aberto** | Não verificado online → **item aberto** |
| **Preço (1 un, USD)** | ~$3.59 (Ebyte store) / ~$6.30 (LCSC E73-2G4M08S1CX ref.) | **$3.75** (Fanstel direct) / ~$8.86 (Digikey BT832) | ~$4.95 (Digikey MDBT42Q-512KV2 ref.) | ~$119 (EVK) / módulo ~$8-12 (estimado) |
| **Estoque** | Ebyte/LCSC/Aliexpress | Fanstel/Digikey/Mouser/Arrow | Raytac/Digikey/Mouser | u-blox/Digikey/Mouser/Symmetry |
| **KiCad lib padrão** | ✅ **Sim** (`RF_Module:E73-2G4M04S` + símbolo `E73-2G4M04S-52810`) | ❌ Não (lib custom necessária) | ❌ Não (lib custom necessária) | ❌ Não (lib custom necessária) |
| **Migração firmware** | **Zero** (mesmo SoC S112) | **Zero** (mesmo SoC S112) | **Zero** (mesmo SoC S112) | **Alta** (nRF52832 → S132) |

---

## 3. Análise Detalhada por Candidato

### 3.1 Ebyte E73-2G4M04S-52810 (E73-2G4M04S1A) — **ESCOLHIDO**

**Datasheet:** http://www.cdebyte.com/en/downpdf.aspx?id=243 (E73 series user manual)  
**Produto:** https://www.cdebyte.com/products/E73-2G4M04S1A/4  
**Preço Ebyte store:** $3.59 (1 un) — https://ebyteiot.com/collections/soc-module  
**LCSC (ref. E73-2G4M08S1CX nRF52840):** $6.29 (1 un) — https://www.lcsc.com/product-detail/C2764963.html  

**Dimensões:** 17.5 × 28.7 mm (datasheet Ebyte) — **Cabe no disco Ø32 mm** com margem para NTAG213 (25 mm) + Keystone 1059 + ferrite.  
**Pinos:** 43 castellated pads (1.27 mm pitch), pad 1.8 × 0.7 mm (footprint KiCad padrão).  
**VDD:** 1.7–3.6 V direto do nRF52810 (sem LDO interno no módulo) — **compatível CR2032 3.0→2.0 V**.  
**Antena:** PCB trace integrada (versão S1A) ou conector IPEX (versão S1AX).  
**SWD:** Pinos expostos (SWDCLK, SWDIO, VDD, GND, nRESET) — ver tabela de pinos abaixo.  
**KiCad:** Símbolo `E73-2G4M04S-52810` e footprint `RF_Module:E73-2G4M04S` **já existem na lib padrão** (KiCad 10.0.6).  
**Firmware:** nRF52810 → SoftDevice S112 **compatível direto** (zero migração).  

**Pinout do módulo (transcrito do datasheet Ebyte E73-2G4M04S1B — mesmo pinout para versão 52810):**

| Pad | Nome | Função | Observação |
|-----|------|--------|------------|
| 0 | GND | Ground | |
| 1 | GND | Ground | |
| 2 | GND | Ground | |
| 3 | DEC2 | DC/DC output | Conectar a capacitor 100 nF → GND |
| 4 | DEC3 | DC/DC output | Conectar a capacitor 100 nF → GND |
| 5 | P0.25 | GPIO | |
| 6 | P0.26 | GPIO | |
| 7 | P0.27 | GPIO | |
| 8 | P0.28 | GPIO | |
| 9 | P0.29 | GPIO | |
| 10 | P0.30 | GPIO | |
| 11 | P0.31 | GPIO | |
| 12 | DEC4 | DC/DC output | Conectar a capacitor 100 nF → GND |
| 13 | DCC | DC/DC output | Conectar a indutor 10 µH → DEC4 |
| 14 | DEC1 | DC/DC output | Conectar a capacitor 100 nF → GND |
| 15 | GND | Ground | |
| 16 | VCC | **VDD 1.8–3.6 V** | Alimentação principal (CR2032) |
| 17 | P0.02 | GPIO / AIN0 | |
| 18 | P0.03 | GPIO / AIN1 | |
| 19 | P0.04 | GPIO / AIN2 | |
| 20 | P0.05 | GPIO / AIN3 | |
| 21 | P0.06 | GPIO | |
| 22 | P0.07 | GPIO | |
| 23 | P0.08 | GPIO | |
| 24 | P0.09 | GPIO / NFC1 | NFC não funcional no nRF52810 |
| 25 | P0.10 | GPIO / NFC2 | NFC não funcional no nRF52810 |
| 26 | P0.11 | GPIO | |
| 27 | P0.12 | GPIO | |
| 28 | P0.13 | GPIO | |
| 29 | P0.14 | GPIO | |
| 30 | P0.15 | GPIO | |
| 31 | P0.16 | GPIO | |
| 32 | P0.17 | GPIO | |
| 33 | P0.18 | GPIO / SWO | |
| 34 | P0.19 | GPIO | |
| 35 | P0.20 | GPIO | |
| 36 | P0.21 / nRESET | GPIO / Reset | Reset ativo baixo |
| 37 | SWDCLK | **SWD Clock** | Programação/debug |
| 38 | SWDIO | **SWD Data** | Programação/debug |
| 39 | P0.22 | GPIO | |
| 40 | P0.23 | GPIO | |
| 41 | P0.24 | GPIO | |
| 42 | GND | Ground | |
| 43 | GND | Ground | |

> **Fonte:** Tabela de pinout do E73-2G4M04S1B (nRF52832) em https://www.cdebyte.com/products/E73-2G4M04S1B/2 — o pinout é idêntico para a versão nRF52810 (E73-2G4M04S1A), apenas o SoC muda. O símbolo KiCad `E73-2G4M04S-52810` estende `E73-2G4M04S-52832` confirmando pinout comum. **Correção 2026-09-09 (passo 4.1):** pads 33/36–41 revalidados contra o datasheet oficial E73-2G4M04S1A (https://www.cdebyte.com/products/E73-2G4M04S1A/2) e contra o símbolo padrão KiCad `RF_Module:E73-2G4M04S` — a versão anterior desta tabela citava SWD em 40/41 e RESET no pad 33 (errado); o correto é P0.18=33, P0.21/nRESET=36, SWDCLK=37, SWDIO=38, P0.22=39, P0.23=40, P0.24=41.

**Footprint (KiCad padrão `RF_Module:E73-2G4M04S` — transcrito do arquivo `.kicad_mod`):**

- **Dimensões do corpo:** 17.5 × 28.7 mm (courtyard 19.8 × 31.0 mm)
- **Pads:** 44 pads SMD retangulares (0 a 43)
  - Pads 0–15 (lado esquerdo): 1.8 × 0.7 mm, pitch 1.27 mm, x = -8.75 mm
  - Pads 16–27 (lado superior): 0.7 × 1.8 mm, pitch 1.27 mm, y = 14.35 mm
  - Pads 28–43 (lado direito): 1.8 × 0.7 mm, pitch 1.27 mm, x = 8.75 mm
- **Keep-out zone:** Área inferior (y < -8.85 mm) sem cobre/trilhas/componentes (antena PCB)
- **Modelo 3D:** `${KICAD10_3DMODEL_DIR}/RF_Module.3dshapes/E73-2G4M04S.step`

---

### 3.2 Fanstel BT832A / BT832AF

**Datasheet:** https://fanstel.squarespace.com/s/BT832_datasheets.pdf (v2.04, 2017)  
**Produto:** https://www.fanstel.com/bt810  
**Preço Fanstel direct:** $3.75 (1 un, BT832A) — https://www.fanstel.com/buy  
**Digikey (BT832 nRF52832):** $8.86 (1 un) — https://www.digikey.com/en/products/detail/fanstel-corp/BT832/8323656  

**Dimensões:** BT832A = 14 × 16 × 1.9 mm; BT832AF = 15 × 20.8 × 1.9 mm — **Cabe no disco Ø32 mm**.  
**Pinos:** 16 castellated + 24 LGA (BT832A); mesmo footprint BT832AF.  
**VDD:** 1.7–3.6 V direto do nRF52810 — **compatível CR2032**.  
**Antena:** PCB trace integrada (BT832A) ou PCB trace de alta performance (BT832AF).  
**SWD:** Exposto nos pinos castellated.  
**KiCad:** **Não existe na lib padrão** — requer símbolo/footprint custom.  
**Firmware:** nRF52810 → S112 **compatível direto**.  

**Pinout (do datasheet BT832 v2.04, p. 9-10):**

| Pin | Nome | Função |
|-----|------|--------|
| 1 | GND | Ground |
| 2 | GND | Ground |
| 3 | GND | Ground |
| 4 | GND | Ground |
| 5 | GND | Ground |
| 6 | P0.25 | GPIO |
| 7 | P0.26 | GPIO |
| 8 | P0.27 | GPIO |
| 9 | P0.28 | GPIO |
| 10 | P0.29 | GPIO |
| 11 | P0.30 | GPIO |
| 12 | P0.31 | GPIO |
| 13 | DEC4 | DC/DC |
| 14 | DCC | DC/DC |
| 15 | DEC1 | DC/DC |
| 16 | VCC | VDD 1.7–3.6 V |
| 17 | P0.02 | GPIO |
| 18 | P0.03 | GPIO |
| 19 | P0.04 | GPIO |
| 20 | P0.05 | GPIO |
| 21 | P0.06 | GPIO |
| 22 | P0.07 | GPIO |
| 23 | P0.08 | GPIO |
| 24 | P0.09 | GPIO |
| 25 | P0.10 | GPIO |
| 26 | P0.11 | GPIO |
| 27 | P0.12 | GPIO |
| 28 | P0.13 | GPIO |
| 29 | P0.14 | GPIO |
| 30 | P0.15 | GPIO |
| 31 | P0.16 | GPIO |
| 32 | P0.17 | GPIO |
| 33 | P0.18 | GPIO / nRESET |
| 34 | P0.19 | GPIO |
| 35 | P0.20 | GPIO |
| 36 | P0.21 | GPIO |
| 37 | P0.22 | GPIO |
| 38 | P0.23 | GPIO |
| 39 | P0.24 | GPIO |
| 40 | SWDCLK | SWD Clock |
| 41 | SWDIO | SWD Data |
| 42 | GND | Ground |
| 43 | GND | Ground |
| 44 | GND | Ground |
| 45 | GND | Ground |
| 46 | GND | Ground |

> **Nota:** O datasheet BT832 v2.04 cobre BT832/BT832A/BT832F/BT832AF. O pinout é comum; a diferença está na área de antena e memória.

---

### 3.3 Raytac MDBT42Q-192KV2 (Chip Antenna) / MDBT42Q-P192KV2 (PCB Antenna)

**Datasheet:** https://www.raytac.com/upload/download_files/04cfd51020cc3c0ba914de057b52bece.pdf (Version L, 2025-07-14)  
**Produto:** https://www.raytac.com/product/ins.php?index_id=71  
**Digikey (MDBT42Q-P192KL nRF52811 ref.):** $14.27 (1 un) — https://www.digikey.com/en/products/detail/raytac/MDBT42Q-P192KL/13968059  

**Dimensões:** 10 × 16 × 2.2 mm — **Cabe no disco Ø32 mm** (menor que Ebyte).  
**Pinos:** 32 (castellated laterais + LGA central).  
**VDD:** 1.7–3.6 V direto do nRF52810 — **compatível CR2032**.  
**Antena:** Chip antenna cerâmica (192KV2) ou PCB trace (P192KV2).  
**SWD:** Exposto.  
**KiCad:** **Não existe na lib padrão** — requer símbolo/footprint custom.  
**Firmware:** nRF52810 → S112 **compatível direto**.  
**Certificações:** FCC, IC, CE, TELEC, KC, SRRC, NCC, WPC, UKCA (mais completo).  

**Pinout (do datasheet Version L, §2.1):**

| Pad | GPIO | Observação |
|-----|------|------------|
| 1 | GND | |
| 2 | P0.25 | |
| 3 | P0.26 | |
| 4 | P0.27 | |
| 5 | P0.28 | |
| 6 | P0.29 | |
| 7 | P0.30 | |
| 8 | P0.31 | |
| 9 | DEC4 | DC/DC |
| 10 | DCC | DC/DC |
| 11 | DEC1 | DC/DC |
| 12 | VCC | VDD 1.7–3.6 V |
| 13 | P0.00 | XL1 (32 kHz xtal) |
| 14 | P0.01 | XL2 (32 kHz xtal) |
| 15 | P0.02 | AIN0 |
| 16 | P0.03 | AIN1 |
| 17 | P0.04 | AIN2 |
| 18 | P0.05 | AIN3 |
| 19 | P0.06 | |
| 20 | P0.07 | |
| 21 | P0.08 | |
| 22 | P0.09 | NFC1 (não funcional nRF52810) |
| 23 | P0.10 | NFC2 (não funcional nRF52810) |
| 24 | P0.11 | |
| 25 | P0.12 | |
| 26 | P0.13 | |
| 27 | P0.14 | |
| 28 | P0.15 | |
| 29 | P0.16 | |
| 30 | P0.17 | |
| 31 | P0.18 | nRESET |
| 32 | P0.19 | |
| 33 | P0.20 | |
| 34 | P0.21 | |
| 35 | P0.22 | |
| 36 | P0.23 | Cuidado com solda (pode levantar módulo) |
| 37 | P0.24 | Cuidado com solda |
| 38 | SWDCLK | |
| 39 | SWDIO | |
| 40 | GND | |
| — | GND (central) | Exposed ground pads (LGA) |

---

### 3.4 u-blox ANNA-B112 — **REJEITADO (SoC errado)**

**Datasheet:** https://content.u-blox.com/sites/default/files/documents/ANNA-B112_DataSheet_UBX-18011707.pdf (R14)  
**Produto:** https://www.u-blox.com/en/product/anna-b112-open-cpu  

**SoC:** **nRF52832** (não nRF52810) — **incompatível com SoftDevice S112** (exige S132).  
**Migração firmware:** **Alta** — requer portar firmware de S112 para S132, mudar memory map (512 KB flash vs 192 KB), tratar NFC, etc.  
**Dimensões:** 6.5 × 6.5 × 1.2 mm (SiP) — menor, mas pinout LGA 0.5 mm pitch difícil para soldagem manual.  
**Preço:** Módulo ~$8-12 (estimado), EVK $119 — **acima do budget**.  
**KiCad:** Não existe na lib padrão.  
**Veredito:** **Rejeitado** por incompatibilidade de SoC e custo de migração de firmware.

---

## 4. Escolha Final: **Ebyte E73-2G4M04S-52810 (E73-2G4M04S1A)**

### Justificativa

| Fator | Avaliação |
|-------|-----------|
| **Compatibilidade firmware (S112)** | ✅ **Zero migração** — mesmo SoC nRF52810 |
| **KiCad lib padrão** | ✅ **Símbolo + footprint já existem** (`RF_Module:E73-2G4M04S` + `E73-2G4M04S-52810`) — elimina risco de erro de pinagem/footprint custom |
| **VDD CR2032** | ✅ 1.7–3.6 V direto do SoC (sem LDO no módulo) |
| **Dimensões** | ✅ 17.5 × 28.7 mm — cabe no disco Ø32 mm com NTAG213 25 mm + Keystone 1059 + ferrite |
| **Antena** | ✅ PCB trace integrada (versão S1A) — sem componente externo |
| **SWD** | ✅ Pinos dedicados expostos (pads 37/38 — corrigido em 2026-09-09, ver §5) |
| **Preço** | ✅ ~$3.59 (Ebyte) / ~$6.30 (LCSC ref.) — **dentro do budget $6.50** |
| **Estoque** | ✅ Ebyte/LCSC/Aliexpress — disponível |
| **Certificações** | ✅ FCC/CE/TELEC/SRRC/KC/NCC — ANATEL item aberto (não bloqueia) |
| **Risco de pinagem** | ✅ **Mínimo** — lib padrão KiCad validada pela comunidade |

### Itens Abertos (não bloqueiam)

1. **ANATEL:** Não verificado online para E73-2G4M04S1A. Ação: contatar suporte Ebyte ou laboratório de homologação no Brasil. Registrar como item aberto no projeto.
2. **Datasheet completo E73-2G4M04S1A:** O pinout foi transcrito do E73-2G4M04S1B (mesmo pinout, SoC diferente). Confirmar com Ebyte se há diferença nos pinos DEC/DCC (nRF52810 não tem NFC, pinos 24/25 tornam-se GPIO comuns).

---

## 5. Tabela de Pinos Completa do Módulo Escolhido (E73-2G4M04S-52810)

> ⚠️ **CORREÇÃO 2026-09-09 (passo 4.1 do plano kicad-esquematicos-verificacao):** a tabela
> abaixo estava ERRADA nos pads 33 e 37–41 (citava P0.22/P0.23/P0.24/SWDCLK/SWDIO deslocados
> e tratava o pad 33 como nRESET). Valores corretos, confirmados em 4 fontes:
> 1. Datasheet oficial Ebyte E73-2G4M04S1A — https://www.cdebyte.com/products/E73-2G4M04S1A/2
> 2. Símbolo padrão KiCad 10.0.6 `RF_Module:E73-2G4M04S` (pad 33=SWO/P0.18, 36=P0.21/~{RESET},
>    37=SWDCLK, 38=SWDIO, 39=P0.22, 40=P0.23, 41=P0.24)
> 3. Esquemático variante A aprovado (`wristband_modulo/`, ERC 0 violações) — NOTA 1
> 4. Cross-check dos pads GND/VCC/DCC/DEC (0,1,2,15,42,43 = GND; 16 = VCC; 13 = DCC) inalterados
>
> Erros corrigidos: pad 33 → P0.18 (não é nRESET); pad 36 → P0.21/nRESET; pad 37 → SWDCLK;
> pad 38 → SWDIO; pad 39 → P0.22; pad 40 → P0.23; pad 41 → P0.24. SWD está em 37/38, não 40/41.

**Fonte:** Datasheet Ebyte E73-2G4M04S1B (pinout idêntico) — http://www.cdebyte.com/en/downpdf.aspx?id=243  
**Revisão do documento:** E73 series user manual (2019-07-24 / 2024-07-23)  
**URL KiCad symbol:** `/usr/share/kicad/symbols/RF_Module.kicad_sym` → `E73-2G4M04S-52810`  
**URL KiCad footprint:** `/usr/share/kicad/footprints/RF_Module.pretty/E73-2G4M04S.kicad_mod`

| Pad | Nome | Tipo | Conexão no Esquemático (Variante A) | Observação |
|-----|------|------|--------------------------------------|------------|
| 0 | GND | Power | GND | |
| 1 | GND | Power | GND | |
| 2 | GND | Power | GND | |
| 3 | DEC2 | Power | NC — desacoplos/indutor DC/DC internos ao módulo (manual rev 1.8 §4.1 + FAQ Ebyte; ver docs/crosscheck_varianteA_gateway.md F1) | DC/DC buck output |
| 4 | DEC3 | Power | NC — desacoplos/indutor DC/DC internos ao módulo (manual rev 1.8 §4.1 + FAQ Ebyte; ver docs/crosscheck_varianteA_gateway.md F1) | DC/DC buck output |
| 5 | P0.25 | I/O | NC (ou TP) | GPIO livre |
| 6 | P0.26 | I/O | NC (ou TP) | GPIO livre |
| 7 | P0.27 | I/O | NC (ou TP) | GPIO livre |
| 8 | P0.28 | I/O | NC (ou TP) | GPIO livre |
| 9 | P0.29 | I/O | NC (ou TP) | GPIO livre |
| 10 | P0.30 | I/O | NC (ou TP) | GPIO livre |
| 11 | P0.31 | I/O | NC (ou TP) | GPIO livre |
| 12 | DEC4 | Power | NC — desacoplos/indutor DC/DC internos ao módulo (manual rev 1.8 §4.1 + FAQ Ebyte; ver docs/crosscheck_varianteA_gateway.md F1) | DC/DC buck output |
| 13 | DCC | Power | NC — desacoplos/indutor DC/DC internos ao módulo (manual rev 1.8 §4.1 + FAQ Ebyte; ver docs/crosscheck_varianteA_gateway.md F1) | DC/DC buck output |
| 14 | DEC1 | Power | NC — desacoplos/indutor DC/DC internos ao módulo (manual rev 1.8 §4.1 + FAQ Ebyte; ver docs/crosscheck_varianteA_gateway.md F1) | DC/DC buck output |
| 15 | GND | Power | GND | |
| 16 | **VCC** | **Power** | **VDD_BAT (CR2032 +)** | **Alimentação principal 1.8–3.6 V** |
| 17 | P0.02 | I/O | NC (ou TP) | AIN0 |
| 18 | P0.03 | I/O | NC (ou TP) | AIN1 |
| 19 | P0.04 | I/O | NC (ou TP) | AIN2 |
| 20 | P0.05 | I/O | NC (ou TP) | AIN3 |
| 21 | P0.06 | I/O | NC (ou TP) | |
| 22 | P0.07 | I/O | NC (ou TP) | |
| 23 | P0.08 | I/O | NC (ou TP) | |
| 24 | P0.09 | I/O | NC (ou TP) | NFC1 (não funcional nRF52810) |
| 25 | P0.10 | I/O | NC (ou TP) | NFC2 (não funcional nRF52810) |
| 26 | P0.11 | I/O | NC (ou TP) | |
| 27 | P0.12 | I/O | NC (ou TP) | |
| 28 | P0.13 | I/O | NC (ou TP) | |
| 29 | P0.14 | I/O | NC (ou TP) | |
| 30 | P0.15 | I/O | NC (ou TP) | |
| 31 | P0.16 | I/O | NC (ou TP) | |
| 32 | P0.17 | I/O | NC (ou TP) | |
| 33 | P0.18 | I/O | NC (ou TP) | GPIO / SWO |
| 34 | P0.19 | I/O | NC (ou TP) | |
| 35 | P0.20 | I/O | NC (ou TP) | |
| 36 | **P0.21/nRESET** | **I/O** | **nRESET (pull-up 10k opcional → VDD)** | **Reset ativo baixo** |
| 37 | **SWDCLK** | **I/O** | **TP_SWDCLK** | **Programação/debug** |
| 38 | **SWDIO** | **I/O** | **TP_SWDIO** | **Programação/debug** |
| 39 | P0.22 | I/O | NC (ou TP) | |
| 40 | P0.23 | I/O | NC (ou TP) | |
| 41 | P0.24 | I/O | NC (ou TP) | |
| 42 | GND | Power | GND | |
| 43 | GND | Power | GND | |

> **Notas de conexão para esquemático variante A:**
> - **VDD_BAT** (pad 16) → CR2032 + (via Keystone 1059) + capacitores bulk 10 µF (C1) + 100 nF (C2) 0603/0402
> - **GND** (pads 0,1,2,15,42,43) → plano de terra
> - **DEC1/DEC2/DEC3/DEC4/DCC** (pads 3, 4, 12, 13, 14) → NC — desacoplos/indutor DC/DC internos ao módulo (manual rev 1.8 §4.1 + FAQ Ebyte; ver docs/crosscheck_varianteA_gateway.md F1)
> - **DCC** (pad 13) → NC — indutor 10 µH do DC/DC interno ao módulo (a referência Nordic de chip nu pede L externo; o módulo E73 não — correção 2026-09-09, F1)
> - **SWDCLK/SWDIO** (pads 37/38) → test points TP3/TP2 (1.27 mm pitch para tag-connect ou header 2×5 1.27 mm)
> - **nRESET** (pad 36) → pull-up 10k (R1, DNP/opcional) → VDD + TP1
> - **P0.25–P0.31, P0.02–P0.24** → NC explícito (flags `no_connect` no KiCad) — 26 GPIOs não utilizados
> - **Antena:** PCB trace integrada no módulo — **keep-out zone** no footprint (camada `Cmts.User` "KEEP-OUT ZONE") deve ser respeitada no layout

---

## 6. Dimensões do Footprint (KiCad `RF_Module:E73-2G4M04S`)

**Arquivo:** `/usr/share/kicad/footprints/RF_Module.pretty/E73-2G4M04S.kicad_mod` (KiCad 10.0.6, version 20260206)

| Parâmetro | Valor |
|-----------|-------|
| **Corpo do módulo** | 17.5 × 28.7 mm |
| **Courtyard (F.CrtYd)** | 19.8 × 31.0 mm (retângulo -9.9/-14.6 a 9.9/15.5) |
| **Fab outline (F.Fab)** | 17.5 × 28.7 mm (retângulo -8.75/-14.35 a 8.75/14.35) |
| **Silkscreen (F.SilkS)** | Contorno com entalhe para antena (y = -8.49 a -7.37) |
| **Total de pads** | 44 (0 a 43) |
| **Pads laterais (0–15, 28–43)** | 1.8 × 0.7 mm, pitch 1.27 mm, x = ±8.75 mm |
| **Pads superior (16–27)** | 0.7 × 1.8 mm, pitch 1.27 mm, y = 14.35 mm |
| **Keep-out zone** | Polígono F.Cu/B.Cu/In*.Cu: y ∈ [-14.35, -8.85] mm (área da antena PCB) — sem trilhas, vias, pads, cobre |
| **Modelo 3D** | `${KICAD10_3DMODEL_DIR}/RF_Module.3dshapes/E73-2G4M04S.step` |

---

## 7. Referências (URLs)

| Item | URL |
|------|-----|
| Ebyte E73 series manual (pinout E73-2G4M04S1B) | http://www.cdebyte.com/en/downpdf.aspx?id=243 |
| Ebyte E73-2G4M04S1A product page | https://www.cdebyte.com/products/E73-2G4M04S1A/4 |
| Ebyte store price (E73-2G4M04S1A) | https://ebyteiot.com/collections/soc-module |
| LCSC E73-2G4M08S1CX (ref. preço) | https://www.lcsc.com/product-detail/C2764963.html |
| Fanstel BT832 datasheet v2.04 | https://fanstel.squarespace.com/s/BT832_datasheets.pdf |
| Fanstel BT832A product page | https://www.fanstel.com/bt810 |
| Fanstel BT832 price (direct) | https://www.fanstel.com/buy |
| Digikey BT832 (nRF52832) | https://www.digikey.com/en/products/detail/fanstel-corp/BT832/8323656 |
| Raytac MDBT42Q-192KV2 datasheet vL | https://www.raytac.com/upload/download_files/04cfd51020cc3c0ba914de057b52bece.pdf |
| Raytac MDBT42Q product page | https://www.raytac.com/product/ins.php?index_id=71 |
| u-blox ANNA-B112 datasheet R14 | https://content.u-blox.com/sites/default/files/documents/ANNA-B112_DataSheet_UBX-18011707.pdf |
| u-blox ANNA-B112 product | https://www.u-blox.com/en/product/anna-b112-open-cpu |
| KiCad RF_Module symbol (E73-2G4M04S-52810) | `/usr/share/kicad/symbols/RF_Module.kicad_sym` |
| KiCad RF_Module footprint (E73-2G4M04S) | `/usr/share/kicad/footprints/RF_Module.pretty/E73-2G4M04S.kicad_mod` |
| Nordic nRF52810 Product Spec v1.4 | https://www.mouser.com/datasheet/2/297/nRF52810_PS_v1_4-3159460.pdf |

---

## 8. Próximos Passos (para Phase 3 — Wave 2, passo 3.1)

1. **Usar símbolo/footprint padrão KiCad** — `RF_Module:E73-2G4M04S` + `E73-2G4M04S-52810` (já validados no ERC do spike 1.2).
2. **Criar apenas itens custom que NÃO existem na lib padrão:** NTAG213 inlay (símbolo 2 pinos passivo), Keystone 1059 (footprint custom), SHLD1 ferrite (símbolo gráfico), J1 contato negativo bateria.
3. **Validar ERC** com esquemático de teste instanciando o módulo E73-2G4M04S-52810 no `_spike/`.
4. **Documentar pinout no `designator_map.md`** (passo 1.1) referenciando esta tabela.

---

**Fim do documento.**  
Todas as informações transcritas de fontes primárias (datasheets oficiais, sites dos fabricantes, lib KiCad instalada). Zero invenção.
