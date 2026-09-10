#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gerador do Relatorio de Auditoria de Seguranca — NibasRockBar.

Uso:
    docs/security-audit/.venv/bin/python docs/security-audit/gerar_relatorio.py

Saida:
    docs/security-audit/relatorio-auditoria-seguranca.pdf (A4, margens 2 cm,
    cabecalho/rodape com titulo + numero da pagina).
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (
    Flowable,
    Image,
    LongTable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.join(BASE_DIR, "relatorio-auditoria-seguranca.pdf")
TMP_DIR = "/tmp/opencode"
ROSCA_PNG = os.path.join(TMP_DIR, "audit_rosca.png")
BARRAS_PNG = os.path.join(TMP_DIR, "audit_barras.png")

TITULO = "Relatório de Auditoria de Segurança — NibasRockBar"
DATA = "10/09/2026"

C_CRIT = "#B91C1C"
C_ALTA = "#EA580C"
C_MEDIA = "#D97706"
C_BAIXA = "#2563EB"
C_INFO = "#6B7280"
C_FORTE = "#059669"
C_TINTA = "#1F2937"
C_ACENTO = "#B91C1C"


# ---------------------------------------------------------------- gráficos
def gerar_graficos():
    os.makedirs(TMP_DIR, exist_ok=True)

    # Rosca por severidade (+ fatia de pontos fortes)
    rotulos = ["Alta (2)", "Média (4)", "Baixa (5)", "Informativa (2)", "Pontos fortes (9)"]
    valores = [2, 4, 5, 2, 9]
    cores_rosca = [C_ALTA, C_MEDIA, C_BAIXA, C_INFO, C_FORTE]
    fig, ax = plt.subplots(figsize=(5.2, 3.1), dpi=170)
    wedges, _ = ax.pie(
        valores,
        colors=cores_rosca,
        startangle=90,
        counterclock=False,
        wedgeprops=dict(width=0.46, edgecolor="white", linewidth=2),
    )
    ax.add_artist(Circle((0, 0), 0.58, fc="white", ec="#E5E7EB", lw=1))
    ax.text(0, 0.08, "13", ha="center", va="center", fontsize=20, fontweight="bold", color=C_TINTA)
    ax.text(0, -0.14, "achados", ha="center", va="center", fontsize=9, color="#4B5563")
    ax.legend(wedges, rotulos, loc="center left", bbox_to_anchor=(0.92, 0.5), fontsize=8.5, frameon=False)
    ax.set_title("Achados por severidade (+ pontos fortes)", fontsize=10, fontweight="bold", color=C_TINTA, pad=10)
    fig.tight_layout()
    fig.savefig(ROSCA_PNG, bbox_inches="tight")
    plt.close(fig)

    # Barras por categoria
    cats = ["Cat. 1\nAcesso\n(3)", "Cat. 2\nFrontend\n(0 · N/A)", "Cat. 3\nComunicação\n(2)", "Cat. 4\nValidação\n(3)", "Cat. 5\nConfig/Deps\n(5)"]
    vals = [3, 0, 2, 3, 5]
    cores_barras = [C_ALTA, "#D1D5DB", C_MEDIA, C_BAIXA, C_FORTE]
    fig, ax = plt.subplots(figsize=(5.6, 2.9), dpi=170)
    bars = ax.bar(cats, vals, color=cores_barras, edgecolor="white", width=0.62)
    for b, v in zip(bars, vals):
        etiqueta = "N/A" if v == 0 else str(v)
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.08, etiqueta,
                ha="center", va="bottom", fontsize=10, fontweight="bold", color=C_TINTA)
    ax.set_ylim(0, 6.2)
    ax.set_ylabel("nº de achados", fontsize=9, color="#4B5563")
    ax.set_title("Achados por categoria de auditoria", fontsize=10, fontweight="bold", color=C_TINTA, pad=10)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="x", labelsize=8)
    fig.tight_layout()
    fig.savefig(BARRAS_PNG, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- estilos
def estilos():
    ss = getSampleStyleSheet()
    s_titulo = ParagraphStyle("Titulo", parent=ss["Title"], fontSize=24, leading=28,
                              textColor=colors.HexColor(C_TINTA), alignment=TA_CENTER, spaceAfter=4)
    s_sub = ParagraphStyle("Sub", parent=ss["Normal"], fontSize=11, leading=14,
                           textColor=colors.HexColor("#4B5563"), alignment=TA_CENTER, spaceAfter=2)
    s_h1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=14, leading=17,
                          textColor=colors.HexColor(C_TINTA), spaceBefore=14, spaceAfter=6,
                          borderPadding=(0, 0, 4, 0))
    s_h2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=11, leading=14,
                          textColor=colors.HexColor(C_TINTA), spaceBefore=10, spaceAfter=4)
    s_corpo = ParagraphStyle("Corpo", parent=ss["Normal"], fontSize=9.5, leading=13.5,
                             alignment=TA_JUSTIFY, textColor=colors.HexColor("#111827"), spaceAfter=4)
    s_bullet = ParagraphStyle("Bullet", parent=s_corpo, alignment=TA_LEFT, leftIndent=14,
                              bulletIndent=4, spaceAfter=3)
    s_peq = ParagraphStyle("Peq", parent=ss["Normal"], fontSize=8, leading=10.5,
                           textColor=colors.HexColor("#4B5563"), alignment=TA_LEFT, spaceAfter=2)
    s_codigo = ParagraphStyle("Codigo", parent=ss["Code"], fontName="Courier", fontSize=7,
                              leading=8.6, textColor=colors.HexColor("#111827"),
                              leftIndent=8, spaceAfter=1, spaceBefore=0, alignment=TA_LEFT)
    s_cel = ParagraphStyle("Cel", parent=ss["Normal"], fontSize=7.5, leading=9.5,
                           textColor=colors.HexColor("#111827"), alignment=TA_LEFT)
    s_cel_c = ParagraphStyle("CelC", parent=s_cel, alignment=TA_CENTER)
    s_chip = ParagraphStyle("Chip", parent=ss["Normal"], fontSize=7.5, leading=9.5,
                            alignment=TA_CENTER, textColor=colors.white)
    return ss, s_titulo, s_sub, s_h1, s_h2, s_corpo, s_bullet, s_peq, s_codigo, s_cel, s_cel_c, s_chip


