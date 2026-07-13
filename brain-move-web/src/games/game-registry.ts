import { RespiroFaro } from './respiro-faro'
import { PassiRicorda } from './passi-ricorda'
import { SemaforoEsecutivo } from './semaforo-esecutivo'
import { MappaStanza } from './mappa-stanza'
import { CostruisciModello } from './costruisci-modello'
import { DiarioMissioni } from './diario-missioni'
import { MemoryCarte } from './memory-carte'
import { SequenzaSimboli } from './sequenza-simboli'
import { ParoleIncrociate } from './parole-incrociate'
import { Basket } from './basket'
import { Puzzle } from './puzzle'
import { MemoryImmagini } from './memory-immagini'
import { BrainTrainer } from './brain-trainer'
import { MusicalMemory } from './musical-memory'
import { Palloncini } from './palloncini'
import { Quiz } from './quiz'
import { Valutazione } from './valutazione'
import { CercaParole } from './cerca-parole'
import { Difficulty } from '../engine/difficulty'
import { Scoring } from '../engine/scoring'
import type { BaseGame } from './base-game'

export interface GameEntry {
  name: string
  displayName: string
  description: string
  icon: string
  create: () => BaseGame
}

export function createAllGames(difficulty: Difficulty, scoring: Scoring): BaseGame[] {
  return [
    new RespiroFaro(difficulty, scoring),
    new PassiRicorda(difficulty, scoring),
    new SemaforoEsecutivo(difficulty, scoring),
    new MappaStanza(difficulty, scoring),
    new CostruisciModello(difficulty, scoring),
    new DiarioMissioni(difficulty, scoring),
    new MemoryCarte(difficulty, scoring),
    new SequenzaSimboli(difficulty, scoring),
    new ParoleIncrociate(difficulty, scoring),
    new Basket(difficulty, scoring),
    new Puzzle(difficulty, scoring),
    new MemoryImmagini(difficulty, scoring),
    new BrainTrainer(difficulty, scoring),
    new MusicalMemory(difficulty, scoring),
    new Palloncini(difficulty, scoring),
    new Quiz(difficulty, scoring),
    new CercaParole(difficulty, scoring),
    new Valutazione(difficulty, scoring),
  ]
}

export const GAME_MENU_DATA: Array<{ name: string; displayName: string; description: string; icon: string; cognitive: string }> = [
  { name: "respiro_faro", displayName: "Respiro del Faro", description: "Respirazione guidata", icon: "\u{1F4A1}", cognitive: "Respirazione" },
  { name: "passi_ricorda", displayName: "Passi e Ricorda", description: "Memoria + movimento", icon: "\u{1F9CD}", cognitive: "Memoria episodica" },
  { name: "semaforo_esecutivo", displayName: "Semaforo Esecutivo", description: "Inibizione risposta", icon: "\u{1F6A6}", cognitive: "Funzioni esecutive" },
  { name: "mappa_stanza", displayName: "Mappa della Stanza", description: "Memoria visuospaziale", icon: "\u{1F3E0}", cognitive: "Abilità visuospaziali" },
  { name: "costruisci_modello", displayName: "Costruisci il Modello", description: "Memoria di lavoro", icon: "\u{1F9E9}", cognitive: "Memoria di lavoro" },
  { name: "diario_missioni", displayName: "Diario delle Missioni", description: "Questionario caregiver", icon: "\u{1F4DD}", cognitive: "Autobiografica" },
  { name: "memory_carte", displayName: "Memory Carte", description: "Coppie di carte", icon: "\u{1F0CF}", cognitive: "Memoria visiva" },
  { name: "sequenza_simboli", displayName: "Sequenza Simboli", description: "Sequenza di simboli", icon: "\u{1F522}", cognitive: "Memoria sequenziale" },
  { name: "parole_incrociate", displayName: "Parole Incrociate", description: "Cruciverba", icon: "\u{1F30D}", cognitive: "Linguaggio" },
  { name: "basket", displayName: "Basket", description: "Coordinazione motoria", icon: "\u{1F3C0}", cognitive: "Coordinazione" },
  { name: "puzzle", displayName: "Puzzle", description: "Riordino griglia", icon: "\u{1F9E9}", cognitive: "Organizzazione" },
  { name: "memory_immagini", displayName: "Memory Immagini", description: "Coppie di immagini", icon: "\u{1F5BC}", cognitive: "Memoria visiva" },
  { name: "brain_trainer", displayName: "Brain Trainer", description: "Calcolo e attenzione", icon: "\u{1F9E0}", cognitive: "Calcolo" },
  { name: "musical_memory", displayName: "Musical Memory", description: "Memoria musicale", icon: "\u{1F3B5}", cognitive: "Memoria uditiva" },
  { name: "palloncini", displayName: "Palloncini", description: "Scoppia i palloncini", icon: "\u{1F388}", cognitive: "Attenzione" },
  { name: "quiz", displayName: "Quiz", description: "Domande culturali", icon: "\u{2753}", cognitive: "Cultura generale" },
  { name: "cerca_parole", displayName: "Cerca Parole", description: "Trova le parole nella griglia", icon: "\u{1F50D}", cognitive: "Attenzione visiva" },
  { name: "valutazione", displayName: "Test Valutativo", description: "Valutazione cognitiva", icon: "\u{1F9D1}\u200D\u{1F3EB}", cognitive: "Assessment" },
]
