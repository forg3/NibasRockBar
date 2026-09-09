# Verificação Matemática Independente — 27 Afirmações (passo 5.1)

**Data:** 2026-09-09 · **Verificador:** sessão fresh, sem acesso aos artefatos das waves anteriores
como fonte de verdade. **Regra:** toda conta refeita do zero; nenhum número copiado do
`RELATORIO_REVISAO_TECNICA.md` sem confronto com fonte primária.

**Fontes primárias usadas (com revisão):**

| Fonte | Revisão | Como foi verificada |
|---|---|---|
| nRF52810 Product Specification | **v1.3** (4430_161 v1.3, 2019-01-31), 415 p. | PDF baixado e text-extraído; tabelas de pinos (T114), correntes (§5.2), TXPOWER (§6.14.14.30) e circuito de referência (§7.3.4, Fig. 146) lidas **pino a pino / vetor a vetor** (PyMuPDF sobre a geometria vetorial da Fig. 146). Changelog v1.4/v1.5 (debug, RADIO preamble/RSSI, UICR, CLOCK, POWER erratum) **não altera** pinagem nem reference circuitry. |
| Nordic DevZone #53125 | 2019 | Confirma pinos 9 e 32 = VDD no QFN32. |
| Símbolo KiCad `MCU_Nordic:nRF52810-QCxx` | KiCad 10.0.6 (lib oficial) | Terceira fonte independente de pinagem — idêntica à Tabela 114. |
| Energizer CR2032 datasheet | data.energizer.com/pdfs/cr2032.pdf | 235 mAh (15 kΩ→2.0 V, 21 °C); curva/pulso 400 Ω. |
| Johanson 2450AT18A100E-AEC datasheet | Ver 1.0, 2014 | Rede de casamento do EVB + ressalva de tuning. |
| Ebyte E73-2G4M04S1A (pin definition) | cdebyte.com/products/E73-2G4M04S1A/2 | Pinos 37/38 = SWDCLK/SWDIO; 16 = VCC 1.8–3.6 V. |
| Raytac MDBT42Q-512KV2 datasheet | Ver P (nRF52832) | SoC = nRF52832; nota "DC-DC mode → add L2/L3/C14". |
| espressif/arduino-esp32 `BLEScan.cpp` | master | `setInterval()` recebe **ms** (converte `/0.625`). |
| Footprint KiCad `RF_Module:E73-2G4M04S` | lib oficial | 17,5 × 28,7 mm (pads y=±14.35, x=±8.75). |

⚠️ **Aviso sobre `datasheet_facts_nordic.md` (base da wave 2.3):** a tabela de pinagem §1.1
desse arquivo está **ERRADA** (ver afirmação 13). O restante do arquivo (correntes, reference
circuitry, cristal, Johanson, Keystone) confere com as fontes primárias. O arquivo cita
"PS v1.5 (2021-11-15)" — a data 2021-11-15 é da **v1.4**; v1.5 existe, mas a data citada
está imprecisa. Não afeta as conclusões abaixo (pinagem é fato de silício).

---

## Resumo dos 27 vereditos

| # | Afirmação | Veredito |
|---|---|---|
| 1 | I_a ≈ 5 mA (TX 0 dBm c/ DC/DC) | **DIVERGENTE (parcial)** — sistema c/ DC/DC = 5,8 mA (4,6 mA é pico do rádio) |
| 2 | I_s ≈ 1,5 µA (System ON + RTC) | **CONFIRMADO** |
| 3 | t_a = 3 ms (adv 3 canais) | **CONFIRMADO** (estimativa conservadora, não é constante de datasheet) |
| 4 | CR2032 220 mAh → 180–200 úteis + R_int vs pulso 5 mA | **CONFIRMADO c/ matiz** (180–200 é estimativa, não dado de datasheet) |
| 5 | Autonomia 16.500 h ≈ 1,9 anos | **CONFIRMADO** (aritmética) — c/ I_a=5,8 mA cai p/ ~1,65 a (ainda > meta) |
| 6 | Margem p/ adv 1 s | **CONFIRMADO** (1,15–1,31 a > 12 meses) |
| 7 | TX default 0 dBm | **CONFIRMADO** (TXPOWER Reset = 0x00 = 0 dBm) |
| 8 | FSPL(10 m, 2400 MHz) = 60 dB | **CONFIRMADO** (60,05 dB) |
| 9 | Sensibilidade −96 dBm (1M PHY) | **CONFIRMADO** |
| 10 | Margem de link >10 dB pior caso | **CONFIRMADO c/ ressalva** (≈10–11 dB; no limite) |
| 11 | n = 2,5–4 + corpo 10–20 dB | **CONFIRMADO** (faixa de literatura, conservadora) |
| 12 | ±6 dB → +58,5 % / −36,9 % (n=3) | **CONFIRMADO** (assimetria correta) |
| 13 | DEC1=1; VDD = 9/25/32 | **CONFIRMADO** — projeto certo; **facts file §1.1 errado** |
| 14 | nRESET=16, SWDCLK=17, SWDIO=18 | **CONFIRMADO** |
| 15 | ANT=19; VSS=20/29 + die pad | **CONFIRMADO** |
| 16 | DEC2=21, DEC3=22; XC1=23, XC2=24 | **CONFIRMADO** (números de pino) |
| 17 | DEC4=30, DCC=31 + DC/DC 10 µH | **CONFIRMADO** (topologia DCC→L2→DEC4, C10 1.0 µF) |
| 18 | Rede Π RF (L1/C3/L3/C7) = "referência Nordic" | **DIVERGENTE (topologia)** — valores existem no BOM Nordic, mas a Π de 4 elementos no caminho RF **não é** o circuito de referência |
| 19 | Cristal CL=8 pF → 2×12 pF | **CONFIRMADO** |
| 20 | C8 100 nF em DEC2+DEC3 "obrigatório" | **DIVERGENTE** — ref Nordic: DEC3→100 pF, DEC2→N.C., C8 é do VDD |
| 21 | Ferrite entre bateria e bobina NFC | **CONFIRMADO** (física + prática padrão) |
| 22 | Geometria Ø32 mm | **CONFIRMADO c/ ressalva** (variante A com E73 fica apertada) |
| 23 | EWMA α ≈ 0,15–0,25 | **CONFIRMADO** (firmware usa 0,2) |
| 24 | Unidades de scan ESP32 (0.625 ms) | **CONFIRMADO** (API em ms; 0.625 ms é a unidade HCI interna) |
| 25 | MDBT42Q = nRF52832 vs S112 | **CONFIRMADO** (incompatível com S112; resolvido pelo E73) |
| 26 | ANATEL por módulo | **CONFIRMADO** (princípio; certificado do E73 = item aberto) |
| 27 | Aritmética do orçamento | **CONFIRMADO** (todas as somas fecham) |

