import argparse
import ctypes
import json
import os
import struct
import sys
import time
import zlib
from ctypes import wintypes

from align_roblox import find_roblox_window, user32, SW_RESTORE


gdi32 = ctypes.windll.gdi32
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SPAWN_TEMPLATE_DIR = os.path.join(PROJECT_ROOT, "data", "vision", "spawn-anchors")
MOVEMENT_DIR = os.path.join(PROJECT_ROOT, "data", "vision", "movement")

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_WHEEL = 0x0800
KEYEVENTF_KEYUP = 0x0002
VK_CONTROL = 0x11
VK_A = 0x41
VK_BACK = 0x08
VK_D = 0x44
VK_S = 0x53
VK_W = 0x57
INPUT_KEYBOARD = 1
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_SCANCODE = 0x0008
SCAN_W = 0x11
SCAN_A = 0x1E
SCAN_T = 0x14
SCAN_R = 0x13
SCAN_X = 0x2D
SCAN_Z = 0x2C
SCAN_5 = 0x06

STORY_MAPS = [
    "Planet Namak",
    "Sand Village",
    "Double Dungeon",
    "Shibuya Station",
    "Underground Church",
    "Spirit Society",
    "Martial Island",
    "Edge of Heaven",
    "Lebereo Raid",
    "Hill of Swords",
    "Frozen Port",
    "Downtown Tokyo",
    "Hidden Village",
]

LEGEND_MAPS = [
    "Sand Village",
    "Double Dungeon",
    "Shibuya Aftermath",
    "Golden Castle",
    "Kuinshi Palace",
    "Land of the Gods",
    "Shining Castle",
    "Crystal Chapel",
    "Burning Spirit Tree",
    "Imprisoned Island",
    "Tokyo Railway",
    "Destroyed Hidden Village",
]

AREA_SEARCH_TERMS = {
    "story": "story",
    "infinite": "story",
    "legend": "story",
}

MAP_GROUPS = {
    "story": {
        "maps": STORY_MAPS,
        "tab": None,
    },
    "infinite": {
        "maps": STORY_MAPS,
        "tab": None,
    },
    "legend": {
        "maps": LEGEND_MAPS,
        "tab": (548, 496),
    },
}

ROUTE_ACTS = [
    "Act 1",
    "Act 2",
    "Act 3",
    "Act 4",
    "Act 5",
    "Act 6",
    "Infinite",
]

LIST_SCROLL_SETTLE = 0.18
LIST_CLICK_DELAY = 0.28

ACT_ALIASES = {
    "Stage 1": "Act 1",
    "Stage 2": "Act 2",
    "Stage 3": "Act 3",
    "Default": "Act 1",
}

MAP_LIST = {
    "x": 222,
    "first_y": 202,
    "row_h": 42,
    "visible_rows": 5,
    "scroll_x": 220,
    "scroll_y": 318,
    "rows_per_wheel": 2,
}

STORY_MAP_PAGES = [
    {"scrolls": 0, "first_index": 0, "indices": range(0, 5)},
    {"scrolls": 2, "first_index": 5, "indices": range(5, 10)},
    {"scrolls": 2, "first_index": 8, "indices": range(10, 13)},
]

ACT_LIST = {
    "x": 360,
    "first_y": 244,
    "row_h": 41,
    "visible_rows": 5,
    "scroll_x": 370,
    "scroll_y": 328,
    "rows_per_wheel": 2,
    "scroll_after_rows": 2,
    "infinite_index": 6,
    "infinite_x": 320,
    "infinite_y": 400,
}

PLANET_NAMEK_CAMERA = {
    "spawn_template_map": "planet-namek",
    "zoom_x": 405,
    "zoom_y": 300,
    "zoom_in_ticks": 25,
    "zoom_out_ticks": 12,
    "settings_x": 20,
    "settings_y": 580,
    "settings_open_delay": 0.75,
    "settings_close_x": 690,
    "settings_close_y": 150,
    "teleport_spawn_x": 648,
    "teleport_spawn_y": 292,
    "restart_match_x": 648,
    "restart_match_y": 264,
    "teleport_spawn_max_attempts": None,
    "spawn_track_x": 275,
    "spawn_track_y_values": [455, 490, 525, 560],
    "spawn_track_scan_w": 42,
    "spawn_track_scan_h": 12,
    "spawn_track_line_threshold": 0.28,
    "spawn_track_required_lines": 3,
    "spawn_template_x": 230,
    "spawn_template_y": 452,
    "spawn_template_w": 120,
    "spawn_template_h": 58,
    "spawn_template_step": 4,
    "spawn_template_threshold": 0.96,
    # Slot 5 is intentionally used for camera setup because it is the cheapest unit.
    "place_slot_scan": SCAN_5,
    "place_x": 400,
    "place_y": 140,
    "unit_view_x": 125,
    "unit_view_y": 230,
    "view_left_x": 338,
    "view_left_y": 525,
    "view_exit_x": 400,
    "view_exit_y": 585,
    "sell_unit_scan": SCAN_X,
    "movement_record_poll": 0.02,
    "movement_stop_flag": os.path.join(MOVEMENT_DIR, "planetnamek.stop"),
    "movement_output_path": os.path.join(MOVEMENT_DIR, "planetnamek.json"),
    "movement_screenshot_path": os.path.join(PROJECT_ROOT, "data", "map", "Planet_Namek.png"),
    "movement_screenshot_zoom_out_ticks": 35,
}

