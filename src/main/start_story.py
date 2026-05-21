import argparse
import ctypes
import sys
import time
from ctypes import wintypes

from align_roblox import find_roblox_window, user32, SW_RESTORE


MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_WHEEL = 0x0800
KEYEVENTF_KEYUP = 0x0002
VK_CONTROL = 0x11
VK_A = 0x41
VK_BACK = 0x08
VK_W = 0x57
INPUT_KEYBOARD = 1
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_SCANCODE = 0x0008
SCAN_W = 0x11
SCAN_A = 0x1E

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

ACT_LIST = {
    "x": 360,
    "first_y": 249,
    "row_h": 41,
    "visible_rows": 5,
    "scroll_x": 370,
    "scroll_y": 328,
    "rows_per_wheel": 2,
}

user32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
user32.SetCursorPos.restype = wintypes.BOOL
user32.mouse_event.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, ctypes.c_int, ctypes.POINTER(ctypes.c_ulong)]
user32.mouse_event.restype = None
user32.keybd_event.argtypes = [ctypes.c_ubyte, ctypes.c_ubyte, wintypes.DWORD, ctypes.POINTER(ctypes.c_ulong)]
user32.keybd_event.restype = None

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
    sleep(0.12)
    user32.mouse_event(MOUSEEVENTF_MOVE, 1, 0, 0, None)
    sleep(0.04)
    user32.mouse_event(MOUSEEVENTF_MOVE, -1, 0, 0, None)
    sleep(0.08)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, None)
    sleep(0.08)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, None)
    sleep(delay)


def scroll(bounds, x, y, steps, delay=0.18):
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
    sleep(0.2)


def select_ordered_item(bounds, options, target, geometry, reset=True):
    if reset:
        reset_ordered_list(bounds, geometry)

    target_index = find_index(options, target)
    if target_index is None:
        raise ValueError(f"Unknown option: {target}")

    if target_index > 0:
        scroll_steps = target_index // geometry["rows_per_wheel"]
        scroll(bounds, geometry["scroll_x"], geometry["scroll_y"], scroll_steps)
        sleep(0.35)

    row = target_index % geometry["rows_per_wheel"]
    click(bounds, geometry["x"], geometry["first_y"] + row * geometry["row_h"], 0.45)


def select_mode_tab(bounds, mode):
    tab = MAP_GROUPS[mode]["tab"]
    if tab:
        click(bounds, tab[0], tab[1], 0.45)


def key_down(vk):
    user32.keybd_event(vk, 0, 0, None)


def key_up(vk):
    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, None)


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


def click_visible_ordered_item(bounds, geometry, index, label):
    if index > 0 and index % geometry["rows_per_wheel"] == 0:
        scroll(bounds, geometry["scroll_x"], geometry["scroll_y"], 1)
        sleep(0.25)

    row = index % geometry["rows_per_wheel"]
    log(f"Selecting {label}...")
    click(bounds, geometry["x"], geometry["first_y"] + row * geometry["row_h"], 0.45)


def select_route(bounds, mode, map_name, act):
    select_map(bounds, mode, map_name)
    select_act(bounds, act)
    log(f"Selected {map_name} / {act}.")


def select_acts_for_current_map(bounds, map_name, acts):
    reset_ordered_list(bounds, ACT_LIST)

    for index, act in enumerate(acts):
        click_visible_ordered_item(bounds, ACT_LIST, index, act)
        log(f"Selected {map_name} / {act}.")


def sweep_routes(bounds, mode):
    map_group = MAP_GROUPS[mode]
    acts = selectable_acts_for_mode(mode)

    select_mode_tab(bounds, mode)
    reset_ordered_list(bounds, MAP_LIST)

    for index, map_name in enumerate(map_group["maps"]):
        click_visible_ordered_item(bounds, MAP_LIST, index, map_name)
        select_acts_for_current_map(bounds, map_name, acts)

    log(f"Finished selecting {len(map_group['maps']) * len(acts)} route combinations.")


def run(bounds, mode, map_name, act, sweep_routes_enabled=False):
    mode = canonical_mode(mode)
    act = canonical_act(mode, act)

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
    args = parser.parse_args()

    run(
        {"x": args.x, "y": args.y, "width": args.width, "height": args.height},
        args.mode,
        args.map,
        args.act,
        args.sweep_routes,
    )
    print("Started route flow.", flush=True)


if __name__ == "__main__":
    main()
