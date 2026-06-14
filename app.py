"""
Interfaz gráfica de FocusOrDie — widget flotante conectado al motor lógico.
"""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from audio_alerts import play_defeat, play_success, play_vip_unlock, play_warning
from engine import FocusOrDieEngine, PetState

# --- Paleta neón / oscuro ---

COLOR_BG = "#0a0a0a"
COLOR_SURFACE = "#141414"
COLOR_GREEN = "#39FF14"
COLOR_YELLOW = "#FFD700"
COLOR_RED = "#FF073A"
COLOR_PINK = "#FF10F0"
COLOR_PINK_DIM = "#661044"
COLOR_TEXT = "#E8E8E8"
COLOR_TEXT_DIM = "#888888"

REFRESH_MS = 250
WARNING_ALERT_MS = 1800
BLINK_MS = 450
STREAK_VIP_THRESHOLD = 4
VIP_ACCESSORY = "👑"

PET_EMOJI: dict[str, str] = {
    PetState.TRABAJANDO.value: "🐣",
    PetState.FINALIZANDO.value: "😰",
    PetState.DESCANSO.value: "😴",
    PetState.PAUSADO.value: "😑",
    PetState.PROCRASTINANDO.value: "😡",
    PetState.MUERTO.value: "☠️",
    PetState.EXITO.value: "🎉",
}

GREEN_STATES = {
    PetState.TRABAJANDO.value,
    PetState.FINALIZANDO.value,
    PetState.DESCANSO.value,
    PetState.EXITO.value,
}
ALERT_STATES = {PetState.PAUSADO.value, PetState.PROCRASTINANDO.value}


def format_time(seconds: int) -> str:
    minutes, secs = divmod(max(0, seconds), 60)
    return f"{minutes:02d}:{secs:02d}"


def format_pet_display(state: str, streak: int) -> str:
    base = PET_EMOJI.get(state, "🐣")
    if streak >= STREAK_VIP_THRESHOLD and state != PetState.MUERTO.value:
        return f"{VIP_ACCESSORY}\n{base}"
    return base


def life_bar_color(life_percent: float) -> str:
    if life_percent > 60:
        return COLOR_GREEN
    if life_percent > 30:
        return COLOR_YELLOW
    return COLOR_RED