user32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
user32.SetCursorPos.restype = wintypes.BOOL
user32.mouse_event.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, ctypes.c_int, ctypes.POINTER(ctypes.c_ulong)]
user32.mouse_event.restype = None
user32.keybd_event.argtypes = [ctypes.c_ubyte, ctypes.c_ubyte, wintypes.DWORD, ctypes.POINTER(ctypes.c_ulong)]
user32.keybd_event.restype = None
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
user32.GetAsyncKeyState.restype = ctypes.c_short
user32.GetDC.argtypes = [wintypes.HWND]
user32.GetDC.restype = wintypes.HDC
user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
user32.ReleaseDC.restype = ctypes.c_int
gdi32.GetPixel.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
gdi32.GetPixel.restype = wintypes.DWORD
gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
gdi32.CreateCompatibleDC.restype = wintypes.HDC
gdi32.DeleteDC.argtypes = [wintypes.HDC]
gdi32.DeleteDC.restype = wintypes.BOOL
gdi32.CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
gdi32.SelectObject.restype = wintypes.HGDIOBJ
gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
gdi32.DeleteObject.restype = wintypes.BOOL
gdi32.BitBlt.argtypes = [
    wintypes.HDC,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.HDC,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.DWORD,
]
gdi32.BitBlt.restype = wintypes.BOOL
gdi32.GetDIBits.argtypes = [
    wintypes.HDC,
    wintypes.HBITMAP,
    wintypes.UINT,
    wintypes.UINT,
    ctypes.c_void_p,
    ctypes.c_void_p,
    wintypes.UINT,
]
gdi32.GetDIBits.restype = ctypes.c_int

SRCCOPY = 0x00CC0020
DIB_RGB_COLORS = 0

ULONG_PTR = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("union", INPUT_UNION)]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [
        ("bmiHeader", BITMAPINFOHEADER),
        ("bmiColors", wintypes.DWORD * 3),
    ]


user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
user32.SendInput.restype = wintypes.UINT


def sleep(seconds=0.28):
    time.sleep(seconds)


def log(message):
    print(message, flush=True)


def screen_point(bounds, x, y):
    return (
        int(bounds["x"] + (x / 800) * bounds["width"]),
        int(bounds["y"] + (y / 600) * bounds["height"]),
    )


def click(bounds, x, y, delay=0.32):
    sx, sy = screen_point(bounds, x, y)
    user32.SetCursorPos(sx, sy)
    sleep(0.08)
    user32.mouse_event(MOUSEEVENTF_MOVE, 1, 0, 0, None)
    sleep(0.03)
    user32.mouse_event(MOUSEEVENTF_MOVE, -1, 0, 0, None)
    sleep(0.05)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, None)
    sleep(0.05)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, None)
    sleep(delay)


def move_to(bounds, x, y):
    sx, sy = screen_point(bounds, x, y)
    user32.SetCursorPos(sx, sy)


def scroll(bounds, x, y, steps, delay=0.12):
    sx, sy = screen_point(bounds, x, y)
    user32.SetCursorPos(sx, sy)
    sleep(0.14)
    user32.mouse_event(MOUSEEVENTF_MOVE, 1, 0, 0, None)
    sleep(0.04)
    user32.mouse_event(MOUSEEVENTF_MOVE, -1, 0, 0, None)
    sleep(0.08)
    delta = -120 if steps > 0 else 120
    for _ in range(abs(steps)):
        user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, delta, None)
        sleep(delay)


def normalize_name(value):
    return "".join(char for char in value.lower() if char.isalnum())


def find_index(options, target):
    target_key = normalize_name(target)
    return next((index for index, name in enumerate(options) if normalize_name(name) == target_key), None)


def reset_ordered_list(bounds, geometry):
    scroll(bounds, geometry["scroll_x"], geometry["scroll_y"], -20, delay=0.04)
    move_to(bounds, geometry["x"], geometry["first_y"])
    sleep(0.1)


