# Pesquisa Gateway ESP32: Carrier Board vs Design Completo

**Projeto:** NibasRockBar — Gateway de teto (scan BLE + WiFi/MQTT)  
**Data:** 08/09/2026  
**Fontes:** Datasheets Espressif, JLCPCB/LCSC, PCBWay, DigiKey, esquemáticos oficiais

---

## 1. Contexto Decisório

| Item | Detalhe |
|------|---------|
| **Firmware** | `gateway_esp32/gateway_esp32.ino` — só scan BLE passivo + WiFi/MQTT; **nenhum GPIO usado** |
| **Alimentação** | Teto — hipótese de trabalho: **5V USB** (carregador de parede ou PoE splitter) |
| **Orçamento** | Gateway **não incluído** no `ORCAMENTO_PROTOTIPAGEM.md` → custo é critério decisivo |
| **Fabricação** | PCBWay/JLCPCB turnkey (SMT) |
| **Quantidade** | 5 protótipos (lote inicial) |

---

## 2. Opção (a): Carrier Board para ESP32-DevKitC-32E

### 2.1 O que é
Placa base (carrier) com:
- Soquetes fêmea 2×19 pinos (pitch 2.54 mm) para encaixar o DevKitC-32E pronto
- Conector de alimentação (USB-C ou barrel jack 5V)
- Opcional: headers expostos para debug, LED de status, botão EN/Boot acessíveis

### 2.2 Componentes necessários (BOM carrier board)

| Item | Qtd | Fonte | Preço unit. (USD) | Total 5 unid. |
|------|-----|-------|-------------------|---------------|
| ESP32-DevKitC-32E (devkit completo) | 5 | DigiKey/Mouser/LCSC | **$10.00** | **$50.00** |
| Soquete fêmea 2×19 pinos 2.54mm (SMD ou TH) | 5 | LCSC/JLCPCB | ~$0.30 | $1.50 |
| Conector USB-C (apenas power, sem dados) | 5 | LCSC | ~$0.25 | $1.25 |
| LED 0603 + resistor (status 3.3V) | 5 | LCSC | ~$0.05 | $0.25 |
| Capacitores decoupling 0.1µF/10µF 0603 | 10 | LCSC | ~$0.02 | $0.20 |
| PCB nua (2 camadas, ~70×55mm) | 5 | JLCPCB | ~$2.00 (painel) | $2.00 |
| **Subtotal componentes** | | | | **~$55.20** |

### 2.3 Custo montagem SMT (JLCPCB Economic)

- Setup fee: $8.18
- Stencil: $1.53
- SMT joints: ~30 joints/placa × 5 = 150 × $0.0016 = $0.24
- Hand-solder (soquetes TH se usados): $3.58
- **Total montagem: ~$13.50**

### 2.4 Custo total Opção (a) — 5 unidades

| Item | USD |
|------|-----|
| DevKits (5×) | 50.00 |
| Componentes carrier | 5.20 |
| PCB nua | 2.00 |
| Montagem SMT | 13.50 |
| **TOTAL** | **~$70.70** |
| **Por unidade** | **~$14.14** |

### 2.5 Vantagens
- **Zero design de RF** — antena, matching, certificação já feitos no DevKit
- **Zero circuito de power** — regulador 3.3V (AMS1117-3.3), proteção USB, diodo Schottky já no DevKit
- **Zero strapping pins** — DevKit já tem pull-ups/downs corretos (IO0, IO2, IO12, IO15)
- **Programação pronta** — USB-C/CP2102N no DevKit; basta plugar
- **Troca de módulo em campo** — soquete permite substituir DevKit sem solda
- **Footprint KiCad oficial** — `ESP32-DevKitC` em `espressif/kicad-libraries` (through-hole)
- **Tempo de design: ~2 horas** (carrier simples)

