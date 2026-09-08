# NibasRockBar — Contexto do projeto (ler antes de qualquer tarefa)

Pulseira eletrônica (NFC + BLE) para identificação de clientes e localização indoor no salão
do pub, integrada ao sistema de caixa **Deli** (plataforma Fudo, API pública em `api.fu.do`).

## Decisões já fechadas (não reabrir sem motivo novo)
- **Sem self-service**: garçom tira o pedido, equipe serve tudo. A pulseira só identifica e
  localiza — não aciona nada fisicamente (sem torneira automática, sem válvula).
- **Forma física**: disco Ø32 mm (não 24 mm — não cabe bateria CR2032 + antena BLE + bobina
  NFC nesse tamanho), cápsula IP67, pulseira esportiva de silicone.
- **Rádio**: módulo BLE certificado com SoC Nordic (nRF52810/832), não SoC+antena discretos —
  evita ajuste de RF em bancada e simplifica homologação ANATEL.
- **Identificação**: NXP NTAG213, inlay pronto (não die nu), com blindagem de ferrite entre a
  bobina e a bateria.
- **Fluxo**: check-in (abre comanda no Deli) → pedido (garçom lança no Deli, pulseira só
  identifica) → localização (BLE, assistência ao garçom, não crítico) → checkout automático
  quando o caixa fecha a comanda no Deli (polling de `saleState`, nunca fechamos a comanda
  por conta própria).
- **Divisão de responsabilidade**: Deli é o sistema de registro de pedido/pagamento/fiscal.
  Este projeto nunca duplica cardápio nem processa pagamento.

## Integração Deli (verificada, não é suposição)
- Deli roda sobre a plataforma Fudo — mesma API pública (`https://api.fu.do/v1alpha1`).
- Auth: `POST https://auth.fu.do/api` com `apiKey`/`apiSecret` → token Bearer (24h).
- Credenciais: variáveis de ambiente `DELI_API_KEY` / `DELI_API_SECRET` (nunca hardcode).
- Ver `backend/deli_adapter.py` e `integracao_deli/README.md` para detalhes e passo a passo
  de habilitação (formulário oficial, Plano Pro).
- Ponto em aberto: `saleIdentifier` no modelo de dados do Deli pode ser um recurso nativo para
  número de comanda física — não confirmado como criável via API pública. Perguntar ao
  suporte Deli antes de assumir que existe.

## Mapa de arquivos
Ver `README.md` na raiz — tabela completa. Resumo: `firmware/` (pulseira, nRF5 SDK),
`gateway_esp32/` (scan BLE + MQTT), `backend/` (FastAPI, localização + integração Deli),
`RELATORIO_REVISAO_TECNICA.md` (matemática de engenharia: bateria, RF, RSSI, NFC),
`ORCAMENTO_PROTOTIPAGEM.md` (custo de 5 protótipos, ~R$ 2.514,00).

## Estilo de trabalho esperado
- Respostas diretas e objetivas, sem inflar texto.
- Não afirmar valor técnico sem verificar (datasheet, doc oficial, ou teste real) — este
  projeto já teve erros de pinagem/datasheet corrigidos uma vez; não repetir o padrão.
- Não reintroduzir self-service nem qualquer automação de bebida — é decisão de negócio já
  fechada com o proprietário.
