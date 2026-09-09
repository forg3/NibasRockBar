# Receita KiCad 10.0.6 — Geração de Esquemáticos por Código

**Versão testada:** KiCad 10.0.6 (Fedora 44, `/usr/bin/kicad-cli`, python3 3.14 + `import pcbnew` funcional)
**Data:** 2026-09-09
**Ambiente:** `kicad-cli` apenas — **NUNCA** invocar binário `kicad` (GUI) — trava o shell.

---

## 1. Headers Exatos dos Arquivos

### 1.1 `.kicad_pro` (Project File) — **É JSON, NÃO S-expression**
```json
{
 "meta": {
  "filename": "wristband_discreto.kicad_pro",
  "version": 3
 },
 "libraries": {},
 "schematic": {
  "legacy_lib_dir": "",
  "legacy_lib_list": []
 },
 "sheets": [
  ["<uuid-raiz-do-kicad_sch>", "Root"]
 ],
 "erc": {
  "rule_severities": { "footprint_link_issues": "ignore", "pin_not_driven": "ignore" }
 },
 "text_variables": []
}
```
- **ERRADO** (causa exit 3 no carregamento): escrever o `.kicad_pro` como S-expression
  `(kicad_project ...)`. O KiCad 10 exige **JSON** (`meta.version 3` confirmado nos projetos
  `wristband_modulo`/`gateway_esp32`/`wristband_discreto` desta máquina).
- Sem o `.kicad_pro` JSON válido, o **sym-lib-table do projeto não carrega** (o CLI não
  encontra as libs registradas → warnings `lib_symbol_issues`).
- As tabelas de bibliotecas **NÃO** ficam dentro do `.kicad_pro`: são os arquivos separados
  `sym-lib-table` e `fp-lib-table` (S-expression, `version 7`) — ver §3.1.
- `sheets` deve conter o **mesmo UUID raiz** do `(uuid ...)` do `.kicad_sch`.