def ordered_list_position(index, total_count, geometry):
    max_first_index = max(0, total_count - geometry["visible_rows"])
    max_scroll_steps = (max_first_index + geometry["rows_per_wheel"] - 1) // geometry["rows_per_wheel"]
    scroll_steps = min(index // geometry["rows_per_wheel"], max_scroll_steps)
    first_visible_index = min(scroll_steps * geometry["rows_per_wheel"], max_first_index)
    return scroll_steps, index - first_visible_index


def story_map_page_position(index):
    total_scrolls = 0
    for page in STORY_MAP_PAGES:
        total_scrolls += page["scrolls"]
        if index in page["indices"]:
            return total_scrolls, index - page["first_index"]
    return ordered_list_position(index, len(STORY_MAPS), MAP_LIST)


def select_ordered_item(bounds, options, target, geometry, reset=True):
    if reset:
        reset_ordered_list(bounds, geometry)

    target_index = find_index(options, target)
    if target_index is None:
        raise ValueError(f"Unknown option: {target}")

    if geometry is ACT_LIST and target_index >= geometry["scroll_after_rows"]:
        scroll(bounds, geometry["scroll_x"], geometry["scroll_y"], 1)
        sleep(LIST_SCROLL_SETTLE)
        if target_index == geometry["infinite_index"]:
            click(bounds, geometry["infinite_x"], geometry["infinite_y"], LIST_CLICK_DELAY)
            return
        else:
            row = target_index - geometry["scroll_after_rows"]
        click(bounds, geometry["x"], geometry["first_y"] + row * geometry["row_h"], LIST_CLICK_DELAY)
        return

    if geometry is MAP_LIST and options == STORY_MAPS:
        scroll_steps, row = story_map_page_position(target_index)
        if scroll_steps:
            scroll(bounds, geometry["scroll_x"], geometry["scroll_y"], scroll_steps)
            sleep(LIST_SCROLL_SETTLE)
    elif target_index > 0:
        scroll_steps, row = ordered_list_position(target_index, len(options), geometry)
        scroll(bounds, geometry["scroll_x"], geometry["scroll_y"], scroll_steps)
        sleep(LIST_SCROLL_SETTLE)
    else:
        row = 0

    click(bounds, geometry["x"], geometry["first_y"] + row * geometry["row_h"], LIST_CLICK_DELAY)


def select_mode_tab(bounds, mode):
    tab = MAP_GROUPS[mode]["tab"]
    if tab:
        click(bounds, tab[0], tab[1], 0.45)


def key_down(vk):
    user32.keybd_event(vk, 0, 0, None)


def key_up(vk):
    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, None)


def tap_key(vk):
    user32.keybd_event(vk, 0, 0, None)
    sleep(0.06)
    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, None)
    sleep(0.12)


def clear_text_field():
    key_down(VK_CONTROL)
    user32.keybd_event(VK_A, 0, 0, None)
    user32.keybd_event(VK_A, 0, KEYEVENTF_KEYUP, None)
    key_up(VK_CONTROL)
    sleep(0.05)
    user32.keybd_event(VK_BACK, 0, 0, None)
    user32.keybd_event(VK_BACK, 0, KEYEVENTF_KEYUP, None)
    sleep(0.08)


def type_text(text):
    for char in text:
        user32.VkKeyScanW.restype = ctypes.c_short
        vk_scan = user32.VkKeyScanW(ord(char))
        vk = vk_scan & 0xFF
        shift = (vk_scan >> 8) & 0xFF
        if shift & 1:
            user32.keybd_event(0x10, 0, 0, None)
        user32.keybd_event(vk, 0, 0, None)
        user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, None)
        if shift & 1:
            user32.keybd_event(0x10, 0, KEYEVENTF_KEYUP, None)
        sleep(0.035)


def hold_key(vk, seconds):
    user32.keybd_event(vk, 0, 0, None)
    sleep(seconds)
    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, None)
    sleep(0.2)


def normalize_planet_namek_camera(bounds, map_key=None):
    log("Normalizing Planet Namek camera...")
    focus_roblox()
    orient_planet_namek_camera(bounds)
    teleport_until_spawn_anchor(bounds, map_key)
    log("Planet Namek camera normalized.")


def orient_planet_namek_camera(bounds):
    log("Orienting Planet Namek camera...")
    # Roblox zooms in on wheel-up and out on wheel-down. Start from a known close zoom,
    # then step back out to a repeatable camera distance.
    scroll(
        bounds,
        PLANET_NAMEK_CAMERA["zoom_x"],
        PLANET_NAMEK_CAMERA["zoom_y"],
        -PLANET_NAMEK_CAMERA["zoom_in_ticks"],
        delay=0.025,
    )
    scroll(
        bounds,
        PLANET_NAMEK_CAMERA["zoom_x"],
        PLANET_NAMEK_CAMERA["zoom_y"],
        PLANET_NAMEK_CAMERA["zoom_out_ticks"],
        delay=0.035,
    )

    log("Placing cheapest unit from slot 5...")
    tap_scan(PLANET_NAMEK_CAMERA["place_slot_scan"])
    click(bounds, PLANET_NAMEK_CAMERA["place_x"], PLANET_NAMEK_CAMERA["place_y"], 0.5)
    click(bounds, PLANET_NAMEK_CAMERA["unit_view_x"], PLANET_NAMEK_CAMERA["unit_view_y"], 0.45)
    click(bounds, PLANET_NAMEK_CAMERA["view_left_x"], PLANET_NAMEK_CAMERA["view_left_y"], 0.45)
    click(bounds, PLANET_NAMEK_CAMERA["view_exit_x"], PLANET_NAMEK_CAMERA["view_exit_y"], 0.35)
    log("Selling temporary camera unit...")
    tap_scan(PLANET_NAMEK_CAMERA["sell_unit_scan"])


