/*
 * Smart Badge Pub - Firmware da pulseira (nRF52810, nRF5 SDK v17.x, SoftDevice S112)
 *
 * Escopo deste arquivo: esqueleto de referencia, NAO e um projeto compilavel standalone.
 * Precisa ser integrado a um projeto nRF5 SDK real (pca10040e/blank + S112) com os
 * arquivos sdk_config.h, ble_advdata, nrf_pwr_mgmt, etc. do SDK da Nordic.
 *
 * Responsabilidades deste firmware:
 *   1. Habilitar o regulador DC/DC (economiza energia vs. LDO interno)
 *   2. Emitir pacotes de advertising BLE nao-conectaveis a cada ADV_INTERVAL_MS
 *   3. Incluir no payload: MAC address (automatico), nivel de bateria, numero de sequencia
 *   4. Dormir em System ON low-power entre eventos
 *
 * O NFC (NTAG213) e 100% passivo - nao precisa nem pode ser controlado por este firmware,
 * ele funciona por acoplamento indutivo com o leitor, sem consumir energia da bateria.
 */

#include "nrf_sdh.h"
#include "nrf_sdh_ble.h"
#include "nrf_pwr_mgmt.h"
#include "ble_advdata.h"
#include "nrf_drv_saadc.h"
#include "app_timer.h"

#define ADV_INTERVAL_MS         1500                    // intervalo entre pacotes de advertising
#define ADV_INTERVAL_UNITS      MSEC_TO_UNITS(ADV_INTERVAL_MS, UNIT_0_625_MS)
#define DEVICE_NAME             "PUBBADGE"
#define MANUFACTURER_ID         0xFFFF                  // trocar por ID registrado se for a mercado
#define APP_BLE_CONN_CFG_TAG    1                       // tag de conn_cfg usada nas chamadas sd_ble_*

APP_TIMER_DEF(m_battery_timer);

typedef struct __attribute__((packed))
{
    uint16_t company_id;
    uint8_t  proto_version;
    uint8_t  battery_pct;      // 0-100
    uint16_t seq;              // numero de sequencia (detecta pacotes perdidos no gateway)
} adv_payload_t;

static adv_payload_t m_payload = { .company_id = MANUFACTURER_ID, .proto_version = 1 };
static ble_gap_adv_params_t m_adv_params;
static ble_gap_adv_data_t   m_adv_data;
static uint8_t              m_enc_advdata[BLE_GAP_ADV_SET_DATA_SIZE_MAX];
static uint32_t             ram_start     = 0;      // RAM requisitada ao SoftDevice (preenchida por nrf_sdh_ble_default_cfg_set)
static uint8_t              m_adv_handle;           // handle do advertising set

/* --- 1. Energia: habilita DC/DC interno no boot --- */
static void power_init(void)
{
    ret_code_t err_code = nrf_sdh_ble_default_cfg_set(APP_BLE_CONN_CFG_TAG, &ram_start);
    APP_ERROR_CHECK(err_code);

    // Ativa o conversor DC/DC do nRF52810 (requer L2=10uH, C10=1.0uF no hardware - ver BOM)
    err_code = sd_power_dcdc_mode_set(NRF_POWER_DCDC_ENABLE);
    APP_ERROR_CHECK(err_code);
}

/* --- 2. Leitura de bateria via SAADC (VDD direto, sem divisor resistivo) ---
 * Canal 0 = NRF_SAADC_INPUT_VDD; gain 1/6 com referencia interna 0.6V ->
 * full-scale = 0.6V * 6 = 3.6V (CR2032 ~3.0V cabe com folga).
 * Mapa 3.0V=100% .. 2.0V=0% (curva de descarga da CR2032 e' bem plana, entao esse
 * mapeamento e' grosseiro por natureza - suficiente para "bateria fraca/ok").
 * Matematica em mV inteiros (nRF52810 roda soft-float por padrao no SDK).
 */
#define SAADC_CH_VDD            0                       // canal 0 ligado ao VDD
#define BATTERY_EMPTY_MV        2000                    // 0% do mapa
#define BATTERY_FULL_MV         3000                    // 100% do mapa
#define SAADC_FULL_SCALE_MV     3600                    // ref 0.6V / gain 1/6
#define SAADC_MAX_COUNTS        4096                    // resolucao 12 bits

