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
| `firmware/nrf/` | Projeto de compilação nRF5 SDK 17.1.0 (pca10040e/s112, nRF52810 + SoftDevice S112 7.2.0) — compila com `make -C firmware/nrf/armgcc` (requer `arm-none-eabi-gcc`) |
| `gateway_esp32/gateway_esp32.ino` | Firmware do gateway de teto (scan BLE + filtro EWMA + MQTT) — compila no Arduino IDE com esquema de partição Huge APP |
| `backend/app.py` | Servidor local (FastAPI) — localização por RSSI + inventário de pulseiras |
| `backend/deli_adapter.py` | Integração real com a API pública do Deli (plataforma Fudo) |
| `integracao_deli/README.md` | Como habilitar e usar a API do Deli |
| `hardware/kicad/docs/decisao_forma_fisica.md` | Decisão da variante A: troca do módulo E73 pelo Fanstel BM832A |
| `hardware/kicad/docs/layout_status.md` | Estado atual dos layouts das placas |
| `hardware/kicad/docs/procedimento_vna.md` | Procedimento de tuning da antena/RF com VNA |
| `hardware/kicad/docs/cotacao_fabricacao.md` | Cotação de fabricação (com GATE — nada submetido ainda) |
| `hardware/kicad/*/exports/fab/` | Pacote de fabricação gerado (Gerbers, furação, BOM, posição) |
| `docs/security-audit/relatorio-auditoria-seguranca.pdf` | Relatório da auditoria de segurança |

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
export NIBAS_API_KEY="..."  # exigida em toda chamada via header X-API-Key
uvicorn app:app --host 0.0.0.0 --port 8000
```

Requer um broker MQTT local (ex: Mosquitto) publicando em `pub/telemetria/#`.

## Hardware

- Disco Ø32 mm, cápsula IP67, pulseira esportiva de silicone.
- Identificação: NXP NTAG213 (inlay pronto, 25 mm).
- Localização (variante A): módulo **Fanstel BM832A** (SoC Nordic nRF52810) — substitui o
  Ebyte E73, decisão documentada em `hardware/kicad/docs/decisao_forma_fisica.md`.
- Bateria: CR2032 com suporte **Keystone 1060** (SMD — o 1059 é THM e não serve),
  ~1,5–2 anos de autonomia estimada.
- Fabricação recomendada: PCBWay ou JLCPCB, regime turnkey.

Detalhes completos, matemática de engenharia e decisões de projeto: ver
`RELATORIO_REVISAO_TECNICA.md` e `PROPOSTA_SMART_BADGE_PUB_v3.md`.
Estado dos layouts: `hardware/kicad/docs/layout_status.md`.
Tuning da antena/RF: `hardware/kicad/docs/procedimento_vna.md`.

## Fabricação

- Pacote de fabricação gerado em `hardware/kicad/*/exports/fab/` (Gerbers, furação, BOM, posição).
- Cotação e checklist de submissão em `hardware/kicad/docs/cotacao_fabricacao.md` —
  **GATE: nada submetido a fabricante ainda.**

## Segurança

- O backend exige autenticação em toda chamada via header `X-API-Key` (chave em `NIBAS_API_KEY`).
- Relatório da auditoria de segurança em `docs/security-audit/relatorio-auditoria-seguranca.pdf`.

## Status

Fase de especificação e protótipo — orçamento para lote de 5 unidades de teste em
`ORCAMENTO_PROTOTIPAGEM.md`. Integração com o Deli implementada e documentada, pendente de
credenciais reais (`DELI_API_KEY`/`DELI_API_SECRET`) para teste de ponta a ponta.

## Pendências

- ANATEL: certificado do módulo não localizado — item aberto (não bloqueia bancada;
  homologação a confirmar antes de operar com público).
- BOM raiz: corrigir Keystone 1059 → 1060.
- Alimentação do BM832A: indutores do DC/DC integrados ao módulo (fonte: página oficial
  Fanstel) — fecha o item aberto #2.
