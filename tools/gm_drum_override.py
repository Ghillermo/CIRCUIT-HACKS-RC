"""General MIDI drum override support for the Setup Memory / Setup view.

This module models the beta feature described in the request:

- each of the four drum channels can have a target GM note (35..81)
- each channel has an enabled/disabled override flag
- when enabled, a trigger on that channel emits the configured GM Note On
  instead of the stock drum pitch
- state is persisted with the project/setup memory

The code is intentionally written as a clear, firmware-friendly reference
implementation that can be adapted into the real patching flow used by the
project's ARM patch generators.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List


GM_NOTE_MIN = 35
GM_NOTE_MAX = 81
DRUM_CHANNELS = 4


@dataclass
class DrumGMOverride:
    """Per-drum override state.

    `enabled` toggles the override for that drum.
    `target_note` is a valid MIDI note number in 35..81.
    """

    enabled: bool = False
    target_note: int = 36

    def __post_init__(self) -> None:
        self.target_note = self._clamp_target_note(self.target_note)

    @staticmethod
    def _clamp_target_note(note: int) -> int:
        return max(GM_NOTE_MIN, min(GM_NOTE_MAX, int(note)))

    def set_target_note(self, note: int) -> None:
        self.target_note = self._clamp_target_note(note)

    def note_on_value(self, stock_note: int) -> int:
        if not self.enabled:
            return stock_note
        return self.target_note


@dataclass
class SetupMemoryDrumOverride:
    """Persistent setup memory for the four drum channels.

    The raw memory layout is represented as four slots of 2 bytes each:
    - byte 0: enabled flag (0x00 / 0x01)
    - byte 1: target note (35..81)
    """

    channels: List[DrumGMOverride] = field(
        default_factory=lambda: [DrumGMOverride() for _ in range(DRUM_CHANNELS)]
    )

    def __post_init__(self) -> None:
        if len(self.channels) != DRUM_CHANNELS:
            self.channels = [DrumGMOverride() for _ in range(DRUM_CHANNELS)]

    @classmethod
    def from_bytes(cls, payload: bytes) -> "SetupMemoryDrumOverride":
        if len(payload) != DRUM_CHANNELS * 2:
            raise ValueError(
                f"expected {DRUM_CHANNELS * 2} bytes of setup payload, got {len(payload)}"
            )

        state = cls()
        for i in range(DRUM_CHANNELS):
            offset = i * 2
            enabled = bool(payload[offset] & 0x01)
            target_note = payload[offset + 1]
            state.channels[i] = DrumGMOverride(enabled=enabled, target_note=target_note)
        return state

    def to_bytes(self) -> bytes:
        out = bytearray(DRUM_CHANNELS * 2)
        for i, drum in enumerate(self.channels):
            offset = i * 2
            out[offset] = 0x01 if drum.enabled else 0x00
            out[offset + 1] = drum.target_note & 0xFF
        return bytes(out)

    def set_channel(self, drum_index: int, *, enabled: bool | None = None, target_note: int | None = None) -> None:
        if not 0 <= drum_index < DRUM_CHANNELS:
            raise IndexError(f"drum index must be between 0 and {DRUM_CHANNELS - 1}")

        drum = self.channels[drum_index]
        if enabled is not None:
            drum.enabled = bool(enabled)
        if target_note is not None:
            drum.set_target_note(target_note)

    def note_on_for(self, drum_index: int, stock_note: int) -> int:
        if not 0 <= drum_index < DRUM_CHANNELS:
            raise IndexError(f"drum index must be between 0 and {DRUM_CHANNELS - 1}")
        return self.channels[drum_index].note_on_value(stock_note)

    def enabled_channels(self) -> List[int]:
        return [i for i, drum in enumerate(self.channels) if drum.enabled]


def validate_target_note(note: int) -> int:
    """Return a clamped value for a user-selected GM drum note."""
    return DrumGMOverride._clamp_target_note(note)


def build_setup_memory_from_user_selection(
    selection: Iterable[tuple[int, bool, int]],
) -> SetupMemoryDrumOverride:
    """Create setup memory from a list of `(drum_index, enabled, target_note)` tuples.

    Example:
        [(0, True, 36), (1, False, 38), (2, True, 42), (3, True, 55)]
    """

    state = SetupMemoryDrumOverride()
    for drum_index, enabled, target_note in selection:
        state.set_channel(drum_index, enabled=enabled, target_note=target_note)
    return state


def apply_drum_trigger(
    state: SetupMemoryDrumOverride,
    drum_index: int,
    stock_note: int,
) -> int:
    """Return the externally sent MIDI Note On value for the drum trigger."""
    return state.note_on_for(drum_index, stock_note)


__all__ = [
    "DRUM_CHANNELS",
    "GM_NOTE_MIN",
    "GM_NOTE_MAX",
    "DrumGMOverride",
    "SetupMemoryDrumOverride",
    "apply_drum_trigger",
    "build_setup_memory_from_user_selection",
    "validate_target_note",
]
