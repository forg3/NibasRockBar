# Smart Badge Pub — Revisão Técnica e Especificação Corrigida (v2)

Revisão feita cruzando o documento original com a documentação oficial Nordic Semiconductor
(nRF52810 Product Specification, pin assignments QFN32 e Reference Circuitry — consultados
diretamente em docs.nordicsemi.com nesta revisão).

## 1. Veredito rápido

O conceito (NFC passivo para comanda + BLE para localização, servidor local) é sólido e é
exatamente como produtos comerciais reais deste tipo funcionam (ex.: pulseiras de festival com
RFID + beacons BLE de mesa). **O problema não é a ideia, é a implementação em 24 mm de diâmetro**
e alguns erros de datasheet que impediriam o circuito de funcionar como desenhado. Nenhum é
inviabilizante do projeto — todos têm correção conhecida — mas nenhum pode ser ignorado.

## 2. Erros críticos encontrados (verificados no datasheet Nordic)

### 2.1 Pinagem do nRF52810 QFN32 está incorreta
O documento original usa números de pino que não existem no encapsulamento QFN32 real (ex.: cita
VDD nos pinos 13/32, DEC1 no pino 31, cristal nos pinos 2/3, ANT no pino 27). A pinagem real do
**QFN32 (variante QCAA)**, confirmada na documentação oficial, é:

| Sinal | Pino real QFN32 | Observação |
|---|---|---|
| DEC1 | 1 | Desacoplo regulador 0.9V digital |
| VDD | 9, 25, 32 | 3 pinos de alimentação, todos devem ser decoupled |
| SWDCLK | 17 | |
| SWDIO | 18 | |
| ANT | 19 | Saída RF single-ended |
| VSS (rádio) | 20 | |
| **DEC2** | **21** | **Desacoplo regulador 1.3V do rádio — pino obrigatório, omitido no doc original** |
| **DEC3** | **22** | **Desacoplo de alimentação — pino obrigatório, omitido no doc original** |
| XC1 / XC2 | 23 / 24 | Cristal 32 MHz (não pino 2/3) |
| VSS | 29 | |
| DEC4 | 30 | Entrada do DC/DC, saída do LDO 1.3V |
| DCC | 31 | Saída do regulador DC/DC |
| Die pad (exposto) | — | VSS, deve ir para o plano de terra com múltiplas vias |

**Impacto se não corrigido:** com DEC2/DEC3 flutuando ou mal decoupled, o rádio 2.4 GHz não
atende as especificações de potência/sensibilidade do datasheet — na prática, alcance BLE
reduzido, instabilidade, ou falha de certificação. Isso teria passado despercebido até os
primeiros testes de bancada.

### 2.2 Rede de casamento de RF — valores corretos, mas peça errada
Os valores de L1/L2/L3 do documento original (10 µH, 15 nH, 3.9 nH) **batem** com o circuito de
referência oficial da Nordic para QFN32 com DC/DC (o que sugere que a fonte usada era legítima,
só foi mal transcrita). Porém:
- O capacitor C7 do doc original ("1.0 pF de casamento") não existe como peça única — o circuito
  de referência usa **dois** capacitores na malha Π: C3 = 0.8 pF e C7 = 100 pF, em posições
  diferentes da rede.
- Essa malha é calibrada para o **layout de referência da Nordic**, não para a antena chip
  Johanson 2450AT18A100 num plano de terra circular de 24–32 mm. **Só serve como ponto de
  partida.** Fabricação turnkey não inclui ajuste de RF — isso é feito em bancada com VNA
  (analisador de rede) medindo S11 e trocando indutores/capacitores até casar em 2.4 GHz. Prever
  isso no cronograma (normalmente 1–3 rodadas de PCB).

### 2.3 NFC + bateria moeda metálica no mesmo disco de 24–28 mm — conflito físico
Uma CR2032 já tem 20 mm de diâmetro. O suporte metálico (Keystone 1059) ocupa área equivalente.
Uma antena de bobina NFC precisa de uma área livre de metal por baixo/dentro do laço para
acoplar com o leitor (ISO 14443 a 13.56 MHz). Colocar o suporte metálico da bateria dentro (ou
sobreposto) à bobina NFC causa correntes de Foucault na peça metálica, que:
- reduzem o Q da bobina e desalinham a frequência de ressonância de 13.56 MHz;
- na prática, isso reduz alcance de leitura de ~3–5 cm para próximo de zero (tag "morta").

