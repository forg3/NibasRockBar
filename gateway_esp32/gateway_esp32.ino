/*
 * Smart Badge Pub - Firmware do Gateway de Teto (ESP32 + Arduino framework)
 *
 * Bibliotecas necessarias (Library Manager do Arduino IDE):
 *   - "ESP32 BLE Arduino" (API classica: BLEDevice/BLEScan/BLEAdvertisedDevice).
 *     NAO instalar "NimBLE-Arduino" junto - tem nomes de classe diferentes
 *     (NimBLEScan, NimBLEAdvertisedDevice) e quebra este codigo se for usada no lugar.
 *   - "PubSubClient" (Nick O'Leary) para MQTT
 *   - "ArduinoJson" para montar o payload
 *
 * Funcao: varrer continuamente pacotes BLE advertising das pulseiras, filtrar o RSSI com
 * EWMA (media movel exponencial) para reduzir a flutuacao causada por corpos/reflexos, e
 * publicar no broker MQTT local.
 */

#include <BLEDevice.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>
#include <WiFi.h>
#include <PubSubClient.h> // compilacao validada com PubSubClient 2.8 (nao trocar sem testar)
#include <ArduinoJson.h>  // compilacao validada com ArduinoJson 7.4.3; StaticJsonDocument e API v6 com deprecation na v7 (manter ate migracao dedicada para JsonDocument)
#include <map>

// ---------- CONFIG (placeholders - preencher por device antes do deploy) ----------
// TODO: provisioning via Preferences/NVS - gravar os valores por device na flash
// (NVS do ESP32) no primeiro boot e ler aqui; nao commitar credenciais reais.
const char* WIFI_SSID      = "PUB_WIFI";
const char* WIFI_PASSWORD  = "SENHA_AQUI";
const char* MQTT_BROKER    = "192.168.0.10";     // IP do servidor local (Mosquitto)
const int   MQTT_PORT      = 1883;
// TODO: preencher por device antes do deploy; vazio = sem auth (comportamento atual).
const char* MQTT_USER      = "";
const char* MQTT_PASSWORD  = "";
const char* GATEWAY_ID     = "gateway_teto_02";  // TROCAR por gateway - identifica a zona
const char* MFG_COMPANY_ID_HEX = "FFFF";         // referencial: deve bater com MANUFACTURER_ID em firmware/main.c

// Filtro do manufacturer data - deve bater com MANUFACTURER_ID (0xFFFF) em firmware/main.c
const uint16_t EXPECTED_COMPANY_ID = 0xFFFF;
const uint8_t EXPECTED_PROTO = 1;

const unsigned long CONNECT_TIMEOUT_MS = 15000;  // timeout de conexao Wi-Fi/MQTT

const float  EWMA_ALPHA        = 0.2f;   // 0.1 (mais suave/lento) .. 0.3 (mais reativo)
const int    SCAN_WINDOW_MS    = 1000;   // janela de cada ciclo de scan
const int    PUBLISH_PERIOD_MS = 1000;   // periodicidade de publicacao por tag vista

WiFiClient   wifiClient;
PubSubClient mqttClient(wifiClient);
BLEScan*     pBLEScan;

struct TagState {
    float    rssi_ewma;
    uint32_t last_seen_ms;
    uint16_t seq;
};

std::map<std::string, TagState> g_tags; // chave = MAC address da pulseira

// ---------- Wi-Fi / MQTT ----------
// Conexoes com timeout (nunca travam o boot indefinidamente).
bool connectWiFi() {
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    uint32_t t0 = millis();
    while (WiFi.status() != WL_CONNECTED) {
        if (millis() - t0 >= CONNECT_TIMEOUT_MS) {
            // TODO: apos falhas repetidas, entrar em modo de configuracao (AP
            // proprio de provisioning) em vez de retentar no proximo loop.
            return false;
        }
        delay(300);
    }
    return true;
}

bool connectMQTT() {
    uint32_t t0 = millis();
    while (!mqttClient.connected()) {
        String clientId = String("gw_") + GATEWAY_ID;
        // Para TLS usar WiFiClientSecure no lugar de WiFiClient (fora do escopo: requer cert + NTP).
        bool ok;
        if (strlen(MQTT_USER) > 0) {
            ok = mqttClient.connect(clientId.c_str(), MQTT_USER, MQTT_PASSWORD);
        } else {
            ok = mqttClient.connect(clientId.c_str());
        }
        if (ok) return true;
        if (millis() - t0 >= CONNECT_TIMEOUT_MS) return false;
        delay(1000);
    }
    return true;
}