# ---------------------------------------------------------------- dados
ACHADOS = [
    ("A1", "ALTA", "1", "backend/app.py:246",
     "POST /pulseiras/checkin abre comanda no Deli (sistema fiscal externo) sem autenticação/autorização — "
     "qualquer host na rede cria vendas. Trecho: <font face=\"Courier\" size=\"7\">def checkin_pulseira(req: CheckinRequest)</font> + "
     "<font face=\"Courier\" size=\"7\">DeliClient.abrir_comanda()</font>."),
    ("A2", "ALTA", "1", "backend/app.py:278",
     "POST /pulseiras/checkout libera qualquer pulseira (nfc_uid no body, sem verificar chamador) — "
     "qualquer host encerra comandas. Trecho: <font face=\"Courier\" size=\"7\">def checkout_pulseira(req: CheckoutRequest)</font> + "
     "<font face=\"Courier\" size=\"7\">UPDATE pulseiras SET status='livre'</font>."),
    ("M1", "MÉDIA", "1", "backend/app.py:217",
     "GET /localizacao/{mac} expõe localização em tempo real de qualquer cliente sem auth (privacidade). "
     "Trecho: <font face=\"Courier\" size=\"7\">def get_localizacao(mac: str)</font> lê "
     "<font face=\"Courier\" size=\"7\">_tag_states[mac]</font>."),
    ("M2", "MÉDIA", "5", "backend/app.py:323",
     "GET /pulseiras retorna dump completo (nfc_uid, ble_mac, status, comanda_id) sem filtro/paginação/auth."),
    ("M3", "MÉDIA", "5", "backend/app.py:335",
     "GET /localizacoes expõe todas as tags online sem auth."),
    ("M4", "MÉDIA", "3", "gateway_esp32/gateway_esp32.ino:75 + backend/app.py:41-43",
     "MQTT sem auth/TLS (broker 192.168.0.10:1883, connect sem user/pass) — qualquer host publica "
     "telemetria falsa ou assina dados."),
    ("B1", "BAIXA", "4", "backend/app.py:233-240",
     "CheckinRequest/CheckoutRequest sem pattern/min_length (nfc_uid/ble_mac/table_id arbitrários) — "
     "vão para SQLite e API Deli sem validação de formato."),
    ("B2", "BAIXA", "4", "backend/deli_adapter.py:124-133",
     "comanda_id do banco vai direto para <font face=\"Courier\" size=\"7\">GET /sales/{sale_id}</font> sem validar "
     "<font face=\"Courier\" size=\"7\">^[A-Za-z0-9_-]+$</font>."),
    ("B3", "BAIXA", "4", "backend/deli_adapter.py:75,92 + backend/app.py:263",
     "Corpo de erro do Deli (resp.text) refletido no detail do 502 — info-leak menor (JSON, não HTML)."),
    ("B4", "BAIXA", "5", ".gitignore:1-8 + backend/app.py:44",
     ".gitignore não cobre *.db/_build — smartbadge.db (dados de clientes) e .bin/.hex do nRF podem ser "
     "commitados por acidente."),
    ("B5", "BAIXA", "3", "gateway_esp32/gateway_esp32.ino:90-108",
     "proto_version do pacote BLE ignorado — pacote futuro/incompatível passa (battery/seq sem range-check)."),
    ("I1", "INFORMATIVA", "5", "gateway_esp32/gateway_esp32.ino:24-28",
     "Placeholders WiFi commitados de propósito (PUB_WIFI/SENHA_AQUI) com TODO — risco futuro se "
     "credencial real for commitada."),
    ("I2", "INFORMATIVA", "5", "backend/requirements.txt:1-4 + gateway .ino:20-21 + modelo_3d_prototipo.html:7",
     "Deps sem lock/pin (paho-mqtt 1.6 ramo antigo, ArduinoJson/PubSubClient sem versão, three.js r128 CDN 2021)."),
]