def teleport_to_spawn(bounds):
    click(bounds, PLANET_NAMEK_CAMERA["teleport_spawn_x"], PLANET_NAMEK_CAMERA["teleport_spawn_y"], 0.55)
    sleep(0.35)


def open_settings(bounds):
    log("Opening settings from bottom-left gear...")
    click(
        bounds,
        PLANET_NAMEK_CAMERA["settings_x"],
        PLANET_NAMEK_CAMERA["settings_y"],
        PLANET_NAMEK_CAMERA["settings_open_delay"],
    )


def close_settings(bounds):
    click(bounds, PLANET_NAMEK_CAMERA["settings_close_x"], PLANET_NAMEK_CAMERA["settings_close_y"], 0.45)
    focus_roblox()


def teleport_until_spawn_anchor(bounds, map_key=None):
    max_attempts = PLANET_NAMEK_CAMERA["teleport_spawn_max_attempts"]

    open_settings(bounds)

    try:
        if has_spawn_anchor(bounds, map_key):
            log("Spawn found.")
            log("Correct spawn anchor detected before teleporting.")
            close_settings(bounds)
            return

        attempt = 0
        while max_attempts is None or attempt < max_attempts:
            attempt += 1
            total = "∞" if max_attempts is None else str(max_attempts)
            log(f"Spawn anchor not found. Teleporting to spawn ({attempt}/{total})...")
            teleport_to_spawn(bounds)
            log("Checking spawn while settings is still open...")
            if has_spawn_anchor(bounds, map_key):
                log("Spawn found.")
                log(f"Correct spawn anchor detected after {attempt} teleport(s).")
                close_settings(bounds)
                return
    except Exception:
        close_settings(bounds)
        raise

    close_settings(bounds)
    raise RuntimeError("Could not find Planet Namek bottom-left spawn anchor after teleport attempts.")


def test_namek_spawn_detector(bounds, map_key=None, attempts=100):
    log(f"Testing Planet Namek spawn detector for {attempts} teleport(s)...")
    focus_roblox()
    open_settings(bounds)

    found_count = 0
    try:
        for attempt in range(attempts):
            log(f"Spawn detector test teleport ({attempt + 1}/{attempts})...")
            teleport_to_spawn(bounds)
            if has_spawn_anchor(bounds, map_key):
                found_count += 1
                log(f"Spawn found during detector test at attempt {attempt + 1}.")
            else:
                log(f"Spawn not found during detector test at attempt {attempt + 1}.")
    finally:
        close_settings(bounds)

    log(f"Spawn detector test finished. Found {found_count}/{attempts}.")


def pressed(vk):
    return bool(user32.GetAsyncKeyState(vk) & 0x8000)


def current_movement_state():
    keys = []
    if pressed(VK_W):
        keys.append("W")
    if pressed(VK_A):
        keys.append("A")
    if pressed(VK_S):
        keys.append("S")
    if pressed(VK_D):
        keys.append("D")
    return keys


def movement_segments(samples):
    if not samples:
        return []

    segments = []
    start = samples[0]["t"]
    previous = tuple(samples[0]["keys"])
    for sample in samples[1:]:
        keys = tuple(sample["keys"])
        if keys == previous:
            continue
        if previous:
            segments.append({
                "keys": list(previous),
                "start": round(start, 3),
                "duration": round(sample["t"] - start, 3),
            })
        start = sample["t"]
        previous = keys

    if previous:
        segments.append({
            "keys": list(previous),
            "start": round(start, 3),
            "duration": round(samples[-1]["t"] - start, 3),
        })
    return [segment for segment in segments if segment["duration"] >= 0.03]


def optimized_movement(samples):
    raw_segments = movement_segments(samples)
    totals = {key: 0.0 for key in ("W", "A", "S", "D")}
    for segment in raw_segments:
        for key in segment["keys"]:
            totals[key] += segment["duration"]

    return {
        "actions": [{"keys": segment["keys"], "duration": segment["duration"]} for segment in raw_segments],
        "rawTotals": {key: round(value, 3) for key, value in totals.items()},
        "mode": "raw",
    }