class DeathDialog(ctk.CTkToplevel):
    """Alerta dramática al llegar la mascota a 0% de vida."""

    def __init__(self, master: ctk.CTk, on_reset: Callable[[], None]) -> None:
        super().__init__(master)
        self._on_reset = on_reset

        self.title("FocusOrDie — GAME OVER")
        self.configure(fg_color=COLOR_BG)
        self.attributes("-topmost", True)
        self.resizable(False, False)
        self.grab_set()

        width, height = 480, 320
        x = master.winfo_x() + (master.winfo_width() - width) // 2
        y = master.winfo_y() + (master.winfo_height() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

        lines = (
            "¡¡BASTA DE DISTRACCIONES!!",
            "Céntrate, y mantenme con vida.",
            "¿Acaso no te importo?",
        )
        for index, text in enumerate(lines):
            font = ctk.CTkFont(size=22 if index == 0 else 16, weight="bold")
            label = ctk.CTkLabel(
                self,
                text=text,
                text_color=COLOR_RED,
                font=font,
                wraplength=440,
            )
            label.pack(pady=(24 if index == 0 else 8, 8), padx=20)

        ctk.CTkButton(
            self,
            text="Reiniciar y volver a intentarlo",
            fg_color=COLOR_RED,
            hover_color="#CC0028",
            command=self._handle_reset,
            height=40,
            corner_radius=12,
        ).pack(pady=24)

    def _handle_reset(self) -> None:
        self._on_reset()
        self.destroy()


class FlowStateDialog(ctk.CTkToplevel):
    """Modal épico al completar 4 Pomodoros seguidos (Vibe Check)."""

    def __init__(self, master: ctk.CTk) -> None:
        super().__init__(master)

        self.title("FocusOrDie — ULTRA INSTINTO")
        self.configure(fg_color=COLOR_BG)
        self.attributes("-topmost", True)
        self.resizable(False, False)
        self.grab_set()

        width, height = 520, 280
        x = master.winfo_x() + (master.winfo_width() - width) // 2
        y = master.winfo_y() + (master.winfo_height() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

        ctk.CTkLabel(
            self,
            text=f"{VIP_ACCESSORY}  NIVEL: ULTRA INSTINTO  {VIP_ACCESSORY}",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLOR_YELLOW,
        ).pack(pady=(28, 12), padx=20)

        ctk.CTkLabel(
            self,
            text=(
                'Has entrado en el "Flow State".\n'
                "Ni el mismísimo Elon Musk te distrae hoy."
            ),
            font=ctk.CTkFont(size=15),
            text_color=COLOR_GREEN,
            wraplength=480,
            justify="center",
        ).pack(pady=(0, 8), padx=20)

        ctk.CTkLabel(
            self,
            text="Accesorio VIP desbloqueado para tu mascota.",
            font=ctk.CTkFont(size=13),
            text_color=COLOR_TEXT_DIM,
        ).pack(pady=(0, 16))

        ctk.CTkButton(
            self,
            text="Seguir en modo bestia 🚀",
            fg_color=COLOR_GREEN,
            hover_color="#28CC10",
            text_color=COLOR_BG,
            command=self.destroy,
            height=40,
            corner_radius=12,
        ).pack(pady=8)


class FocusOrDieApp(ctk.CTk):
    """Widget principal siempre visible sobre el escritorio."""

    def __init__(self) -> None:
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.title("FocusOrDie")
        self.configure(fg_color=COLOR_BG)
        self.attributes("-topmost", True)
        self.resizable(False, False)
        self.geometry("340x520")

        self._engine = FocusOrDieEngine()
        self._engine_started = False
        self._last_state = ""
        self._blink_on = True
        self._death_dialog: DeathDialog | None = None
        self._flow_dialog: FlowStateDialog | None = None
        self._warning_job: str | None = None
        self._last_streak = 0

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(BLINK_MS, self._tick_blink)
        self.after(REFRESH_MS, self._refresh_ui)

    # --- Construcción de la UI ---

    def _build_ui(self) -> None:
        header = ctk.CTkLabel(
            self,
            text="FOCUS OR DIE",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLOR_TEXT_DIM,
        )
        header.pack(pady=(16, 4))

        self._timer_label = ctk.CTkLabel(
            self,
            text="25:00",
            font=ctk.CTkFont(family="Consolas", size=56, weight="bold"),
            text_color=COLOR_GREEN,
        )
        self._timer_label.pack(pady=(8, 4))

        self._phase_label = ctk.CTkLabel(
            self,
            text="Trabajo",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_DIM,
        )
        self._phase_label.pack(pady=(0, 12))

        self._pet_label = ctk.CTkLabel(
            self,
            text="🐣",
            font=ctk.CTkFont(size=72),
        )
        self._pet_label.pack(pady=(0, 8))

        self._state_label = ctk.CTkLabel(
            self,
            text=PetState.TRABAJANDO.value,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLOR_GREEN,
        )
        self._state_label.pack(pady=(0, 16))

        life_frame = ctk.CTkFrame(self, fg_color="transparent")
        life_frame.pack(fill="x", padx=24, pady=(0, 8))

        ctk.CTkLabel(
            life_frame,
            text="Vida de la mascota",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_DIM,
        ).pack(anchor="w")

        self._life_bar = ctk.CTkProgressBar(
            life_frame,
            height=18,
            corner_radius=10,
            progress_color=COLOR_GREEN,
            fg_color=COLOR_SURFACE,
        )
        self._life_bar.pack(fill="x", pady=(6, 4))
        self._life_bar.set(1.0)

        self._life_percent_label = ctk.CTkLabel(
            life_frame,
            text="100%",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_DIM,
        )
        self._life_percent_label.pack(anchor="e")

        self._streak_label = ctk.CTkLabel(
            self,
            text="Racha: 0 🔥",
            font=ctk.CTkFont(size=13),
            text_color=COLOR_TEXT_DIM,
        )
        self._streak_label.pack(pady=(4, 16))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(0, 20))

        self._toggle_btn = ctk.CTkButton(
            btn_frame,
            text="Iniciar",
            command=self._toggle_start_pause,
            height=42,
            corner_radius=12,
            fg_color="#1f538d",
            hover_color="#14375e",
        )
        self._toggle_btn.pack(side="left", expand=True, fill="x", padx=(0, 6))

        self._reset_btn = ctk.CTkButton(
            btn_frame,
            text="Reiniciar",
            command=self._reset_all,
            height=42,
            corner_radius=12,
            fg_color=COLOR_SURFACE,
            hover_color="#2a2a2a",
            border_width=1,
            border_color="#333333",
        )
        self._reset_btn.pack(side="right", expand=True, fill="x", padx=(6, 0))

    # --- Acciones del usuario ---

    def _ensure_engine_running(self) -> None:
        if not self._engine_started:
            self._engine.start()
            self._engine_started = True

    def _toggle_start_pause(self) -> None:
        status = self._engine.get_status()

        if status.pet_state == PetState.MUERTO.value:
            return

        if status.pet_state == PetState.PAUSADO.value:
            self._ensure_engine_running()
            self._engine.resume()
            self._toggle_btn.configure(text="Pausar")
            return

        if not self._engine_started:
            self._ensure_engine_running()
            self._toggle_btn.configure(text="Pausar")
            return

        self._engine.pause()
        self._toggle_btn.configure(text="Reanudar")

    def _reset_all(self) -> None:
        self._stop_warning_alert()
        if self._death_dialog is not None and self._death_dialog.winfo_exists():
            self._death_dialog.destroy()
            self._death_dialog = None
        if self._flow_dialog is not None and self._flow_dialog.winfo_exists():
            self._flow_dialog.destroy()
            self._flow_dialog = None

        self._engine.reset()
        self._last_state = ""
        self._last_streak = 0
        self._toggle_btn.configure(text="Pausar" if self._engine_started else "Iniciar")

    def _on_close(self) -> None:
        self._stop_warning_alert()
        self._engine.stop()
        self.destroy()

    def _tick_blink(self) -> None:
        self._blink_on = not self._blink_on
        self.after(BLINK_MS, self._tick_blink)

    # --- Actualización fluida vía .after() ---

    def _refresh_ui(self) -> None:
        status = self._engine.get_status()
        state = status.pet_state

        self._timer_label.configure(text=format_time(status.remaining_seconds))
        self._phase_label.configure(
            text="Descanso ☕" if status.phase == "break" else "Trabajo 💼"
        )
        self._pet_label.configure(
            text=format_pet_display(state, status.streak)
        )
        self._state_label.configure(text=state)
        self._apply_state_color(state)

        life_ratio = max(0.0, min(1.0, status.life_percent / 100.0))
        self._life_bar.set(life_ratio)
        bar_color = life_bar_color(status.life_percent)
        self._life_bar.configure(progress_color=bar_color)
        self._life_percent_label.configure(text=f"{status.life_percent:.1f}%")

        streak_text = f"Racha: {status.streak} 🔥"
        if status.streak >= STREAK_VIP_THRESHOLD:
            streak_text += f"  {VIP_ACCESSORY} VIP"
        self._streak_label.configure(text=streak_text)

        self._check_vip_milestone(status.streak)

        if state == PetState.MUERTO.value:
            self._toggle_btn.configure(state="disabled")
        else:
            self._toggle_btn.configure(state="normal")

        self._handle_state_transitions(state)
        self._last_state = state
        self.after(REFRESH_MS, self._refresh_ui)

    def _apply_state_color(self, state: str) -> None:
        if state in GREEN_STATES:
            self._state_label.configure(text_color=COLOR_GREEN)
            self._timer_label.configure(text_color=COLOR_GREEN)
            return

        if state == PetState.PAUSADO.value:
            color = COLOR_PINK if self._blink_on else COLOR_PINK_DIM
            self._state_label.configure(text_color=color)
            self._timer_label.configure(text_color=color)
            return

        if state in (PetState.PROCRASTINANDO.value, PetState.MUERTO.value):
            self._state_label.configure(text_color=COLOR_RED)
            self._timer_label.configure(text_color=COLOR_RED)

    def _handle_state_transitions(self, state: str) -> None:
        if state != self._last_state:
            if state == PetState.EXITO.value:
                play_success()
            elif state == PetState.MUERTO.value:
                play_defeat()
                self._show_death_dialog()

            if state in ALERT_STATES:
                self._start_warning_alert()
            else:
                self._stop_warning_alert()

    def _check_vip_milestone(self, streak: int) -> None:
        if (
            streak >= STREAK_VIP_THRESHOLD
            and self._last_streak < STREAK_VIP_THRESHOLD
        ):
            play_vip_unlock()
            self._show_flow_state_dialog()
        self._last_streak = streak

    # --- Alertas intermitentes ---

    def _start_warning_alert(self) -> None:
        if self._warning_job is not None:
            return
        self._schedule_warning_beep()

    def _schedule_warning_beep(self) -> None:
        status = self._engine.get_status()
        if status.pet_state not in ALERT_STATES:
            self._warning_job = None
            return

        play_warning()
        self._warning_job = self.after(WARNING_ALERT_MS, self._schedule_warning_beep)

    def _stop_warning_alert(self) -> None:
        if self._warning_job is not None:
            self.after_cancel(self._warning_job)
            self._warning_job = None

    # --- Pantalla de muerte ---

    def _show_flow_state_dialog(self) -> None:
        if self._flow_dialog is not None and self._flow_dialog.winfo_exists():
            return
        self._flow_dialog = FlowStateDialog(self)

    def _show_death_dialog(self) -> None:
        if self._death_dialog is not None and self._death_dialog.winfo_exists():
            return
        self._death_dialog = DeathDialog(self, on_reset=self._reset_all)


def main() -> None:
    app = FocusOrDieApp()
    app.mainloop()


if __name__ == "__main__":
    main()