SEV_COR = {
    "ALTA": ("#9A3412", "#FFF7ED"),
    "MÉDIA": ("#92400E", "#FFFBEB"),
    "BAIXA": ("#1E40AF", "#EFF6FF"),
    "INFORMATIVA": ("#374151", "#F3F4F6"),
}

PONTOS_FORTES = [
    "SQL 100% parametrizado (app.py:250, 267-274, 285, 292-293, 309, 317-318, 327 — sem concatenação).",
    "Segredos Deli somente via env com fail-fast (deli_adapter.py:54-59) e nunca hardcode.",
    "Histórico git limpo de segredos reais; .env ignorado.",
    "Parser BLE do gateway valida length/company_id/casts (ino:93, 99, 102-103, 107-108).",
    "SAADC com clamp (main.c).",
    "snprintf com sizeof (ino:142-143).",
    "MQTT com try/except (app.py:185-197).",
    "HTMLs sem innerHTML/fetch.",
    "Sem Jinja/smtplib no backend.",
]

RECOMENDACOES = [
    ("P1", "Exigir API key/Bearer no backend + checar chamador nas rotas de escrita",
     "Cobre A1, A2. Autenticar todas as rotas de escrita (checkin/checkout) e validar que o chamador tem "
     "permissão sobre a pulseira/comanda informada."),
    ("P2", "Habilitar auth + TLS no Mosquitto e credenciais por gateway",
     "Cobre M4. Configurar username/senha por gateway, TLS no broker e ACLs por tópico; remover o connect "
     "anônimo contra 192.168.0.10:1883."),
    ("P3", "Rate-limit/paginação e auth nas rotas de leitura",
     "Cobre M1, M2, M3. Exigir autenticação nas rotas de leitura, adicionar paginação/filtro e rate-limit "
     "para conter enumeração de clientes e tags."),
    ("P4", "Validar formatos (UUID/MAC/table/sale_id) com pydantic pattern",
     "Cobre B1, B2 e gateway proto (B5). Adicionar pattern/min_length nos schemas e validar "
     "sale_id contra ^[A-Za-z0-9_-]+$; checar proto_version e ranges (battery/seq) no gateway."),
    ("P5", ".gitignore += *.db *.sqlite firmware/**/_build *.bin *.hex",
     "Cobre B4. Impedir commit acidental de smartbadge.db (dados de clientes) e binários do nRF."),
    ("P6", "Parar de ecoar resp.text do Deli; logar interno",
     "Cobre B3. Retornar mensagem genérica no 502 e registrar o corpo upstream apenas em log interno."),
    ("P7", "Pinar deps (pip freeze/SBOM, paho-mqtt 2.x, ArduinoJson v7) + trocar three.js r128",
     "Cobre I2. Travar versões, gerar SBOM, migrar paho-mqtt para o ramo 2.x e substituir o three.js r128 "
     "(CDN, 2021) por versão atual."),
    ("P8", "Provisioning NVS + nunca commitar WiFi real",
     "Cobre I1. Manter placeholders fora do repo ou usar provisioning em NVS; bloquear credenciais reais "
     "com pre-commit/CI."),
]