def record_movement(bounds):
    stop_flag = PLANET_NAMEK_CAMERA["movement_stop_flag"]
    output_path = PLANET_NAMEK_CAMERA["movement_output_path"]
    screenshot_path = PLANET_NAMEK_CAMERA["movement_screenshot_path"]
    poll = PLANET_NAMEK_CAMERA["movement_record_poll"]

    os.makedirs(os.path.dirname(stop_flag), exist_ok=True)
    if os.path.exists(stop_flag):
        os.remove(stop_flag)

    log("Movement recording started. Move with WASD, then press F11 again to stop.")
    focus_roblox()
    start = time.perf_counter()
    samples = []
    try:
        while not os.path.exists(stop_flag):
            samples.append({
                "t": time.perf_counter() - start,
                "keys": current_movement_state(),
            })
            sleep(poll)
    finally:
        if os.path.exists(stop_flag):
            os.remove(stop_flag)

    samples.append({
        "t": time.perf_counter() - start,
        "keys": current_movement_state(),
    })
    raw_segments = movement_segments(samples)
    optimized = optimized_movement(samples)

    log("Zooming fully out before coordinate screenshot...")
    scroll(
        bounds,
        PLANET_NAMEK_CAMERA["zoom_x"],
        PLANET_NAMEK_CAMERA["zoom_y"],
        PLANET_NAMEK_CAMERA["movement_screenshot_zoom_out_ticks"],
        delay=0.025,
    )
    sleep(0.3)
    width, height, rows = capture_viewport_pixels(bounds)
    write_png(screenshot_path, width, height, rows)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf8") as file:
        json.dump({
            "map": PLANET_NAMEK_CAMERA["spawn_template_map"],
            "recordedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "duration": round(samples[-1]["t"], 3),
            "rawSegments": raw_segments,
            "optimized": optimized,
            "screenshot": os.path.relpath(screenshot_path, PROJECT_ROOT),
        }, file, indent=2)

    log(f"Movement recording stopped. Raw segments: {len(raw_segments)}.")
    log(f"Optimized movement: {optimized['actions']}")
    log(f"Saved movement route: {output_path}")
    log(f"Updated coordinate screenshot: {screenshot_path}")


def scan_for_key(key):
    scans = {
        "W": SCAN_W,
        "A": SCAN_A,
        "S": 0x1F,
        "D": 0x20,
    }
    if key not in scans:
        raise ValueError(f"Unsupported movement key: {key}")
    return scans[key]


def hold_scans(scan_codes, seconds):
    for scan_code in scan_codes:
        send_scan(scan_code, False)
    sleep(seconds)
    for scan_code in reversed(scan_codes):
        send_scan(scan_code, True)
    sleep(0.12)


def play_movement(bounds):
    output_path = PLANET_NAMEK_CAMERA["movement_output_path"]
    screenshot_path = PLANET_NAMEK_CAMERA["movement_screenshot_path"]
    if not os.path.exists(output_path):
        raise RuntimeError(f"No saved movement route found: {output_path}")

    with open(output_path, "r", encoding="utf8") as file:
        route = json.load(file)

    actions = route.get("rawSegments") or route.get("optimized", {}).get("actions", [])
    if not actions:
        raise RuntimeError("Saved movement route has no optimized actions.")

    log(f"Playing saved movement route with {len(actions)} raw action(s)...")
    focus_roblox()
    for index, action in enumerate(actions):
        keys = action.get("keys") or ([action["key"]] if "key" in action else [])
        duration = float(action.get("duration", 0))
        if not keys or duration <= 0:
            continue
        log(f"Movement action {index + 1}/{len(actions)}: {'+'.join(keys)} for {duration:.3f}s")
        hold_scans([scan_for_key(key) for key in keys], duration)

    log("Zooming fully out before coordinate screenshot...")
    scroll(
        bounds,
        PLANET_NAMEK_CAMERA["zoom_x"],
        PLANET_NAMEK_CAMERA["zoom_y"],
        PLANET_NAMEK_CAMERA["movement_screenshot_zoom_out_ticks"],
        delay=0.025,
    )
    sleep(0.3)
    width, height, rows = capture_viewport_pixels(bounds)
    write_png(screenshot_path, width, height, rows)
    log(f"Updated coordinate screenshot: {screenshot_path}")
    log("Saved movement route finished.")


def spawn_template_path(map_key=None):
    key = normalize_name(map_key or PLANET_NAMEK_CAMERA["spawn_template_map"]) or "unknown-map"
    return os.path.join(SPAWN_TEMPLATE_DIR, f"{key}.json")


def capture_namek_spawn_anchor(bounds, map_key=None):
    template_path = spawn_template_path(map_key)
    log("Capturing Planet Namek spawn anchor reference...")
    focus_roblox()
    open_settings(bounds)
    try:
        reference = capture_spawn_template(bounds)
        reference["map"] = normalize_name(map_key or PLANET_NAMEK_CAMERA["spawn_template_map"])
        os.makedirs(os.path.dirname(template_path), exist_ok=True)
        with open(template_path, "w", encoding="utf8") as file:
            json.dump(reference, file)
        log(f"Saved spawn anchor reference: {template_path}")
    finally:
        close_settings(bounds)


def capture_spawn_template(bounds):
    x = PLANET_NAMEK_CAMERA["spawn_template_x"]
    y = PLANET_NAMEK_CAMERA["spawn_template_y"]
    width = PLANET_NAMEK_CAMERA["spawn_template_w"]
    height = PLANET_NAMEK_CAMERA["spawn_template_h"]
    step = PLANET_NAMEK_CAMERA["spawn_template_step"]
    hdc = user32.GetDC(None)
    if not hdc:
        raise OSError("GetDC failed")

    pixels = []
    try:
        for py in range(y, y + height, step):
            for px in range(x, x + width, step):
                sx, sy = screen_point(bounds, px, py)
                color = gdi32.GetPixel(hdc, sx, sy)
                red, green, blue = colorref_to_rgb(color)
                pixels.append([red, green, blue])
    finally:
        user32.ReleaseDC(None, hdc)

    return {
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "step": step,
        "pixels": pixels,
    }


