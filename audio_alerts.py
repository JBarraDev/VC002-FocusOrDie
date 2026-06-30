"""
Alertas de audio ligeras para FocusOrDie (winsound en Windows, nativo en macOS).
"""

from __future__ import annotations

import subprocess
import sys
import threading


def _run_async(func) -> None:
    threading.Thread(target=func, daemon=True).start()


def play_success() -> None:
    """Pitido corto de victoria al completar un ciclo de trabajo."""
    if sys.platform == "win32":
        _run_async(_success_windows)
    elif sys.platform == "darwin":
        _run_async(_success_macos)
    else:
        _run_async(_success_fallback)


def play_defeat() -> None:
    """Sonido grave de fallo catastrófico al morir la mascota."""
    if sys.platform == "win32":
        _run_async(_defeat_windows)
    elif sys.platform == "darwin":
        _run_async(_defeat_macos)
    else:
        _run_async(_defeat_fallback)


def play_vip_unlock() -> None:
    """Fanfarria al desbloquear el accesorio VIP (4 Pomodoros seguidos)."""
    if sys.platform == "win32":
        _run_async(_vip_windows)
    elif sys.platform == "darwin":
        _run_async(_success_macos)
    else:
        _run_async(_success_fallback)


def play_warning() -> None:
    """Pitido sutil de aviso (pausa o procrastinación)."""
    if sys.platform == "win32":
        _run_async(_warning_windows)
    elif sys.platform == "darwin":
        _run_async(_warning_macos)
    else:
        _run_async(_warning_fallback)


# --- Windows (winsound) ---

def _success_windows() -> None:
    import winsound

    for freq, duration in ((880, 120), (1100, 120), (1320, 200)):
        winsound.Beep(freq, duration)


def _defeat_windows() -> None:
    import winsound

    for freq, duration in ((220, 350), (165, 500), (110, 700)):
        winsound.Beep(freq, duration)


def _warning_windows() -> None:
    import winsound

    winsound.Beep(620, 90)


def _vip_windows() -> None:
    import winsound

    for freq, duration in ((523, 100), (659, 100), (784, 100), (1047, 250)):
        winsound.Beep(freq, duration)


# --- macOS ---

def _success_macos() -> None:
    subprocess.run(
        ["afplay", "/System/Library/Sounds/Glass.aiff"],
        check=False,
        capture_output=True,
    )


def _defeat_macos() -> None:
    subprocess.run(
        ["afplay", "/System/Library/Sounds/Basso.aiff"],
        check=False,
        capture_output=True,
    )


def _warning_macos() -> None:
    subprocess.run(
        ["afplay", "/System/Library/Sounds/Tink.aiff"],
        check=False,
        capture_output=True,
    )


# --- Fallback (otros SO) ---

def _success_fallback() -> None:
    print("\a", end="", flush=True)


def _defeat_fallback() -> None:
    print("\a\a\a", end="", flush=True)


def _warning_fallback() -> None:
    print("\a", end="", flush=True)
