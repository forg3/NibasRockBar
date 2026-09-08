# Integração com o Deli — confirmada

O Deli roda sobre a plataforma **Fudo** e expõe a mesma API pública documentada em
`dev.fu.do/api` (confirmado pela Central de Ajuda oficial do Deli e pelo padrão de URL
`app-v2.deli.com.br/app/#!/tables/{id}/sale/{id}`, idêntico ao do Fudo).

## Passo 1 — Habilitar a API (feito uma vez, pelo administrador da conta)

1. Confirmar que o plano contratado é o **Plano Pro** (a API pública é exclusiva dele).
2. Preencher o formulário oficial de solicitação: https://forms.gle/mBNDdSvmxFeBtCi3A
   (resposta em até 48h).
3. Depois de habilitado: **Configurações > Usuários** no Deli → escolher um usuário
   dedicado à integração → botão **"Estabelecer API Secret"** → copiar `apiKey`/`apiSecret`
   na hora (não aparecem de novo depois).
4. Guardar como variáveis de ambiente, nunca no código:
   ```
   export DELI_API_KEY="..."
   export DELI_API_SECRET="..."
   ```

## Passo 2 — Descobrir os IDs de mesa e garçom

```
GET https://api.fu.do/v1alpha1/tables
GET https://api.fu.do/v1alpha1/users
```
(usar `deli_adapter.listar_mesas()` / `listar_garcons()`). Escolher qual mesa representa a
recepção/check-in — pode ser uma mesa física de balcão já cadastrada no Deli.

## Passo 3 — Fluxo real (já implementado em `backend/app.py` + `backend/deli_adapter.py`)

- **Check-in**: `POST /pulseiras/checkin` deste backend chama `deli_adapter.abrir_comanda()`,
  que faz `POST /sales` no Deli (`saleType: EAT-IN`, mesa de recepção, garçom, nº de
  pessoas) e recebe de volta o `id` real da venda — o mesmo que aparece na URL do Deli
  (`.../tables/39/sale/7627`). Esse id fica salvo como `comanda_id` da pulseira.
- **Pedidos**: continuam sendo lançados pelo garçom **direto no Deli** (app/tablet), na
  mesma comanda — nosso sistema não duplica isso.
- **Checkout automático**: uma rotina em background (`poll_deli_sales`, a cada 15s) consulta
  `GET /sales/{id}` de cada pulseira em uso; quando o caixa fecha/paga a comanda no próprio
  Deli (`saleState` vira `CLOSED` ou `CANCELED`), a pulseira é liberada sozinha — ninguém
  precisa lembrar de "devolver" a pulseira no sistema. `POST /pulseiras/checkout` continua
  existindo como liberação manual de emergência.

## O que este adaptador **não** faz (por design)
- Não fecha nem paga a comanda pelo Deli — isso é sempre feito pelo caixa, com o controle
  fiscal e de pagamento do próprio Deli.
- Não duplica cardápio/produtos — pedidos continuam sendo lançados no Deli normalmente.

## Ponto em aberto (verificar com o suporte Deli antes de ir para produção)
O modelo de dados do Deli tem um relacionamento `saleIdentifier` nas vendas — indício de que
exista um recurso nativo para "número de comanda física" (que poderia mapear 1:1 com o UID
da tag NFC, dispensando a tabela `pulseiras` própria). Isso **não está confirmado** como
disponível para criação via API pública atual — vale perguntar ao suporte (suporte@deli.com.br)
se dá para pré-cadastrar um `SaleIdentifier` por pulseira. Se sim, simplifica a integração;
se não, a solução com `POST /sales` + `customerName` já implementada funciona sem depender disso.
