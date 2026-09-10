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
#include <Preferences.h>  // provisioning WiFi/MQTT via NVS (namespace "nibas")
#include <map>

// ---------- CONFIG (placeholders - fallback quando o NVS esta vazio) ----------
// Provisionamento por gateway via monitor serial (115200, com newline):
//   config ssid=<WIFI> pass=<SENHA> broker=<IP_OU_HOST> gw=<gateway_teto_XX>
// Exemplo:
//   config ssid=PUB_WIFI pass=troque_aqui broker=192.168.0.10 gw=gateway_teto_02
// Regras: salva no NVS (namespace "nibas", chaves ssid/pass/broker/gateway_id);
// vale por device e sobrevive a reflash (so apaga com erase flash). Sem espacos
// nos valores (parse simples por espaco). A senha NUNCA e ecoada de volta.
// Apos salvar, reinicie o ESP32 para reconectar com os novos valores.
// Provisioning via NVS implementado; ver bloco CONFIG.
char WIFI_SSID[33]     = "PUB_WIFI";       // NVS "nibas"/ssid (max 32 chars)
char WIFI_PASSWORD[64] = "SENHA_AQUI";     // NVS "nibas"/pass (max 63 chars)
char MQTT_BROKER[64]   = "192.168.0.10";   // NVS "nibas"/broker - IP do servidor local (Mosquitto)
const int   MQTT_PORT      = 1883;
// TODO: preencher por device antes do deploy; vazio = sem auth (comportamento atual).
const char* MQTT_USER      = "";
const char* MQTT_PASSWORD  = "";
char GATEWAY_ID[32]    = "gateway_teto_02";  // NVS "nibas"/gateway_id - TROCAR por gateway, identifica a zona
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

// ---------- Provisioning via NVS (namespace "nibas") ----------
// Le os valores salvos; campo ausente ou vazio = mantem o placeholder do CONFIG.
void loadProvisioning() {
    Preferences prefs;
    if (!prefs.begin("nibas", true)) {
        Serial.println("NVS: sem namespace nibas - usando placeholders do CONFIG");
        return;
    }
    String v;
    v = prefs.getString("ssid", "");
    if (v.length() > 0) v.toCharArray(WIFI_SSID, sizeof(WIFI_SSID));
    v = prefs.getString("pass", "");
    if (v.length() > 0) v.toCharArray(WIFI_PASSWORD, sizeof(WIFI_PASSWORD));
    v = prefs.getString("broker", "");
    if (v.length() > 0) v.toCharArray(MQTT_BROKER, sizeof(MQTT_BROKER));
    v = prefs.getString("gateway_id", "");
    if (v.length() > 0) v.toCharArray(GATEWAY_ID, sizeof(GATEWAY_ID));
    prefs.end();
}

// Extrai "chave=<valor>" da linha (valor vai ate o proximo espaco ou fim).
String cfgArg(const String& line, const char* key) {
    int i = line.indexOf(key);
    if (i < 0) return String();
    i += strlen(key);
    int j = line.indexOf(' ', i);
    if (j < 0) return line.substring(i);
    return line.substring(i, j);
}

// Comando serial: config ssid=<..> pass=<..> broker=<..> gw=<..>
// Salva no NVS e aplica nos buffers ativos (reinicie para reconectar).
void handleSerialConfig() {
    if (!Serial.available()) return;
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (!line.startsWith("config ")) return;
    String ssid   = cfgArg(line, "ssid=");
    String pass   = cfgArg(line, "pass=");
    String broker = cfgArg(line, "broker=");
    String gw     = cfgArg(line, "gw=");
    if (ssid.isEmpty() && pass.isEmpty() && broker.isEmpty() && gw.isEmpty()) {
        Serial.println("Uso: config ssid=<WIFI> pass=<SENHA> broker=<IP> gw=<gateway_teto_XX>");
        return;
    }
    Preferences prefs;
    if (!prefs.begin("nibas", false)) {
        Serial.println("NVS: falha ao abrir namespace nibas");
        return;
    }
    if (ssid.length() > 0) {
        prefs.putString("ssid", ssid);
        ssid.toCharArray(WIFI_SSID, sizeof(WIFI_SSID));
    }
    if (pass.length() > 0) {
        prefs.putString("pass", pass);
        pass.toCharArray(WIFI_PASSWORD, sizeof(WIFI_PASSWORD));
    }
    if (broker.length() > 0) {
        prefs.putString("broker", broker);
        broker.toCharArray(MQTT_BROKER, sizeof(MQTT_BROKER));
    }
    if (gw.length() > 0) {
        prefs.putString("gateway_id", gw);
        gw.toCharArray(GATEWAY_ID, sizeof(GATEWAY_ID));
    }
    prefs.end();
    // Confirmacao sem ecoar a senha.
    Serial.println("NVS: configuracao salva. Reinicie para reconectar.");
    Serial.print("ssid: "); Serial.println(WIFI_SSID);
    Serial.println("pass: *****");
    Serial.print("broker: "); Serial.println(MQTT_BROKER);
    Serial.print("gw: "); Serial.println(GATEWAY_ID);
}

// ---------- Setup / Loop ----------
void setup() {
    Serial.begin(115200);
    loadProvisioning(); // NVS "nibas" (read-only); vazio = placeholders do CONFIG
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
    handleSerialConfig(); // provisioning via monitor serial (nao-bloqueante)
    if (WiFi.status() != WL_CONNECTED) connectWiFi();
    if (!mqttClient.connected()) connectMQTT();
    mqttClient.loop();

    pBLEScan->start(SCAN_WINDOW_MS / 1000.0, false);
    pBLEScan->clearResults();
}
