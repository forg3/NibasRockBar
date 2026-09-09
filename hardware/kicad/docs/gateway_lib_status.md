# Status da Biblioteca KiCad — Gateway ESP32-DevKitC-32E

**Data:** 09/09/2026  
**Verificação:** Baseada em `pesquisa_gateway_esp32.md` (linhas 66, 333) e repositório oficial Espressif

---

## Resultado

✅ **Biblioteca padrão EXISTE — nenhum item custom necessário**

---

## Detalhes

| Item | Biblioteca Oficial Espressif | Referência |
|------|------------------------------|------------|
| **Footprint (through-hole, 2×19 headers)** | `Espressif:ESP32-DevKitC` | `footprints/Espressif.pretty/ESP32-DevKitC.kicad_mod` |
| **Símbolo esquemático** | `espressif:ESP32-DevKitC` | `symbols/espressif.kicad_sym` |
| **Repositório** | `github.com/espressif/kicad-libraries` | https://github.com/espressif/kicad-libraries |

---

## Como usar no projeto KiCad

1. **Adicionar biblioteca de footprints:**
   - Preferences → Manage Footprint Libraries → Add Existing Library
   - Apontar para `Espressif.pretty` (clonado do repo oficial ou via Plugin Library Manager)

2. **Adicionar biblioteca de símbolos:**
   - Preferences → Manage Symbol Libraries → Add Existing Library
   - Apontar para `espressif.kicad_sym`

3. **No esquemático:** Place Symbol → `espressif:ESP32-DevKitC`
4. **No layout:** Place Footprint → `Espressif:ESP32-DevKitC`

---

## Pinout relevante (apenas alimentação/EN/USB — firmware não usa GPIOs)

| Header Pin | Nome | Função no Carrier |
|------------|------|-------------------|
| J2-1 | 3V3 | Saída 3.3V do LDO onboard (até 1A) — **desacoplar com 0.1µF + 10µF** |
| J2-2 | EN | CHIP_PU / Reset (active high) — **já tem RC 10k/1µF no DevKit** |
| J2-19 | 5V | Entrada 5V (USB ou header) — **alimenta LDO AMS1117-3.3** |
| J1/J2 GND | GND | Ground comum — **múltiplos pinos, conectar todos** |

> **Nota:** O DevKitC-32E já implementa internamente: LDO 3.3V (AMS1117-3.3), proteção USB (Schottky BAT760-7 + TVS), circuito EN (RC 10kΩ/1µF), strapping pins corretos (pull-ups/downs), USB-UART (CP2102N). O carrier board só precisa rotear 5V/GND/3V3/EN e adicionar capacitores de decoupling nos headers.

---

## Conclusão

**Não criar `nibas_gateway.kicad_sym` nem `.pretty/` customizados.**  
Usar diretamente a lib oficial `espressif/kicad-libraries` → `Espressif:ESP32-DevKitC` (footprint) + `espressif:ESP32-DevKitC` (símbolo).

---

## Referências

- `hardware/kicad/docs/pesquisa_gateway_esp32.md` — linhas 66, 280-292, 333
- Espressif KiCad Libraries: https://github.com/espressif/kicad-libraries
- ESP32-DevKitC V4 Schematic: https://dl.espressif.com/dl/schematics/esp32_devkitc_v4-sch.pdf
- ESP32-DevKitC User Guide: https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html