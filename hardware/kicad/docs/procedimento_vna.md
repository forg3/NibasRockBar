# Procedimento VNA — Tuning RF Variante B (bancada)

**Escopo:** variante B (`hardware/kicad/wristband_discreto/`) — nRF52810-QCAA.
**Data:** 2026-09-10 · **Revisão:** A.

## 1. Objetivo

Casar a saída ANT (pino 19 do U1) com a antena chip ANT1
Johanson 2450AT18A100 em 2,4 GHz, através da rede de 2 elementos
da referência Nordic (PS v1.3 Fig. 146):

- `NET_ANT` = {U1.19, C3.1, L1.1}
- C3 0,8 pF shunt → GND (C3.2 em GND)
- L1 3,9 nH série entre `NET_ANT` e `NET_RF`
- `NET_RF` = {L1.2, ANT1.1} (feed da antena)
- ANT1.2 → GND

O tuning corrige o deslocamento causado por FR-4 0,8 mm,
cápsula, bateria CR2032 e ferrite — não o valor nominal.

## 2. Equipamento e pré-condições

- VNA com faixa até 3 GHz ou mais (NanoVNA V2 aceito p/ triagem).
- Calibração SOLT (curto-aberto-carga) no plano de medição.
- Cabo semi-rígido curto + conector U.FL de teste no footprint,
  ou sonda RF com GND próximo ao feed.
- Kit de valores 0402 NP0 / alta-Q para C3 e L1 (ver §5).
- Placa de sacrifício com a antena montada + keep-out respeitado.
- Bateria e ferrite presentes (condição real de uso).

## 3. Pontos de teste

- Nó A: junção C3.1 / L1.1 / U1.19 (`NET_ANT`).
- Nó B: saída L1.2 / ANT1.1 (`NET_RF`, feed da antena).
- GND: pad ANT1.2 ou plano próximo ao feed.
- Medir S11 com a placa na posição final (dentro da cápsula
  se possível; mão e mesa afetam o resultado).

## 4. Leitura de S11

- Faixa de varredura: 2,0–3,0 GHz; marcador em 2400–2480 MHz.
- Alvo: mínimo de S11 (vale de ressonância) dentro de 2400–2480 MHz.
- Critério: VSWR < 2 (S11 < −9,5 dB) em toda a faixa BLE.
- Registrar também a carta de Smith: ponto deve estar
  próximo ao centro (50 Ω) em 2440 MHz.

## 5. Sequência de ajuste

1. Montar valores nominais: C3 = 0,8 pF, L1 = 3,9 nH.
2. Medir S11 de referência e anotar na tabela (§7).
3. Ajustar C3 primeiro (move a parte imaginária):
   tentar 0,5 / 0,8 / 1,0 / 1,2 pF, um valor por vez.
4. Fixar o melhor C3 e ajustar L1 (move a ressonância):
   tentar 2,7 / 3,3 / 3,9 / 4,7 nH.
5. Repetir uma rodada fina C3 ± 0,2 pF se o vale ainda
   estiver deslocado mais que 40 MHz.
6. Footprints 0402 de C3/L1 aceitam 0 Ω ou fio como
   bypass temporário só para diagnóstico — nunca como final.
7. Uma variável por vez; re-soldar com ponta fina e limpar
   fluxo antes de cada medida.

## 6. O que NÃO mexer

- Topologia é de 2 elementos (C3 + L1). Não adicionar C/L extra.
- L3 (15 nH) pertence ao ladder do DC/DC
  (DCC → L2 10 µH → L3 → DEC4 + C10) — fora do caminho RF.
- Não trocar ANT1 por outro modelo sem repetir todo o tuning.
- Não remover o keep-out da antena nem o plano GND sob o nRF.
- Não fechar comanda nem alterar firmware durante o tuning:
  medir com o rádio em TX contínuo ou placa desligada
  conforme o método do VNA (seguir o manual do equipamento).

## 7. Critério de aceite + registro

Aceite: S11 < −9,5 dB (VSWR < 2) de 2400 a 2480 MHz,
vale principal dentro da faixa, medida com bateria + ferrite.

| Tentativa | C3 (pF) | L1 (nH) | S11 @2440 (dB) | Freq. vale (MHz) | VSWR máx. 2400–2480 | OK? |
|---|---|---|---|---|---|---|
| 0 (nominal) | 0,8 | 3,9 | | | | |
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |
| Final | | | | | | |

Anexar print da tela do VNA (S11 + Smith) da tentativa final
ao dossiê do protótipo.