def template_spawn_similarity(bounds, map_key=None):
    template_path = spawn_template_path(map_key)
    if not os.path.exists(template_path):
        return None

    with open(template_path, "r", encoding="utf8") as file:
        reference = json.load(file)

    live = capture_spawn_template(bounds)
    for key in ("x", "y", "width", "height", "step"):
        if live.get(key) != reference.get(key):
            log("Spawn template geometry changed; recapture this map with F9.")
            return None

    if len(live["pixels"]) != len(reference.get("pixels", [])):
        return None

    total_delta = 0
    channels = 0
    for live_pixel, reference_pixel in zip(live["pixels"], reference["pixels"]):
        for live_channel, reference_channel in zip(live_pixel, reference_pixel):
            total_delta += abs(live_channel - reference_channel)
            channels += 1

    average_delta = total_delta / channels if channels else 255
    return max(0, 1 - (average_delta / 255))


def colorref_to_rgb(color):
    return color & 0xFF, (color >> 8) & 0xFF, (color >> 16) & 0xFF


def capture_viewport_pixels(bounds):
    width = int(bounds["width"])
    height = int(bounds["height"])
    screen_dc = user32.GetDC(None)
    if not screen_dc:
        raise OSError("GetDC failed")

    memory_dc = gdi32.CreateCompatibleDC(screen_dc)
    bitmap = gdi32.CreateCompatibleBitmap(screen_dc, width, height)
    if not memory_dc or not bitmap:
        user32.ReleaseDC(None, screen_dc)
        raise OSError("CreateCompatibleDC/CreateCompatibleBitmap failed")

    try:
        old_object = gdi32.SelectObject(memory_dc, bitmap)
        if not gdi32.BitBlt(memory_dc, 0, 0, width, height, screen_dc, bounds["x"], bounds["y"], SRCCOPY):
            raise OSError("BitBlt failed")

        info = BITMAPINFO()
        info.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        info.bmiHeader.biWidth = width
        info.bmiHeader.biHeight = -height
        info.bmiHeader.biPlanes = 1
        info.bmiHeader.biBitCount = 24
        info.bmiHeader.biCompression = 0

        stride = ((width * 3 + 3) // 4) * 4
        buffer = (ctypes.c_ubyte * (stride * height))()
        copied = gdi32.GetDIBits(memory_dc, bitmap, 0, height, buffer, ctypes.byref(info), DIB_RGB_COLORS)
        if copied != height:
            raise OSError("GetDIBits failed")

        rows = []
        for y in range(height):
            row = bytearray()
            offset = y * stride
            for x in range(width):
                index = offset + x * 3
                blue = buffer[index]
                green = buffer[index + 1]
                red = buffer[index + 2]
                row.extend((red, green, blue))
            rows.append(bytes(row))
        gdi32.SelectObject(memory_dc, old_object)
        return width, height, rows
    finally:
        gdi32.DeleteObject(bitmap)
        gdi32.DeleteDC(memory_dc)
        user32.ReleaseDC(None, screen_dc)


def png_chunk(kind, data):
    return (
        struct.pack(">I", len(data))
        + kind
        + data
        + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    )


def write_png(path, width, height, rows):
    raw = b"".join(b"\x00" + row for row in rows)
    data = b"\x89PNG\r\n\x1a\n"
    data += png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    data += png_chunk(b"IDAT", zlib.compress(raw, 6))
    data += png_chunk(b"IEND", b"")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as file:
        file.write(data)


def is_namek_track_pixel(color):
    red, green, blue = colorref_to_rgb(color)
    return (
        75 <= red <= 195
        and 45 <= green <= 150
        and 25 <= blue <= 115
        and red >= green + 8
        and green >= blue - 5
    )


def anchor_region_score(hdc, bounds, x, y, width, height):
    matches = 0
    samples = 0
    for py in range(y, y + height, 3):
        for px in range(x, x + width, 3):
            sx, sy = screen_point(bounds, px, py)
            color = gdi32.GetPixel(hdc, sx, sy)
            if color == 0xFFFFFFFF:
                continue
            samples += 1
            if is_namek_track_pixel(color):
                matches += 1
    return matches / samples if samples else 0


def has_spawn_anchor(bounds, map_key=None):
    similarity = template_spawn_similarity(bounds, map_key)
    if similarity is not None:
        threshold = PLANET_NAMEK_CAMERA["spawn_template_threshold"]
        log(f"Spawn template similarity: {similarity:.3f} threshold={threshold:.3f}")
        return similarity >= threshold

    track_x = PLANET_NAMEK_CAMERA["spawn_track_x"]
    scan_w = PLANET_NAMEK_CAMERA["spawn_track_scan_w"]
    scan_h = PLANET_NAMEK_CAMERA["spawn_track_scan_h"]
    hdc = user32.GetDC(None)
    if not hdc:
        raise OSError("GetDC failed")

    try:
        line_scores = [
            anchor_region_score(
                hdc,
                bounds,
                track_x - (scan_w // 2),
                y - (scan_h // 2),
                scan_w,
                scan_h,
            )
            for y in PLANET_NAMEK_CAMERA["spawn_track_y_values"]
        ]
    finally:
        user32.ReleaseDC(None, hdc)

    line_threshold = PLANET_NAMEK_CAMERA["spawn_track_line_threshold"]
    required_lines = PLANET_NAMEK_CAMERA["spawn_track_required_lines"]
    passing_lines = sum(1 for score in line_scores if score >= line_threshold)
    log(
        "Spawn anchor scores: "
        f"track={','.join(f'{score:.2f}' for score in line_scores)} "
        f"pass={passing_lines}/{required_lines}"
    )
    return passing_lines >= required_lines


def send_scan(scan_code, key_up=False):
    flags = KEYEVENTF_SCANCODE | (KEYEVENTF_KEYUP if key_up else 0)
    input_event = INPUT(
        type=INPUT_KEYBOARD,
        union=INPUT_UNION(ki=KEYBDINPUT(0, scan_code, flags, 0, 0)),
    )
    sent = user32.SendInput(1, ctypes.byref(input_event), ctypes.sizeof(input_event))
    if sent != 1:
        error_code = ctypes.get_last_error()
        raise OSError(error_code, "SendInput failed")


def hold_scan(scan_code, seconds):
    send_scan(scan_code, False)
    sleep(seconds)
    send_scan(scan_code, True)
    sleep(0.25)


def tap_scan(scan_code):
    send_scan(scan_code, False)
    sleep(0.08)
    send_scan(scan_code, True)
    sleep(0.18)


def focus_roblox():
    hwnd = find_roblox_window()
    if hwnd:
      user32.ShowWindow(hwnd, SW_RESTORE)
      user32.BringWindowToTop(hwnd)
      user32.SetForegroundWindow(hwnd)
      sleep(0.2)


def canonical_mode(mode):
    normalized = normalize_name(mode)
    if normalized in {"story", "infinitemode", "infinite"}:
        return "infinite" if "infinite" in normalized else "story"
    if normalized in {"legend", "legendstages"}:
        return "legend"
    raise ValueError(f"Unsupported macro mode for this route: {mode}")


def canonical_act(mode, act):
    if mode == "infinite":
        return "Infinite"
    if act in ACT_ALIASES:
        return ACT_ALIASES[act]
    normalized = normalize_name(act)
    if normalized in {"default", ""}:
        return "Act 1"
    return act


def selectable_acts_for_mode(mode):
    if mode == "legend":
        return ["Act 1", "Act 2", "Act 3"]
    return ROUTE_ACTS


def select_map(bounds, mode, map_name):
    map_group = MAP_GROUPS[mode]
    log(f"Selecting {map_name}...")
    select_mode_tab(bounds, mode)
    select_ordered_item(bounds, map_group["maps"], map_name, MAP_LIST)


def select_act(bounds, act, reset=True):
    log(f"Selecting {act}...")
    select_ordered_item(bounds, ROUTE_ACTS, act, ACT_LIST, reset=reset)


def click_visible_ordered_item(bounds, geometry, index, label, total_count=None):
    if total_count is None:
        if index > 0 and index % geometry["rows_per_wheel"] == 0:
            scroll(bounds, geometry["scroll_x"], geometry["scroll_y"], 1)
            sleep(LIST_SCROLL_SETTLE)
        row = index % geometry["rows_per_wheel"]
    else:
        previous_scroll_steps = ordered_list_position(index - 1, total_count, geometry)[0] if index > 0 else 0
        scroll_steps, row = ordered_list_position(index, total_count, geometry)
        if scroll_steps > previous_scroll_steps:
            scroll(bounds, geometry["scroll_x"], geometry["scroll_y"], scroll_steps - previous_scroll_steps)
            sleep(LIST_SCROLL_SETTLE)

    log(f"Selecting {label}...")
    click(bounds, geometry["x"], geometry["first_y"] + row * geometry["row_h"], LIST_CLICK_DELAY)


def select_route(bounds, mode, map_name, act):
    select_map(bounds, mode, map_name)
    select_act(bounds, act)
    log(f"Selected {map_name} / {act}.")


def select_acts_for_current_map(bounds, map_name, acts):
    reset_ordered_list(bounds, ACT_LIST)

    if acts == ROUTE_ACTS:
        for index, act in enumerate(acts):
            if index == ACT_LIST["scroll_after_rows"]:
                scroll(bounds, ACT_LIST["scroll_x"], ACT_LIST["scroll_y"], 1)
                sleep(LIST_SCROLL_SETTLE)

            if index == ACT_LIST["infinite_index"]:
                log(f"Selecting {act}...")
                click(bounds, ACT_LIST["infinite_x"], ACT_LIST["infinite_y"], LIST_CLICK_DELAY)
                log(f"Selected {map_name} / {act}.")
                continue
            else:
                row = index if index < ACT_LIST["scroll_after_rows"] else index - ACT_LIST["scroll_after_rows"]
            log(f"Selecting {act}...")
            click(bounds, ACT_LIST["x"], ACT_LIST["first_y"] + row * ACT_LIST["row_h"], LIST_CLICK_DELAY)
            log(f"Selected {map_name} / {act}.")
        return

    for index, act in enumerate(acts):
        click_visible_ordered_item(bounds, ACT_LIST, index, act)
        log(f"Selected {map_name} / {act}.")


def sweep_story_maps(bounds, acts):
    for page in STORY_MAP_PAGES:
        if page["scrolls"]:
            scroll(bounds, MAP_LIST["scroll_x"], MAP_LIST["scroll_y"], page["scrolls"])
            sleep(LIST_SCROLL_SETTLE)

        for index in page["indices"]:
            map_name = STORY_MAPS[index]
            row = index - page["first_index"]
            log(f"Selecting {map_name}...")
            click(bounds, MAP_LIST["x"], MAP_LIST["first_y"] + row * MAP_LIST["row_h"], LIST_CLICK_DELAY)
            select_acts_for_current_map(bounds, map_name, acts)


def sweep_routes(bounds, mode):
    map_group = MAP_GROUPS[mode]
    acts = selectable_acts_for_mode(mode)

    select_mode_tab(bounds, mode)
    reset_ordered_list(bounds, MAP_LIST)

    if map_group["maps"] == STORY_MAPS:
        sweep_story_maps(bounds, acts)
    else:
        for index, map_name in enumerate(map_group["maps"]):
            click_visible_ordered_item(bounds, MAP_LIST, index, map_name, len(map_group["maps"]))
            select_acts_for_current_map(bounds, map_name, acts)

    log(f"Finished selecting {len(map_group['maps']) * len(acts)} route combinations.")


def run(
    bounds,
    mode,
    map_name,
    act,
    sweep_routes_enabled=False,
    normalize_namek_camera=False,
    capture_namek_spawn=False,
    spawn_template_map=None,
    test_namek_spawn=False,
    spawn_test_attempts=100,
    record_movement_enabled=False,
    play_movement_enabled=False,
):
    mode = canonical_mode(mode)
    act = canonical_act(mode, act)

    if normalize_namek_camera:
        normalize_planet_namek_camera(bounds, spawn_template_map)
        return

    if capture_namek_spawn:
        capture_namek_spawn_anchor(bounds, spawn_template_map)
        return

    if test_namek_spawn:
        test_namek_spawn_detector(bounds, spawn_template_map, spawn_test_attempts)
        return

    if record_movement_enabled:
        record_movement(bounds)
        return

    if play_movement_enabled:
        play_movement(bounds)
        return

    focus_roblox()
    sleep(0.45)

    # Close chat/player list if visible, then close the daily reward style popup if present.
    log("Closing lobby overlays...")
    click(bounds, 636, 83, 0.45)
    click(bounds, 606, 184, 0.45)

    # Open Areas from the left rail.
    log("Opening Areas...")
    click(bounds, 66, 292, 0.55)
    click(bounds, 66, 292, 0.65)

    # Search for Story, then click the Story result tile.
    search_term = AREA_SEARCH_TERMS[mode]
    log(f"Searching {search_term.title()}...")
    click(bounds, 400, 118, 0.25)
    clear_text_field()
    type_text(search_term)
    sleep(0.55)
    log(f"Entering {search_term.title()} area...")
    click(bounds, 66, 352, 0.45)
    sleep(2.0)

    focus_roblox()
    log("Walking to Fractures menu...")
    hold_scan(SCAN_W, 0.4)
    hold_scan(SCAN_A, 4.5)
    sleep(0.5)

    log("Opening Create Match...")
    click(bounds, 82, 270, 0.9)

    if sweep_routes_enabled:
        sweep_routes(bounds, mode)
    else:
        select_route(bounds, mode, map_name, act)


def main():
    parser = argparse.ArgumentParser(description="Open the Story area from the Anime Vanguards lobby.")
    parser.add_argument("--x", type=int, required=True)
    parser.add_argument("--y", type=int, required=True)
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--height", type=int, required=True)
    parser.add_argument("--mode", default="story")
    parser.add_argument("--map", default="Lebereo Raid")
    parser.add_argument("--act", default="Act 2")
    parser.add_argument("--sweep-routes", action="store_true")
    parser.add_argument("--normalize-namek-camera", action="store_true")
    parser.add_argument("--capture-namek-spawn-anchor", action="store_true")
    parser.add_argument("--spawn-template-map", default=PLANET_NAMEK_CAMERA["spawn_template_map"])
    parser.add_argument("--test-namek-spawn-detector", action="store_true")
    parser.add_argument("--spawn-test-attempts", type=int, default=100)
    parser.add_argument("--record-movement", action="store_true")
    parser.add_argument("--play-movement", action="store_true")
    args = parser.parse_args()

    run(
        {"x": args.x, "y": args.y, "width": args.width, "height": args.height},
        args.mode,
        args.map,
        args.act,
        args.sweep_routes,
        args.normalize_namek_camera,
        args.capture_namek_spawn_anchor,
        args.spawn_template_map,
        args.test_namek_spawn_detector,
        args.spawn_test_attempts,
        args.record_movement,
        args.play_movement,
    )
    print("Started route flow.", flush=True)


if __name__ == "__main__":
    main()
