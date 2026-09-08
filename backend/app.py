"""
Smart Badge Pub - Backend local (Edge)

Responsabilidades:
  1. Assinar o broker MQTT local (Mosquitto) e receber telemetria dos gateways ESP32
  2. Decidir a qual gateway/mesa cada pulseira esta mais proxima, com histerese
     (evita "piscar" entre mesas vizinhas por flutuacao de RSSI)
  3. Expor API REST (FastAPI) para o app do garcom consultar a localizacao atual
  4. Persistir em SQLite (trocar por Postgres em producao/varias unidades)

Executar:  uvicorn app:app --host 0.0.0.0 --port 8000
Requer:    paho-mqtt, fastapi, uvicorn (ver requirements.txt)
"""

import json
import sqlite3
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field

import paho.mqtt.client as mqtt
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from deli_adapter import DeliClient, DeliAPIError, DeliAuthError

# Instanciado sob demanda (so falha se realmente for chamado sem credenciais
# configuradas via DELI_API_KEY/DELI_API_SECRET) — permite rodar o backend
# so com localizacao BLE mesmo antes de integrar o Deli.
_deli_client: DeliClient | None = None


def get_deli_client() -> DeliClient:
    global _deli_client
    if _deli_client is None:
        _deli_client = DeliClient()
    return _deli_client

# ---------------- Configuracao ----------------
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "pub/telemetria/#"
DB_PATH = "smartbadge.db"

# Histerese: so troca a mesa atribuida se o novo gateway estiver pelo menos
# HYSTERESIS_DB mais forte (em dB) do que o gateway atualmente atribuido, e isso
# se mantiver por MIN_STABLE_READINGS leituras seguidas.
HYSTERESIS_DB = 4.0
MIN_STABLE_READINGS = 3
TAG_TIMEOUT_S = 15  # se nao ver a pulseira por esse tempo, considera "fora de alcance"

app = FastAPI(title="Smart Badge Pub - Localizacao")

# ---------------- Estado em memoria ----------------
@dataclass
class TagLocationState:
    current_gateway: str | None = None
    candidate_gateway: str | None = None
    candidate_count: int = 0
    last_rssi_by_gateway: dict = field(default_factory=dict)  # gateway_id -> (rssi_ewma, ts)
    last_update_ts: float = 0.0
    battery_pct: int = 100

_state_lock = threading.Lock()
_tag_states: dict[str, TagLocationState] = {}


# ---------------- Persistencia ----------------
@contextmanager
def db_conn():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with db_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS localizacao_atual (
                wristband_mac TEXT PRIMARY KEY,
                gateway_id TEXT,
                battery_pct INTEGER,
                atualizado_em REAL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS historico_telemetria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wristband_mac TEXT,
                gateway_id TEXT,
                rssi_raw INTEGER,
                rssi_ewma REAL,
                ts REAL
            )
        """)
        # Inventario de pulseiras: liga o UID da tag NFC (usado pelo garcom/caixa) ao MAC
        # BLE (usado para localizacao) da MESMA pulseira fisica, e ao id da comanda aberta
        # no sistema de caixa. O pedido/pagamento em si vive no sistema de caixa, nao aqui.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pulseiras (
                nfc_uid TEXT PRIMARY KEY,
                ble_mac TEXT,
                status TEXT NOT NULL DEFAULT 'livre',
                comanda_id TEXT,
                vinculada_em REAL
            )
        """)


def persist_location(mac: str, gateway_id: str, battery_pct: int):
    with db_conn() as conn:
        conn.execute("""
            INSERT INTO localizacao_atual (wristband_mac, gateway_id, battery_pct, atualizado_em)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(wristband_mac) DO UPDATE SET
                gateway_id=excluded.gateway_id,
                battery_pct=excluded.battery_pct,
                atualizado_em=excluded.atualizado_em
        """, (mac, gateway_id, battery_pct, time.time()))


