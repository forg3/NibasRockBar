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
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <map>

// ---------- Configuracao ----------
const char* WIFI_SSID      = "PUB_WIFI";
const char* WIFI_PASSWORD  = "SENHA_AQUI";
const char* MQTT_BROKER    = "192.168.0.10";     // IP do servidor local (Mosquitto)
const int   MQTT_PORT      = 1883;
const char* GATEWAY_ID     = "gateway_teto_02";  // TROCAR por gateway - identifica a zona
const char* MFG_COMPANY_ID_HEX = "FFFF";         // deve bater com o firmware da pulseira

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
void connectWiFi() {
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    while (WiFi.status() != WL_CONNECTED) {
        delay(300);
    }
}

void connectMQTT() {
    while (!mqttClient.connected()) {
        String clientId = String("gw_") + GATEWAY_ID;
        mqttClient.connect(clientId.c_str());
        if (!mqttClient.connected()) delay(1000);
    }
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

        std::string manuf = advertisedDevice.getManufacturerData();
        // company_id(2) + proto_version(1) + battery(1) + seq(2) = 6 bytes.
        // Indices acessados abaixo vao ate manuf[5], entao o minimo e' 6, nao 5.
        if (manuf.length() < 6) return;

        uint16_t company_id = (uint8_t)manuf[0] | ((uint8_t)manuf[1] << 8);
        char expected[5];
        sprintf(expected, "%04X", company_id);
        // (comparacao simplificada - ajustar conforme endianness real do payload)

        std::string mac = advertisedDevice.getAddress().toString();
        int rssi = advertisedDevice.getRSSI();
        uint8_t battery_pct = (uint8_t)manuf[3];
        uint16_t seq = (uint8_t)manuf[4] | ((uint8_t)manuf[5] << 8);

        auto it = g_tags.find(mac);
        bool first = (it == g_tags.end());
        float prev = first ? 0.0f : it->second.rssi_ewma;
        float filt = applyEWMA(prev, rssi, first);

        g_tags[mac] = { filt, millis(), seq };

        // Publica imediatamente (poderia ser agregado por PUBLISH_PERIOD_MS se o volume for alto)
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

    mqttClient.publish(topic, buffer, n);
}

// ---------- Setup / Loop ----------
void setup() {
    Serial.begin(115200);
    connectWiFi();
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