static void battery_saadc_init(void)
{
    nrf_drv_saadc_config_t saadc_cfg = NRF_DRV_SAADC_DEFAULT_CONFIG;
    saadc_cfg.resolution = NRF_SAADC_RESOLUTION_12BIT;
    saadc_cfg.oversample = NRF_SAADC_OVERSAMPLE_4X;

    // Config SE padrao do SDK: gain 1/6 + referencia interna 0.6V + acq 10us
    nrf_saadc_channel_config_t ch_cfg =
        NRF_DRV_SAADC_DEFAULT_CHANNEL_CONFIG_SE(NRF_SAADC_INPUT_VDD);
    ch_cfg.burst = NRF_SAADC_BURST_ENABLED; // com burst, 1 gatilho de SAMPLE entrega a media das 4 amostras

    ret_code_t err_code = nrf_drv_saadc_init(&saadc_cfg, NULL); // handler NULL = modo bloqueante
    APP_ERROR_CHECK(err_code);

    err_code = nrf_drv_saadc_channel_init(SAADC_CH_VDD, &ch_cfg);
    APP_ERROR_CHECK(err_code);
}

static uint8_t read_battery_percent(void)
{
    nrf_saadc_value_t raw;
    ret_code_t err_code = nrf_drv_saadc_sample_convert(SAADC_CH_VDD, &raw);
    APP_ERROR_CHECK(err_code);

    int32_t vbat_mv = ((int32_t)raw * SAADC_FULL_SCALE_MV) / SAADC_MAX_COUNTS;
    if (vbat_mv > BATTERY_FULL_MV)  vbat_mv = BATTERY_FULL_MV;
    if (vbat_mv < BATTERY_EMPTY_MV) vbat_mv = BATTERY_EMPTY_MV;
    return (uint8_t)(((vbat_mv - BATTERY_EMPTY_MV) * 100) / (BATTERY_FULL_MV - BATTERY_EMPTY_MV));
}

/* --- 3. Monta e atualiza o payload de advertising --- */
static void advdata_update(void)
{
    static uint16_t seq_counter = 0;

    m_payload.battery_pct = read_battery_percent();
    m_payload.seq         = seq_counter++;

    ble_advdata_manuf_data_t manuf_data;
    manuf_data.company_identifier = MANUFACTURER_ID;
    manuf_data.data.p_data        = (uint8_t *)&m_payload.proto_version;
    manuf_data.data.size          = sizeof(m_payload) - sizeof(m_payload.company_id);

    ble_advdata_t advdata;
    memset(&advdata, 0, sizeof(advdata));
    advdata.name_type          = BLE_ADVDATA_SHORT_NAME;
    advdata.short_name_len     = 4; // "PUBB"
    advdata.p_manuf_specific_data = &manuf_data;

    uint16_t len = sizeof(m_enc_advdata);
    ret_code_t err_code = ble_advdata_encode(&advdata, m_enc_advdata, &len);
    APP_ERROR_CHECK(err_code);

    m_adv_data.adv_data.p_data = m_enc_advdata;
    m_adv_data.adv_data.len    = len;

    err_code = sd_ble_gap_adv_data_set(m_adv_handle, &m_adv_data.adv_data, NULL);
    APP_ERROR_CHECK(err_code);
}

/* --- 4. Configura advertising nao-conectavel (economiza energia vs. conectavel) --- */
static void advertising_init(void)
{
    memset(&m_adv_params, 0, sizeof(m_adv_params));
    m_adv_params.properties.type = BLE_GAP_ADV_TYPE_NONCONNECTABLE_NONSCANNABLE_UNDIRECTED;
    m_adv_params.p_peer_addr     = NULL;
    m_adv_params.filter_policy   = BLE_GAP_ADV_FP_ANY;
    m_adv_params.interval        = ADV_INTERVAL_UNITS;
    m_adv_params.duration        = 0; // sem limite de tempo

    advdata_update();
}

/* --- 5. Timer que atualiza bateria/sequencia a cada ciclo de advertising --- */
static void battery_timer_handler(void *p_context)
{
    advdata_update();
}

int main(void)
{
    power_init();
    battery_saadc_init();
    advertising_init();

    app_timer_create(&m_battery_timer, APP_TIMER_MODE_REPEATED, battery_timer_handler);
    app_timer_start(m_battery_timer, APP_TIMER_TICKS(ADV_INTERVAL_MS), NULL);

    sd_ble_gap_adv_start(m_adv_handle, APP_BLE_CONN_CFG_TAG);

    for (;;)
    {
        nrf_pwr_mgmt_run();   // dorme em System ON ate o proximo evento (RTC/radio)
    }
}
