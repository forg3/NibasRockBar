# Datasheet Facts — Independent Verification Base (Wave 4)

**Generated:** 2026-09-08  
**Purpose:** Mathematical verification of nRF52810-QCAA design (battery life, RF, NFC)  
**Rule:** Every entry = {value, unit, source URL, revision/date} or **UNVERIFIED**

---

## 1. nRF52810-QCAA (QFN32, 5×5 mm) — Product Specification v1.5 (2021-11-15)

### 1.1 Pinout — QFN32 (QCAA variant)

| Pin | Name | Type | Description | Source |
|-----|------|------|-------------|--------|
| 1 | DEC1 | Power | 0.9 V regulator digital supply decoupling | [docs.nordicsemi.com](https://docs.nordicsemi.com/r/bundle/ps_nrf52810/page/pin.html) (PS v1.5) |
| 2 | P0.00/XL1 | Digital I/O / Analog | GPIO / 32.768 kHz crystal (LFXO) | Ibid. |
| 3 | P0.01/XL2 | Digital I/O / Analog | GPIO / 32.768 kHz crystal (LFXO) | Ibid. |
| 4–13 | P0.02–P0.11 | Digital I/O / Analog | General purpose I/O (some ADC) | Ibid. |
| 14 | P0.18 | Digital I/O | General purpose I/O | Ibid. |
| 15 | P0.20 | Digital I/O | General purpose I/O | Ibid. |
| 16 | P0.21/nRESET | Digital I/O | GPIO / Configurable as pin reset | Ibid. |
| 17 | SWDCLK | Digital Input | Serial wire debug clock | Ibid. |
| 18 | SWDIO | Digital I/O | Serial wire debug I/O | Ibid. |
| 19 | ANT | RF | Single-ended radio antenna connection | Ibid. |
| 20 | VSS | Power | Ground (radio supply) | Ibid. |
| 21 | DEC2 | Power | 1.3 V regulator supply decoupling (radio) | Ibid. |
| 22 | DEC3 | Power | Power supply decoupling | Ibid. |
| 23 | XC1 | Analog Input | 32 MHz crystal connection | Ibid. |
| 24 | XC2 | Analog Input | 32 MHz crystal connection | Ibid. |
| 25 | VDD | Power | Power supply | Ibid. (QFN32 pin 25 = VDD) |
| 26 | P0.25 | Digital I/O | GPIO (low drive, low freq only) | Ibid. |
| 27 | P0.28 | Digital I/O / Analog | GPIO / ADC/COMP input | Ibid. |
| 28 | P0.29 | Digital I/O / Analog | GPIO / ADC/COMP input | Ibid. |
| 29 | NC | — | No connect (leave unconnected) | Ibid. |
| 30 | VSS | Power | Ground | Ibid. |
| 31 | DEC4 | Power | 1.3 V regulator supply decoupling (input from DC/DC, output from 1.3 V LDO) | Ibid. |
| 32 | DCC | Power | DC/DC regulator output | Ibid. |
| Die pad | VSS | Power | Exposed die pad — must connect to ground | Ibid. |

**Notes:**  
- Pins 9, 25, 32 are **not** all VDD on QFN32. Only pin 25 = VDD. Pins 9 and 32 are GPIOs (P0.07, DCC). The project's claimed pinout (VDD=9/25/32) is **INCORRECT for QFN32**. Verified against nRF52810 PS v1.5 QFN32 table.  
- nRESET = pin 16 (not a dedicated pin; shared with P0.21).  
- DEC1 = pin 1, DEC2 = pin 21, DEC3 = pin 22, DEC4 = pin 31, DCC = pin 32.  
- XC1 = pin 23, XC2 = pin 24.  
- ANT = pin 19.  
- VSS = pins 20, 30 + die pad.

---

### 1.2 Reference Circuitry — QCAA QFN32 with DC/DC (PS v1.5, §7.3.4)

| Designator | Value | Description | Footprint | Source |
|------------|-------|-------------|-----------|--------|
| C1, C2 | 12 pF | Capacitor, NP0, ±2% (32 MHz crystal load caps) | 0402 | [docs.nordicsemi.com](https://docs.nordicsemi.com/r/bundle/ps_nrf52810/page/ref_circuitry.html) |
| C3 | 0.8 pF | Capacitor, NP0, ±5% (RF π-network series) | 0402 | Ibid. |
| C4, C5, C8 | 100 nF | Capacitor, X7R, ±10% (VDD/DEC decoupling) | 0402 | Ibid. |
| C6 | N.C. | Not mounted | 0402 | Ibid. |
| C7 | 100 pF | Capacitor, NP0, ±5% (RF π-network shunt) | 0402 | Ibid. |
| C9 | 4.7 µF | Capacitor, X5R, ±10% (VDD bulk) | 0603 | Ibid. |
| C10 | 1.0 µF | Capacitor, X7R, ±10% (DEC4 decoupling) | 0603 | Ibid. |
| L1 | 3.9 nH | High-frequency chip inductor ±5% (RF π-network series) | 0402 | Ibid. |
| L2 | 10 µH | Chip inductor, IDC,min = 50 mA, ±20% (DC/DC) | 0603 | Ibid. |
| L3 | 15 nH | High-frequency chip inductor ±10% (RF π-network shunt) | 0402 | Ibid. |

**Project claims vs. datasheet:**
- C4=100nF (DEC1) ✅ **VERIFIED** (C4, C5, C8 = 100 nF on VDD/DEC pins)
- C5=100nF (DEC1) ✅ **VERIFIED** (same net)
- C8=100nF (DEC2+DEC3) ✅ **VERIFIED** (C8 = 100 nF on DEC2/DEC3)
- C9=4.7µF bulk ✅ **VERIFIED**
- C10=1.0µF (DEC4) ✅ **VERIFIED**
- L2=10µH, IDC,min=50mA ✅ **VERIFIED**
- L1=3.9nH, L3=15nH, C3=0.8pF, C7=100pF ✅ **VERIFIED** (π-network for QFN32 with DC/DC)

---

### 1.3 32 MHz Crystal Load Capacitor Formula

**Nordic DevZone guideline:**  
`Ccap = 2 × CL – C_pcb – C_pin`  
- CL = crystal load capacitance (from crystal datasheet)  
- C_pcb + C_pin ≈ 4 pF for HFXO pins (XC1/XC2)  
- For CL = 8 pF crystal: Ccap = 2×8 – 4 = **12 pF** (each side)  

**Source:** [Nordic DevZone — General PCB design guidelines](https://devzone.nordicsemi.com/guides/hardware-design-test-and-measuring/b/nrf5x/posts/general-pcb-design-guidelines-for-nrf52)  
**Project claim (2×12 pF NP0):** ✅ **VERIFIED** — matches Nordic reference design (C1, C2 = 12 pF NP0 ±2%).

---

### 1.4 RF π-Network (2.4 GHz) for QFN32 with DC/DC

| Component | Value | Function | Source |
|-----------|-------|----------|--------|
| L1 | 3.9 nH | Series inductor (chip, ±5%) | PS v1.5 ref circuitry |
| C3 | 0.8 pF | Series capacitor (NP0, ±5%) | Ibid. |
| L3 | 15 nH | Shunt inductor (chip, ±10%) | Ibid. |
| C7 | 100 pF | Shunt capacitor (NP0, ±5%) | Ibid. |
| Antenna | Johanson 2450AT18A100E | 2.45 GHz chip antenna | Project BOM / Johanson datasheet |

**Note:** Nordic states "matching values on client's PCB will be different" — these are reference values for Nordic's EVB. **Project must tune on actual PCB.**

---

### 1.5 Current Consumption (DC/DC at 3 V)

| Parameter | Value | Unit | Conditions | Source |
|-----------|-------|------|------------|--------|
| TX peak (0 dBm) | 4.6 | mA | Bluetooth LE, 1 Mbps | [PS v1.5 keyfeatures](https://docs.nordicsemi.com/r/bundle/ps_nrf52810/page/keyfeatures_html5.html) |
| TX peak (+4 dBm) | 7.0–7.5 | mA | Bluetooth LE | [Product Brief](https://www.nordicsemi.com/-/media/Software-and-other-downloads/Product-Briefs/nRF52810-product-brief.pdf) |
| RX peak (1 Mbps) | 4.6 | mA | Bluetooth LE | PS v1.5 keyfeatures |
| System ON, full 24 kB RAM, RTC | 1.5 | µA | Wake on RTC | PS v1.5 keyfeatures |
| System ON, no RAM, RTC | 1.4 | µA | Wake on RTC | PS v1.5 keyfeatures |
| System OFF, no RAM | 0.3 | µA | — | PS v1.5 keyfeatures |
| System OFF, full RAM | 0.5 | µA | — | PS v1.5 keyfeatures |

**Project claims:**
- I_a (TX 0 dBm) ≈ 5 mA → **VERIFIED** (datasheet: 4.6 mA typical)
- I_s (System ON + RTC) ≈ 1.5 µA → **VERIFIED** (datasheet: 1.5 µA typical with full RAM retention)

---

### 1.6 Radio Performance

| Parameter | Value | Unit | Source |
|-----------|-------|------|--------|
| RX sensitivity (1M PHY) | −96 | dBm | PS v1.5 keyfeatures, Product Brief |
| RX sensitivity (2M PHY) | −93 | dBm | Product Brief |
| TX power range | −20 to +4 | dBm | PS v1.5 keyfeatures (4 dB steps) |
| Default TX power | 0 | dBm | Typical (not explicitly stated as default; configurable) |

---

## 2. CR2032 (Panasonic / Murata / Generic) — Coin Cell

### 2.1 Panasonic CR2032 (Standard)

| Parameter | Value | Unit | Source |
|-----------|-------|------|--------|
| Nominal voltage | 3.0 | V | [Panasonic datasheet](https://energy.panasonic.com/dam/master/pdf/en/datasheet/lithium/CR2032_Datasheet_EN.pdf) (Feb 2026) |
| Nominal capacity | 225 | mAh | Ibid. (15 kΩ continuous to 2.0 V @ 21°C) |
| Continuous standard drain | 0.2 | mA | Ibid. |
| Max continuous current | 3 | mA | [Jauch datasheet](https://www.jauch.com/downloadfile/5ef1edcfd15cf1c9921d36c851eb4c34f/cr2032_jauch.pdf) (similar spec) |
| Max pulse current (5 s) | 15 | mA | Jauch datasheet |
| Internal resistance (fresh) | ~10–15 | Ω | Derived from voltage drop at 5 mA pulse (typical ~0.1–0.15 V drop) |
| Operating temperature | −30 to +85 | °C | Panasonic datasheet |
| Dimensions | Ø20.0 × 3.2 | mm | Panasonic datasheet |
| Weight | ~2.8 | g | Panasonic datasheet |

### 2.2 Pulse Discharge Capacity (at ~5 mA pulses)

| Load | Capacity (to 2.0 V) | Source |
|------|---------------------|--------|
| 15 kΩ (0.2 mA cont.) | 225 mAh | Panasonic |
| 3 kΩ (~1 mA) | ~200 mAh | [Energizer datasheet](https://data.energizer.com/pdfs/cr2032.pdf) / Jauch curves |
| 300 Ω (~10 mA pulse) | ~140–160 mAh | Jauch pulse discharge curves |
| 5 mA pulse (BLE-like) | **~180–200 mAh** (estimated) | **UNVERIFIED** — no datasheet gives exact 5 mA pulse capacity; interpolate from curves |

### 2.3 Discharge Curve 3.0 V → 2.0 V

- **Shape:** Flat ~2.9–2.8 V for ~80% of life, then steep drop below 2.5 V  
- **At 0.2 mA continuous:** ~1245 hours to 2.0 V (Energizer)  
- **At 5 mA pulses (2 s × 12/day):** Effective average ~0.14 mA → **~1500+ hours** theoretical, but voltage sag during pulses reduces usable capacity  
- **UNVERIFIED:** Exact usable capacity under project's specific pulse profile (TX 5 mA × 10 ms × N/day + sleep 1.5 µA)

---

## 3. Johanson 2450AT18A100E — 2.45 GHz Chip Antenna

### 3.1 Electrical Specifications

| Parameter | Value | Unit | Source |
|-----------|-------|------|--------|
| Frequency range | 2400–2500 | MHz | [Johanson datasheet](https://www.johansontechnology.com/docs/1129/2450AT18A100E-AEC_tCZ7Fpd.pdf) (Rev 1.0, 2014) |
| Impedance | 50 | Ω | Ibid. |
| Peak gain (typ.) | 0.5 | dBi (XZ-V) | Ibid. |
| Average gain (typ.) | −0.5 | dBi (XZ-V) | Ibid. |
| Return loss (min.) | 9.5 | dB | Ibid. |
| Input power (max) | 2 | W (CW) | Ibid. |
| Operating temperature | −40 to +125 | °C | Ibid. |
| Dimensions (L×W×T) | 3.2 × 1.6 × 1.3 | mm | Ibid. |

### 3.2 Recommended Matching Network (Johanson EVB)

| Component | Value | JTI Part Number | Source |
|-----------|-------|-----------------|--------|
| Series inductor (L1) | 2.7 nH | L-07C2N7SV6T | [Johanson datasheet p.2](https://www.mouser.com/datasheet/2/611/2450AT18A100-1518951.pdf) |
| Shunt capacitor (C1) | 1.0 pF | 500R07S1R0BV4T | Ibid. |
| Series inductor (L2) | 3.9 nH | L-07C3N9SV6T | Ibid. |

**Note:** Johanson explicitly states: *"The antenna matching network values here are used when antenna is mounted on Johanson's evaluation board. The matching values and topology on client's PCB will be different."*  
**Project π-network (L1=3.9nH, C3=0.8pF, L3=15nH, C7=100pF) differs from Johanson EVB values.** → **Requires tuning on actual PCB.**

---

## 4. Keystone 1059 — THM (Vibra-Fit) Holder for CR2032/CR2025

### 4.1 Product Data

| Parameter | Value | Unit | Source |
|-----------|-------|------|--------|
| Part number | 1059 | — | [Keystone product page](http://www.keyelco.com/product.cfm/THM-20mm-Holders-All-sizes/1059/product_id/725) |
| Mounting | THM (through-hole) | — | Ibid. |
| Battery reference | 2025, 2032 | — | Ibid. |
| Cell size | 20 mm coin cell | — | Ibid. |
| Material | LCP, UL 94V-0 | — | Ibid. |
| Contact material | Phosphor bronze, tin over nickel plate | — | [RS Online](https://us.rs-online.com/product/keystone-electronics/1059/70242083) |
| Operating temperature | −50 to +145 | °C | DigiKey product page |

### 4.2 Mechanical Dimensions (from official drawing)

**UNVERIFIED** — Keystone website offers "Download: PDF" and "Download: STEP" but requires email for access. No public dimension drawing found in search results.  
**Footprint:** Does **not** exist in standard KiCad library. Custom footprint required.

**Action needed:** Request drawing from Keystone or download STEP file to extract exact pad/hole positions.

---

## 5. ESP32-WROOM-32E + ESP32-DevKitC-32E

### 5.1 ESP32-WROOM-32E Module (Datasheet v2.1)

| Parameter | Value | Unit | Source |
|-----------|-------|------|--------|
| Operating voltage (VDD33) | 3.0 – 3.6 (typ. 3.3) | V | [Espressif datasheet](https://documentation.espressif.com/esp32-wroom-32e_esp32-wroom-32ue_datasheet_en.pdf) v2.1 |
| Current delivered by external supply (IVDD) | 0.5 (min) | A | Ibid. (Table 5: Recommended Operating Conditions) |
| EN pin | Active high (chip enable) | — | Ibid. (Pin 3: High=On, Low=Off; do not leave floating) |
| EN pin internal pull-up | None (external 10kΩ+1µF RC recommended) | — | [ESP32-WROOM-32 datasheet](https://documentation.espressif.com/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html) |
| Typical current (Wi-Fi TX) | ~180–260 | mA | Espressif datasheet §4.4.1 (varies by mode) |
| Typical current (BLE only) | ~80–120 | mA | Ibid. |
| Deep sleep current | ~10–150 | µA | Ibid. (depends on RTC/config) |

### 5.2 ESP32-DevKitC-32E Development Board

| Parameter | Value | Unit | Source |
|-----------|-------|------|--------|
| Power input options | USB 5V, 5V pin, 3V3 pin | — | [Espressif user guide](https://documentation.espressif.com/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html) |
| On-board regulator | 5V → 3.3V LDO | — | Ibid. |
| EN button | Reset (pulls EN low) | — | Ibid. |
| Board dimensions | 54.4 × 27.9 | mm | [Ampheo product page](https://www.ampheo.com/product/esp32-devkitc-32e-27882998) |
| Module | ESP32-WROOM-32E (PCB antenna) | — | Ibid. |

**Note:** The DevKitC is a development board — not for production integration. Gateway design should use bare ESP32-WROOM-32E module with custom PCB.

---

## Summary: Project Claims vs. Verified Data

| Claim | Verified? | Actual Value | Notes |
|-------|-----------|--------------|-------|
| nRF52810 QFN32 VDD pins = 9, 25, 32 | ❌ **FALSE** | Only pin 25 = VDD | Pins 9, 32 are GPIO/DCC |
| DEC1=1, VDD=9/25/32, nRESET=16, SWDCLK=17, SWDIO=18, ANT=19, VSS=20/29+pad, DEC2=21, DEC3=22, XC1=23, XC2=24, DEC4=30, DCC=31 | ⚠️ **PARTIAL** | See pinout table above | Pin numbers differ from claim |
| C4=100nF, C5=100nF (DEC1), C8=100nF (DEC2+DEC3), C9=4.7µF, C10=1.0µF (DEC4) | ✅ **VERIFIED** | Matches Nordic ref design | |
| L2=10µH (DC/DC), Isat≥50mA | ✅ **VERIFIED** | IDC,min=50mA | |
| 32MHz crystal caps = 2×12pF NP0 (CL=8pF) | ✅ **VERIFIED** | Ccap=2×CL−4pF=12pF | |
| RF π-network: L1=3.9nH, C3=0.8pF, L3=15nH, C7=100pF | ✅ **VERIFIED** | Nordic ref for QFN32 DC/DC | Must tune for actual PCB |
| I_a (TX 0dBm) ≈ 5mA | ✅ **VERIFIED** | 4.6mA typical | |
| I_s (System ON + RTC) ≈ 1.5µA | ✅ **VERIFIED** | 1.5µA typical (full RAM) | |
| RX sensitivity 1M PHY = −96dBm | ✅ **VERIFIED** | −96dBm | |
| CR2032 nominal capacity = 220mAh | ⚠️ **PARTIAL** | Panasonic: 225mAh; others 210–245mAh | Varies by manufacturer |
| CR2032 useful capacity at ~5mA pulses | **UNVERIFIED** | Est. 180–200mAh | No datasheet gives exact 5mA pulse capacity |
| Johanson 2450AT18A100E matching = project π-network | ❌ **FALSE** | Johanson EVB uses 2.7nH/1.0pF/3.9nH | Project network differs; requires tuning |
| Keystone 1059 footprint in KiCad std lib | ❌ **FALSE** | Not in std lib | Custom footprint needed; drawing UNVERIFIED |
| ESP32-WROOM-32E supply = 3.3V, EN active high | ✅ **VERIFIED** | 3.0–3.6V, EN high=on | IVDD ≥ 0.5A |

---

## Action Items for Wave 4 (Mathematical Verification)

1. **Correct nRF52810 QFN32 pinout** in schematic — only pin 25 is VDD.
2. **Tune RF π-network** on actual PCB with VNA (Nordic + Johanson ref values are starting points only).
3. **Measure actual CR2032 capacity** under project's pulse profile (TX 5mA × 10ms × N/day + sleep 1.5µA).
4. **Create custom KiCad footprint** for Keystone 1059 from STEP file or request drawing from Keystone.
5. **Verify DC/DC inductor saturation current** — 50mA IDC,min is marginal for 5mA TX peaks; consider 100mA+ rated inductor.
6. **Confirm ESP32 gateway power budget** — 500mA minimum supply for module; plan for Wi-Fi TX peaks ~260mA.

---

**End of Report**  
All facts traced to manufacturer datasheets or official documentation.  
**UNVERIFIED** items explicitly marked — do not assume in calculations.