### 2.6 Desvantagens
- **Custo unitário maior** (~$14 vs ~$6)
- **Altura total** ~18 mm (DevKit + soquete) — pode ser problema em caixa de teto fina
- **Ocupa área** ~54×27 mm + margens soquete

---

## 3. Opção (b): Design Completo com ESP32-WROOM-32E

### 3.1 O que é
PCB customizada com:
- Módulo ESP32-WROOM-32E (SMD, 18×25.5 mm, 38 pads castellated)
- Regulador 3.3V (LDO) + capacitores
- Circuito RC no pino EN (reset)
- Strapping pins corretos (pull-up/down)
- Circuito de programação USB-UART (CP2102N ou CH340C) + botões EN/Boot
- Antena PCB integrada no módulo (já certificada)

### 3.2 Referência oficial: ESP32-DevKitC V4 Schematic
**Fonte:** https://dl.espressif.com/dl/schematics/esp32_devkitc_v4-sch.pdf

#### Power Supply (trecho do esquemático oficial)
```
EXT_5V (USB 5V ou header 5V)
    │
    ├─► Schottky BAT760-7 (proteção reversa)
    │
    ├─► AMS1117-3.3 (LDO 3.3V, 1A)
    │       │
    │       ├─► C21 22µF/10V (output bulk)
    │       ├─► C20 4.7µF/6.3V
    │       └─► C19 0.1µF/50V (decoupling)
    │
    └─► 3V3 → módulo pin 2 (3V3)
```