def persist_raw_sample(mac: str, gateway_id: str, rssi_raw: int, rssi_ewma: float, ts: float):
    with db_conn() as conn:
        conn.execute("""
            INSERT INTO historico_telemetria (wristband_mac, gateway_id, rssi_raw, rssi_ewma, ts)
            VALUES (?, ?, ?, ?, ?)
        """, (mac, gateway_id, rssi_raw, rssi_ewma, ts))


# ---------------- Logica de decisao (vizinho mais proximo com histerese) ----------------
def process_sample(mac: str, gateway_id: str, rssi_raw: int, rssi_ewma: float,
                    battery_pct: int, ts: float):
    with _state_lock:
        state = _tag_states.setdefault(mac, TagLocationState())
        state.last_rssi_by_gateway[gateway_id] = (rssi_ewma, ts)
        state.last_update_ts = ts
        state.battery_pct = battery_pct

        # gateway com maior RSSI (mais proximo) entre os que reportaram recentemente
        recent = {gw: rssi for gw, (rssi, t) in state.last_rssi_by_gateway.items()
                  if ts - t <= TAG_TIMEOUT_S}
        if not recent:
            return
        best_gateway = max(recent, key=recent.get)
        best_rssi = recent[best_gateway]

        if state.current_gateway is None:
            state.current_gateway = best_gateway
            state.candidate_gateway = None
            state.candidate_count = 0
        elif best_gateway == state.current_gateway:
            state.candidate_gateway = None
            state.candidate_count = 0
        else:
            current_rssi = recent.get(state.current_gateway, -999)
            # so considera trocar se o candidato for HYSTERESIS_DB mais forte
            if best_rssi - current_rssi >= HYSTERESIS_DB:
                if state.candidate_gateway == best_gateway:
                    state.candidate_count += 1
                else:
                    state.candidate_gateway = best_gateway
                    state.candidate_count = 1

                if state.candidate_count >= MIN_STABLE_READINGS:
                    state.current_gateway = best_gateway
                    state.candidate_gateway = None
                    state.candidate_count = 0
            else:
                state.candidate_gateway = None
                state.candidate_count = 0

        persist_location(mac, state.current_gateway, battery_pct)
        persist_raw_sample(mac, gateway_id, rssi_raw, rssi_ewma, ts)


# ---------------- MQTT ----------------
def on_connect(client, userdata, flags, rc):
    client.subscribe(MQTT_TOPIC)


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        process_sample(
            mac=payload["wristband_mac"],
            gateway_id=payload["gateway_id"],
            rssi_raw=int(payload["rssi_raw"]),
            rssi_ewma=float(payload["rssi_ewma"]),
            battery_pct=int(payload.get("battery_pct", 0)),
            ts=time.time(),
        )
    except (KeyError, ValueError, json.JSONDecodeError):
        pass  # payload malformado - descartar (logar em producao)


def start_mqtt_thread():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=30)
    thread = threading.Thread(target=client.loop_forever, daemon=True)
    thread.start()


# ---------------- API REST ----------------
@app.on_event("startup")
def startup():
    init_db()
    start_mqtt_thread()
    threading.Thread(target=poll_deli_sales, daemon=True).start()


@app.get("/localizacao/{mac}")
def get_localizacao(mac: str):
    with _state_lock:
        state = _tag_states.get(mac)
    if state is None or state.current_gateway is None:
        raise HTTPException(status_code=404, detail="Pulseira nao localizada")
    if time.time() - state.last_update_ts > TAG_TIMEOUT_S:
        raise HTTPException(status_code=404, detail="Pulseira fora de alcance")
    return {
        "wristband_mac": mac,
        "gateway_id": state.current_gateway,
        "battery_pct": state.battery_pct,
        "atualizado_ha_s": round(time.time() - state.last_update_ts, 1),
    }


class CheckinRequest(BaseModel):
    nfc_uid: str
    ble_mac: str
    table_id: str          # id da mesa/recepcao no Deli (GET /tables para listar)
    waiter_id: str | None = None
    people: int = 1
    customer_name: str | None = None


class CheckoutRequest(BaseModel):
    nfc_uid: str


