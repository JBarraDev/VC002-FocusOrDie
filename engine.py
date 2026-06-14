"""
Motor lógico de FocusOrDie: temporizador Pomodoro, vida de la mascota
y detección de procrastinación por ventana activa.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional

try:
    import pygetwindow as gw
except ImportError:
    gw = None  # type: ignore


# --- Constantes por defecto (25 min trabajo / 5 min descanso) ---

WORK_DURATION_SEC = 25 * 60
BREAK_DURATION_SEC = 5 * 60
FINALIZANDO_THRESHOLD_SEC = 3 * 60
WINDOW_CHECK_INTERVAL_SEC = 3
TIMER_TICK_SEC = 1

LIFE_MAX = 100.0
PROCRASTINATION_DRAIN_PER_SEC = 2.0
PAUSE_LIFE_PENALTY = 25.0

FORBIDDEN_KEYWORDS = (
    "twitter",
    "youtube",
    "facebook",
    "instagram",
    "netflix",
)


class Phase(str, Enum):
    WORK = "work"
    BREAK = "break"


class PetState(str, Enum):
    TRABAJANDO = "Trabajando"
    FINALIZANDO = "Finalizando"
    DESCANSO = "Descanso"
    PAUSADO = "Pausado"
    PROCRASTINANDO = "Procrastinando"
    MUERTO = "Muerto"
    EXITO = "Éxito"


@dataclass(frozen=True)
class EngineStatus:
    """Instantánea del estado actual del motor."""

    pet_state: str
    life_percent: float
    remaining_seconds: int
    phase: str
    streak: int
    is_procrastinating: bool
    active_window_title: str


def _get_active_window_title() -> str:
    """Obtiene el título de la ventana enfocada con manejo de errores."""
    if gw is None:
        return ""
    try:
        window = gw.getActiveWindow()
        if window is None:
            return ""
        title = window.title
        return title if title else ""
    except Exception:
        return ""


def _title_is_forbidden(title: str) -> bool:
    if not title:
        return False
    lower = title.lower()
    normalized = f" {lower} "
    if any(keyword in normalized for keyword in FORBIDDEN_KEYWORDS):
        return True
    # "X" (Twitter): x.com, títulos tipo "Home / X", o ventana cuyo título es solo "X"
    if "x.com" in lower:
        return True
    if lower.strip() == "x":
        return True
    if any(marker in lower for marker in (" / x", "| x", "x |", "x -")):
        return True
    return False


class FocusOrDieEngine:
    """
    Motor central: temporizador cíclico, vida de la mascota, estados y rachas.
    """

    def __init__(
        self,
        work_duration_sec: int = WORK_DURATION_SEC,
        break_duration_sec: int = BREAK_DURATION_SEC,
    ) -> None:
        self._work_duration = work_duration_sec
        self._break_duration = break_duration_sec

        self._lock = threading.Lock()
        self._phase = Phase.WORK
        self._remaining = work_duration_sec
        self._life = LIFE_MAX
        self._streak = 0
        self._manual_pause = False
        self._forbidden_window_active = False
        self._just_completed_work = False
        self._dead = False
        self._active_window_title = ""

        self._running = False
        self._timer_thread: Optional[threading.Thread] = None
        self._window_thread: Optional[threading.Thread] = None

    # --- API pública ---

    def start(self) -> None:
        """Arranca los hilos de temporizador y monitor de ventanas."""
        if self._running:
            return
        self._running = True
        self._timer_thread = threading.Thread(
            target=self._timer_loop, name="FocusOrDie-Timer", daemon=True
        )
        self._window_thread = threading.Thread(
            target=self._window_loop, name="FocusOrDie-WindowMonitor", daemon=True
        )
        self._timer_thread.start()
        self._window_thread.start()

    def stop(self) -> None:
        """Detiene los hilos en segundo plano."""
        self._running = False
        for thread in (self._timer_thread, self._window_thread):
            if thread is not None and thread.is_alive():
                thread.join(timeout=2.0)

    def pause(self) -> None:
        """Pausa manual: -25% vida y reinicia la racha."""
        with self._lock:
            if self._dead:
                return
            if self._manual_pause:
                return
            self._manual_pause = True
            self._life = max(0.0, self._life - PAUSE_LIFE_PENALTY)
            self._streak = 0
            if self._life <= 0.0:
                self._dead = True

    def resume(self) -> None:
        """Reanuda tras una pausa manual."""
        with self._lock:
            if self._dead:
                return
            self._manual_pause = False

    def reset(self) -> None:
        """Reinicia ciclo, vida y racha (útil tras muerte o pruebas)."""
        with self._lock:
            self._phase = Phase.WORK
            self._remaining = self._work_duration
            self._life = LIFE_MAX
            self._streak = 0
            self._manual_pause = False
            self._forbidden_window_active = False
            self._just_completed_work = False
            self._dead = False

    def get_status(self) -> EngineStatus:
        """Retorna el estado exacto actual y el porcentaje de vida."""
        with self._lock:
            return EngineStatus(
                pet_state=self._compute_pet_state(),
                life_percent=round(self._life, 1),
                remaining_seconds=self._remaining,
                phase=self._phase.value,
                streak=self._streak,
                is_procrastinating=self._forbidden_window_active,
                active_window_title=self._active_window_title,
            )

    # --- Bucles en segundo plano ---

    def _timer_loop(self) -> None:
        while self._running:
            time.sleep(TIMER_TICK_SEC)
            with self._lock:
                if self._dead:
                    continue

                if self._manual_pause:
                    continue

                if (
                    self._phase == Phase.WORK
                    and self._forbidden_window_active
                ):
                    self._life = max(
                        0.0, self._life - PROCRASTINATION_DRAIN_PER_SEC
                    )
                    if self._life <= 0.0:
                        self._dead = True
                        self._streak = 0

                if self._just_completed_work:
                    self._just_completed_work = False
                    continue

                if self._remaining <= 0:
                    self._advance_phase()
                    continue

                if self._dead:
                    continue

                self._remaining -= 1
                if self._remaining <= 0:
                    self._advance_phase()

    def _window_loop(self) -> None:
        while self._running:
            title = _get_active_window_title()
            forbidden = _title_is_forbidden(title)

            with self._lock:
                self._active_window_title = title
                if self._dead:
                    self._forbidden_window_active = False
                elif (
                    self._phase == Phase.WORK
                    and not self._manual_pause
                ):
                    self._forbidden_window_active = forbidden
                else:
                    self._forbidden_window_active = False

            time.sleep(WINDOW_CHECK_INTERVAL_SEC)

    # --- Lógica interna ---

    def _advance_phase(self) -> None:
        if self._phase == Phase.WORK:
            self._streak += 1
            self._phase = Phase.BREAK
            self._remaining = self._break_duration
            self._just_completed_work = True
            self._forbidden_window_active = False
        else:
            self._phase = Phase.WORK
            self._remaining = self._work_duration
            self._just_completed_work = False

    def _compute_pet_state(self) -> str:
        if self._dead or self._life <= 0.0:
            return PetState.MUERTO.value

        if self._manual_pause:
            return PetState.PAUSADO.value

        if self._just_completed_work:
            return PetState.EXITO.value

        if self._phase == Phase.BREAK:
            return PetState.DESCANSO.value

        if self._forbidden_window_active:
            return PetState.PROCRASTINANDO.value

        if self._remaining <= FINALIZANDO_THRESHOLD_SEC:
            return PetState.FINALIZANDO.value

        return PetState.TRABAJANDO.value


if __name__ == "__main__":
    # Demo acelerada: 15 s trabajo / 8 s descanso para verificar en consola.
    DEMO_WORK = 15
    DEMO_BREAK = 8

    engine = FocusOrDieEngine(
        work_duration_sec=DEMO_WORK,
        break_duration_sec=DEMO_BREAK,
    )
    engine.start()

    print("=== FocusOrDie — prueba de motor ===")
    print(f"Ciclo demo: {DEMO_WORK}s trabajo / {DEMO_BREAK}s descanso")
    print("Comandos: [p] pausar | [r] reanudar | [q] salir")
    print("Abre Twitter/YouTube/etc. durante el trabajo para probar procrastinación.\n")

    last_state = ""
    try:
        while True:
            status = engine.get_status()

            line = (
                f"[{status.pet_state:14}] "
                f"Vida: {status.life_percent:5.1f}% | "
                f"Tiempo: {status.remaining_seconds:3d}s | "
                f"Fase: {status.phase:5} | "
                f"Racha: {status.streak} | "
                f"Ventana: {status.active_window_title[:40]!r}"
            )
            print(line, end="\r", flush=True)

            if status.pet_state != last_state:
                print(f"\n>>> Cambio de estado: {last_state!r} -> {status.pet_state!r}")
                last_state = status.pet_state

            if status.pet_state == PetState.MUERTO.value:
                print("\n\nLa mascota murió. Reiniciando en 3 s...")
                time.sleep(3)
                engine.reset()
                last_state = ""
                print("Motor reiniciado.\n")

            import msvcrt

            if msvcrt.kbhit():
                key = msvcrt.getch().decode("utf-8", errors="ignore").lower()
                if key == "p":
                    engine.pause()
                    print("\n>>> Pausa manual (-25% vida, racha reiniciada)")
                elif key == "r":
                    engine.resume()
                    print("\n>>> Reanudado")
                elif key == "q":
                    break

            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        engine.stop()
        print("\n\nMotor detenido.")