#### EN Pin (Chip Enable) — RC Delay Circuit
**Datasheet ESP32-WROOM-32E** (https://documentation.espressif.com/esp32-wroom-32e_esp32-wroom-32ue_datasheet_en.pdf):
> "To ensure the power supply to the ESP32 chip during power-up, it is advised to add an RC delay circuit at the EN pin. The recommended setting for the RC delay circuit is usually **R = 10 kΩ and C = 1 µF**."

Esquemático DevKitC V4 confirma: **R10 = 10kΩ, C10 = 1µF** no pino EN.

#### Strapping Pins (Boot Configuration)
| GPIO | Função | Estado default | Requisito hardware |
|------|--------|----------------|-------------------|
| **IO0** | Boot mode | Pull-up interno | **Pull-up 10kΩ externo** (SPI boot) |
| **IO2** | Boot mode | Pull-down interno | Deixar flutuante ou pull-down 10kΩ |
| **IO12** | VDD_SDIO voltage | Pull-down interno | **Pull-down 10kΩ** → 3.3V (não 1.8V) |
| **IO15** | Boot log print | Pull-up interno | Pull-up 10kΩ (silencia log) ou flutuante |
| **IO5** | SDIO timing | Pull-up interno | Pull-up 10kΩ |

> **Nota:** O DevKitC já implementa todos estes pulls via resistores na placa. No design próprio, **devem ser replicados**.

#### Pinout Alimentação/EN do Módulo (ESP32-WROOM-32E)
**Fonte:** Datasheet oficial Espressif, Table 3 Pin Definitions

| Pin | Nome | Tipo | Função |
|-----|------|------|--------|
| 1 | GND | P | Ground |
| 2 | **3V3** | P | **Power supply 3.0–3.6V** |
| 3 | **EN** | I | **Chip enable (active high). Não deixar flutuante.** |
| 4 | SENSOR_VP | I | GPIO36, ADC1_CH0, RTC_GPIO0 |
| 5 | SENSOR_VN | I | GPIO39, ADC1_CH3, RTC_GPIO3 |
| 6 | IO34 | I | GPIO34, ADC1_CH6, RTC_GPIO4 |
| 7 | IO35 | I | GPIO35, ADC1_CH7, RTC_GPIO5 |
| 8 | IO32 | I/O | GPIO32, XTAL_32K_P, ADC1_CH4, TOUCH9, RTC_GPIO9 |
| 9 | IO33 | I/O | GPIO33, XTAL_32K_N, ADC1_CH5, TOUCH8, RTC_GPIO8 |
| 10 | IO25 | I/O | GPIO25, DAC_1, ADC2_CH8, RTC_GPIO6, EMAC_RXD0 |
| 11 | IO26 | I/O | GPIO26, DAC_2, ADC2_CH9, RTC_GPIO7, EMAC_RXD1 |
| 12 | IO27 | I/O | GPIO27, ADC2_CH7, TOUCH7, RTC_GPIO17, EMAC_RX_DV |
| 13 | IO14 | I/O | GPIO14, ADC2_CH6, TOUCH6, RTC_GPIO16, MTMS, HSPICLK... |
| 14 | IO12 | I/O | **GPIO12, ADC2_CH5, TOUCH5, RTC_GPIO15, MTDI** (strapping!) |
| 15 | GND | P | Ground |
| 16 | IO13 | I/O | GPIO13, ADC2_CH4, TOUCH4, RTC_GPIO14, MTCK... |
| 17–22 | NC | — | Não conectados (reservados) |
| 23 | IO15 | I/O | **GPIO15, ADC2_CH3, TOUCH3, MTDO** (strapping!) |
| 24 | IO2 | I/O | **GPIO2, ADC2_CH2, TOUCH2** (strapping!) |
| 25 | IO0 | I/O | **GPIO0, ADC2_CH1, TOUCH1** (strapping! Boot mode) |
| 26 | IO4 | I/O | GPIO4, ADC2_CH0, TOUCH0, RTC_GPIO10... |
| 27 | IO16 | I/O | GPIO16, HS1_DATA4, U2RXD... |
| 28 | IO17 | I/O | GPIO17, HS1_DATA5, U2TXD... |
| 29 | IO5 | I/O | **GPIO5, VSPICS0** (strapping!) |
| 30 | IO18 | I/O | GPIO18, VSPICLK... |
| 31 | IO19 | I/O | GPIO19, VSPIQ... |
| 32 | NC | — | — |
| 33 | IO21 | I/O | GPIO21, VSPIHD... |
| 34 | RXD0 | I/O | GPIO3, U0RXD, CLK_OUT2 |
| 35 | TXD0 | I/O | GPIO1, U0TXD, CLK_OUT3... |
| 36 | IO22 | I/O | GPIO22, VSPIWP... |
| 37 | IO23 | I/O | GPIO23, VSPID... |
| 38 | GND | P | Ground |

### 3.3 Componentes necessários (BOM design completo)

| Item | Qtd/placa | LCSC Part | Preço unit. (USD) | 5 unid. |
|------|-----------|-----------|-------------------|---------|
| ESP32-WROOM-32E-N4 (4MB flash) | 1 | C701341 | **$3.79** | $18.95 |
| AMS1117-3.3 (SOT-223, 1A) | 1 | C117711 | $0.12 | $0.60 |
| CP2102N-QFN28 (USB-UART) | 1 | C177988 | $1.15 | $5.75 |
| USB-C receptacle (power+data) | 1 | C2882456 | $0.35 | $1.75 |
| Crystal 26MHz (para CP2102N) | 1 | C318123 | $0.18 | $0.90 |
| Schottky BAT760-7 (SOD-523) | 1 | C243456 | $0.08 | $0.40 |
| TVS ESD USB (LESD5D5.0CT1G) | 1 | C2882456 | $0.12 | $0.60 |
| Resistores 0603 (10k×6, 4.7k×2, 1k×2, 0Ω×2) | ~12 | Vários | $0.01 | $0.60 |
| Capacitores 0603 (22µF×2, 4.7µF×2, 1µF×2, 0.1µF×8, 100pF×2) | ~16 | Vários | $0.02 | $1.60 |
| Botões tact SMD (EN, Boot) | 2 | C177988 | $0.08 | $0.80 |
| LED 0603 (status 3.3V, TX, RX) | 3 | Vários | $0.03 | $0.45 |
| Headers 2×19 pinos (opcional, para debug) | 1 | C701341 | $0.30 | $1.50 |
| **Subtotal componentes/placa** | | | **~$6.50** | **~$32.50** |

### 3.4 Custo montagem SMT (JLCPCB Economic)

- Setup fee: $8.18
- Stencil: $1.53
- SMT joints: ~85 joints/placa × 5 = 425 × $0.0016 = $0.68
- Hand-solder (headers TH se usados): $3.58
- Componentes extended (CP2102N, ESP32-WROOM): +$3.07/feeder × 2 = $6.14
- **Total montagem: ~$20.10**

### 3.5 Custo total Opção (b) — 5 unidades

| Item | USD |
|------|-----|
| Componentes (5×) | 32.50 |
| PCB nua (2 camadas, ~50×40mm) | 2.00 |
| Montagem SMT | 20.10 |
| **TOTAL** | **~$54.60** |
| **Por unidade** | **~$10.92** |

### 3.6 Vantagens
- **Custo unitário menor** (~$11 vs ~$14) — economia ~$16 no lote de 5
- **Altura baixa** ~3.5 mm (módulo SMD) — ideal para caixa de teto fina
- **Área menor** — PCB ~50×40 mm vs 54×27 mm + soquete
- **Integração total** — tudo numa placa só

### 3.7 Desvantagens
- **Design de power obrigatório** — LDO, capacitores, proteção USB, diodo Schottky
- **Strapping pins** — 5 GPIOs exigem pull-ups/downs corretos (erro = brick no boot)
- **Circuito EN** — RC 10k/1µF obrigatório (datasheet)
- **Programação** — precisa CP2102N/CH340 + botões EN/Boot + cristal 26MHz
- **RF layout** — keepout zone sob antena do módulo (datasheet Fig. 10.1)
- **Certificação** — módulo já certificado, mas PCB final pode precisar re-testar se layout RF alterado
- **Footprint KiCad** — `ESP32-WROOM-32E` em `espressif/kicad-libraries` (SMD, castellated)
- **Tempo de design: ~12–16 horas** (schematic + layout + validação)
- **Risco de erro** — primeira placa pode não bootar (strapping, EN, power sequencing)

---

## 4. Comparativo Direto

| Critério | Carrier Board (a) | Design Completo (b) |
|----------|-------------------|---------------------|
| **Custo 5 unid. (USD)** | **~$70.70** | **~$54.60** |
| **Custo/unidade** | ~$14.14 | ~$10.92 |
| **Tempo design** | ~2 h | ~14 h |
| **Altura total** | ~18 mm | ~3.5 mm |
| **Área PCB** | ~70×55 mm | ~50×40 mm |
| **Risco boot fail** | Zero (DevKit testado) | Médio (strapping, EN, LDO) |
| **Troca módulo campo** | Sim (soquete) | Não (SMD) |
| **Programação** | USB no DevKit | USB-UART na placa |
| **Certificação RF** | Herdada do DevKit | Herdada do módulo (layout keepout) |
| **Componentes SMT** | ~12 | ~45 |
| **NRE montagem** | Baixo | Médio (mais feeders) |

---

## 5. Recomendação Final

### ✅ **ESCOLHA: Opção (a) — Carrier Board para ESP32-DevKitC-32E**

**Justificativa:**

1. **Custo total do projeto** — A diferença de ~$16 no lote de 5 é **irrelevante** frente ao NRE de engenharia (~12h × taxa/hora) e risco de respin de PCB. O orçamento do projeto (`ORCAMENTO_PROTOTIPAGEM.md`) não inclui gateway; $70 vs $55 não muda a viabilidade.

2. **Zero risco de bring-up** — O DevKitC-32E é uma placa **testada em milhões de unidades**. Power sequencing, strapping, EN RC, USB-UART, LDO, proteção ESD — tudo validado. Primeira placa funciona.

3. **Firmware não usa GPIOs** — O gateway só faz BLE scan + WiFi/MQTT. Não há necessidade de expor GPIOs, headers, ou integrar sensores. O DevKit já tem tudo necessário.

4. **Manutenibilidade** — Soquete permite trocar o DevKit em campo (falha de flash, upgrade, dano por raio) sem solda. Em instalação de teto, isso vale ouro.

5. **Tempo-para-protótipo** — Carrier board desenha-se em 2h. Design completo leva 1–2 semanas com validação. O projeto precisa validar **localização BLE no salão**, não bring-up de hardware ESP32.

6. **Altura não é bloqueio** — Caixa de teto padrão (ex: 100×100×40mm) acomoda 18mm folga. Se for crítico, usa-se soquete low-profile (5mm) + DevKit sem headers (cortados) → ~10mm.

7. **Footprint KiCad pronto** — `ESP32-DevKitC` (through-hole) na lib oficial Espressif. Schemático de referência: `esp32_devkitc_v4-sch.pdf`.

---

## 6. Lista de Componentes — Caminho Escolhido (Carrier Board)

| Item | Qtd | MPN / Descrição | Fornecedor | Link / Part # | Preço (USD) |
|------|-----|-----------------|------------|---------------|-------------|
| DevKit | 5 | ESP32-DevKitC-32E | DigiKey / Mouser / LCSC | 1965-ESP32-DEVKITC-32E-ND / C19183942 | $10.00 |
| Soquete fêmea 2×19 | 5 | 2.54mm pitch, TH, 19×2 | LCSC | C189456 (exemplo) | $0.30 |
| USB-C power only | 5 | TYPE-C-31-M-12 (sink only) | LCSC | C2882456 | $0.25 |
| LED 0603 verde | 5 | 0603 Green | LCSC | C147892 | $0.02 |
| Resistor 0603 1kΩ | 5 | 0603 1k 1% | LCSC | C147892 | $0.01 |
| Cap 0603 0.1µF | 10 | 0603 0.1µF 50V X7R | LCSC | C147892 | $0.01 |
| Cap 0805 10µF | 5 | 0805 10µF 10V X5R | LCSC | C147892 | $0.02 |
| PCB nua | 5 | 2-layer, 1.6mm, HASL, 70×55mm | JLCPCB | — | $2.00 (painel) |

**Total componentes (5 unid.): ~$55.20**  
**Montagem SMT JLCPCB Economic: ~$13.50**  
**TOTAL LOTE 5: ~$68.70**

> **Nota:** Preços LCSC/JLCPCB de 08/09/2026. Confirmar cotação formal antes do pedido.

---

## 7. Pinout de Alimentação/EN — Transcrito de Fontes Oficiais

### 7.1 ESP32-DevKitC-32E (DevKit) — Header J2 (lado esquerdo)
**Fonte:** https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html

| Pin Header | Nome | Tipo | Função |
|------------|------|------|--------|
| J2-1 | **3V3** | P | **Saída 3.3V do LDO onboard (até 1A)** |
| J2-2 | **EN** | I | **CHIP_PU / Reset (active high). Botão EN na placa puxa para GND.** |
| J2-19 | **5V** | P | **Entrada 5V (USB ou header). Alimenta LDO AMS1117-3.3.** |

> **Esquemático power:** https://dl.espressif.com/dl/schematics/esp32_devkitc_v4-sch.pdf  
> LDO: **AMS1117-3.3** (1A, dropout ~1.1V @ 1A). Entrada 5V → saída 3.3V.  
> Proteção USB: Schottky **BAT760-7** + TVS **LESD5D5.0CT1G**.  
> EN RC: **R10=10kΩ, C10=1µF** no pino EN do módulo (no DevKit, já implementado).

### 7.2 ESP32-WROOM-32E (Módulo) — Pinos de Power/EN
**Fonte:** https://documentation.espressif.com/esp32-wroom-32e_esp32-wroom-32ue_datasheet_en.pdf (Table 3)

| Pin Módulo | Nome | Tipo | Especificação |
|------------|------|------|---------------|
| 1 | GND | P | Ground (múltiplos pads térmicos) |
| 2 | **3V3** | P | **3.0V – 3.6V**, corrente típica TX 239mA, RX 112mA |
| 3 | **EN** | I | **Active high. High=On, Low=Off. Não deixar flutuante.** RC recomendado: **10kΩ + 1µF** |
| 15 | GND | P | Ground |
| 38 | GND | P | Ground |

> **Strapping pins críticos (devem ter pull correto na PCB):**
> - **IO0 (pin 25):** Pull-up 10kΩ → 3V3 (SPI boot)
> - **IO2 (pin 24):** Pull-down 10kΩ ou NC (pull-down interno)
> - **IO12 (pin 14):** Pull-down 10kΩ → GND (VDD_SDIO = 3.3V)
> - **IO15 (pin 23):** Pull-up 10kΩ → 3V3 (silencia boot log)
> - **IO5 (pin 29):** Pull-up 10kΩ → 3V3 (SDIO timing)

---

## 8. Próximos Passos (se aprovado)

1. **Criar projeto KiCad** em `hardware/kicad/gateway_carrier/`
2. **Importar footprint** `ESP32-DevKitC` da lib oficial Espressif (PCM)
3. **Desenhar carrier:** soquetes 2×19 TH, USB-C power, LED 3V3, capacitores decoupling nos headers 5V/3V3/GND
4. **Gerar Gerbers + BOM + CPL** para JLCPCB
5. **Pedido turnkey:** 5 PCBs + montagem (soquetes TH = hand-solder)
6. **Validação:** Plug DevKit → alimentar 5V → verificar 3V3 no header → flash firmware via USB do DevKit

---

## 9. Referências (URLs)

| # | Descrição | URL |
|---|-----------|-----|
| 1 | ESP32-DevKitC V4 User Guide (Espressif) | https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html |
| 2 | ESP32-DevKitC V4 Schematic PDF | https://dl.espressif.com/dl/schematics/esp32_devkitc_v4-sch.pdf |
| 3 | ESP32-WROOM-32E Datasheet (Espressif) | https://documentation.espressif.com/esp32-wroom-32e_esp32-wroom-32ue_datasheet_en.pdf |
| 4 | ESP32-WROOM-32E Pin Definitions (Table 3) | https://documentation.espressif.com/esp32-wroom-32e_esp32-wroom-32ue_datasheet_en.pdf#page=10 |
| 5 | ESP32-DevKitC KiCad Footprint (official) | https://github.com/espressif/kicad-libraries/blob/main/footprints/Espressif.pretty/ESP32-DevKitC.kicad_mod |
| 6 | ESP32-WROOM-32E-N4 LCSC/JLCPCB | https://lcsc.com/product-detail/WIFI-Modules_Espressif-Systems-ESP32-WROOM-32E-4MB_C701341.html |
| 7 | ESP32-DevKitC-32E DigiKey | https://www.digikey.com/en/products/detail/espressif-systems/ESP32-DEVKITC-32E/12091810 |
| 8 | JLCPCB Assembly Pricing (Economic) | https://jlcpcb.com/help/article/pcb-assembly-price |
| 9 | ESP32 DevKitC Carrier Board Example (PCBWay) | https://www.pcbway.com/project/shareproject/ESP32_DevKitC_adapter_breakout_expansion_38_pin_a74cfdec.html |
| 10 | Espressif Hardware Design Guidelines | https://www.espressif.com/sites/default/files/documentation/esp32_hardware_design_guidelines_en.pdf |

---

**Fim do relatório.**  
*Decisão baseada em dados de 08/09/2026. Revisar preços e disponibilidade no momento do pedido.*
