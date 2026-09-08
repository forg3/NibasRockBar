"""
Adaptador da API Publica do Deli (Deli roda sobre a plataforma Fudo — mesma API,
mesmo dominio api.fu.do, confirmado pela documentacao oficial de suporte do Deli).

Como obter credenciais (uma vez, feito por quem administra a conta Deli):
  1. Pedir habilitacao da API Publica (Plano Pro): formulario oficial do Deli
     -> https://forms.gle/mBNDdSvmxFeBtCi3A (resposta em ate 48h)
  2. No Deli: Configuracoes > Usuarios > escolher um usuario dedicado a integracao
     > "Estabelecer API Secret" > copiar apiKey/apiSecret na hora (nao sao
     mostrados de novo depois).
  3. Colocar as credenciais em variaveis de ambiente (nunca no codigo):
     DELI_API_KEY, DELI_API_SECRET

Autenticacao (verificada na documentacao oficial):
  POST https://auth.fu.do/api  {"apiKey": "...", "apiSecret": "..."}
  -> {"token": "...", "exp": <epoch seconds>}
  Token dura 24h. Usar como "Authorization: Bearer <token>" em toda chamada.

Endpoints usados aqui (API pública, OpenAPI 3.1, estilo JSON:API):
  Base: https://api.fu.do/v1alpha1
  POST /sales        -> abre uma comanda (check-in da pulseira)
  GET  /sales/{id}   -> consulta status da comanda (saleState)
  GET  /tables       -> lista mesas cadastradas no Deli
  GET  /users        -> lista garcons/usuarios cadastrados no Deli

Divisao de responsabilidade (mantida do design anterior):
  - Pagamento, cardapio e emissao fiscal continuam 100% no Deli.
  - Este adaptador só abre a comanda (check-in) e LÊ o status para saber
    quando ela foi fechada/paga (checkout automático) — nunca fecha a
    venda por conta própria, isso evitaria o controle de pagamento do Deli.
"""

import os
import time
import requests

DELI_AUTH_URL = "https://auth.fu.do/api"
DELI_BASE_URL = "https://api.fu.do/v1alpha1"

# Estados de saleState que significam "comanda encerrada" (segundo o schema
# publico do Deli): CLOSED = paga e fechada, CANCELED = cancelada.
SALE_STATES_ENCERRADOS = {"CLOSED", "CANCELED"}


class DeliAuthError(Exception):
    pass


class DeliAPIError(Exception):
    pass


class DeliClient:
    def __init__(self, api_key: str | None = None, api_secret: str | None = None):
        self.api_key = api_key or os.environ.get("DELI_API_KEY")
        self.api_secret = api_secret or os.environ.get("DELI_API_SECRET")
        if not self.api_key or not self.api_secret:
            raise DeliAuthError(
                "DELI_API_KEY/DELI_API_SECRET nao configurados (variaveis de ambiente)"
            )
        self._token = None
        self._token_exp = 0

    def _ensure_token(self):
        # Renova com 60s de folga antes do vencimento (token dura 24h).
        if self._token and time.time() < self._token_exp - 60:
            return
        resp = requests.post(
            DELI_AUTH_URL,
            json={"apiKey": self.api_key, "apiSecret": self.api_secret},
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=10,
        )
        if resp.status_code != 200:
            raise DeliAuthError(f"Falha ao autenticar no Deli: {resp.status_code} {resp.text}")
        data = resp.json()
        self._token = data["token"]
        self._token_exp = float(data["exp"])

    def _headers(self):
        self._ensure_token()
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _request(self, method: str, path: str, **kwargs):
        resp = requests.request(method, f"{DELI_BASE_URL}{path}",
                                 headers=self._headers(), timeout=10, **kwargs)
        if resp.status_code >= 400:
            raise DeliAPIError(f"{method} {path} -> {resp.status_code}: {resp.text}")
        return resp.json() if resp.content else None

    # ---------------- Operacoes usadas pelo fluxo da pulseira ----------------

    def listar_mesas(self):
        """GET /tables — usar para mapear o id da mesa de recepcao/check-in."""
        return self._request("GET", "/tables")

    def listar_garcons(self):
        """GET /users — usar para descobrir o id do usuario/garcom do check-in."""
        return self._request("GET", "/users")

    def abrir_comanda(self, table_id: str, waiter_id: str | None = None,
                       people: int = 1, customer_name: str | None = None) -> str:
        """
        Abre uma venda (comanda) no Deli para o check-in da pulseira.
        Retorna o id da sale criada (o mesmo id que aparece na URL do Deli,
        ex: app-v2.deli.com.br/app/#!/tables/{table_id}/sale/{id}).
        """
        attributes = {"saleType": "EAT-IN", "people": people}
        if customer_name:
            attributes["customerName"] = customer_name

        relationships = {"table": {"data": {"id": str(table_id), "type": "Table"}}}
        if waiter_id:
            relationships["waiter"] = {"data": {"id": str(waiter_id), "type": "User"}}

        body = {"data": {"type": "Sale", "attributes": attributes, "relationships": relationships}}
        result = self._request("POST", "/sales", json=body)
        return result["data"]["id"]

    def consultar_comanda(self, sale_id: str) -> dict:
        """GET /sales/{id} — retorna saleState e total atual da comanda."""
        result = self._request("GET", f"/sales/{sale_id}")
        attrs = result["data"]["attributes"]
        return {
            "sale_id": sale_id,
            "sale_state": attrs.get("saleState"),
            "total": attrs.get("total"),
            "closed_at": attrs.get("closedAt"),
        }

    def comanda_encerrada(self, sale_id: str) -> bool:
        estado = self.consultar_comanda(sale_id)["sale_state"]
        return estado in SALE_STATES_ENCERRADOS