**Balanço: 21 CONFIRMADO (6 com ressalva/matiz) · 4 DIVERGENTE (1, 18, 20, + mapeamento linear
bateria [extra]) · 0 INVERIFICÁVEL sem tratamento** (os itens sem dado de datasheet exato estão
marcados como estimativa dentro dos vereditos 3/4).

---

## Detalhamento por afirmação

Formato: {afirmação | recalculado (conta) | fonte | veredito}.

### 1. I_a ≈ 5 mA (TX 0 dBm com DC/DC) — **DIVERGENTE (parcial)**

- **Afirmação (RELATORIO §4.1):** I_a ≈ 5 mA.
- **Recalculado / medido no PS:**
  - Feature list PS v1.3: "**4.6 mA peak current in TX (0 dBm)**" — é o **pico do bloco de rádio**, não a corrente de sistema.
  - PS §5.2.1.2 (cenários de sistema, VDD 3 V): **IRADIO_TX1 = 5,8 mA typ** (TX 0 dBm, 1 Mbps, HFXO, **Regulator = DCDC**); IRADIO_TX3 = **10,5 mA** (mesmo cenário com **LDO**).
- **Impacto (recalculado):** com D = 0,2 % e I_s = 1,5 µA:
  - I_a = 5,0 mA → I_avg = 0,002·5000 + 0,998·1,5 = **11,50 µA** → 190.000 µAh / 11,50 = **16.522 h ≈ 1,89 a**
  - I_a = 5,8 mA → I_avg = 0,002·5800 + 0,998·1,5 = **13,10 µA** → **14.504 h ≈ 1,66 a**
  - I_a = 10,5 mA (sem DC/DC) → I_avg = **22,50 µA** → **8.444 h ≈ 0,96 a** (fica **abaixo** de 12 meses)
- **Conclusão:** o número correto para a matemática de bateria é **5,8 mA** (sistema, DC/DC). O 4,6 mA citado como "fato real" é o pico do rádio (feature list) — ambos existem no PS, mas medem coisas diferentes. A autonomia continua acima da meta de 6–12 meses **desde que o DC/DC esteja habilitado** (ver Extra E2 — risco na variante A).
- **Fonte:** PS v1.3 feature list + §5.2.1.2 (espelho: datasheet.chipsmall.com/nRF52810-QCAA-R_Nordic-Semicon/877779.pdf; oficial: docs.nordicsemi.com/bundle/nRF52810-PS/).

### 2. I_s ≈ 1,5 µA (System ON + RTC) — **CONFIRMADO**

- **Recalculado:** PS §5.2 electrical spec: **ION_RAMON_RTC = 1,5 µA typ** (System ON, full 24 kB RAM, wake on RTC, **LFRC**). Com LFXO: ION_RAMON_RTC_LFXO = 1,1 µA. System OFF: 0,3 µA (no RAM) / 0,5 µA (full RAM).
- O firmware usa LFCLK default (RC) → **1,5 µA é o número certo** para este design.
- **Fonte:** PS v1.3 §5.2.1.3 (tabela Power management).

### 3. t_a = 3 ms (adv em 3 canais) — **CONFIRMADO (estimativa conservadora)**