ISSUES = [
    {
        "titulo": "[Segurança] Rotas de escrita sem autenticação — checkin/checkout",
        "labels": "security, alta",
        "md": [
            "## Problema",
            "",
            "`POST /pulseiras/checkin` e `POST /pulseiras/checkout` não exigem autenticação nem",
            "autorização: qualquer host com acesso à rede do backend abre comandas no Deli",
            "(sistema fiscal externo) e libera pulseiras.",
            "",
            "## Evidência",
            "",
            "- `backend/app.py:246` — `def checkin_pulseira(req: CheckinRequest)` +",
            "  `DeliClient.abrir_comanda()`",
            "- `backend/app.py:278` — `def checkout_pulseira(req: CheckoutRequest)` +",
            "  `UPDATE pulseiras SET status='livre'` (nfc_uid vem do body, chamador não verificado)",
            "",
            "## Impacto",
            "",
            "Criação de vendas fraudulentas no sistema fiscal, encerramento indevido de comandas,",
            "divergência de caixa e risco fiscal/contábil.",
            "",
            "## Correção",
            "",
            "- Exigir API key/Bearer em todas as rotas de escrita (P1).",
            "- Verificar que o chamador tem permissão sobre a pulseira/comanda (check de chamador).",
            "- Considerar rate-limit e trilha de auditoria (quem/quando).",
            "",
            "## Aceite",
            "",
            "- [ ] Requisição sem credencial retorna 401/403 em `/pulseiras/checkin` e `/pulseiras/checkout`.",
            "- [ ] Credencial válida sem permissão sobre a pulseira é negada.",
            "- [ ] Teste automatizado cobre os dois casos.",
        ],
    },
    {
        "titulo": "[Segurança] Leitura de localização/comandas sem auth",
        "labels": "security, média",
        "md": [
            "## Problema",
            "",
            "Rotas de leitura expõem localização em tempo real e dump de comandas sem autenticação,",
            "filtro ou paginação.",
            "",
            "## Evidência",
            "",
            "- `backend/app.py:217` — `def get_localizacao(mac: str)` lê `_tag_states[mac]`",
            "- `backend/app.py:323` — `GET /pulseiras` retorna `nfc_uid, ble_mac, status, comanda_id`",
            "- `backend/app.py:335` — `GET /localizacoes` expõe todas as tags online",
            "",
            "## Impacto",
            "",
            "Rastreamento de clientes (privacidade), enumeração de comandas ativas e vazamento de",
            "identificadores (nfc_uid/ble_mac).",
            "",
            "## Correção",
            "",
            "- Exigir auth nas rotas de leitura (P3).",
            "- Adicionar paginação/filtro e rate-limit contra enumeração.",
            "- Avaliar minimização: retornar só o necessário por chamador.",
            "",
            "## Aceite",
            "",
            "- [ ] Rotas retornam 401/403 sem credencial.",
            "- [ ] Listagens paginadas com limite padrão.",
            "- [ ] Rate-limit ativo e testado.",
        ],
    },
    {
        "titulo": "[Segurança] MQTT sem auth/TLS permite telemetria falsa",
        "labels": "security, média",
        "md": [
            "## Problema",
            "",
            "O gateway conecta ao broker sem usuário/senha e sem TLS; qualquer host pode publicar",
            "telemetria falsa ou assinar os dados de localização.",
            "",
            "## Evidência",
            "",
            "- `gateway_esp32/gateway_esp32.ino:75` — connect sem user/pass",
            "- `backend/app.py:41-43` — cliente MQTT sem auth/TLS",
            "- Broker `192.168.0.10:1883` (porta plaintext)",
            "",
            "## Impacto",
            "",
            "Localização forjada (garçom vai à mesa errada), replay de pacotes e espionagem do tráfego",
            "de telemetria na rede do pub.",
            "",
            "## Correção",
            "",
            "- Habilitar auth + TLS no Mosquitto, credencial por gateway (P2).",
            "- ACLs por tópico; negar anonymous.",
            "- Provisionar senhas fora do código (NVS/secret).",
            "",
            "## Aceite",
            "",
            "- [ ] Broker recusa conexão anônima e plaintext.",
            "- [ ] Gateway e backend conectam via TLS com credenciais.",
            "- [ ] ACL impede gateway de assinar/publicar fora do seu namespace.",
        ],
    },
    {
        "titulo": "[Segurança] Validar formatos de input",
        "labels": "security, baixa",
        "md": [
            "## Problema",
            "",
            "Identificadores entram sem validação de formato e fluem para SQLite, API Deli e parser BLE.",
            "",
            "## Evidência",
            "",
            "- `backend/app.py:233-240` — `CheckinRequest`/`CheckoutRequest` sem `pattern`/`min_length`",
            "  (`nfc_uid`/`ble_mac`/`table_id` arbitrários)",
            "- `backend/deli_adapter.py:124-133` — `comanda_id` vai direto a `GET /sales/{sale_id}`",
            "  sem validar `^[A-Za-z0-9_-]+$`",
            "- `gateway_esp32/gateway_esp32.ino:90-108` — `proto_version` ignorado; `battery`/`seq`",
            "  sem range-check",
            "",
            "## Impacto",
            "",
            "Dados malformados chegam ao sistema fiscal, erro de localização por pacote incompatível e",
            "superfície para injection/path-confusion no `sale_id`.",
            "",
            "## Correção",
            "",
            "- Schemas pydantic com `pattern` (UUID/MAC/table/sale_id) — P4.",
            "- Rejeitar `proto_version` desconhecido e validar ranges no gateway.",
            "",
            "## Aceite",
            "",
            "- [ ] Inputs fora do formato retornam 422.",
            "- [ ] Pacote BLE com versão desconhecida é descartado (log).",
            "- [ ] Testes de formato para cada campo.",
        ],
    },
    {
        "titulo": "[Segurança] .gitignore não cobre banco e binários",
        "labels": "security, baixa",
        "md": [
            "## Problema",
            "",
            "O `.gitignore` não cobre `*.db`/`_build`, permitindo commit acidental do banco de clientes",
            "e de binários do firmware.",
            "",
            "## Evidência",
            "",
            "- `.gitignore:1-8` — sem regra para `*.db`, `*.sqlite`, `_build`, `*.bin`, `*.hex`",
            "- `backend/app.py:44` — `smartbadge.db` (dados de clientes)",
            "",
            "## Impacto",
            "",
            "Vazamento de dados de clientes no histórico git (difícil de expurgar) e poluição do repo",
            "com artefatos de build.",
            "",
            "## Correção",
            "",
            "- `.gitignore += *.db *.sqlite firmware/**/_build *.bin *.hex` (P5).",
            "- Auditar histórico por artefatos já commitados.",
            "",
            "## Aceite",
            "",
            "- [ ] `git status` limpo após build + execução local.",
            "- [ ] CI falha se artefato for adicionado.",
        ],
    },
    {
        "titulo": "[Segurança] Erro upstream refletido no 502",
        "labels": "security, baixa",
        "md": [
            "## Problema",
            "",
            "O corpo de erro da API Deli é refletido no `detail` do 502, expondo conteúdo upstream",
            "ao chamador.",
            "",
            "## Evidência",
            "",
            "- `backend/deli_adapter.py:75,92` — usa `resp.text` no erro",
            "- `backend/app.py:263` — repassa ao `detail` do 502",
            "",
            "## Impacto",
            "",
            "Info-leak menor (JSON, não HTML): detalhes internos do integrador/fiscal podem vazar para",
            "qualquer chamador da API.",
            "",
            "## Correção",
            "",
            "- Retornar mensagem genérica no 502 e logar o corpo internamente (P6).",
            "",
            "## Aceite",
            "",
            "- [ ] 502 não contém `resp.text` do upstream.",
            "- [ ] Corpo upstream aparece no log interno com correlation-id.",
        ],
    },
    {
        "titulo": "[Segurança] Higiene de dependências e placeholders",
        "labels": "security, informativa",
        "md": [
            "## Problema",
            "",
            "Dependências sem lock/pin e placeholders de WiFi no código criam risco de supply-chain e",
            "de commit acidental de credencial.",
            "",
            "## Evidência",
            "",
            "- `backend/requirements.txt:1-4` — sem lock (`paho-mqtt 1.6`, ramo antigo)",
            "- `gateway_esp32.ino:20-21` — `ArduinoJson`/`PubSubClient` sem versão",
            "- `modelo_3d_prototipo.html:7` — `three.js r128` via CDN (2021)",
            "- `gateway_esp32.ino:24-28` — placeholders `PUB_WIFI`/`SENHA_AQUI` com TODO",
            "",
            "## Impacto",
            "",
            "Builds não reproduzíveis, vulnerabilidades conhecidas em lib antiga e risco futuro de",
            "credencial real commitada.",
            "",
            "## Correção",
            "",
            "- `pip freeze`/SBOM, paho-mqtt 2.x, ArduinoJson v7, trocar three.js r128 (P7).",
            "- Provisioning via NVS; nunca commitar WiFi real; pre-commit/CI (P8).",
            "",
            "## Aceite",
            "",
            "- [ ] Lockfile/SBOM gerado e CI verifica.",
            "- [ ] `grep` por credencial real no CI.",
            "- [ ] three.js atualizado ou removido do CDN antigo.",
        ],
    },
]


