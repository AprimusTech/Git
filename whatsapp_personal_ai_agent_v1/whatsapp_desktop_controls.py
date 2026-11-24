from pywinauto import Desktop
import time

app = Desktop(backend="uia").window(title="WhatsApp")
app.wait("exists", timeout=10)

print("\nWHATSAPP DESKTOP UI TREE")
print("=" * 70)
app.print_control_identifiers(depth=12)