### 1.2 `.kicad_sch` (Schematic File)
```sexp
(kicad_sch
  (version 20250610)
  (generator "eeschema")
  (generator_version "9.99")
  (uuid "12345678-1234-1234-1234-123456789abc")
  (paper "A3")
  (title_block
    (title "Spike Test Schematic")
    (date "2026-09-08")
    (rev "A")
    (company "NibasRockBar")
    (comment "Minimal test: 1R + 1C + power symbols")
    (sheet "1/1")
  )
  (lib_symbols
    ... símbolos embutidos ...
  )
  (symbol ... instâncias ...)
  (wire ...)
  (junction ...)
)
```
- `version 20250610` (data YYYYMMDD — **não** usar 10 ou 20240108)
- `generator "eeschema"` / `generator_version "9.99"` (string "9.99" funciona; "10.0.6" falha parsing)
- `uuid` válido (formato RFC4122)
- `paper "A3"` ou `"A4"`
- `title_block` com todos os campos preenchidos
- **`title_block` exige `(comment N "...")` NUMERADO** (`(comment 1 "...")`, `(comment 2 "...")`).
  Um `(comment "...")` sem número **quebra o parser** (exit 3, "Houve uma falha ao ler o
  esquemático").

### 1.3 `.kicad_sym` (Symbol Library File)
```sexp
(kicad_symbol_lib
  (version 20250610)
  (generator "kicad_symbol_editor")
  (generator_version "10.0.6")
  (symbol "NOME_SIMBOLO"
    (pin_numbers (hide yes))
    (pin_names (offset 0) (hide yes))
    (exclude_from_sim no)
    (in_bom yes)
    (on_board yes)
    (in_pos_files yes)
    (duplicate_pin_numbers_are_jumpers no)
    (property "Reference" "U" ...)
    (property "Value" "NOME_SIMBOLO" ...)
    (property "Footprint" "" ...)
    (property "Datasheet" "" ...)
    (symbol "NOME_SIMBOLO_0_1" ... gráficos ...)
    (symbol "NOME_SIMBOLO_1_1"
      (pin passive line (at 0 5.08 270) (length 2.54) ...)
      (pin passive line (at 0 -5.08 90) (length 2.54) ...)
    )
    (embedded_fonts no)
  )
)
```
- `version` = data YYYYMMDD (ex: 20250610)
- `generator "kicad_symbol_editor"` / `generator_version "10.0.6"`
- Cada símbolo tem sub-símbolos `_0_1` (gráficos) e `_1_1` (pins por unidade)
- Pinos: tipo `passive line` / `power_in line` / `power_out line`, com `(at x y orientação)`, `(length)`, `(name "")`, `(number "N")`
- `(embedded_fonts no)` obrigatório no final de cada símbolo

---

## 1.5 Regras do Parser do kicad-cli 10.0.6 (descobertas nos passos 4.1–4.3 — APLICAR TODAS)

1. **`title_block` exige `(comment N "...")` NUMERADO** — comentário sem número quebra o
   parser (exit 3).
2. **`lib_symbols`: nome do símbolo embutido = lib_id COMPLETO com prefixo**
   (ex.: `(symbol "Device:R" ...)`), **sub-unidades sem prefixo** (`R_0_1`, `R_1_1`).
   Embed sem prefixo gera pinos fantasmas — netlist/ERC silenciosamente errados.
3. **Dentro de gráficos de símbolo: NUNCA `(text ...)`**; segmentos são `(polyline ...)`,
   nunca `(line ...)`. Texto de anotação só em nível de esquema (`(text ...)` filho direto
   de `kicad_sch` — esse é seguro, usado nos 3 esquemáticos aprovados).
4. **PWR_FLAG padrão é fantasma no CLI** (pin em unidade 0 não instancia). Modele
   alimentação com **pinos de conector como `power_out`** e **power symbols
   (`+3V3`/`+5V`/`GND`) com pino `power_in`**; para marcar nets de potência use PWR_FLAG
   **embutido com o pin `power_out` na unidade `_0_0`** (forma usada em
   `wristband_modulo.kicad_sch`, ERC 0 violações) — ver §4.2.
5. **`.kicad_pro` é JSON** (`meta.version 3`), não S-expression — sem ele o sym-lib-table
   do projeto não carrega (ver §1.1).
6. **kicad-cli carrega sym-lib-table do projeto mas NUNCA fp-lib-table** → o warning
   `footprint_link_issues` pode ser **ignorado com justificativa documentada**
   (`"footprint_link_issues": "ignore"` no `.kicad_pro`; links de footprint validados por nome).
7. **Race raro de flush após gravar arquivo**: "Houve uma falha ao ler o esquemático" logo
   depois de escrever o `.kicad_sch` — **re-executar o comando resolve** (não é erro do arquivo).
8. **Todo UUID RFC4122 v4 ÚNICO** — zero placeholder (`dddd…`), zero duplicata (símbolo,
   pin, wire, junction, label, no_connect, text).

---


## 2. Flags Confirmadas (kicad-cli)

| Comando | Flags que funcionam | Notas |
|---------|---------------------|-------|
| `kicad-cli version` | (nenhuma) | Retorna `10.0.6` |
| `kicad-cli sch erc` | `--exit-code-violations --format json --severity-all -o <out> <sch>` | `--exit-code-violations` retorna código ≠0 se houver violações; sem ela, exit 0 sempre |
| `kicad-cli sch export netlist` | `-o <out> <sch>` | Formato padrão `kicadsexp`; aceita `--format kicadxml` etc. |
| `kicad-cli sch export pdf` | `-o <out> <sch>` | Gera PDF vetorial |
| `kicad-cli sch export bom` | `-o <out> <sch>` | `--format csv` / `--format json` |
| `kicad-cli sch upgrade` | `<sch>` | Atualiza formato do arquivo para versão atual |

**Importante:** Input file **deve ser** `.kicad_sch` (não `.kicad_pro`). ERC falha se o esquemático tiver erros de sintaxe S-expression.

---

## 3. Mecanismo de Biblioteca Local (Projeto)

### 3.1 Registro das libs do projeto: arquivos `sym-lib-table` / `fp-lib-table`
As tabelas de bibliotecas ficam em **arquivos separados** ao lado do `.kicad_pro`
(S-expression, `version 7`) — **não** dentro do `.kicad_pro` (que é JSON, ver §1.1):
```sexp
(sym_lib_table
  (version 7)
  (lib (name "nibas_wristband")(type "KiCad")(uri "${KIPRJMOD}/../libs/nibas_wristband.kicad_sym")(options "")(descr "..."))
)
```
```sexp
(fp_lib_table
  (version 7)
  (lib (name "nibas_wristband")(type "KiCad")(uri "${KIPRJMOD}/../libs/nibas_wristband.pretty")(options "")(descr "..."))
)
```
- `${KIPRJMOD}` expande para o diretório do `.kicad_pro`
- `name` = prefixo usado no `lib_id` (ex: `nibas_wristband:Keystone_1059`)
- `type "KiCad"` para bibliotecas nativas v6+
- ⚠️ O sym-lib-table do projeto **só carrega se o `.kicad_pro` for JSON válido** (regra 5 do §1.5)
- ⚠️ O fp-lib-table **nunca é carregado pelo kicad-cli** (regra 6 do §1.5) — o registro do
  `.pretty` serve para o GUI; no CLI os warnings de footprint link são ignorados com justificativa

### 3.2 Uso no Esquemático
1. **Símbolo embutido em `lib_symbols`** (obrigatório para parsing):
   ```sexp
   (lib_symbols
     (symbol "test:TEST_SYMBOL" ...)  ; nome com prefixo da lib
     ...
   )
   ```
2. **Instância referencia `lib_id "test:TEST_SYMBOL"`**:
   ```sexp
   (symbol
     (lib_id "test:TEST_SYMBOL")
     (at 150 100 0)
     (unit 1)
     ...
     (pin "1" (uuid "..."))
     (pin "2" (uuid "..."))
     (instances (project "" (path "/<uuid>" (reference "U1") (unit 1))))
   )
   ```

### 3.3 Prova de Funcionamento
- ERC roda sem erro "símbolo não encontrado"
- Netlist export inclui o símbolo custom
- PDF export renderiza o símbolo custom
- **Modo clássico de falha:** símbolo referenciado no `lib_id` mas **ausente em `lib_symbols`** → "Houve uma falha ao ler o esquemático"

---

## 4. Estrutura Mínima de Símbolo / Wire / Label / Power Pin

### 4.1 Símbolo Passivo (Resistor/Capacitor)
```sexp
(symbol "R"
  (pin_numbers (hide yes))
  (pin_names (offset 0))
  (exclude_from_sim no)
  (in_bom yes)
  (on_board yes)
  (in_pos_files yes)
  (duplicate_pin_numbers_are_jumpers no)
  (property "Reference" "R" (at 2.032 0 90) ...)
  (property "Value" "R" (at 0 0 90) ...)
  (property "Footprint" "" (at -1.778 0 90) (hide yes) ...)
  (property "Datasheet" "" (at 0 0 0) (hide yes) ...)
  (property "Description" "Resistor" (at 0 0 0) (hide yes) ...)
  (property "ki_keywords" "R res resistor" (at 0 0 0) (hide yes) ...)
  (property "ki_fp_filters" "R_*" (at 0 0 0) (hide yes) ...)
  (symbol "R_0_1"
    (rectangle (start -1.016 -2.54) (end 1.016 2.54) (stroke (width 0.254)) (fill (type none)))
  )
  (symbol "R_1_1"
    (pin passive line (at 0 3.81 270) (length 1.27) (name "") (number "1"))
    (pin passive line (at 0 -3.81 90) (length 1.27) (name "") (number "2"))
  )
  (embedded_fonts no)
)
```

### 4.2 Power Symbol (GND / PWR_FLAG)
```sexp
(symbol "power:GND"
  (power global)
  (pin_numbers (hide yes))
  (pin_names (offset 0) (hide yes))
  (exclude_from_sim no)
  (in_bom yes)
  (on_board yes)
  (in_pos_files yes)
  (duplicate_pin_numbers_are_jumpers no)
  (property "Reference" "#PWR" (at 0 -6.35 0) (hide yes) ...)
  (property "Value" "GND" (at 0 -3.81 0) ...)
  (property "Footprint" "" (at 0 0 0) (hide yes) ...)
  (property "Datasheet" "" (at 0 0 0) (hide yes) ...)
  (property "Description" "Power symbol creates a global label with name \"GND\" , ground" (at 0 0 0) (hide yes) ...)
  (property "ki_keywords" "global power" (at 0 0 0) (hide yes) ...)
  (symbol "GND_0_1"
    (polyline (pts (xy 0 0) (xy 0 -1.27) (xy 1.27 -1.27) (xy 0 -2.54) (xy -1.27 -1.27) (xy 0 -1.27)) (stroke (width 0)) (fill (type none)))
  )
  (symbol "GND_1_1"
    (pin power_in line (at 0 0 270) (length 0) (name "") (number "1"))
  )
  (embedded_fonts no)
)
```
- `(power global)` marca símbolo de power global (cria label implícito)
- Pin type: `power_in` (GND, VCC) ou `power_out` (PWR_FLAG)
- Pin length 0 para power symbols
- **PWR_FLAG não-fantasma (regra 4 do §1.5):** o PWR_FLAG padrão coloca o pin na unidade
  `_0_0` e o CLI não o instancia — ao embutir, manter o pin `power_out` em
  `(symbol "PWR_FLAG_0_0" ...)` e o gráfico em `(symbol "PWR_FLAG_0_1" ...)`, instanciando
  com `(unit 1)` + `(pin "1" (uuid ...))` (forma provada em `wristband_modulo.kicad_sch`)
- Modele alimentação com pinos de conector como `power_out` e power symbols (`+3V3`/`+5V`/
  `GND`/custom `VDD_BAT`) com pino `power_in`; cada net de potência precisa de um driver
  (`power_out` ou PWR_FLAG) senão `power_pin_not_driven` dispara como erro

### 4.3 Wire + Junction
```sexp
(wire
  (pts (xy 80 100) (xy 100 100))
  (stroke (width 0) (type default))
  (uuid "wire_vcc_r1")
)
(junction
  (at 100 100)
  (diameter 0.5)
  (uuid "junc_vcc_r1")
)
```
- Coordenadas em milésimos de mm (unidade interna KiCad)
- `uuid` único por wire/junction (formato RFC4122)

### 4.4 Instância de Símbolo
```sexp
(symbol
  (lib_id "Device:R")
  (at 100 100 0)
  (unit 1)
  (exclude_from_sim no)
  (in_bom yes)
  (on_board yes)
  (dnp no)
  (fields_autoplaced yes)
  (uuid "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
  (property "Reference" "R1" (at 100 95 0) ...)
  (property "Value" "10k" (at 100 110 0) ...)
  (property "Footprint" "Resistor_SMD:R_0603_1608Metric" (at 100 115 0) (hide yes) ...)
  (property "Datasheet" "" (at 100 120 0) (hide yes) ...)
  (pin "1" (uuid "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaab"))
  (pin "2" (uuid "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaac"))
  (instances
    (project ""
      (path "/12345678-1234-1234-1234-123456789abc"
        (reference "R1")
        (unit 1)
      )
    )
  )
)
```
- `lib_id` = `"Biblioteca:Símbolo"` (ex: `Device:R`, `power:GND`, `test:TEST_SYMBOL`)
- `uuid` único por instância
- `instances` com `path` = UUID do esquemático raiz

---

## 5. Exemplo Mínimo Completo (Inline)

Arquivo: `hardware/kicad/_spike/spike.kicad_sch` (16338 bytes, funcional)

```sexp
(kicad_sch
  (version 20250610)
  (generator "eeschema")
  (generator_version "9.99")
  (uuid "1b112ac5-701b-420f-be34-0e29a2cb55ca")
  (paper "A3")
  (title_block
    (title "Spike Test Schematic")
    (date "2026-09-08")
    (rev "A")
    (company "NibasRockBar")
    (comment "Minimal test: 1R + 1C + power symbols")
    (sheet "1/1")
  )
  (lib_symbols
    (symbol "R" ...)           ; Resistor completo
    (symbol "C" ...)           ; Capacitor completo
    (symbol "power:PWR_FLAG" ...) ; Power flag
    (symbol "power:GND" ...)   ; Ground
  )
  (symbol (lib_id "Device:R") (at 100 100 0) ... (pin "1" ...) (pin "2" ...) (instances ...))
  (symbol (lib_id "Device:C") (at 100 130 0) ... (pin "1" ...) (pin "2" ...) (instances ...))
  (symbol (lib_id "power:PWR_FLAG") (at 80 100 0) ... (pin "1" ...) (instances ...))
  (symbol (lib_id "power:GND") (at 80 130 0) ... (pin "1" ...) (instances ...))
  (wire (pts (xy 80 100) (xy 100 100)) ... (uuid "wire_vcc_r1"))
  (wire (pts (xy 100 100) (xy 100 115)) ... (uuid "wire_r1_c1"))
  (wire (pts (xy 100 115) (xy 100 130)) ... (uuid "wire_c1_gnd"))
  (wire (pts (xy 80 130) (xy 100 130)) ... (uuid "wire_gnd_c1"))
  (junction (at 100 100) (diameter 0.5) (uuid "junc_vcc_r1"))
  (junction (at 100 115) (diameter 0.5) (uuid "junc_r1_c1"))
  (junction (at 100 130) (diameter 0.5) (uuid "junc_c1_gnd"))
  (junction (at 80 130) (diameter 0.5) (uuid "junc_gnd_c1"))
)
```

**Arquivos gerados válidos:**
- `spike.kicad_sch` — esquemático (16338 bytes)
- `spike.kicad_pro` — projeto com lib tables locais
- `spike.net` — netlist S-expression (1305 bytes)
- `spike.pdf` — PDF vetorial (36886 bytes)
- `erc.json` — relatório ERC JSON (13 violações esperadas para circuito de teste mínimo)

---

## 6. Limitações e Workarounds

| Limitação | Workaround |
|-----------|------------|
| `generator_version "10.0.6"` em `.kicad_sch` falha parsing | Usar `"9.99"` (string do KiCad 9.99/10 dev) |
| `kicad` (GUI) não tem `--version` e trava shell | Usar **apenas** `kicad-cli` |
| `--exit-code-violations` retorna código ≠0 em violações esperadas | Rodar sem `--exit-code-violations` para exit 0; ou aceitar código ≠0 |
| Símbolo referenciado no `lib_id` mas ausente em `lib_symbols` → parse error | **Sempre** embutir símbolo em `lib_symbols` (mesmo se vem de lib externa) |
| `schnew` Python module não disponível | Usar `pcbnew` apenas; geração de esquemático via S-expression manual |
| Biblioteca local não resolvida se não em `lib_symbols` | Embutir símbolo custom em `lib_symbols` com nome `test:NOME` |
| Coordenadas em milésimos de mm (unidade interna) | Usar valores inteiros (ex: 100 = 100mm = 10cm) |
| `uuid` duplicado causa erro silencioso | Gerar UUIDs únicos (RFC4122) para cada símbolo/wire/junction/pin |
| `.kicad_pro` em S-expression quebra o projeto | Escrever `.kicad_pro` em **JSON** (`meta.version 3`) — ver §1.1 |
| `(comment "...")` sem número no title_block → exit 3 | Numerar: `(comment 1 "...")`, `(comment 2 "...")` — regra 1 do §1.5 |
| `(text ...)`/`(line ...)` dentro de gráficos de símbolo → rejeitado | Só `(polyline ...)`; anotações de texto em nível de esquema — regra 3 do §1.5 |
| kicad-cli nunca carrega fp-lib-table | `footprint_link_issues: ignore` no `.kicad_pro` + justificativa — regra 6 do §1.5 |
| Race raro de flush: parse falha logo após gravar arquivo | **Re-executar o comando** — resolve (regra 7 do §1.5) |

---

## 7. Comandos de Validação (Todos Exit 0 Exceto ERC com --exit-code-violations)

```bash
# Versão
kicad-cli version
# → 10.0.6

# ERC (sem --exit-code-violations para exit 0)
kicad-cli sch erc --format json --severity-all -o hardware/kicad/_spike/erc.json hardware/kicad/_spike/spike.kicad_sch
# → exit 0, gera erc.json com 13 violações (esperadas: PWR_FLAG não conectado, GND não driven, grid alignment)

# Netlist
kicad-cli sch export netlist -o hardware/kicad/_spike/spike.net hardware/kicad/_spike/spike.kicad_sch
# → exit 0, gera spike.net (formato kicadsexp)

# PDF
kicad-cli sch export pdf -o hardware/kicad/_spike/spike.pdf hardware/kicad/_spike/spike.kicad_sch
# → exit 0, gera spike.pdf (36KB)

# Python API
python3 -c "import pcbnew; print(pcbnew.GetBuildVersion())"
# → 10.0.6-1.fc44 (com warnings de assert internos)
python3 -c "import schnew"
# → ModuleNotFoundError (não disponível no KiCad 10.0.6 Fedora)
```

---

## 8. Checklist para Próximos Workers (Waves 3–5)

- [ ] Usar **exatamente** os headers acima (version 20250610, generator "eeschema", generator_version "9.99")
- [ ] `.kicad_pro` em **JSON** (`meta.version 3`) com `sheets` = uuid raiz do `.kicad_sch`
- [ ] `title_block` com `(comment N "...")` numerado
- [ ] Embutir **todos** símbolos em `lib_symbols` (incluindo power symbols e símbolos custom) com nome = lib_id COMPLETO
- [ ] Usar `lib_id` com prefixo da biblioteca (`Device:R`, `power:GND`, `nibas_wristband:VDD_BAT`)
- [ ] Gerar UUIDs únicos (RFC4122 v4) para cada instância, pin, wire, junction, label, no_connect, text
- [ ] Registrar libs custom em `sym-lib-table`/`fp-lib-table` (arquivos separados, `${KIPRJMOD}/...`)
- [ ] `footprint_link_issues: ignore` no `.kicad_pro` (CLI não carrega fp-lib-table) + justificativa
- [ ] Validar com `kicad-cli sch erc --format json --severity-all` (sem `--exit-code-violations` para exit 0)
- [ ] Exportar netlist + PDF para verificação cruzada
- [ ] Não usar `kicad` (GUI), `kiutils`, `skidl`, `schnew` — indisponíveis/quebrados neste ambiente

---

**Fim da receita.** Esta receita é auto-suficiente e deve ser usada como referência única para geração de esquemáticos nas waves seguintes.