// ---------- Filtro EWMA ----------
// RSSI_filt[n] = alpha * RSSI_raw[n] + (1 - alpha) * RSSI_filt[n-1]
float applyEWMA(float previous, int raw_rssi, bool first_sample) {
    if (first_sample) return (float)raw_rssi;
    return EWMA_ALPHA * raw_rssi + (1.0f - EWMA_ALPHA) * previous;
}

// ---------- Callback de deteccao BLE ----------
class GatewayCallback : public BLEAdvertisedDeviceCallbacks {
    void onResult(BLEAdvertisedDevice advertisedDevice) override {
        // Filtra apenas pacotes com o Company ID esperado (manufacturer specific data)
        if (!advertisedDevice.haveManufacturerData()) return;

        // Core esp32 3.x: getManufacturerData() retorna String (binario preservado com length)
        String manuf = advertisedDevice.getManufacturerData();
        // company_id(2) + proto_version(1) + battery(1) + seq(2) = 6 bytes.
        // Indices acessados abaixo vao ate manuf[5], entao o minimo e' 6, nao 5.
        if (manuf.length() < 6) return;

        // company_id little-endian (mesma ordem escrita pelo ble_advdata_encode no firmware)
        uint16_t company_id = (uint8_t)manuf[0] | ((uint8_t)manuf[1] << 8);
        if (company_id != EXPECTED_COMPANY_ID) return; // advertiser desconhecido: descarta

        uint8_t proto_version = (uint8_t)manuf[2];
        if (proto_version != EXPECTED_PROTO) return; // versao de protocolo desconhecida: descarta

        std::string mac = advertisedDevice.getAddress().toString().c_str(); // toString() = String no core 3.x
        int rssi = advertisedDevice.getRSSI();
        uint8_t battery_pct = (uint8_t)manuf[3];
        uint16_t seq = (uint8_t)manuf[4] | ((uint8_t)manuf[5] << 8);

        uint32_t now = millis();
        auto it = g_tags.find(mac);
        bool first = (it == g_tags.end());

        // Rate-limit por tag: publica no maximo 1x a cada PUBLISH_PERIOD_MS.
        // Pacotes dentro do periodo sao descartados (last_seen_ms marca o ultimo
        // ciclo efetivamente medido/publicado pela tag).
        if (!first && (now - it->second.last_seen_ms) < PUBLISH_PERIOD_MS) return;

        float prev = first ? 0.0f : it->second.rssi_ewma;
        float filt = applyEWMA(prev, rssi, first);

        g_tags[mac] = { filt, now, seq };

        publishTelemetry(mac, filt, rssi, battery_pct, seq);
    }
};

void publishTelemetry(const std::string& mac, float rssi_filt, int rssi_raw,
                       uint8_t battery_pct, uint16_t seq) {
    StaticJsonDocument<256> doc;
    doc["wristband_mac"] = mac;
    doc["gateway_id"]     = GATEWAY_ID;
    doc["rssi_raw"]       = rssi_raw;
    doc["rssi_ewma"]      = rssi_filt;
    doc["battery_pct"]    = battery_pct;
    doc["seq"]            = seq;
    doc["ts_ms"]          = millis();

    char buffer[256];
    size_t n = serializeJson(doc, buffer);

    char topic[64];
    snprintf(topic, sizeof(topic), "pub/telemetria/%s", GATEWAY_ID);

    // Cast explicito: sem ele a overload (topic, payload, retained) e' escolhida e o
    // tamanho n vira flag retained. O correto e' o publish length-based.
    mqttClient.publish(topic, (const uint8_t*)buffer, (unsigned int)n);
}

// ---------- Setup / Loop ----------
void setup() {
    Serial.begin(115200);
    // Aviso de credencial placeholder — nao trava o boot, so alerta via Serial.
    if (strcmp(WIFI_PASSWORD, "SENHA_AQUI") == 0) {
        Serial.println("ATENÇÃO: credenciais placeholder — configure antes do deploy");
    }
    if (!connectWiFi()) {
        // Timeout - nao trava o boot; reconnect e retomado no loop().
        Serial.println("WiFi: timeout na conexao - seguindo sem rede");
    }
    mqttClient.setServer(MQTT_BROKER, MQTT_PORT);

    BLEDevice::init("");
    pBLEScan = BLEDevice::getScan();
    pBLEScan->setAdvertisedDeviceCallbacks(new GatewayCallback(), true);
    pBLEScan->setActiveScan(false);   // scan passivo - nao gasta tempo de radio pedindo scan response
    pBLEScan->setInterval(100);
    pBLEScan->setWindow(99);
}

void loop() {
    if (WiFi.status() != WL_CONNECTED) connectWiFi();
    if (!mqttClient.connected()) connectMQTT();
    mqttClient.loop();

    pBLEScan->start(SCAN_WINDOW_MS / 1000.0, false);
    pBLEScan->clearResults();
}
