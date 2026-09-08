# NibasRockBar — Pulseira Inteligente de Identificação e Localização

Sistema de pulseira eletrônica (NFC + BLE) para identificação de clientes e localização
indoor no salão, integrado ao sistema de caixa **Deli**. Atendimento continua 100% humano —
garçom tira o pedido, equipe serve bebidas e a cozinha prepara os pratos. A pulseira só
identifica o cliente e ajuda a equipe a localizá-lo mais rápido.

## Fluxo do produto

1. **Check-in** — cliente recebe uma pulseira livre; o sistema abre a comanda no Deli.
2. **Pedido** — garçom lê a pulseira (NFC) e lança o pedido na comanda certa, em qualquer mesa.
3. **Localização** — o app do garçom mostra a área do salão onde cada comanda está (BLE).
4. **Conferência e saída** — caixa fecha a comanda no Deli, cliente paga, pulseira libera
   sozinha para o próximo cliente.

## Estrutura do repositório

| Caminho | Conteúdo |
|---|---|
| `PROPOSTA_SMART_BADGE_PUB_v3.md` | Especificação do produto (hardware, fluxo, fabricação) |
| `proposta_proprietario.html` | Proposta visual para apresentar ao proprietário do pub |
| `modelo_3d_prototipo.html` | Modelo 3D interativo do protótipo (pulseira + disco) |
| `ORCAMENTO_PROTOTIPAGEM.md` | Orçamento detalhado para 5 unidades protótipo |
| `BOM_custos_prototipos.csv` | BOM com custo por unidade (lote de teste) |
| `BOM_smartbadge_v2.csv` | BOM recomendada (módulo BLE certificado) |
| `BOM_discreta_corrigida_nRF52810_QFN32.csv` | BOM alternativa (SoC discreto), pinagem verificada no datasheet Nordic |
| `netlist_conexoes.md` | Tabela de conexões pino a pino, pronta para KiCad |
| `RELATORIO_REVISAO_TECNICA.md` | Revisão técnica completa (matemática de bateria, RF, RSSI, NFC) |
| `firmware/main.c` | Firmware da pulseira (nRF5 SDK) — beacon BLE + leitura de bateria |
| `gateway_esp32/gateway_esp32.ino` | Firmware do gateway de teto (scan BLE + filtro EWMA + MQTT) |
| `backend/app.py` | Servidor local (FastAPI) — localização por RSSI + inventário de pulseiras |
| `backend/deli_adapter.py` | Integração real com a API pública do Deli (plataforma Fudo) |
| `integracao_deli/README.md` | Como habilitar e usar a API do Deli |

## Arquitetura (visão geral)

```
Pulseira (NFC + BLE) ──► Gateway ESP32 (scan BLE) ──► MQTT ──► Backend local (FastAPI)
                                                                      │
                                                                      ├─► Localização por mesa/zona
                                                                      └─► Deli API (abre/monitora comanda)

Garçom (app/tablet) ──► lê NFC da pulseira ──► lança pedido direto no Deli
```

- **Identificação (NFC)**: tag passiva na pulseira, lida pelo garçom para abrir/lançar pedidos.
- **Localização (BLE)**: pulseira transmite beacon; gateways de teto (ESP32) captam RSSI e
  publicam via MQTT; o backend decide a zona mais próxima (vizinho mais próximo com histerese).
- **Caixa/pagamento**: sempre no Deli — este projeto não duplica cardápio, pagamento nem fiscal.

## Como rodar o backend localmente

```bash
cd backend
pip install -r requirements.txt
export DELI_API_KEY="..."
export DELI_API_SECRET="..."
uvicorn app:app --host 0.0.0.0 --port 8000
```

Requer um broker MQTT local (ex: Mosquitto) publicando em `pub/telemetria/#`.

## Hardware

- Disco Ø32 mm, cápsula IP67, pulseira esportiva de silicone.
- Identificação: NXP NTAG213 (inlay pronto, 25 mm).
- Localização: módulo BLE certificado (SoC Nordic nRF52810/832).
- Bateria: CR2032, ~1,5–2 anos de autonomia estimada.
- Fabricação recomendada: PCBWay ou JLCPCB, regime turnkey.

Detalhes completos, matemática de engenharia e decisões de projeto: ver
`RELATORIO_REVISAO_TECNICA.md` e `PROPOSTA_SMART_BADGE_PUB_v3.md`.

## Status

Fase de especificação e protótipo — orçamento para lote de 5 unidades de teste em
`ORCAMENTO_PROTOTIPAGEM.md`. Integração com o Deli implementada e documentada, pendente de
credenciais reais (`DELI_API_KEY`/`DELI_API_SECRET`) para teste de ponta a ponta.