- **Recalculado:** advertising **NONCONNECTABLE_NONSCANNABLE** (main.c) → sem SCAN_RSP. Pacote ADV_NONCONN_IND com payload do projeto (~23–31 octets no ar): preamble 1 + AA 4 + PDU ~23 + CRC 3 ≈ 31 octets ≈ **248 µs** (1 Mbps). Evento = 3 × (ramp-up ~40–140 µs + pacote 248 µs) + 2 gaps inter-canal (~150 µs) ≈ **1,2–1,8 ms**, + partida do HFXO (~0,3–0,5 ms) ≈ **1,5–2,3 ms**.
- **Veredito:** 3 ms é um **teto conservador** plausível (não é constante de datasheet). Para a bateria, conservador = seguro. Sensibilidade: se t_a real = 1,5 ms → I_avg ≈ 6,5 µA → autonomia ≈ 29.200 h ≈ 3,3 a (t_a é a incerteza dominante, junto com a capacidade útil).
- **Fonte:** Bluetooth Core Spec Vol. 6 Part B §4.4.2 (estrutura do evento de advertising); PS (ramp-up/HFXO).

### 4. CR2032 220 mAh → 180–200 mAh úteis + R_int vs pulso 5 mA — **CONFIRMADO c/ matiz**

- **Nominal:** Energizer CR2032 = **235 mAh** (15 kΩ → 2,0 V, 21 °C — verificado no PDF); Panasonic = 225 mAh; Murata = 220 mAh. "220 mAh nominal" está na faixa de mercado (210–240) — ok/conservador.
- **180–200 mAh úteis sob pulso:** **nenhum datasheet publica curva exata para o perfil do projeto** (picos 5,8 mA, duty 0,2 %, média ~13 µA). Interpolação honesta: 15 kΩ (0,19 mA) = 235 mAh; ~3 kΩ (~1 mA) ≈ 200 mAh; carga média do projeto é ~13 µA com picos curtos → capacidade esperada **entre 200 e 235 mAh**; o derate para **180–200 mAh** (autodescarga ~1 %/a — desprezível — + sag sob pulso + tolerância de fabricante) é razoável. **Marcar como estimativa** (o número exato só com medição).
- **R_int vs pulso 5,8 mA:** dados de pulso Energizer (fundo 0,19 mA @2,9 V; pulso 400 Ω ≈ 6,8 mA @2,7 V) → ΔV ≈ 0,2 V / ΔI ≈ 6,6 mA → **R_eff ≈ 30 Ω** (dinâmico, meio de vida; fresca ~10–20 Ω; sobe no fim). Sag no pico: 5,8 mA × 10–30 Ω ≈ **0,06–0,17 V** (fresca) a ~0,3 V+ (fim de vida). UVLO do nRF52810 = 1,7 V → sem risco de brownout até o fim da plataforma da CR2032. Pulso 5,8 mA ≪ 15 mA max pulse (Jauch). **Seguro.**
- **Fonte:** data.energizer.com/pdfs/cr2032.pdf; Jauch CR2032 (via facts file); Panasonic CR2032.

### 5. Autonomia 16.500 h ≈ 1,9 anos — **CONFIRMADO (aritmética), com sensibilidade declarada**

- **Recalculado do zero:** T = 1500 ms; t_a = 3 ms → D = 3/1500 = **0,002 (0,2 %)** ✓.
  - I_avg = D·I_a + (1−D)·I_s = 0,002·5000 + 0,998·1,5 = 10,0 + 1,497 = **11,497 µA** ✓ (RELATORIO: 11,5).
  - Capacidade útil adotada: 190.000 µAh (ponto médio de 180–200 mAh).
  - Autonomia = 190.000 / 11,497 = **16.526 h**; 16.526 / 8.766 h/a = **1,885 anos ≈ 1,9 a** ✓.
- **Com I_a corrigido (5,8 mA):** I_avg = 13,10 µA → **14.504 h = 1,66 a** — ainda > meta de 6–12 meses.
- **Sem DC/DC (LDO, I_a = 10,5 mA):** I_avg = 22,50 µA → **8.444 h = 0,96 a** — **perde a meta de 12 meses**. O DC/DC é condição do resultado (firmware habilita ✓; variante B tem L2/C10 ✓; variante A: ver Extra E2).
- **Fonte:** contas acima; PS para I_a/I_s.

### 6. Margem para adv 1 s — **CONFIRMADO**

- **Recalculado:** T = 1000 ms → D = 0,003.
  - I_a = 5,8 mA: I_avg = 0,003·5800 + 0,997·1,5 = 17,40 + 1,50 = **18,90 µA** → 190.000/18,90 = **10.053 h = 1,15 a** (com 180 mAh: 9.524 h = 1,09 a).
  - I_a = 5,0 mA: I_avg = 16,50 µA → **11.515 h = 1,31 a**.
- Ambos > 12 meses → a afirmação do RELATORIO ("dá margem para 1 s sem comprometer a meta") **fecha**, inclusive com o I_a corrigido.

### 7. TX default 0 dBm — **CONFIRMADO**

- **Recalculado:** PS §6.14.14.30 RADIO.TXPOWER: **Reset = 0x00000000**; código 0x00 = **0 dBm** (escala: −20…+4 dBm em passos de 4 dB). O firmware não escreve TXPOWER e o S112 não altera o reset → default real = 0 dBm.
- **Fonte:** PS v1.3 §6.14.14.30 (p. 202).

### 8. FSPL(10 m, 2400 MHz) = 60 dB — **CONFIRMADO**

