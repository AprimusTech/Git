"""Read-only UI Automation diagnostic for the WhatsApp Desktop app on Windows.
Run this first to inspect the UIA tree; it does not click or send messages."""
from pywinauto import Desktop


def main():
    desktop = Desktop(backend="uia")
    candidates = []
    for w in desktop.windows():
        title = (w.window_text() or "").strip()
        if "whatsapp" in title.casefold():
            candidates.append(w)
    if not candidates:
        print("WhatsApp Desktop window not found. Open the WhatsApp Desktop app, then retry.")
        return
    win = candidates[0]
    print(f"FOUND WINDOW: {win.window_text()!r} | handle={win.handle}")
    print("--- UI Automation controls (read-only) ---")
    for i, el in enumerate(win.descendants()):
        try:
            info = el.element_info
            name = (info.name or "").strip().replace("\n", " ")
            ctype = info.control_type or "?"
            if name:
                print(f"{i:04d} | {ctype:16s} | {name[:240]}")
        except Exception:
            continue
if __name__ == "__main__":
    main()
