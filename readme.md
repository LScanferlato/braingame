# Brain-Move

Piattaforma di stimolazione cognitiva e motoria per persone con disturbi neurocognitivi (MCI / Alzheimer lieve-moderato).

Basata sul protocollo **Brain-IT** ([paper](https://alz-journals.onlinelibrary.wiley.com/doi/epdf/10.1002/alz.13913)): exergame motorio-cognitivi + respirazione guidata con biofeedback HRV.

> **Disclaimer:** Questi giochi non curano l'Alzheimer e non sostituiscono terapia, medico o neuropsicologo. Vanno intesi come prototipi di stimolazione cognitiva e motoria sicura, da adattare al livello della persona.

## Abstract

Brain-Move implementa un sistema di exergame cognitivo-motorio pensato per la stimolazione di pazienti con Mild Cognitive Impairment (MCI) e Alzheimer lieve-moderato. Il sistema integra (i) rilevamento posturale in tempo reale via MediaPipe Pose, (ii) un motore adattivo di difficoltà, (iii) un sistema di sicurezza con rilevamento di cadute e affaticamento, e (iv) 14 giochi che sollecitano distinti domini cognitivi (memoria, funzioni esecutive, abilità visuospaziali, attenzione, linguaggio, memoria di lavoro, coordinazione motoria, memoria procedurale, respirazione e memoria autobiografica). L'architettura è modulare, basata su classi BaseGame — ogni gioco specializza `update()`, `get_progress()` e la logica di interazione. La UI utilizza Pygame con supporto multi-risoluzione (1920×1080), feedback vocale (TTS) e visivo adattivo, ottimizzato per utenti anziani (80+ anni). La sessione standard prevede 6 giochi per circa 24 minuti, con escalation progressiva della difficoltà.

## Indice

1. [Architettura del sistema](#architettura-del-sistema)
2. [Metodi](#metodi)
3. [Interfacce e protocolli](#interfacce-e-protocolli)
4. [Giochi](#giochi)
5. [Installazione](#installazione)
6. [Utilizzo](#utilizzo)
7. [Licenza](#licenza)

## Architettura del sistema

```
brain-move/
├── main.py                  # Entry point — dependency injection container
├── avvia.sh                 # Wrapper per avvio automatico con check dipendenze
├── requirements.txt         # Dipendenze Python
├── games/                   # Dominio giochi (n=14)
│   ├── __init__.py
│   ├── base_game.py         # Classe astratta BaseGame
│   ├── passi_ricorda.py     # Memoria episodica + camminata
│   ├── semaforo_esecutivo.py # Inibizione risposta (EF)
│   ├── mappa_stanza.py      # Memoria visuospaziale
│   ├── costruisci_modello.py # Memoria di lavoro
│   ├── respiro_faro.py      # Respirazione guidata
│   ├── diario_missioni.py   # Memoria autobiografica + caregiver
│   ├── memory_carte.py      # Memoria visiva (coppie)
│   ├── sequenza_simboli.py  # Memoria sequenziale
│   ├── parole_incrociate.py # Linguaggio e lessico
│   ├── basket.py            # Coordinazione motoria + lateralità
│   ├── puzzle.py            # Organizzazione visuospaziale
│   ├── memory_immagini.py   # Memoria visiva (volti/oggetti)
│   ├── brain_trainer.py     # Calcolo, attenzione, conteggio
│   └── musical_memory.py    # Memoria uditiva + sequenze
├── engine/                  # Core logico del sistema
│   ├── __init__.py
│   ├── session.py           # Gestione sessione e persistenza
│   ├── scoring.py           # Sistema di punteggio
│   ├── difficulty.py        # Algoritmo adattivo (accuracy + fatica)
│   ├── safety.py            # Sicurezza posturale
│   └── profile.py           # Profilazione utente
├── vision/                  # Computer vision pipeline
│   ├── __init__.py
│   ├── pose_detector.py     # MediaPipe Pose Landmarker (33 keypoints)
│   ├── movement_rules.py    # Euristiche movimento (step, ginocchia, braccia)
│   ├── fatigue_detector.py  # Rilevamento fatica (instabilità, trunk angle)
│   ├── fall_risk.py         # Rischio caduta (drop, rotazione, stabilità)
│   └── facial_expression.py # Face Mesh — classificazione umore (n=5 classi)
├── ui/                      # Interfaccia utente (Pygame)
│   ├── __init__.py
│   ├── main_window.py       # Finestra principale, layout, event-loop
│   ├── widgets.py           # Button, ProgressBar, WebcamView, FeedbackBar
│   └── mood_indicator.py    # Indicatore umore (da facial_expression)
└── data/
    ├── user_profiles.json   # Profili persistiti
    └── pose_landmarker.task # MediaPipe model (da scaricare)
```

## Metodi

### Motore adattivo di difficoltà (`engine/difficulty.py`)

L'algoritmo adatta il livello di gioco (range 1–5) in funzione di due variabili: **accuratezza** (media delle risposte corrette normalizzata a [0,1]) e **livello di fatica** rilevato dalla CV pipeline. Le transizioni seguono una logica a soglie:

| Condizione | Azione |
|---|---|
| accuracy > 0.8 AND fatica == "bassa" | increase() → livello +1 |
| accuracy < 0.5 OR fatica == "alta" | decrease() → livello -1 |
| altrimenti | keep() |

### Sicurezza posturale (`engine/safety.py`)

Il SafetyEngine valuta ogni frame di pose con tre parametri critici:

- `trunk_angle` (angolo del busto): soglia warning a 25°, rischio a >30°
- `instability` (indice di oscillazione normalizzato): soglia a 0.7
- `in_frame` (presenza nel campo visivo)

Stati restituiti: `"ok"`, `"warning"`, `"pause"`, `"no_pose"`.

### CV pipeline (`vision/`)

1. **PoseDetector** — MediaPipe Pose Landmarker (33 keypoints): estrae coordinate (x,y) di spalle, anche, ginocchia, caviglie, polsi, gomiti, naso. Calcola `trunk_angle`, `instability` (derivata seconda della posizione dell'anca), `knee_hip_ratio`.
2. **MovementRules** — Euristiche per step detection (`detect_step_direction`), knee raise (`detect_knee_raise`), alternanza gambe (`detect_alternating_legs`), alzata braccia (`detect_arm_raise`).
3. **FatigueDetector** — Finestra mobile di 30 frame su velocità di movimento (derivata prima anca) e instabilità. Tre livelli: "bassa", "media", "alta".
4. **FallRiskDetector** — Eventi: uscita improvvisa dal frame (>50px drop anca), rotazione brusca (>40% variazione shoulder width), busto inclinato (>30°), instabilità elevata (>0.8).
5. **FacialExpressionDetector** — MediaPipe Face Mesh (468 landmarks). Calcola indici di smile (rapporto altezza/larghezza bocca + curvatura angoli), sopracciglia (distanza occhio-sopracciglio), apertura occhi. Classifica 5 mood: felice, neutro, concentrato, stanco, preoccupato.

### Persistenza sessioni

`Session._save()` salva in formato JSON (`data/session_YYYY-MM-DD-HHMMSS.json`):
```json
{
  "session_id": "2026-07-13-105604",
  "duration_seconds": 1440.0,
  "total_score": 85,
  "final_difficulty": 3,
  "safety_events": [],
  "games": [{"game": "passi_ricorda", "difficulty": 2, "result": {...}}]
}
```

### Profilazione utente

`Profile` carica/salva `data/user_profiles.json` con campi: ID utente, livello mobilità (basso/medio/alto), modalità preferita (in piedi con supporto, seduto), flag webcam e sicurezza.

## Interfacce e protocolli

### BaseGame (classe astratta)

| Metodo | Descrizione |
|---|---|
| `start()` | Inizializza stato, imposta `running=True`, registra `start_time` |
| `stop()` | Conclude gioco, setta `state="finished"`, calcola `duration_seconds` |
| `update(pose_data, dt)` | **Abstract** — logica di gioco per frame |
| `get_state()` | Dizionario serializzabile dello stato corrente |
| `is_finished()` | Predicato di terminazione |
| `get_progress()` | Float in [0,1] per barra di avanzamento |

### System interface (main.py)

`main()` funge da container DI, istanziando:
- **Engine layer**: Profile, Scoring, Difficulty, SafetyEngine, Session
- **Vision layer**: PoseDetector (opzionale), FatigueDetector, FallRiskDetector, MovementRules, FacialExpressionDetector
- **Game layer**: 14 istanze di BaseGame iniettate con difficulty + scoring
- **UI layer**: MainWindow riceve tutte le dipendenze

Flag CLI: `--no-webcam` (modalità sintetica), `--game <nome>` (singolo gioco), `--profile <path>`.

### MainWindow (UI)

- Layout ottimizzato 1900×1000 con sidebar (webcam + mood) e pannello principale
- Event-loop Pygame a 60 FPS con gestione: mouse, tastiera, touch (finger events)
- 3 stati: `menu`, `playing`, `finished` + 1 stato accessorio: `report`
- Supporto multi-gioco in sessione (sequenziale) e gioco singolo

## Giochi

### Griglia cognitiva

| # | Gioco | Dominio cognitivo | Interazione | Durata |
|---|---|---|---|---|
| 1 | Respiro del Faro | Respirazione guidata, biofeedback | Visivo (cerchio che si espande) | 2 min |
| 2 | Passi e Ricorda | Memoria episodica + motoria | Camminata + richiamo sequenza | 5 min |
| 3 | Semaforo Esecutivo | Funzioni esecutive (inibizione) | Step direction (verde/rosso/blu/giallo) | 5 min |
| 4 | Mappa della Stanza | Memoria visuospaziale | Posizionamento oggetti su griglia | 5 min |
| 5 | Costruisci il Modello | Memoria di lavoro | Ricostruzione sequenza di forme | 4 min |
| 6 | Diario delle Missioni | Memoria autobiografica + caregiver | Questionario + note assistente | 2 min |
| 7 | Memory Carte | Memoria visiva (associativa) | Coppie di carte (emoji animali) | 3 min |
| 8 | Sequenza Simboli | Memoria sequenziale | Ripetizione sequenza di simboli | 3 min |
| 9 | Parole Incrociate | Linguaggio e lessico | Cruciverba semplice con indizi | 4 min |
| 10 | Basket | Coordinazione motoria, lateralità | Lancio palla con braccio dx/sx | 2 min |
| 11 | Puzzle | Organizzazione visuospaziale | Riordino griglia di emoji | 4 min |
| 12 | Memory Immagini | Memoria visiva (volti/oggetti) | Coppie di icone quotidiane | 3 min |
| 13 | Brain Trainer | Calcolo, attenzione, conteggio | Domande matematiche/simboli/ricordo | 5 min |
| 14 | Musical Memory | Memoria uditiva procedurale | Sequenza musicale (Do, Mi, Sol, Do') | 3 min |

### Specifica dei giochi

**Respiro del Faro** — Fase di inspirazione (cerchio si espande) ed espirazione (si contrae) sincronizzate su intervallo regolato dal livello di difficoltà. `get_circle_scale()` modula raggio tra 0 e 1.

**Passi e Ricorda** — Tre fasi: `showing` (mostra item), `moving` (camminata sul posto rilevata da `detect_knee_raise`), `recall` (selezione multipla). La sequenza richiesta scala in lunghezza col livello.

**Semaforo Esecutivo** — Test di Stroop motorio: riconoscere il colore visualizzato ignorando la label incongruente. L'azione motoria (passo avanti/fermo/sinistra/destra) dipende dal colore. `inhibition_errors` traccia fallimenti nel controllo inibitorio.

**Mappa della Stanza** — Griglia `n×n`. Fase di studio (oggetti posizionati) seguita da richiamo (riposizionamento). `grid_size = 2 + level`.

**Costruisci il Modello** — Presentazione di un modello (sequenza di forme con colore e label) da ricostruire selezionando pezzi. `SHAPES` dictionary con 8 forme: cerchio, quadrato, triangolo, stella, cuore, diamante, croce, luna.

**Diario delle Missioni** — Due fasi: questionario auto-valutativo (3 item su scala Molto/Abbastanza/Poco) e note caregiver (checklist selezionabile di osservazioni comportamentali).

**Memory Carte** — Griglia `(2 + level) × 4` carte. Coppie di emoji animali/simboli. Meccanica standard di rivelazione a due carte.

**Sequenza Simboli** — Sequenza crescente di simboli da memorizzare e ripetere. `max_rounds = 8`. Feedback visivo immediato (corretto/flash verde, sbagliato/flash rosso).

**Parole Incrociate** — Griglia di dimensione variabile con parole incrociate. Input da tastiera (letters) o click su cella. Supporto indizi laterali e tracciamento risoluzione.

**Basket** — Fisica parabolica semplificata del pallone. Rilevamento lancio da accelerazione polso (wrist history). Obiettivo: 4 canestri alternando mano destra e sinistra.

**Puzzle** — Griglia riordinabile. Scambio di celle (`select_piece`). Obiettivo: replicare la griglia target. `hint_count` limitato (3 - level).

**Memory Immagini** — Fase di studio (griglia di icone familiari: nonno, nonna, casa, cane...) seguita da fase memory a coppie.

**Brain Trainer** — Tre mini-giochi alternati: `math` (operazioni aritmetiche), `recall` (memoria immediata di item evidenziati), `count` (conteggio simboli). 10 round totali.

**Musical Memory** — Quattro note (Do 262Hz, Mi 330Hz, Sol 392Hz, Do' 523Hz) generate via sintesi sinusoidale. Sequenza Simon-says crescente. 10 round massimi.

## Installazione

```bash
cd brain-move
pip install -r requirements.txt
```

Dipendenze: `pygame>=2.5.0`, `opencv-python>=4.8.0`, `mediapipe>=0.10.0`, `numpy>=1.24.0`, `pyttsx3>=2.90`.

### Model file

MediaPipe Pose Landmarker model (`pose_landmarker.task`) va scaricato in `brain-move/data/`. Se assente, il sistema opera in modalità sintetica.

## Utilizzo

```bash
# Sessione completa con webcam
python main.py

# Senza webcam (dati sintetici, input da tastiera)
python main.py --no-webcam

# Singolo gioco
python main.py --game passi_ricorda

# Profilo personalizzato
python main.py --profile /path/to/profile.json
```

### Avvio rapido

```bash
./avvia.sh
```

Lo script verifica la presenza di Python3, installa le dipendenze se mancanti e avvia.

### Controlli

| Tasto | Azione |
|---|---|
| ESC | Termina gioco corrente / Esci |
| Click / Touch | Selezione opzioni, carte, celle |
| Tastiera (Parole Incrociate) | Lettere A-Z, Backspace, Invio, Frecce |

## Licenza

Progetto didattico/research. Non per uso clinico senza validazione.