- **Recalculado (forma do RELATORIO, d em metros):** FSPL = 20·log10(d) + 20·log10(f_MHz) − 27,55 = 20·log10(10) + 20·log10(2400) − 27,55 = 20 + 67,604 − 27,55 = **60,05 dB** ✓.
- **Forma km (pedida na tarefa):** 32,44 + 20·log10(0,01 km) + 67,604 = 32,44 − 40 + 67,604 = **60,04 dB** ✓ (idêntica).
- **Fonte:** derivação padrão FSPL; conta acima.

### 9. Sensibilidade −96 dBm (1M PHY) — **CONFIRMADO**

- **Fonte:** PS v1.3 feature list: "**−96 dBm sensitivity in Bluetooth low energy mode**" (1 Mbps). 2 Mbps = −93 dBm.
- **Fonte:** PS v1.3 feature list; product brief.

### 10. Margem de link >10 dB no pior caso — **CONFIRMADO c/ ressalva**

- **Recalculado:** PL_max = P_TX − Sens = 0 − (−96) = **96 dB**. FSPL(10 m) = 60 dB → sobra **36 dB** para clutter + antenas. Com o pior caso adotado (25 dB de clutter/corpos): 96 − 60 − 25 = **11 dB**. Com ganhos médios reais das antenas chip (−0,5 dBi × 2 ≈ −1 dB): **≈10 dB**.
- **Ressalva:** ">10 dB" é **no limite** (10–11 dB), não folga confortável — a frase do RELATORIO é aritmeticamente correta mas deve ser lida como "margem apertada". Alavanca disponível: TX +4 dBm (max do chip) adiciona 4 dB se o teste de campo exigir.
- **Fonte:** contas acima + Johanson (ganho médio −0,5 dBi typ).

### 11. n = 2,5–4 + corpo 10–20 dB — **CONFIRMADO (faixa de literatura, conservadora)**

- **Recalculado/justificado:** expoente de path loss indoor: LOS ~1,6–1,8; obstructed/cluttered 2,5–4 (Rappaport, *Wireless Communications*, tabela clássica de expoentes). Corpo humano @2,4 GHz: estudos de body-loss (IEEE/BLE) dão tipicamente **5–10 dB** (dispositivo no pulso/bolso) e **15–20 dB** no pior caso NLOS (corpo direto entre tag e gateway). A faixa 10–20 dB do RELATORIO é o envelope pessimista — adequado para dimensionar pior caso.
- **Fonte:** literatura de propagação (Rappaport; estudos IEEE body-loss 2,4 GHz). Sem URL única — faixa consolidada de literatura.

### 12. ±6 dB → +58,5 % / −36,9 % (n = 3) — **CONFIRMADO**

- **Recalculado:** d = d₀·10^(ΔL/(10·n)).
  - +6 dB, n=3: 10^(6/30) = 10^0,2 = **1,585 → +58,5 %** ✓
  - −6 dB, n=3: 10^(−0,2) = **0,631 → −36,9 %** ✓ (assimetria correta — o "±58 %" do RELATORIO é a simplificação simétrica; a forma assimétrica é a rigorosa)
  - n=2,5 (pedido na tarefa, 10^(6/25)): 10^0,24 = **1,738 → +73,8 %** / 0,575 → **−42,5 %** (pior).
- **Conclusão:** reforça a tese do RELATORIO (RSSI → zona, não trilateração).

### 13. Pinagem QFN32: DEC1=1; VDD = 9/25/32 — **CONFIRMADO (projeto certo; facts file errado)**

- **Recalculado/verificado (PS v1.3, Tabela 114 "QFN32 pin assignments", p. 390–391):**
  pin 1 = DEC1; **pin 9 = VDD**; **pin 25 = VDD**; **pin 32 = VDD**; die pad = VSS.
- **Três fontes independentes convergem:** Tabela 114 do PS; DevZone #53125 ("pin 32 … is VDD", "pin 9 is also VDD"); símbolo KiCad `MCU_Nordic:nRF52810-QCxx` (VDD em 9/25/32).
- **⚠️ O `datasheet_facts_nordic.md` §1.1 afirma "VDD = 25 único", pino 29 = NC, DEC4=31, DCC=32 e lista um "P0.29" que não existe no QFN32 — está ERRADO.** Seguindo essa tabela, DEC4/DCC/VDD ficariam deslocados em 1 pino e o esquema não funcionaria. O resumo do facts file ("pinagem do projeto é INCORRETA") **inverte o veredito real**. A pinagem do projeto (9/25/32, VSS 20/29+pad, DEC4=30, DCC=31) é a correta.
- **Fonte:** PS v1.3 Tabela 114; devzone.nordicsemi.com/f/nordic-q-a/53125; /usr/share/kicad/symbols/MCU_Nordic.kicad_sym.

### 14. nRESET=16, SWDCLK=17, SWDIO=18 — **CONFIRMADO**