Isso não estava endereçado no documento original — era um problema de dia-1 de bancada.
**Correção:** blindagem com folha de ferrite (mesma técnica usada atrás de baterias em NFC de
celular), bobina fora da área ocupada pela bateria, ou — mais simples e barato — comprar o
NTAG213 já pronto como **inlay adesivo com antena própria** (não como die nu) dimensionado para
ficar na borda do disco, com a bateria posicionada no centro/verso protegido por blindagem.

### 2.4 Homologação ANATEL (não mencionada no documento original)
Qualquer equipamento que transmita rádio frequência para uso/comercialização no Brasil precisa de
homologação ANATEL (Lei 9.472/1997 e resoluções correlatas) — isso vale tanto para BLE quanto
para NFC ativo. Homologar um design próprio de RF do zero é caro e lento para um produto de
pequena/média escala. **Recomendação:** usar um **módulo BLE certificado** (que já embute o
SoC Nordic + antena + casamento de RF pré-validado, ex. linhas Fanstel, Raytac, u-blox
baseadas no nRF528xx) — isso reduz o processo de homologação para "homologação por
módulo/derivada", muito mais simples e barato do que homologar uma antena chip discreta.
**Verificar homologação vigente do módulo escolhido na Consulta de Produtos Homologados da
ANATEL antes de fechar o BOM.**

### 2.5 Torneira de self-pour: falta o subsistema de controle de fluxo
O documento resolve "abrir/autorizar" a torneira via NFC, mas não especifica **quem corta o
fluxo de chope**: isso exige válvula solenoide + medidor de vazão (flow meter de pulso, tipo
turbina hall) por torneira, com sua própria placa controladora (relé/MOSFET de potência,
alimentação 12–24V para a válvula) e lógica de "descontar do saldo enquanto verte". Isso é um
subsistema físico separado e não trivial — não pode ser tratado como "detalhe do backend".
Está fora do escopo elétrico da pulseira, mas precisa entrar no orçamento e cronograma do
projeto como um segundo hardware (placa por torneira).

## 3. Decisões de projeto (v2 — realista e fabricável)

| Item | Decisão |
|---|---|
| Forma/tamanho | Disco de **Ø32 mm** (comparável a uma Apple AirTag, 31.9 mm — não menor, fisicamente não dá para ser menor com bateria moeda + 2 antenas) |
| Rádio | **Módulo BLE certificado** com nRF52810/52832 embutido (elimina ajuste de RF em bancada e simplifica homologação ANATEL) |
| NFC | NTAG213 como **inlay pronto** (antena + chip), diâmetro ~25 mm, anel na borda do disco |
| Bateria | CR2032 no verso, com **disco de ferrite** entre bateria e bobina NFC |
| Empilhamento (stack-up) | PCB 2 camadas, FR4, 0.8 mm, acabamento **ENIG** (contato de bateria e solda confiáveis) |
| Vedação | Anel O-ring + cápsula usinada/SLA, IP67 — mantém-se do doc original, está correto |
| Firmware | nRF5 SDK (S112 SoftDevice) — mais leve que Zephyr para um único produto (beacon), controle direto do DCDC |
| Backend | Mosquitto (MQTT) + servidor local Python (FastAPI) + SQLite/Postgres — mantém-se do doc original |
| Gateways | ESP32, scan BLE passivo, filtro EWMA de RSSI, publica via MQTT |
| Torneira self-pour | **Fora do escopo desta placa** — subsistema à parte (válvula + flow meter), a especificar em projeto dedicado |

## 4. Matemática de engenharia

### 4.1 Autonomia de bateria (CR2032)
Ciclo: acorda a cada T = 1500 ms, ativo por t_a = 3 ms (TX + processamento em 3 canais de
advertising), dorme o resto do tempo.

- Corrente ativa (TX 0 dBm + CPU): I_a ≈ 5 mA
- Corrente em sono (System ON, RTC ativo): I_s ≈ 1.5 µA
- Duty cycle: D = t_a / T = 3/1500 = 0.2%
- Corrente média: I_avg = D·I_a + (1-D)·I_s ≈ 0.002×5000 µA + 0.998×1.5 µA ≈ **11.5 µA**
- Capacidade útil CR2032 (com margem de queda de tensão sob pulso e autodescarga): ~180–200 mAh
  úteis (nominal 220 mAh, deratado)
