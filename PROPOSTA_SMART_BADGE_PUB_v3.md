# Pulseira de Identificação e Comanda — Especificação do Produto

## 1. O que é

Pulseira eletrônica vestível, formato disco de perfil baixo (Ø32 mm) em pulseira esportiva de
silicone, para identificação de cliente e localização indoor em bares, cervejarias artesanais e
casas de drinks autorais.

A pulseira identifica o cliente perante o sistema de caixa e permite ao garçom localizar sua
mesa rapidamente. Todo o atendimento — cerveja, drinks autorais e produção da cozinha — continua
sendo feito pela equipe da casa; a pulseira não aciona nada fisicamente, ela só identifica e
localiza.

Fluxo de uso:
1. **Check-in**: na chegada, a equipe vincula uma pulseira livre ao cliente (abre comanda no
   sistema de caixa).
2. **Pedidos**: o garçom aproxima o celular/terminal da pulseira para lançar cada pedido na
   comanda certa, em qualquer mesa.
3. **Localização**: o app do garçom mostra a área/mesa aproximada de cada comanda aberta.
4. **Fechamento**: no caixa, o operador confere a comanda vinculada àquela pulseira, o cliente
   paga, a comanda é encerrada e a pulseira volta ao estoque para o próximo cliente.

## 2. Por que esta solução

- **Menor fricção**: cliente não carrega cartão nem celular, nem decora número de comanda.
- **Erro humano reduzido**: pedido sempre lançado na comanda certa (leitura NFC, não digitação
  de número).
- **Localização assistida**: garçom encontra o cliente certo mesmo em salão cheio, sem precisar
  perguntar "qual é sua mesa".
- **Independência de nuvem**: toda a inteligência de localização roda em servidor local
  (Wi-Fi/MQTT); a comanda e o pagamento continuam no sistema de caixa já usado pela casa.
- **Reutilizável**: pulseira devolvida no caixa, sem custo recorrente por cliente.

## 3. Especificação de hardware

| Item | Decisão |
|---|---|
| Forma/tamanho | Disco Ø32 mm, cápsula IP67 (O-ring), montado em pulseira esportiva de silicone |
| Identificação | NFC passivo — NXP NTAG213, inlay pronto de 25 mm, na borda do disco |
| Localização | BLE 5.x — módulo certificado com SoC Nordic (nRF52810/832), antena chip embutida |
| Bateria | CR2032, verso do disco, com disco de ferrite entre a bateria e a bobina NFC |
| Alcance de bateria | Estimado 1,5–2 anos em advertising a cada 1,5 s |
| PCB | 2 camadas, FR4 0.8 mm, acabamento ENIG |
| Vedação | Anel O-ring + cápsula usinada/SLA — suporta imersão e higienização |

### 3.1 Bill of Materials

| Designator | Componente | Função |
|---|---|---|
| U1 | Módulo BLE certificado (nRF52810/832) | Rádio de localização indoor |
| TAG1 | NTAG213 inlay 25 mm | Identificação/comanda |
| SHLD1 | Folha de ferrite ~20 mm | Isola a bobina NFC da bateria |
| BT1 | Suporte CR2032 (Keystone 1059) | Retentor de bateria |
| BAT1 | Bateria CR2032 | Alimentação |
| C1 | 10 µF X5R 0603 | Desacoplo principal |
| C2 | 100 nF X7R 0402 | Filtro de alta frequência |
| TP1–TP4 | Test pads ENIG 1.0 mm | Gravação de firmware (SWD) |

(BOM completa com custos em `BOM_custos_prototipos.csv`.)

## 4. Backend e aplicativo do garçom

- **Gateways de teto**: ESP32, varredura BLE passiva, filtro de RSSI (EWMA) para reduzir
  flutuação por corpos/reflexos, publicação via MQTT.
- **Servidor local**: Mosquitto (MQTT) + serviço Python (FastAPI) + SQLite, atribuindo cada
  pulseira à zona/mesa mais próxima (vizinho mais próximo com histerese — evita trocas
  espúrias de mesa).
- **App do garçom (PWA, Web NFC API)**: lê a tag da pulseira, sugere a mesa por proximidade,
  e envia o pedido ao sistema de caixa.
- **Divisão de responsabilidade**: este backend cuida só de identificação (par pulseira↔cliente)
  e localização indoor. Pedido, cardápio, pagamento e fiscal permanecem no sistema de caixa da
  casa — sem duplicar sistemas.

## 5. Fabricação

- **Fabricante recomendado**: PCBWay ou JLCPCB, regime turnkey (fabricam a placa, compram os
  componentes do módulo BLE/passivos, soldam via Pick & Place).
- **Entregáveis para cotação**: Gerbers/ODB++, BOM (CSV), CPL/Centroid, gerados no KiCad a
  partir do netlist de referência do módulo BLE escolhido.
- **Cápsula/carcaça**: impressão SLA (resina) no mesmo pedido — PCBWay e Seeed Studio oferecem
  esse serviço combinado.
- **Gravação de firmware**: pogo pins de 4 pontas nos test pads + gravador SWD (J-Link/DAPLink).

Orçamento de prototipagem para 5 unidades: ver `ORCAMENTO_PROTOTIPAGEM.md`.