# ---------------------------------------------------------------- construção
def cabecalho_rodape(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#6B7280"))
    canvas.drawString(2 * cm, A4[1] - 1.3 * cm, TITULO)
    canvas.drawRightString(A4[0] - 2 * cm, A4[1] - 1.3 * cm, DATA)
    canvas.setStrokeColor(colors.HexColor("#D1D5DB"))
    canvas.setLineWidth(0.5)
    canvas.line(2 * cm, A4[1] - 1.5 * cm, A4[0] - 2 * cm, A4[1] - 1.5 * cm)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawCentredString(A4[0] / 2, 1.2 * cm, "%s  •  Página %d" % (TITULO, doc.page))
    canvas.restoreState()


def nota_box(texto, s_peq, fundo="#F9FAFB", borda="#D1D5DB"):
    t = Table([[Paragraph(texto, s_peq)]], colWidths=[A4[0] - 4 * cm - 12])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(fundo)),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor(borda)),
        ("INNERPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def md_para_issue(linhas, s_codigo):
    flux = []
    for ln in linhas:
        if ln == "":
            flux.append(Spacer(1, 3))
        else:
            esc = ln.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            flux.append(Paragraph(esc, s_codigo))
    return flux


def construir():
    gerar_graficos()
    (ss, s_titulo, s_sub, s_h1, s_h2, s_corpo, s_bullet,
     s_peq, s_codigo, s_cel, s_cel_c, s_chip) = estilos()

    doc = SimpleDocTemplate(
        PDF_PATH, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        title=TITULO, author="Auditoria de Segurança — NibasRockBar",
    )
    W = A4[0] - 4 * cm
    story = []

    # ---- capa
    story.append(Spacer(1, 2.2 * cm))
    story.append(Paragraph("Relatório de Auditoria de Segurança", s_titulo))
    story.append(Paragraph("<b>NibasRockBar</b> — pulseira NFC + BLE integrada ao Deli",
                           ParagraphStyle("Sub2", parent=s_sub, fontSize=12, leading=15,
                                          textColor=colors.HexColor(C_ACENTO))))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Data: <b>%s</b> &nbsp;•&nbsp; Projeto: <b>NibasRockBar</b> &nbsp;•&nbsp; "
                           "Classificação: <b>uso interno</b>" % DATA, s_sub))
    story.append(Spacer(1, 8 * mm))

    meta = [
        [Paragraph("<b>Escopo</b>", s_peq),
         Paragraph("Backend FastAPI (<font face=\"Courier\">backend/app.py</font>, "
                   "<font face=\"Courier\">backend/deli_adapter.py</font>), firmware "
                   "(<font face=\"Courier\">firmware/main.c</font>, <font face=\"Courier\">firmware/nrf/main.c</font>, "
                   "<font face=\"Courier\">gateway_esp32/gateway_esp32.ino</font>), HTMLs estáticos, "
                   "deploy (inexistente), git history, dependências.", s_peq)],
        [Paragraph("<b>Método</b>", s_peq),
         Paragraph("Revisão manual do código real (arquivo:linha), sem testes dinâmicos nem pentest; "
                   "vereditos já verificados no código-fonte.", s_peq)],
    ]
    tm = Table(meta, colWidths=[2.6 * cm, W - 2.6 * cm])
    tm.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F3F4F6")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#D1D5DB")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E5E7EB")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("INNERPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(tm)
    story.append(Spacer(1, 5 * mm))
    story.append(nota_box(
        "<b>Nota metodológica — mapeamento das 5 categorias para a stack:</b> "
        "Cat. 1 — autenticação, autorização e privacidade no backend (3 achados: A1, A2, M1); "
        "Cat. 2 — controle de acesso por papéis no frontend (0 — <b>N/A</b>: não há frontend com papéis; "
        "sem framework, HTMLs estáticos sem gates isAdmin/role); "
        "Cat. 3 — segurança de comunicação e protocolo BLE/MQTT (2: M4, B5); "
        "Cat. 4 — validação de entrada e tratamento de erros (3: B1, B2, B3); "
        "Cat. 5 — exposição de superfície, configuração, segredos e dependências (5: M2, M3, B4, I1, I2). "
        "Nenhum achado crítico (0).",
        s_peq, fundo="#FFFBEB", borda="#F59E0B"))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("13 achados • 2 altos • 4 médios • 5 baixos • 2 informativos • 9 pontos fortes",
                           ParagraphStyle("Resumo", parent=s_sub, fontSize=10, leading=13,
                                          textColor=colors.HexColor(C_TINTA))))

    # ---- resumo executivo
    story.append(Paragraph("1 &nbsp; Resumo executivo", s_h1))
    story.append(Paragraph(
        "A auditoria encontrou <b>13 achados</b> e nenhum de severidade crítica. Os dois achados altos (A1, A2) "
        "concentram o risco real: as rotas de escrita operam o sistema fiscal externo (Deli) sem autenticação, "
        "de modo que qualquer host na rede cria ou encerra vendas. Quatro achados médios ampliam a superfície "
        "(localização/comandas legíveis sem auth e MQTT sem auth/TLS). Cinco achados baixos e dois informativos "
        "pedem endurecimento de validação, configuração e dependências. Em contrapartida, há <b>9 pontos fortes "
        "verificados</b> — SQL 100% parametrizado, segredos só via ambiente e parser BLE defensivo — que devem "
        "ser preservados. Deploy é inexistente (sem TLS reverso, sem segredo de produção avaliável).", s_corpo))

    tot = [
        [Paragraph("<b>Severidade</b>", s_cel_c), Paragraph("<b>Qtd</b>", s_cel_c)],
        [Paragraph("Crítica", s_cel_c), Paragraph("0", s_cel_c)],
        [Paragraph("<b>Alta</b>", s_cel_c), Paragraph("<b>2</b>", s_cel_c)],
        [Paragraph("Média", s_cel_c), Paragraph("4", s_cel_c)],
        [Paragraph("Baixa", s_cel_c), Paragraph("5", s_cel_c)],
        [Paragraph("Informativa", s_cel_c), Paragraph("2", s_cel_c)],
        [Paragraph("<b>Total de achados</b>", s_cel_c), Paragraph("<b>13</b>", s_cel_c)],
        [Paragraph("Pontos fortes", s_cel_c), Paragraph("9", s_cel_c)],
    ]
    tt = Table(tot, colWidths=[7 * cm, 3 * cm])
    tt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(C_TINTA)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#9CA3AF")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D1D5DB")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(Spacer(1, 3 * mm))
    story.append(tt)
    story.append(Spacer(1, 4 * mm))
    story.append(Image(ROSCA_PNG, width=13.5 * cm, height=8.07 * cm))
    story.append(Paragraph("Figura 1 — distribuição por severidade. Crítica: 0 (sem fatia). "
                           "Informativa em cinza neutro; pontos fortes em verde.", s_peq))
    story.append(Spacer(1, 2 * mm))
    story.append(Image(BARRAS_PNG, width=13.5 * cm, height=7.0 * cm))
    story.append(Paragraph("Figura 2 — achados por categoria. Cat. 2 = 0 (N/A: sem frontend com papéis).", s_peq))

    # ---- pontos fortes vs fracos
    story.append(Paragraph("2 &nbsp; Pontos fortes vs. pontos fracos", s_h1))
    story.append(Paragraph("Pontos fortes (evidência verificada)", s_h2))
    for i, pf in enumerate(PONTOS_FORTES, 1):
        story.append(Paragraph("F%d — %s" % (i, pf), s_bullet, bulletText="•"))
    story.append(Paragraph(
        "Categoria 2 = N/A: não há frontend com papéis — sem framework; HTMLs estáticos sem gates "
        "isAdmin/role; portanto nada a auditar nessa categoria.", s_corpo))
    story.append(Paragraph("Pontos fracos (síntese)", s_h2))
    fracos = [
        "<b>Escrita sem auth (A1, A2 — alta):</b> checkin abre comanda fiscal e checkout libera pulseira "
        "sem verificar o chamador.",
        "<b>Leitura sem auth (M1, M2, M3 — média):</b> localização em tempo real e dumps de "
        "pulseiras/tags acessíveis a qualquer host.",
        "<b>Canal sem proteção (M4 — média):</b> MQTT sem auth/TLS permite telemetria falsa e espionagem.",
        "<b>Validação e erros (B1, B2, B3, B5 — baixa):</b> inputs sem formato, sale_id sem regex, erro "
        "upstream ecoado e proto BLE ignorado.",
        "<b>Higiene (B4, I1, I2 — baixa/informativa):</b> .gitignore incompleto, placeholders WiFi e deps "
        "sem pin.",
    ]
    for f in fracos:
        story.append(Paragraph(f, s_bullet, bulletText="•"))

    # ---- tabela de achados
    story.append(Paragraph("3 &nbsp; Tabela de achados", s_h1))
    story.append(Paragraph(
        "Treze achados verificados no código real. Severidade indicada por chip colorido; "
        "“Cat.” remete às categorias da nota metodológica (capa).", s_corpo))
    cab = [Paragraph("<b>ID</b>", s_cel_c), Paragraph("<b>Sev.</b>", s_cel_c),
           Paragraph("<b>Cat.</b>", s_cel_c), Paragraph("<b>Arquivo:linha</b>", s_cel_c),
           Paragraph("<b>Descrição</b>", s_cel_c)]
    linhas = [cab]
    for aid, sev, cat, local, desc in ACHADOS:
        fg, _bg = SEV_COR[sev]
        linhas.append([
            Paragraph("<b>%s</b>" % aid, s_cel_c),
            Paragraph('<font color="%s"><b>%s</b></font>' % (fg, sev), s_chip),
            Paragraph(cat, s_cel_c),
            Paragraph(local.replace(" + ", "<br/>+ "), s_cel),
            Paragraph(desc, s_cel),
        ])
    larg = [1.1 * cm, 2.2 * cm, 1.0 * cm, 3.6 * cm, W - 7.9 * cm]
    ta = LongTable(linhas, colWidths=larg, repeatRows=1)
    estilo_tab = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(C_TINTA)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#9CA3AF")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D1D5DB")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ])
    ta.setStyle(estilo_tab)
    # chips de severidade: fundo claro por linha
    for r, (_aid, sev, _cat, _loc, _d) in enumerate(ACHADOS, 1):
        fg, bg = SEV_COR[sev]
        ta.setStyle(TableStyle([
            ("BACKGROUND", (1, r), (1, r), colors.HexColor(bg)),
            ("TEXTCOLOR", (1, r), (1, r), colors.HexColor(fg)),
        ]))
    story.append(ta)

    # ---- recomendações
    story.append(Paragraph("4 &nbsp; Recomendações", s_h1))
    story.append(Paragraph("Ordenadas por prioridade (P1 = maior risco/urgência).", s_corpo))
    for pid, titulo, corpo in RECOMENDACOES:
        story.append(Paragraph("<b>%s — %s</b>" % (pid, titulo), s_h2))
        story.append(Paragraph(corpo, s_corpo))

    # ---- issues github
    story.append(Paragraph("5 &nbsp; Issues para o GitHub", s_h1))
    story.append(Paragraph(
        "Sete issues prontas para abertura, com texto Markdown completo entre os delimitadores "
        "--- ISSUE n --- e --- FIM ISSUE n ---.", s_corpo))
    for n, issue in enumerate(ISSUES, 1):
        story.append(Paragraph("<b>--- ISSUE %d ---</b>" % n,
                               ParagraphStyle("Delim", parent=s_peq, alignment=TA_CENTER,
                                              textColor=colors.HexColor(C_TINTA), fontSize=9)))
        story.append(Paragraph("# %s" % issue["titulo"], s_h2))
        story.append(Paragraph("<b>Labels:</b> %s" % issue["labels"], s_corpo))
        story.extend(md_para_issue(issue["md"], s_codigo))
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph("<b>--- FIM ISSUE %d ---</b>" % n,
                               ParagraphStyle("DelimF", parent=s_peq, alignment=TA_CENTER,
                                              textColor=colors.HexColor(C_TINTA), fontSize=9)))
        if n < len(ISSUES):
            story.append(Spacer(1, 4 * mm))

    doc.build(story, onFirstPage=cabecalho_rodape, onLaterPages=cabecalho_rodape)
    return PDF_PATH


if __name__ == "__main__":
    out = construir()
    print("PDF gerado: %s" % out)