- Autonomia = 190.000 µAh / 11.5 µA ≈ **16.500 h ≈ 1,9 anos**

Conclusão: a meta de "6 a 12 meses" do documento original é **conservadora e alcançável** — dá
margem inclusive para aumentar a frequência de advertising (ex. 1s) sem comprometer a meta.

### 4.2 Link budget BLE (a rádio-frequência não é o gargalo)
Perda de espaço livre: FSPL(dB) = 20·log10(d) + 20·log10(f_MHz) − 27.55

Para d = 10 m, f = 2400 MHz → FSPL ≈ 60 dB. Em ambiente interno cluttered, adicionar 15–25 dB de
margem (paredes, corpos, refletores metálicos do balcão). Com TX em 0 dBm e sensibilidade do
nRF52810 de aprox. −96 dBm (PHY 1M), sobra **> 10 dB de margem** mesmo no pior caso — ou seja,
o alcance de conexão não é o problema real.

### 4.3 Por que a localização por RSSI é o elo fraco (e como mitigar)
Modelo log-distância: RSSI(d) = RSSI(d0) − 10·n·log10(d/d0) + X_σ

Em pub cheio, o expoente de perda n fica entre 2.5 e 4 (multipercurso + absorção por corpos —
o corpo humano sozinho atenua 10–20 dB em 2.4 GHz). Um erro de apenas ±6 dB na leitura de RSSI
já gera ±58% de erro na distância estimada (com n=3). **Trilateração (x,y) não é realista** com
uma única antena onidirecional por gateway. Recomendação prática, factível com o hardware
proposto:
- Tratar como problema de **classificação de zona** (mesa/grupo de mesas mais próximo), não de
  posição cartesiana — o algoritmo de "vizinho mais próximo com histerese" do doc original já
  está no caminho certo, é a abordagem certa para esse hardware;
- Suavizar leitura com EWMA (ver 4.4) antes de comparar entre gateways;
- Se no futuro for necessário sub-metro de precisão, migrar para nRF52811/nRF5340 com suporte a
  **Direction Finding (AoA)** — fora do escopo do nRF52810.

### 4.4 Filtro de suavização de RSSI (implementado no gateway)
EWMA (média móvel exponencial), simples e barata em CPU (roda tranquilo no ESP32):

RSSI_filt[n] = α·RSSI_raw[n] + (1−α)·RSSI_filt[n−1], com α ≈ 0.15–0.25

Ver implementação real em `gateway_esp32/gateway_esp32.ino`.

### 4.5 Por que a bateria detona o NFC (intuição física)
Acoplamento NFC depende do fator k = M/√(L1·L2) entre a bobina do leitor e a bobina da tag. Uma
peça metálica maciça (suporte da bateria) dentro do campo magnético da bobina se comporta como
uma "espira em curto": por Lenz, ela induz uma corrente que **se opõe** ao campo, derrubando a
indutância efetiva e o Q da bobina, e desloca a frequência de ressonância para longe de
13.56 MHz. Na prática: alcance de leitura cai de ~3–5 cm para ~0. É por isso que celulares e
cartões contactless sempre mantêm a bateria/chip fora do "miolo" da bobina, ou usam uma folha de
ferrite entre os dois.

## 5. O que este pacote entrega vs. o que ainda depende de bancada/humano

**Entregue neste pacote:** BOM corrigida, tabela de conexões (pino a pino, pronta para digitar
no KiCad), firmware da pulseira (esqueleto nRF5 SDK), firmware do gateway ESP32 (completo,
compilável), backend de localização (completo, executável), adaptador de integração com o
sistema de caixa.

**Não é possível/responsável entregar às cegas, sem ferramenta de EDA gráfica e bancada de RF:**
- Arquivo `.kicad_pcb` com roteamento final — layout de RF exige olho humano e, idealmente, o
  layout de referência do fabricante do módulo BLE escolhido (eles fornecem o desenho da área de
  antena pronto, é só copiar).
- Ajuste fino da rede de casamento de antena — depende de medição com VNA na placa física.
- Processo de homologação ANATEL — depende do módulo final escolhido e de laboratório
  credenciado.

Esses três pontos são normais em qualquer projeto de RF real; nenhum fabricante (JLCPCB, PCBWay,
Seeed) os resolve por você — eles fabricam o que você desenhar.
