# Brain-Move

Piattaforma web di stimolazione cognitiva e motoria con 17 giochi interattivi. Porting moderno (Vite + TypeScript + Canvas) dell'originale Python/Pygame.

## Giochi

| # | Gioco | Area Cognitiva |
|---|-------|---------------|
| 1 | Diario Missioni | Autobiografica |
| 2 | Parole Incrociate | Linguaggio |
| 3 | Quiz | Conoscenza generale |
| 4 | Valutazione | Consapevolezza |
| 5 | Passi e Ricorda | Memoria episodica |
| 6 | Brain Trainer | Calcolo |
| 7 | Costruisci Modello | Prassica |
| 8 | Mappa della Stanza | Visuospaziale |
| 9 | Musical Memory | Attenzione uditiva |
| 10 | Memory Carte | Memoria visiva |
| 11 | Memory Immagini | Memoria visiva |
| 12 | Puzzle | Visuospaziale |
| 13 | Sequenza Simboli | Attenzione sostenuta |
| 14 | Basket | Coordinazione motoria |
| 15 | Palloncini | Coordinazione motoria |
| 16 | Semaforo Esecutivo | Inibizione risposta |
| 17 | Respiro Faro | Rilassamento |

## Tech Stack

- **[Vite](https://vitejs.dev/)** + **TypeScript**
- **Canvas API** per rendering giochi
- **CSS** puro con tema glassmorphism, animazioni e particelle
- Nessun framework frontend

## Sviluppo locale

```bash
cd brain-move-web
npm install
npm run dev        # avvia server di sviluppo su http://localhost:3000
npm run build      # build di produzione in dist/
npm run preview    # preview della build
```

## Deploy

Il progetto include GitHub Actions (`.github/workflows/deploy.yml`) per deploy automatico su GitHub Pages a ogni push su `main`.

**Abilitazione:**
1. Vai a Settings → Pages del repository
2. Source: **GitHub Actions**
3. Il prossimo push su `main` avvierà il deploy

Il sito sarà pubblicato su `https://<user>.github.io/braingame/`.

## Struttura

```
brain-move-web/
├── src/
│   ├── games/          # Logica dei 17 giochi
│   ├── ui/             # UI orchestrator, canvas drawing, DOM rendering
│   ├── engine/         # Session, Scoring, Difficulty, Safety
│   ├── vision/         # Pose detection synthetica
│   └── style.css       # Tema glassmorphism + effetti visivi
├── dist/               # Build di produzione
├── serve.py            # Server statico Python alternativo
├── vite.config.ts
└── package.json
```
