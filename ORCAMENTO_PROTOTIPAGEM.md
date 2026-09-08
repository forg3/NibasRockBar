# Orçamento de Prototipagem — 5 Unidades

Câmbio de referência usado: USD 1 = R$ 5,15 (04/set/2026). **Estimativa orçamentária** —
confirmar com cotação formal da PCBWay/JLCPCB antes de fechar pedido; preços de componentes
foram verificados hoje (LCSC/DigiKey/varejo), preços de NRE de montagem são estimativa de
mercado para este porte de placa (poucos componentes, sem QFN solto).

## Custos únicos (NRE — pagos uma vez, cobrem qualquer quantidade pequena)

| Item | Custo estimado (USD) |
|---|---|
| Fabricação da placa nua (mínimo de painel, 5–10 pcs) | 15 |
| Stencil de solda-pasta | 60 |
| Programação de Pick & Place | 80 |
| Inspeção de primeira peça (First Article) | 60 |
| Setup de impressão SLA da cápsula | 30 |
| Flash inicial de firmware + validação (mão de obra) | 20 |
| **Subtotal NRE** | **265** |

## Custos por unidade × 5

| Item | USD/unidade | 5 unidades |
|---|---|---|
| BOM (módulo BLE, NFC, bateria, passivos) | 9,15 | 45,75 |
| Cápsula SLA + berço de pulseira | 13,50 | 67,50 |
| Mão de obra de montagem | 12,00 | 60,00 |
| **Subtotal por unidade** | **34,65** | **173,25** |

## Frete internacional (China → Brasil, envio expresso, lote pequeno)

| Item | USD |
|---|---|
| Frete expresso (DHL/similar) | 50 |
| **Subtotal frete** | **50** |

## Total do lote de 5 protótipos

| | USD | R$ (câmbio 5,15) |
|---|---|---|
| NRE | 265,00 | 1.364,75 |
| Unidades (5×) | 173,25 | 892,24 |
| Frete | 50,00 | 257,50 |
| **TOTAL** | **488,25** | **~R$ 2.514,00** |
| Custo médio por unidade (com NRE amortizado) | 97,65 | ~R$ 503,00 |

## Não incluído neste orçamento
- Homologação ANATEL do módulo BLE (necessária antes de uso com clientes reais; não é
  necessária para testes internos de bancada).
- Licenciamento/adaptador de integração com o sistema de caixa (depende da API/documentação
  do sistema usado pela casa).
- Eventuais rodadas adicionais de PCB caso o casamento de antena BLE precise de ajuste
  (normal em projeto de RF; se necessário, é só o custo de fabricação da placa, não repete o
  NRE de montagem/stencil).
