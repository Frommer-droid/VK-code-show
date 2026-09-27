VK_NAMES: dict[int, str] = {
    0x01: "Left mouse button",
    0x02: "Right mouse button",
    0x03: "Cancel",
    0x04: "Middle mouse button",
    0x08: "Backspace",
    0x09: "Tab",
    0x0D: "Enter",
    0x10: "Shift",
    0x11: "Ctrl",
    0x12: "Alt",
    0x13: "Pause",
    0x14: "Caps Lock",
    0x1B: "Esc",
    0x20: "Space",
    0x21: "Page Up",
    0x22: "Page Down",
    0x23: "End",
    0x24: "Home",
    0x25: "Left Arrow",
    0x26: "Up Arrow",
    0x27: "Right Arrow",
    0x28: "Down Arrow",
    0x2C: "Print Screen",
    0x2D: "Insert",
    0x2E: "Delete",
    0x5B: "Left Windows",
    0x5C: "Right Windows",
    0x5D: "Applications",
    0x60: "Num 0",
    0x61: "Num 1",
    0x62: "Num 2",
    0x63: "Num 3",
    0x64: "Num 4",
    0x65: "Num 5",
    0x66: "Num 6",
    0x67: "Num 7",
    0x68: "Num 8",
    0x69: "Num 9",
    0x6A: "Num *",
    0x6B: "Num +",
    0x6D: "Num -",
    0x6E: "Num .",
    0x6F: "Num /",
    0x90: "Num Lock",
    0x91: "Scroll Lock",
    0xA0: "Left Shift",
    0xA1: "Right Shift",
    0xA2: "Left Ctrl",
    0xA3: "Right Ctrl",
    0xA4: "Left Alt",
    0xA5: "Right Alt",
}

for number in range(10):
    VK_NAMES[0x30 + number] = str(number)

for offset, letter in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    VK_NAMES[0x41 + offset] = letter

for index in range(1, 25):
    VK_NAMES[0x6F + index] = f"F{index}"


def format_vk_hex(vk_code: int) -> str:
    return f"0x{vk_code:02X}"


def format_vkc_token(vk_code: int) -> str:
    return f"{{VKC:{vk_code}}}"


def key_name_for_vk(vk_code: int, fallback: str = "") -> str:
    if vk_code in VK_NAMES:
        return VK_NAMES[vk_code]
    if fallback:
        return fallback
    return "Unknown"


def visible_text(text: str) -> str:
    if not text:
        return ""
    if text == " ":
        return "Space"
    if text.isprintable():
        return text
    return repr(text)