- Tabela 114: 16 = P0.21/**nRESET** (configurável); 17 = **SWDCLK** (digital input); 18 = **SWDIO**. Bate com BOM/netlist/designator_map e com os TPs como-construídos.
- Nota: P0.21 só é RESET se UICR.PSELRESET estiver programado; por default é GPIO — R1 10k DNP é decisão segura.

### 15. ANT=19; VSS=20/29 + die pad — **CONFIRMADO**

- Tabela 114: 19 = ANT (RF single-ended); 20 = VSS (radio supply); 29 = VSS; die pad = VSS ("must be connected to ground"). Bate com netlist_conexoes.md e designator_map.md.

### 16. DEC2=21, DEC3=22; XC1=23, XC2=24 — **CONFIRMADO (números de pino)**

- Tabela 114: 21 = DEC2 ("1.3 V regulator supply decoupling (radio supply)"); 22 = DEC3 ("Power supply decoupling"); 23/24 = XC1/XC2 (cristal 32 MHz). Os **números** estão certos no projeto; o **desacoplo** associado é o problema — ver afirmação 20.

### 17. DEC4=30, DCC=31 + DC/DC 10 µH — **CONFIRMADO**

- Tabela 114: 30 = DEC4 ("1.3 V regulator supply decoupling / input from DC/DC / output from 1.3 V LDO"); 31 = DCC ("DC/DC regulator output").
- **Topologia (verificada na Fig. 14 "DC/DC regulator setup", p. 50, e na Fig. 146 por extração vetorial):** **DCC → L2 10 µH → DEC4**, com **C10 1,0 µF de DEC4 para GND**. Exatamente o que netlist_conexoes.md e designator_map.md especificam (L2 entre DCC-31 e DEC4-30).
- **Detalhe da referência:** o ladder Nordic desenha **L3 15 nH em série** com L2 (DCC→L2→L3→DEC4; 10 µH + 15 nH ≈ 10,015 µH — eletricamente ≈10 µH; função de isolamento RF do nó comutado). Corroborado pelo Raytac MDBT42Q: *"When using DC-DC mode, please add L2 / L3 / C14"*. O projeto usa L3 na rede RF e **omite o L3 do ladder DC/DC** — desvio menor e documentável (ver 18).
- Tabela 123: L2 = 10 µH, **IDC,min = 50 mA**, ±20%, 0603 ✓ (o projeto exige Isat>50 mA ✓).
- **Fonte:** PS v1.3 §5.3.1 Fig. 14, §7.3.4 Fig. 146 + Tabela 123 (vetores extraídos); Raytac MDBT42Q datasheet §8.

### 18. Rede Π RF (L1=3,9 nH / C3=0,8 pF / L3=15 nH / C7=100 pF) — **DIVERGENTE (topologia)**

- **Valores:** os quatro valores **existem** no BOM de referência Nordic (Tabela 123, QCAA QFN32 c/ DC/DC) ✓.
- **Topologia (o problema):** a Fig. 146 (extraída vetor a vetor) mostra o casamento RF da referência como **2 elementos**: **ANT(19) → C3 0,8 pF (shunt) → L1 3,9 nH (série) → RF**. Na referência, **L3 15 nH está no ladder do DC/DC** (ver 17) e **C7 100 pF é o desacoplo de DEC3** — **nenhum deles está no caminho de antena**. A Π de 4 elementos (L1 série → C3 shunt → L3 série → C7 shunt) do projeto **não é o circuito de referência do PS**.
- **Contexto que salva na prática:** o Johanson 2450AT18A100E recomenda exatamente uma topologia **π (shunt-série-shunt)** — com valores do EVB dele (2,7 nH / 1,0 pF / 3,9 nH) — e avisa: *"The matching values and topology on client's PCB will be different"*. O PS diz o mesmo ("use the PCB layouts and component values provided by Nordic"; matching depende do PCB). Ou seja: π é topologia razoável, mas os valores como-construídos são **ponto de partida para tuning com VNA**, não "a referência Nordic".
- **Impacto:** documentação incorreta (risco de alguém tratar a Π como rede validada); elétrico: a rede final será ajustada em bancada de qualquer forma. **Ação:** rotular a rede como "topologia π genérica, valores de partida — NÃO é o ref. Nordic"; opcionalmente alinhar com a Fig. 146 (C3 shunt + L1 série) como ponto de partida mais fiel.
- **Fonte:** PS v1.3 §7.3.4 Fig. 146 (geometria vetorial); Johanson 2450AT18A100E datasheet p.2.

### 19. Cristal CL=8 pF → 2×12 pF — **CONFIRMADO**

- **Recalculado:** CL = (C1·C2)/(C1+C2) + C_stray; com C1=C2=C: C = 2·(CL − C_stray). Com C_stray ≈ 2 pF/pino: C = 2·(8−2) = **12 pF** por lado ✓.
- **Referência Nordic:** Tabelas 122/123 — X1 = 32 MHz, **Cl = 8 pF**, ±40 ppm + C1/C2 = **12 pF NP0 ±2%** (0402). O projeto replica exatamente.
- **Fonte:** PS v1.3 Tabelas 122/123; DevZone (fórmula com C_pcb+C_pin ≈ 4 pF total → mesmo resultado).

### 20. C8 100 nF em DEC2+DEC3 "obrigatório/crítico" — **DIVERGENTE**

- **O que a referência Nordic realmente mostra (Fig. 146, vetores):**
  - **DEC3 (22) → C7 100 pF → GND**
  - **DEC2 (21) → C6 N.C. → GND** (posição de tuning, **não montada**)
  - **C8 100 nF é desacoplo de VDD** (pino 25 no QFN32 / pino 36 no QFN48 — verificado por coordenada de stub)
  - VDD fica com **C5 100 nF (pino 9) + C8 100 nF (pino 25) + C9 4,7 µF bulk**; DEC1 com C4 100 nF.
- **O projeto faz:** DEC2+DEC3 **amarrados** com C8 100 nF único; DEC3 fica sem o 100 pF; VDD fica com C4 100 nF + C9 4,7 µF (um 100 nF a menos que a referência).
- **Avaliação:**
  1. A afirmação "**sem isso o rádio não atende ao datasheet**" **não é suportada pelo PS** — o próprio circuito de referência deixa DEC2 sem capacitor montado.
  2. Amarrar DEC2+DEC3 só é eletricamente inócuo se forem o mesmo rail interno de 1,3 V — **o PS não documenta isso**. Se forem nós distintos, o tie externo é um desvio num domínio crítico de RF.
  3. Colocar 100 nF onde a referência manda 100 pF (DEC3) muda a impedância de desacoplo do domínio de rádio.
- **Impacto:** provavelmente funcional (capacitores extras em rails de 1,3 V raramente quebram), mas é **desvio não documentado do reference design** num ponto que o próprio projeto rotula de crítico. **Ação recomendada:** seguir a Fig. 146 (C7 100 pF→DEC3; C6 N.C.→DEC2; C8 100 nF→VDD, restaurando 2×100 nF + 4,7 µF em VDD) **ou** obter confirmação Nordic/DevZone para o tie. O cross-check 5.2 deve registrar isso.
- **Fonte:** PS v1.3 §7.3.4 Fig. 146 (extração vetorial pino a pino); Tabela 123.

### 21. NFC: ferrite entre bateria e bobina — **CONFIRMADO**

- **Física (recalculada qualitativamente):** metal dentro do campo da bobina → correntes de Foucault (Lenz) → derruba L_eff e Q, desloca a ressonância de 13,56 MHz → leitura vai a ~zero. Folha de ferrite (µ alta, perdas baixas) entre bateria e bobina desvia o fluxo e restaura o acoplamento — prática padrão em NFC de celular e em inlays sobre metal (guias de antena NXP).
- **Fonte:** NXP NFC antenna design guidance (ferrite shielding para antenas próximas de metal/bateria); física padrão de acoplamento indutivo.

### 22. Geometria Ø32 mm — **CONFIRMADO c/ ressalva**

- **Recalculado/verificado:** CR2032 = **Ø20,0 × 3,2 mm** (Energizer/Panasonic) ✓. AirTag = **Ø31,9 mm** (spec Apple) ✓ — a comparação do RELATORIO está correta. Inlay NTAG213 circular ~25 mm na borda + bateria Ø20 no centro + ferrite ~20–22 mm: empilha em Ø32 com anel livre de ~3,5 mm — **coerente para a variante B** (antena chip + passivos).
- **Ressalva (variante A):** o E73-2G4M04S tem **17,5 × 28,7 mm** (footprint KiCad oficial; confirma `pesquisa_modulo_ble.md`) — 28,7 mm dentro de Ø32 deixa **~1,6 mm de margem no eixo longo** e o corpo do módulo invade a região do anel NFC/bateria. Cabe geometricamente, mas é **apertado** — validar no modelo 3D antes de fechar a variante A.
- **Fonte:** Energizer CR2032 PDF; Apple AirTag specs; footprint KiCad `RF_Module:E73-2G4M04S`.

### 23. EWMA α ≈ 0,15–0,25 — **CONFIRMADO**

- **Verificado no código:** `gateway_esp32.ino` linha 32: `EWMA_ALPHA = 0.2f` ∈ [0,15; 0,25] ✓; fórmula implementada (linha 68): `EWMA_ALPHA*raw + (1-EWMA_ALPHA)*prev` = exatamente a do RELATORIO §4.4 ✓. Primeira amostra inicializada com o valor raw (linha 67) — correto.
- **Fonte:** gateway_esp32/gateway_esp32.ino.

### 24. Unidades de scan ESP32 (0.625 ms) — **CONFIRMADO**

- **Verificado:** na API ESP32 BLE Arduino (Bluedroid), `BLEScan::setInterval(uint16_t intervalMSecs)` e `setWindow()` recebem **milissegundos** e convertem internamente: `m_scan_params.scan_interval = intervalMSecs / 0.625` (fonte: espressif/arduino-esp32, libraries/BLE/src/BLEScan.cpp). A unidade **0.625 ms é a unidade HCI/BLE nativa** — o firmware não precisa lidar com ela.
- **Como-construído:** `setInterval(100)` / `setWindow(99)` = 100 ms / 99 ms → intervalo 160 unidades, janela ~158 → duty ≈ 99 % (scan quase contínuo) ✓; `setActiveScan(false)` (passivo) é **coerente** com a pulseira em ADV_NONCONN_NONSCANNABLE (não há scan response para pedir) ✓; `start(1.0, false)` + loop = varredura contínua em blocos de 1 s ✓.
- **Fonte:** github.com/espressif/arduino-esp32 (BLEScan.cpp); gateway_esp32.ino linhas 133–135, 143.

### 25. MDBT42Q = nRF52832 vs S112 — **CONFIRMADO**

- **Verificado:** Raytac MDBT42Q-512KV2 = **Nordic nRF52832** (512 kB flash / 64 kB RAM, BT 5.x) — datasheet oficial Raytac. O firmware declara **S112 (nRF52810)** → incompatível (exigiria migração para S132).
- **Como-construído:** a variante A usa **E73-2G4M04S-52810** (nRF52810, S112 direto — pin definition Ebyte confirma nRF52810) → divergência **resolvida na prática**. Nota de custo: `BOM_custos_prototipos.csv` orçou o módulo como MDBT42Q-512KV2 (US$ 6,50); o E73 custa ~US$ 3,59 (Ebyte store) → o orçamento tem ~US$ 2,9/un de folga nesse item.
- **Fonte:** raytac.com (MDBT42Q-512KV2 datasheet Ver P); cdebyte.com/products/E73-2G4M04S1A.

### 26. ANATEL por módulo — **CONFIRMADO (princípio; certificado específico = item aberto)**

- **Verificado:** Lei 9.472/1997 exige homologação de equipamentos que emitem RF; usar módulo já homologado permite o enquadramento como equipamento derivado (processo muito mais simples que homologar design discreto próprio). `pesquisa_modulo_ble.md` registra ANATEL como **"não verificado online → item aberto"** para todos os 4 candidatos — tratamento honesto e coerente com o plano (não bloqueia).
- **Item aberto real:** o E73 (Ebyte) publica FCC/CE/TELEC; **certificado ANATEL do E73 não localizado online** — confirmar com Ebyte/suporte antes de operação com público. Para bancada/laboratório interna, não bloqueia.
- **Fonte:** Lei 9.472/1997; pesquisa_modulo_ble.md §2/§3.1.

### 27. Aritmética do orçamento — **CONFIRMADO**

- **Recalculado (`ORCAMENTO_PROTOTIPAGEM.md`):**
  - NRE: 15 + 60 + 80 + 60 + 30 + 20 = **265** ✓
  - Unidade: 9,15 + 13,50 + 12,00 = **34,65** ✓; ×5 = **173,25** ✓
  - BOM eletrônica (`BOM_custos_prototipos.csv`): 6,50 + 1,00 + 0,80 + 0,40 + 0,30 + 0,10 + 0,05 = **9,15** ✓ (bate com a linha "BOM 9,15")
  - Total USD: 265 + 173,25 + 50 = **488,25** ✓
  - R$ (×5,15): NRE 1.364,75 ✓; unidades 892,24 ✓; frete 257,50 ✓; **total 2.514,49 ≈ R$ 2.514,00** ✓; médio 488,25/5 = 97,65 → R$ 502,90 ≈ 503 ✓
- **Gateway ESP32 não incluído** ✓ (confirmado — coerente com o plano; carrier DevKitC ~R$ 50–100/un quando for o caso).
- **Fonte:** ORCAMENTO_PROTOTIPAGEM.md; BOM_custos_prototipos.csv (somas refeitas).

---

## Itens extras (as-built e divergências fora da lista de 27)

### E1. RELATORIO §2.2 (linha ~44): L1/L2/L3 com atribuições trocadas — **CONFIRMADO como divergência documental**

- Texto: *"Os valores de L1/L2/L3 do documento original (**10 µH, 15 nH, 3.9 nH**) batem com o circuito de referência oficial"* — atribui L1=10 µH, L2=15 nH, L3=3,9 nH.
- **Canônico (BOM/netlist/designator_map/ref. Nordic):** **L1 = 3,9 nH (RF série) · L2 = 10 µH (DC/DC) · L3 = 15 nH (RF)**.
- Os valores **como conjunto** batem com o BOM Nordic (Tabela 123), mas a **atribuição por designator na frase está trocada**. Montagem literal pela frase → DC/DC com 15 nH e casamento RF com 10 µH → **rádio morto/instável**. Corrigir o texto do RELATORIO.

### E2. Variante A (E73) × firmware DC/DC — **RISCO a confirmar**

- `firmware/main.c` linha 52: `sd_power_dcdc_mode_set(NRF_POWER_DCDC_ENABLE)`.
- A netlist como-construída da variante A deixa **DEC1(14), DEC2(3), DEC3(4), DEC4(12), DCC(13) do E73 em NC** — sem L2/C10 externos. Módulos do mercado tipicamente **não** incluem o filtro DC/DC (Raytac manda adicionar L2/L3/C14 externos no modo DC-DC).
- **Se o E73 não tiver o LC interno:** habilitar DC/DC na variante A degrada/instabiliza o rail de 1,3 V (e a autonomia cai se desabilitar: 1,66 a → 0,96 a). **Ação:** confirmar no esquemático do E73 (download Ebyte) se há indutor DC/DC a bordo; senão, (a) não habilitar DCDC na variante A, ou (b) adicionar L2 10 µH + C10 1,0 µF (+L3 15 nH) na placa carrier da variante A. *(Não verificado online — o PDF do E73 não baixou; marcado como pendência.)*

### E3. As-built variante A — SWD e alimentação — **CONFIRMADO**

- `wristband_modulo.net`: TP3→U1 pin **37 (SWDCLK)**, TP2→pin **38 (SWDIO)**, VDD_BAT→pin **16 (VCC)**, GND→pins **0/1/2/15/42/43** — **idêntico** ao pin definition oficial Ebyte ✓. Faixa VCC 1,8–3,6 V cobre a CR2032 (3,0→2,0 V) ✓. TAG1 (ANT1/ANT2) NC no esquema — coerente com inlay adesivo off-board (documentar que os pads são representação).

### E4. As-built gateway — **CONFIRMADO**

- `gateway_esp32.net`: 5V→J2-19, EN→J2-2 (R1 10k pull-up p/ 3V3 + SW1 p/ GND), 3V3→J2-1, GND em J2-14/J3-1/J3-7 — confere com o pinout do ESP32-DevKitC V4 (User Guide Espressif, citado no próprio símbolo). R1 externo é redundante com o pull-up onboard do DevKitC (inofensivo). Restante dos pinos NC ✓ (firmware não usa GPIO).

### E5. Variante B — netlist exportada **AUSENTE**

- `wristband_discreto/exports/` está **vazio** (sem `.net`, sem ERC, sem PDF) — o passo 4.1 não completou as exportações (o `.kicad_sch` existe, 73 kB, com os valores corretos: 12 pF×2, 0,8 pF, 100 nF, 100 pF, 1,0 µF, 10 µH, 3,9 nH, 15 nH, 4,7 µF, CL=8 pF, 2450AT18A100E, 18 no_connect). **O cross-check 5.2 não pode rodar sem a netlist** — regenerar (`kicad-cli sch export netlist ...`) antes do 5.2.

### E6. `datasheet_facts_nordic.md` §1.1 — pinagem errada (ver afirmação 13)

- Corrigir a tabela §1.1 e o resumo ("Summary: Project Claims") que inverte o veredito. Os demais itens do arquivo conferem com as fontes primárias.

### E7. XL1/XL2 (pinos 2/3) NC — nota de clock

- Com os pinos 2/3 NC, o LFCLK só pode usar o **RC interno** (default do S112 — consistente com I_s = 1,5 µA). Se no futuro o firmware habilitar LFXO (precisão de RTC), será necessário o cristal de 32,768 kHz (X2 opcional da ref. Nordic, CL=9 pF). Hoje: OK.

### E8. Contagem dos 16 NC — **CONFIRMADO**

- Pinos 2–8 (7) + 10–15 (6) + 26–28 (3) = **16** ✓; todos são GPIO na Tabela 114; pino 9 (VDD) corretamente **fora** da lista; pino 16 (P0.21/nRESET) tratado por R1 DNP ✓.

---

## Bugs de firmware/gateway — fora do escopo hardware (sinalizados, não corrigidos)

Todos confirmados por leitura direta do código:

1. **`firmware/main.c` — bateria placeholder:** `vbat = 3.0f` hardcoded (SAADC comentado, linha 64–65) → `battery_pct` é **sempre 100 %** no payload. O mapeamento linear 3,0→2,0 V (linhas 66–68) nunca roda com dado real.
2. **`gateway_esp32.ino` — filtro de Company ID morto:** `expected` é calculado (linha 83–84) e **nunca comparado** com `MFG_COMPANY_ID_HEX` — o comentário "(comparacao simplificada...)" não esconde que a comparação não existe. Qualquer advertiser BLE entra na telemetria.
3. **`gateway_esp32.ino` — credenciais hardcoded:** `WIFI_SSID="PUB_WIFI"`, `WIFI_PASSWORD="SENHA_AQUI"`, `MQTT_BROKER="192.168.0.10"` sem mecanismo de provisioning (NVS/env) — inviabiliza deploy em múltiplos gateways.
4. **`gateway_esp32.ino` — `connectWiFi()` bloqueante sem timeout** (loop infinito com delay 300 ms) → gateway trava sem rede.
5. **`gateway_esp32.ino` — `PUBLISH_PERIOD_MS` declarado e nunca usado** (publicação é imediata por pacote; o próprio comentário da linha 99 reconhece).
6. **Mapeamento linear 3,0–2,0 V (claim extra da tarefa) — DIVERGENTE como medidor:** a curva da CR2032 é plana (~2,9–2,8 V por ~80–90 % da capacidade, depois queda íngreme). O mapa linear lê ~80–90 % durante quase toda a vida e despenca no fim — inútil como percentual, aceitável apenas como limiar binário "ok/fraca" (o comentário do próprio código admite: "grosseiro por natureza"). Recomendação: limiar (ex. <2,5 V = fraca) + tendência, não percentual.

---

## Conclusão

- **21/27 CONFIRMADOS** (6 com ressalva explícita), **4 DIVERGENTES** (1: I_a 5→5,8 mA; 18: topologia Π não é o ref. Nordic; 20: C8/DEC2+DEC3; extra: mapeamento linear de bateria), **0 sem veredito**.
- **A pinagem QFN32 do projeto está correta** (9/25/32 etc.) — quem está errado é o `datasheet_facts_nordic.md` §1.1; corrigir antes do critic 6.1.
- **Nenhuma divergência inviabiliza o projeto**: as 4 divergências são de documentação/valores-estimativa e têm correção conhecida; a mais sensível é a 20 (desvio do reference design no domínio de RF) e o risco E2 (DC/DC na variante A).
- **Pendências que bloqueiam passos vizinhos:** (a) exports da variante B vazios → 5.2 não roda; (b) confirmar LC do DC/DC no E73; (c) certificado ANATEL do E73 (item aberto de negócio).
