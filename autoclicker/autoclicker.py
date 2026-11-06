import tkinter as tk
import threading
import time
import ctypes
import hashlib
import platform
import uuid
import urllib.request
import urllib.parse
import json


# =============================
# Settings
# =============================

SERVER_URL = "http://127.0.0.1:8000"

running = False
checking_server = False

current_cps = 0

user32 = ctypes.windll.user32

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004


# =============================
# Device ID
# =============================

def get_device_id():

    computer_name = platform.node()
    system = platform.system()
    machine = platform.machine()
    mac = uuid.getnode()

    raw_data = f"{computer_name}-{system}-{machine}-{mac}"

    device_hash = hashlib.sha256(
        raw_data.encode("utf-8")
    ).hexdigest()

    return "PC-" + device_hash[:12].upper()


DEVICE_ID = get_device_id()


# =============================
# Copy ID
# =============================

def copy_id():

    root.clipboard_clear()
    root.clipboard_append(DEVICE_ID)
    root.update()

    copy_status.set("✅ ID کپی شد")

    root.after(
        2000,
        lambda: copy_status.set("")
    )


# =============================
# Server Permission
# =============================

def check_server_permission():

    try:

        encoded_id = urllib.parse.quote(
            DEVICE_ID,
            safe=""
        )

        url = (
            f"{SERVER_URL}/api/software/permission/"
            f"{encoded_id}"
        )

        request = urllib.request.Request(
            url,
            method="GET",
            headers={
                "User-Agent": "ParClicker"
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=5
        ) as response:

            data = response.read().decode("utf-8")

            return json.loads(data)

    except Exception as error:

        return {
            "allowed": False,
            "message": "اتصال به سرور برقرار نشد."
        }


# =============================
# Click Loop
# =============================

def click_loop():

    global running

    if current_cps <= 0:
        running = False
        return

    interval = 1.0 / current_cps

    next_click = time.perf_counter()

    while running:

        user32.mouse_event(
            MOUSEEVENTF_LEFTDOWN,
            0,
            0,
            0,
            0
        )

        user32.mouse_event(
            MOUSEEVENTF_LEFTUP,
            0,
            0,
            0,
            0
        )

        next_click += interval

        remaining = next_click - time.perf_counter()

        if remaining > 0:
            time.sleep(remaining)

        else:
            next_click = time.perf_counter()


# =============================
# Stop
# =============================

def stop_clicker():

    global running

    running = False

    root.after(
        0,
        update_stopped_ui
    )


def update_stopped_ui():

    status_text.set("STOPPED")

    status_label.config(
        fg="#dc2626"
    )

    start_button.config(
        state="normal"
    )

    stop_button.config(
        state="disabled"
    )


# =============================
# Start
# =============================

def start_clicker():

    global checking_server

    if running:
        return

    if checking_server:
        return

    checking_server = True

    start_button.config(
        state="disabled"
    )

    stop_button.config(
        state="disabled"
    )

    status_text.set(
        "CHECKING SERVER..."
    )

    status_label.config(
        fg="#d97706"
    )

    server_status.set(
        "در حال بررسی اشتراک..."
    )

    threading.Thread(
        target=check_before_start,
        daemon=True
    ).start()


# =============================
# Check Before Start
# =============================

def check_before_start():

    global running
    global checking_server
    global current_cps

    result = check_server_permission()

    allowed = result.get(
        "allowed",
        False
    )

    message = result.get(
        "message",
        "اجازه استفاده صادر نشد."
    )

    if not allowed:

        checking_server = False

        root.after(
            0,
            lambda: permission_denied(message)
        )

        return

    # =========================
    # Get CPS From Server
    # =========================

    server_cps = result.get(
        "cps"
    )

    try:

        server_cps = int(server_cps)

    except (TypeError, ValueError):

        checking_server = False

        root.after(
            0,
            lambda: permission_denied(
                "سرور مقدار CPS معتبری ارسال نکرد."
            )
        )

        return

    if server_cps <= 0:

        checking_server = False

        root.after(
            0,
            lambda: permission_denied(
                "CPS اشتراک معتبر نیست."
            )
        )

        return

    # CPS فقط از سرور تعیین می‌شود
    current_cps = server_cps

    running = True
    checking_server = False

    root.after(
        0,
        start_clicking_ui
    )

    threading.Thread(
        target=click_loop,
        daemon=True
    ).start()


# =============================
# Permission Denied
# =============================

def permission_denied(message):

    global running
    global current_cps

    running = False
    current_cps = 0

    status_text.set(
        "NOT AUTHORIZED"
    )

    status_label.config(
        fg="#dc2626"
    )

    start_button.config(
        state="normal"
    )

    stop_button.config(
        state="disabled"
    )

    server_status.set(
        "❌ " + message
    )


# =============================
# Start UI
# =============================

def start_clicking_ui():

    status_text.set(
        "RUNNING"
    )

    status_label.config(
        fg="#16a34a"
    )

    server_status.set(
        f"✅ مجاز | سرعت: {current_cps} CPS"
    )

    speed_label.config(
        text=f"Speed: {current_cps} clicks/sec"
    )

    start_button.config(
        state="disabled"
    )

    stop_button.config(
        state="normal"
    )


# =============================
# F6
# =============================

def keyboard_listener():

    global running

    previous_state = False

    while True:

        key_pressed = bool(
            user32.GetAsyncKeyState(0x75)
            & 0x8000
        )

        if key_pressed and not previous_state:

            if running:
                stop_clicker()

            else:
                start_clicker()

        previous_state = key_pressed

        time.sleep(0.01)


# =============================
# Window
# =============================

root = tk.Tk()

root.title(
    "ParClicker"
)

root.geometry(
    "460x460"
)

root.resizable(
    False,
    False
)

root.configure(
    bg="#f4f4f5"
)


# =============================
# Title
# =============================

title = tk.Label(
    root,
    text="PARCLICKER",
    font=("Segoe UI", 24, "bold"),
    bg="#f4f4f5"
)

title.pack(
    pady=(30, 15)
)


# =============================
# ID
# =============================

id_title = tk.Label(
    root,
    text="Software ID",
    font=("Segoe UI", 11, "bold"),
    bg="#f4f4f5"
)

id_title.pack(
    pady=(5, 5)
)


id_frame = tk.Frame(
    root,
    bg="#f4f4f5"
)

id_frame.pack(
    pady=5
)


id_entry = tk.Entry(
    id_frame,
    font=("Segoe UI", 11),
    width=25,
    justify="center"
)

id_entry.insert(
    0,
    DEVICE_ID
)

id_entry.config(
    state="readonly"
)

id_entry.pack(
    side="left",
    padx=(0, 5)
)


copy_button = tk.Button(
    id_frame,
    text="Copy",
    font=("Segoe UI", 10, "bold"),
    width=7,
    command=copy_id
)

copy_button.pack(
    side="left"
)


copy_status = tk.StringVar()

copy_status.set("")


copy_label = tk.Label(
    root,
    textvariable=copy_status,
    font=("Segoe UI", 9),
    fg="#16a34a",
    bg="#f4f4f5"
)

copy_label.pack(
    pady=(2, 5)
)


# =============================
# Speed
# =============================

speed_label = tk.Label(
    root,
    text="Speed: Waiting for server...",
    font=("Segoe UI", 12),
    bg="#f4f4f5"
)

speed_label.pack(
    pady=5
)


# =============================
# Server Status
# =============================

server_status = tk.StringVar()

server_status.set(
    "برای شروع، دکمه START را بزنید."
)


server_label = tk.Label(
    root,
    textvariable=server_status,
    font=("Segoe UI", 10),
    fg="#555555",
    bg="#f4f4f5",
    wraplength=380
)

server_label.pack(
    pady=(10, 5)
)


# =============================
# Status
# =============================

status_text = tk.StringVar()

status_text.set(
    "STOPPED"
)


status_label = tk.Label(
    root,
    textvariable=status_text,
    font=("Segoe UI", 18, "bold"),
    fg="#dc2626",
    bg="#f4f4f5"
)

status_label.pack(
    pady=10
)


# =============================
# Buttons
# =============================

button_frame = tk.Frame(
    root,
    bg="#f4f4f5"
)

button_frame.pack(
    pady=10
)


start_button = tk.Button(
    button_frame,
    text="START",
    font=("Segoe UI", 13, "bold"),
    width=10,
    command=start_clicker
)

start_button.grid(
    row=0,
    column=0,
    padx=5
)


stop_button = tk.Button(
    button_frame,
    text="STOP",
    font=("Segoe UI", 13, "bold"),
    width=10,
    state="disabled",
    command=stop_clicker
)

stop_button.grid(
    row=0,
    column=1,
    padx=5
)


# =============================
# Hint
# =============================

hint = tk.Label(
    root,
    text="F6 = Start / Stop",
    font=("Segoe UI", 10),
    fg="#555555",
    bg="#f4f4f5"
)

hint.pack(
    pady=10
)


# =============================
# Keyboard Listener
# =============================

threading.Thread(
    target=keyboard_listener,
    daemon=True
).start()


# =============================
# Run
# =============================

root.mainloop()