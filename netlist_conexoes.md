# Netlist de referência — nRF52810 QFN32 (rota discreta corrigida)

Usar apenas se optarem por NÃO usar o módulo BLE certificado recomendado no relatório
(seção 3). Esta tabela já está com a pinagem real verificada no datasheet Nordic
(docs.nordicsemi.com) e serve para digitar as ligações diretamente no editor de esquemático
do KiCad (Place > Wire, ligando os pinos abaixo).

| Rede (net) | Pinos/componentes conectados |
|---|---|
| VDD_BAT | BT1(+), C1(+), C2, VDD pino 9, VDD pino 25, VDD pino 32, TP1 |
| GND | BT1(–), C1(–), C2, die pad exposto (VSS), VSS pino 20, VSS pino 29, TP4, blindagem de ferrite SHLD1 |
| NET_DEC1 | DEC1 (pino 1) — C5 100nF para GND |
| NET_DEC2_DEC3 | DEC2 (pino 21) + DEC3 (pino 22) unidos — C8 100nF para GND (**crítico, ausente no doc original**) |
| NET_DEC4 | DEC4 (pino 30) — C10 1.0µF para GND — também alimenta L2 (10µH) |
| NET_DCC | DCC (pino 31) — outro terminal de L2 (10µH) |
| NET_XC1 | XC1 (pino 23) — X1 (32MHz) — C1_xtal 12pF para GND |
| NET_XC2 | XC2 (pino 24) — X1 (32MHz) — C2_xtal 12pF para GND |
| NET_ANT | ANT (pino 19) — L1 (3.9nH) — nó A |
| Nó A | L1 — C3 (0.8pF) para GND — segue para L3 |
| NET_ANT2 | Nó A — L3 (15nH) — nó B |
| Nó B | L3 — C7 (100pF) para GND — segue para ANT1 |
| NET_ANT_FEED | Nó B — ANT1 (Johanson 2450AT18A100), alimentação |
| NET_SWDIO | SWDIO (pino 18) — TP2 |
| NET_SWDCLK | SWDCLK (pino 17) — TP3 |
| NET_RESET | P0.21/nRESET (pino 16) — deixar livre ou resistor de pull-up 10k para VDD, conforme uso |

**Importante sobre a rede de antena (ANT → ANT1):** a topologia Π (L1–C3–L3–C7) acima é o
ponto de partida da referência Nordic. Na prática, ao montar a placa física, meça S11 com um
VNA e ajuste os valores — principalmente C3 e C7 — até o casamento em 2.4 GHz ficar correto
para o seu plano de terra específico. Deixe footprints 0402 para C3/C7 populáveis com 0Ω
(bypass) e valores alternativos, isso acelera a iteração sem precisar de novo pedido de PCB
a cada teste.

## Camadas e keep-out (para o layout, não gerado automaticamente aqui)
- 2 camadas, plano de terra na camada inferior.
- Keep-out de cobre sob a antena chip ANT1 e sob a rede de casamento (regra do datasheet Nordic).
- Bobina NFC (dentro do inlay TAG1) não deve sobrepor a área do suporte de bateria BT1 —
  ver seção 2.3/4.5 do relatório técnico.
