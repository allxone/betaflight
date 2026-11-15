# Skyzone Cobra X V4 — Configurazione e Hardware

## Identificazione Hardware & Firmware
- **Modello**: Skyzone Cobra X V4
- **HW**: `v4.1.5`
- **FW1**: `v4.1.5`
- **FW2**: `v02.00.00.12`
- **S/N**: `BA260129`

## Configurazione attuale (2026-11-15)
- **Profilo RF**: `RF Normal`
- **Frequenza**: `R8` (`5917 MHz`) — allineata al VTX dell'Air65 Racing (`band 5`, `ch 8`, `5917 MHz`)
- **Modalità ricevitore**: `Mix1` (SteadyView)
- **Aspect Ratio**: `4:3` (aggiornato da `16:9` il 2026-11-15)
- **DVR**:
  - **microSD**: Inserita (`SI`)
  - **REC Automatico**: `FOLLOW` *(consigliato; opzioni disponibili: `OFF`, `AUTO`, `FOLLOW`, `AUTO&FOLLOW`)*
  - **REC Ciclico**: `ON` *(consigliato; sovrascrive i file più vecchi a SD piena)*
- **Head Tracker**: `OFF` *(non serve su droni FPV/whoop; usato solo per gimbal pan/tilt)*

## Note e suggerimenti per Air65 Racing
- **Aspect Ratio (`16:9` vs `4:3`)**: la camera analogica dell'Air65 Racing ha sensore `4:3`. In `16:9` l'immagine viene leggermente stirata in orizzontale; provare **`4:3`** può migliorare la percezione di spazi stretti/porte in indoor.
- **Mix1 vs Diversity**: `Mix1` è ottimo in campo aperto; se in casa tra i muri noti sfarfallii o bande orizzontali da riflessioni (*multipath*), prova **`Diversity`** per confrontare la pulizia del segnale.
- **Auto Record (`OFF` → `ON` opzionale)**: utile attivarlo se vuoi registrare automaticamente ogni volo per rivedere eventuali crash o problemi OSD senza doverti ricordare di premere Rec.
