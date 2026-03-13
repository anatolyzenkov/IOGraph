from __future__ import annotations

from dataclasses import dataclass

from .session_controller import SessionController


@dataclass(frozen=True)
class TrackingUiState:
    can_save: bool
    can_reset: bool
    toggle_label: str
    reset_button_visible: bool


class TrackingUiDecisions:
    LONG_TRACKING_CONFIRM_MS = 30 * 60 * 1000
    RESET_BUTTON_VISIBLE_MS = 2000

    @classmethod
    def compute_state(cls, elapsed_ms: int, tracking: bool) -> TrackingUiState:
        can_save = tracking or elapsed_ms > 0
        can_reset = elapsed_ms > cls.RESET_BUTTON_VISIBLE_MS
        toggle_label = "Pause" if tracking else ("Start" if elapsed_ms == 0 else "Resume")
        return TrackingUiState(
            can_save=can_save,
            can_reset=can_reset,
            toggle_label=toggle_label,
            reset_button_visible=can_reset,
        )

    @classmethod
    def extend_reset_message_for_long_tracking(cls, base_message: str, elapsed_ms: int) -> str:
        if elapsed_ms <= cls.LONG_TRACKING_CONFIRM_MS:
            return base_message
        return f"{base_message}\nAre you sure? After {SessionController.tracking_time_text(elapsed_ms)} of tracking?"
