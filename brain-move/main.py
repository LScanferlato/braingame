#!/usr/bin/env python3
"""
Brain-Move - Piattaforma di stimolazione cognitiva e motoria.
Basata sul protocollo Brain-IT per disturbi neurocognitivi.
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.profile import Profile
from engine.scoring import Scoring
from engine.difficulty import Difficulty
from engine.safety import SafetyEngine
from engine.session import Session

from vision.pose_detector import PoseDetector
from vision.movement_rules import MovementRules
from vision.fatigue_detector import FatigueDetector
from vision.fall_risk import FallRiskDetector
from vision.facial_expression import FacialExpressionDetector

from games.respiro_faro import RespiroFaro
from games.passi_ricorda import PassiRicorda
from games.semaforo_esecutivo import SemaforoEsecutivo
from games.mappa_stanza import MappaStanza
from games.costruisci_modello import CostruisciModello
from games.diario_missioni import DiarioMissioni
from games.memory_carte import MemoryCarte
from games.sequenza_simboli import SequenzaSimboli
from games.parole_incrociate import ParoleIncrociate
from games.basket import Basket
from games.puzzle import Puzzle
from games.memory_immagini import MemoryImmagini
from games.brain_trainer import BrainTrainer
from games.musical_memory import MusicalMemory


def main():
    parser = argparse.ArgumentParser(description="Brain-Move - Stimolazione Cognitiva e Motoria")
    parser.add_argument("--no-webcam", action="store_true", help="Avvia senza webcam")
    parser.add_argument("--game", type=str, help="Avvia un singolo gioco")
    parser.add_argument("--profile", type=str, default=None, help="Percorso profilo utente")
    args = parser.parse_args()

    profile = Profile(args.profile)
    scoring = Scoring()
    difficulty = Difficulty(initial_level=1, min_level=1, max_level=5)
    safety = SafetyEngine()
    session = Session(profile, scoring, difficulty, safety)

    pose_detector = None
    if not args.no_webcam:
        pose_detector = PoseDetector()
        if not pose_detector.open_camera(0):
            print("[INFO] Webcam non trovata, uso modalita sintetica")
            pose_detector = None

    fatigue_detector = FatigueDetector()
    fall_risk_detector = FallRiskDetector()
    movement_rules = MovementRules()
    facial_expression = FacialExpressionDetector()

    game_classes = [
        RespiroFaro, PassiRicorda, SemaforoEsecutivo,
        MappaStanza, CostruisciModello, DiarioMissioni,
        MemoryCarte, SequenzaSimboli, ParoleIncrociate,
        Basket, Puzzle, MemoryImmagini, BrainTrainer, MusicalMemory,
    ]

    games = [cls(difficulty, scoring) for cls in game_classes]

    if args.game:
        game_map = {g.name: g for g in games}
        if args.game in game_map:
            games = [game_map[args.game]]
        else:
            print(f"Gioco '{args.game}' non trovato. Disponibili:")
            for g in games:
                print(f"  - {g.name}")
            sys.exit(1)

    print("=" * 50)
    print("  Brain-Move - Stimolazione Cognitiva e Motoria")
    print("  Basata sul protocollo Brain-IT")
    print("=" * 50)
    print()
    print("  Giochi disponibili:")
    game_labels = [
        "Respiro del Faro", "Passi e Ricorda", "Semaforo Esecutivo",
        "Mappa della Stanza", "Costruisci il Modello", "Diario delle Missioni",
        "Memory Carte", "Sequenza Simboli", "Parole Incrociate",
        "Basket", "Puzzle", "Memory Immagini", "Brain Trainer", "Musical Memory",
    ]
    for i, label in enumerate(game_labels, 1):
        print(f"    {i}. {label}")
    print()
    print(f"  Webcam: {'attiva' if pose_detector else 'sintetica'}")
    print(f"  Avvio interfaccia grafica...")
    print()

    from ui.main_window import MainWindow
    window = MainWindow(session, games, pose_detector,
                        fatigue_detector=fatigue_detector,
                        fall_risk_detector=fall_risk_detector,
                        movement_rules=movement_rules,
                        facial_expression=facial_expression)
    window.run()

    print()
    print("  Sessione terminata. Arrivederci!")


if __name__ == "__main__":
    main()
