# Betaflight Control — BetaFPV Air65 Racing

Tool Python per ispezionare, fare backup e configurare programmaticamente Betaflight via USB (MSP e CLI).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Regole di sicurezza

1. **Chiudi l'app Betaflight Configurator** prima di eseguire gli script (una sola app alla volta può usare `/dev/cu.usbmodem*`).
2. **Scollega la LiPo** (o rimuovi le eliche) durante la configurazione via USB.
3. Fai sempre un **backup** (`diff all`) prima di modificare qualsiasi parametro.

## Comandi principali

```bash
# Elenca le porte seriali rilevate
python bf_tool.py ports

# Legge versione firmware, board ID e target via MSP
python bf_tool.py info

# Salva un backup completo `diff all` in drone/backups/
python bf_tool.py backup --with-dump

# Esegue un comando CLI di sola lettura (es. status, tasks, get min_check)
python bf_tool.py cmd status

# Anteprima applicazione file CLI senza inviare nulla
python bf_tool.py apply drone/configs/rateprofile1_indoor_soft.txt --dry-run

# Applica comandi CLI e salva in EEPROM
python bf_tool.py apply drone/configs/rateprofile1_indoor_soft.txt --save
```