@app.post("/pulseiras/checkin")
def checkin_pulseira(req: CheckinRequest):
    with db_conn() as conn:
        row = conn.execute(
            "SELECT status FROM pulseiras WHERE nfc_uid = ?", (req.nfc_uid,)
        ).fetchone()
        if row is not None and row[0] == "em_uso":
            raise HTTPException(status_code=409, detail="Pulseira ja esta em uso")

    try:
        comanda_id = get_deli_client().abrir_comanda(
            table_id=req.table_id,
            waiter_id=req.waiter_id,
            people=req.people,
            customer_name=req.customer_name,
        )
    except (DeliAuthError, DeliAPIError) as e:
        raise HTTPException(status_code=502, detail=f"Falha ao abrir comanda no Deli: {e}")

    with db_conn() as conn:
        conn.execute("""
            INSERT INTO pulseiras (nfc_uid, ble_mac, status, comanda_id, vinculada_em)
            VALUES (?, ?, 'em_uso', ?, ?)
            ON CONFLICT(nfc_uid) DO UPDATE SET
                ble_mac=excluded.ble_mac,
                status='em_uso',
                comanda_id=excluded.comanda_id,
                vinculada_em=excluded.vinculada_em
        """, (req.nfc_uid, req.ble_mac, comanda_id, time.time()))
    return {"nfc_uid": req.nfc_uid, "status": "em_uso", "comanda_id": comanda_id}


@app.post("/pulseiras/checkout")
def checkout_pulseira(req: CheckoutRequest):
    """Liberacao manual (fallback). O caminho normal é automatico — ver
    poll_deli_sales() abaixo, que libera a pulseira assim que o caixa fecha
    a comanda no proprio Deli."""
    with db_conn() as conn:
        row = conn.execute(
            "SELECT status, comanda_id FROM pulseiras WHERE nfc_uid = ?", (req.nfc_uid,)
        ).fetchone()
        if row is None or row[0] != "em_uso":
            raise HTTPException(status_code=404, detail="Pulseira nao esta em uso")
        comanda_encerrada = row[1]
        conn.execute("""
            UPDATE pulseiras SET status='livre', comanda_id=NULL, vinculada_em=NULL
            WHERE nfc_uid = ?
        """, (req.nfc_uid,))
    return {"nfc_uid": req.nfc_uid, "status": "livre", "comanda_encerrada": comanda_encerrada}


def poll_deli_sales():
    """Roda em background: verifica periodicamente se a comanda de cada
    pulseira 'em_uso' foi fechada/paga no Deli e libera a pulseira sozinha
    quando isso acontece. Nunca fecha a comanda por conta propria."""
    while True:
        time.sleep(15)
        try:
            client = get_deli_client()
        except DeliAuthError:
            continue  # Deli ainda nao configurado - so localizacao BLE roda
        with db_conn() as conn:
            pulseiras_em_uso = conn.execute(
                "SELECT nfc_uid, comanda_id FROM pulseiras WHERE status = 'em_uso'"
            ).fetchall()
        for nfc_uid, comanda_id in pulseiras_em_uso:
            try:
                if client.comanda_encerrada(comanda_id):
                    with db_conn() as conn:
                        conn.execute("""
                            UPDATE pulseiras SET status='livre', comanda_id=NULL,
                                vinculada_em=NULL WHERE nfc_uid = ?
                        """, (nfc_uid,))
            except DeliAPIError:
                continue  # tenta de novo no proximo ciclo


@app.get("/pulseiras")
def listar_pulseiras():
    with db_conn() as conn:
        rows = conn.execute(
            "SELECT nfc_uid, ble_mac, status, comanda_id FROM pulseiras"
        ).fetchall()
    return [
        {"nfc_uid": r[0], "ble_mac": r[1], "status": r[2], "comanda_id": r[3]}
        for r in rows
    ]


@app.get("/localizacoes")
def get_todas_localizacoes():
    with _state_lock:
        agora = time.time()
        return [
            {
                "wristband_mac": mac,
                "gateway_id": s.current_gateway,
                "battery_pct": s.battery_pct,
                "online": (agora - s.last_update_ts) <= TAG_TIMEOUT_S,
            }
            for mac, s in _tag_states.items()
            if s.current_gateway is not None
        ]
