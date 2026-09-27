from __future__ import annotations

from dataclasses import dataclass

from .key_codes import format_vk_hex, format_vkc_token


@dataclass(frozen=True)
class KeyCapture:
    vk_code: int
    qt_key: int
    scan_code: int
    key_name: str
    text: str
    modifiers: str
    is_auto_repeat: bool

    @property
    def vk_decimal(self) -> str:
        return str(self.vk_code)

    @property
    def vk_hex(self) -> str:
        return format_vk_hex(self.vk_code)

    @property
    def vkc_token(self) -> str:
        return format_vkc_token(self.vk_code)

    @property
    def scan_decimal(self) -> str:
        return str(self.scan_code)

    @property
    def scan_hex(self) -> str:
        return f"0x{self.scan_code:04X}"

    @property
    def scan_display(self) -> str:
        return f"{self.scan_decimal} ({self.scan_hex})"

    @property
    def qt_hex(self) -> str:
        return f"0x{self.qt_key:08X}"
