import argparse
import ctypes
import json
import os
import random
import re
import struct
import subprocess
import sys
import time
import zlib
from ctypes import wintypes

from align_roblox import find_roblox_window, user32, SW_RESTORE


gdi32 = ctypes.windll.gdi32
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SPAWN_TEMPLATE_DIR = os.path.join(PROJECT_ROOT, "data", "vision", "spawn-anchors")
MOVEMENT_DIR = os.path.join(PROJECT_ROOT, "data", "vision", "movement")
HUD_DEBUG_DIR = os.path.join(PROJECT_ROOT, "data", "vision", "debug", "hud")
WIN_OCR_SCRIPT = os.path.join(os.path.dirname(__file__), "win_ocr.ps1")

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
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
    "look_down_drag_x": 400,
    "look_down_start_y": 220,
    "look_down_end_y": 560,
    "look_down_steps": 14,
    "look_down_repeats": 1,
    "look_down_relative_dy": 70,
    "settings_x": 20,
    "settings_y": 580,
    "settings_open_delay": 0.75,
    "settings_close_x": 690,
    "settings_close_y": 150,
    "teleport_spawn_x": 648,
    "teleport_spawn_y": 292,
    "restart_match_x": 648,
    "restart_match_y": 264,
    "restart_confirm_yes_x": 352,
    "restart_confirm_yes_y": 331,
    "restart_alert_cancel_x": 410,
    "restart_alert_cancel_y": 328,
    "restart_alert_delay": 1.0,
    "match_start_x": 439,
    "match_start_y": 429,
    "match_confirm_start_x": 58,
    "match_confirm_start_y": 400,
    "match_load_timeout": 90,
    "match_loaded_check_x": 650,
    "match_loaded_check_y": 220,
    "match_loaded_check_w": 145,
    "match_loaded_check_h": 175,
    "match_loaded_threshold": 0.025,
    "chat_toggle_x": 165,
    "chat_toggle_y": 38,
    "chat_input_x": 8,
    "chat_input_y": 20,
    "chat_input_w": 232,
    "chat_input_h": 34,
    "chat_input_step": 6,
    "chat_input_dark_threshold": 0.68,
    "vote_start_yes_x": 460,
    "vote_start_yes_y": 95,
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
    "place_random_min_x": 250,
    "place_random_max_x": 650,
    "place_random_min_y": 115,
    "place_random_max_y": 430,
    "place_attempts": 40,
    "place_hover_delay": 0.04,
    "place_hover_wiggle_px": 2,
    "place_click_delay": 0.04,
    "place_confirm_delay": 0.06,
    "place_invalid_message_x": 250,
    "place_invalid_message_y": 65,
    "place_invalid_message_w": 310,
    "place_invalid_message_h": 34,
    "place_invalid_cursor_w": 56,
    "place_invalid_cursor_h": 56,
    "place_invalid_step": 4,
    "place_invalid_red_threshold": 0.018,
    "unit_panel_x": 10,
    "unit_panel_y": 105,
    "unit_panel_w": 150,
    "unit_panel_h": 170,
    "unit_panel_step": 16,
    "unit_panel_dark_threshold": 0.16,
    "unit_panel_saturated_threshold": 0.025,
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

HUD_OCR = {
    "wave": {"x": 224, "y": 14, "width": 118, "height": 28, "scales": [6, 8]},
    "money": {"x": 370, "y": 502, "width": 54, "height": 20, "scales": [6, 8, 10, 12]},
    "unit_costs": [
        {"slot": "Slot 1", "x": 232, "y": 552, "width": 58, "height": 22, "scales": [6, 8, 10, 12, 16]},
        {"slot": "Slot 2", "x": 288, "y": 548, "width": 68, "height": 30, "scales": [6, 8, 10, 12, 16]},
        {"slot": "Slot 3", "x": 340, "y": 552, "width": 70, "height": 22, "scales": [6, 8, 10, 12, 16]},
        {"slot": "Slot 4", "x": 404, "y": 552, "width": 64, "height": 22, "scales": [6, 8, 10, 12, 16]},
        {"slot": "Slot 5", "x": 462, "y": 550, "width": 64, "height": 26, "scales": [6, 8, 10, 12, 16]},
        {"slot": "Slot 6", "x": 526, "y": 552, "width": 58, "height": 22, "scales": [6, 8, 10, 12, 16]},
    ],
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
    text = str(message)
    try:
        print(text, flush=True)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        safe_text = text.encode(encoding, errors="replace").decode(encoding, errors="replace")
        print(safe_text, flush=True)


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


def click_fast(bounds, x, y, delay=0.04):
    sx, sy = screen_point(bounds, x, y)
    user32.SetCursorPos(sx, sy)
    sleep(0.015)
    wiggle_cursor(1)
    sleep(0.015)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, None)
    sleep(0.025)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, None)
    sleep(delay)


def move_to(bounds, x, y):
    sx, sy = screen_point(bounds, x, y)
    user32.SetCursorPos(sx, sy)


def wiggle_cursor(pixels=1):
    user32.mouse_event(MOUSEEVENTF_MOVE, pixels, 0, 0, None)
    sleep(0.02)
    user32.mouse_event(MOUSEEVENTF_MOVE, -pixels, 0, 0, None)


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


def drag_right(bounds, start_x, start_y, end_x, end_y, steps=20, delay=0.01):
    sx, sy = screen_point(bounds, start_x, start_y)
    ex, ey = screen_point(bounds, end_x, end_y)
    user32.SetCursorPos(sx, sy)
    sleep(0.08)
    user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, None)
    sleep(0.05)
    for step in range(1, steps + 1):
        x = sx + int((ex - sx) * step / steps)
        y = sy + int((ey - sy) * step / steps)
        user32.SetCursorPos(x, y)
        sleep(delay)
    user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, None)
    sleep(0.15)


def drag_right_relative(bounds, x, y, dx, dy, steps=20, delay=0.01):
    sx, sy = screen_point(bounds, x, y)
    user32.SetCursorPos(sx, sy)
    sleep(0.08)
    user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, None)
    sleep(0.05)
    for _ in range(steps):
        user32.mouse_event(MOUSEEVENTF_MOVE, dx, dy, 0, None)
        sleep(delay)
    user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, None)
    user32.mouse_event(MOUSEEVENTF_MOVE, 0, 0, 0, None)
    sleep(0.35)


def pitch_camera_down(bounds):
    log("Pitching camera down...")
    for _ in range(PLANET_NAMEK_CAMERA["look_down_repeats"]):
        drag_right_relative(
            bounds,
            PLANET_NAMEK_CAMERA["look_down_drag_x"],
            PLANET_NAMEK_CAMERA["look_down_start_y"],
            0,
            PLANET_NAMEK_CAMERA["look_down_relative_dy"],
            PLANET_NAMEK_CAMERA["look_down_steps"],
        )


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
    close_match_chat(bounds)
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
    pitch_camera_down(bounds)

    place_temporary_camera_unit(bounds)
    click(bounds, PLANET_NAMEK_CAMERA["unit_view_x"], PLANET_NAMEK_CAMERA["unit_view_y"], 0.45)
    click(bounds, PLANET_NAMEK_CAMERA["view_left_x"], PLANET_NAMEK_CAMERA["view_left_y"], 0.45)
    click(bounds, PLANET_NAMEK_CAMERA["view_exit_x"], PLANET_NAMEK_CAMERA["view_exit_y"], 0.35)
    log("Selling temporary camera unit...")
    tap_scan(PLANET_NAMEK_CAMERA["sell_unit_scan"])


def region_color_ratios(bounds, x, y, width, height, step):
    hdc = user32.GetDC(None)
    if not hdc:
        raise OSError("GetDC failed")

    dark = 0
    saturated = 0
    samples = 0
    try:
        for py in range(y, y + height, step):
            for px in range(x, x + width, step):
                sx, sy = screen_point(bounds, px, py)
                red, green, blue = colorref_to_rgb(gdi32.GetPixel(hdc, sx, sy))
                samples += 1
                if red <= 45 and green <= 45 and blue <= 55:
                    dark += 1
                if max(red, green, blue) >= 115 and max(red, green, blue) - min(red, green, blue) >= 55:
                    saturated += 1
    finally:
        user32.ReleaseDC(None, hdc)

    if not samples:
        return 0, 0
    return dark / samples, saturated / samples


def is_unit_panel_open(bounds):
    dark_ratio, saturated_ratio = region_color_ratios(
        bounds,
        PLANET_NAMEK_CAMERA["unit_panel_x"],
        PLANET_NAMEK_CAMERA["unit_panel_y"],
        PLANET_NAMEK_CAMERA["unit_panel_w"],
        PLANET_NAMEK_CAMERA["unit_panel_h"],
        PLANET_NAMEK_CAMERA["unit_panel_step"],
    )
    return (
        dark_ratio >= PLANET_NAMEK_CAMERA["unit_panel_dark_threshold"]
        and saturated_ratio >= PLANET_NAMEK_CAMERA["unit_panel_saturated_threshold"]
    )


def red_pixel_ratio(bounds, x, y, width, height, step):
    hdc = user32.GetDC(None)
    if not hdc:
        raise OSError("GetDC failed")

    red_pixels = 0
    samples = 0
    try:
        for py in range(y, y + height, step):
            for px in range(x, x + width, step):
                sx, sy = screen_point(bounds, px, py)
                red, green, blue = colorref_to_rgb(gdi32.GetPixel(hdc, sx, sy))
                samples += 1
                if red >= 145 and green <= 80 and blue <= 90:
                    red_pixels += 1
    finally:
        user32.ReleaseDC(None, hdc)

    return red_pixels / samples if samples else 0


def has_invalid_place_feedback(bounds, x, y):
    cursor_ratio = red_pixel_ratio(
        bounds,
        x - PLANET_NAMEK_CAMERA["place_invalid_cursor_w"] // 2,
        y - PLANET_NAMEK_CAMERA["place_invalid_cursor_h"] // 2,
        PLANET_NAMEK_CAMERA["place_invalid_cursor_w"],
        PLANET_NAMEK_CAMERA["place_invalid_cursor_h"],
        PLANET_NAMEK_CAMERA["place_invalid_step"],
    )
    message_ratio = red_pixel_ratio(
        bounds,
        PLANET_NAMEK_CAMERA["place_invalid_message_x"],
        PLANET_NAMEK_CAMERA["place_invalid_message_y"],
        PLANET_NAMEK_CAMERA["place_invalid_message_w"],
        PLANET_NAMEK_CAMERA["place_invalid_message_h"],
        PLANET_NAMEK_CAMERA["place_invalid_step"],
    )
    return max(cursor_ratio, message_ratio) >= PLANET_NAMEK_CAMERA["place_invalid_red_threshold"]


def move_to_viewport_point(bounds, x, y):
    sx, sy = screen_point(bounds, x, y)
    user32.SetCursorPos(sx, sy)


def hover_unit_place_point(bounds, x, y):
    move_to_viewport_point(bounds, x, y)
    sleep(0.04)
    wiggle_cursor(PLANET_NAMEK_CAMERA["place_hover_wiggle_px"])
    sleep(PLANET_NAMEK_CAMERA["place_hover_delay"])


def random_unit_place_point():
    return (
        random.randint(PLANET_NAMEK_CAMERA["place_random_min_x"], PLANET_NAMEK_CAMERA["place_random_max_x"]),
        random.randint(PLANET_NAMEK_CAMERA["place_random_min_y"], PLANET_NAMEK_CAMERA["place_random_max_y"]),
    )


def place_temporary_camera_unit(bounds):
    max_attempts = PLANET_NAMEK_CAMERA["place_attempts"]
    first_point = (PLANET_NAMEK_CAMERA["place_x"], PLANET_NAMEK_CAMERA["place_y"])
    log("Placing cheapest unit from slot 5...")

    for attempt in range(1, max_attempts + 1):
        x, y = first_point if attempt == 1 else random_unit_place_point()
        tap_scan_fast(PLANET_NAMEK_CAMERA["place_slot_scan"])
        hover_unit_place_point(bounds, x, y)
        log(f"Trying temporary unit placement ({attempt}/{max_attempts}) at ({x}, {y})...")
        click_fast(bounds, x, y, PLANET_NAMEK_CAMERA["place_click_delay"])
        sleep(PLANET_NAMEK_CAMERA["place_confirm_delay"])
        if is_unit_panel_open(bounds):
            log("Temporary unit placed and selected.")
            return

    raise RuntimeError("Could not place the temporary camera unit after multiple random attempts.")


def test_temporary_unit_placement(bounds):
    log("Testing temporary unit placement...")
    focus_roblox()
    close_match_chat(bounds)
    place_temporary_camera_unit(bounds)
    sleep(0.2)
    log("Selling test unit...")
    tap_scan_fast(PLANET_NAMEK_CAMERA["sell_unit_scan"])
    log("Temporary unit placement test finished.")


def is_chat_open(bounds):
    dark_ratio, _ = region_color_ratios(
        bounds,
        PLANET_NAMEK_CAMERA["chat_input_x"],
        PLANET_NAMEK_CAMERA["chat_input_y"],
        PLANET_NAMEK_CAMERA["chat_input_w"],
        PLANET_NAMEK_CAMERA["chat_input_h"],
        PLANET_NAMEK_CAMERA["chat_input_step"],
    )
    log(f"Chat input score: {dark_ratio:.2f}")
    return dark_ratio >= PLANET_NAMEK_CAMERA["chat_input_dark_threshold"]


def close_match_chat(bounds):
    if not is_chat_open(bounds):
        return
    log("Closing in-match chat...")
    click(bounds, PLANET_NAMEK_CAMERA["chat_toggle_x"], PLANET_NAMEK_CAMERA["chat_toggle_y"], 0.35)


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
            total = "infinite" if max_attempts is None else str(max_attempts)
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


def restart_match(bounds):
    log("Restarting match from settings...")
    open_settings(bounds)
    try:
        click(bounds, PLANET_NAMEK_CAMERA["restart_match_x"], PLANET_NAMEK_CAMERA["restart_match_y"], 0.6)
        log("Confirming restart vote...")
        click(
            bounds,
            PLANET_NAMEK_CAMERA["restart_confirm_yes_x"],
            PLANET_NAMEK_CAMERA["restart_confirm_yes_y"],
            0.6,
        )
    finally:
        close_settings(bounds)
    sleep(PLANET_NAMEK_CAMERA["restart_alert_delay"])
    log("Closing restart alert...")
    click(
        bounds,
        PLANET_NAMEK_CAMERA["restart_alert_cancel_x"],
        PLANET_NAMEK_CAMERA["restart_alert_cancel_y"],
        0.35,
    )
    log("Restart requested.")


def click_match_start(bounds):
    log("Starting selected match...")
    click(bounds, PLANET_NAMEK_CAMERA["match_start_x"], PLANET_NAMEK_CAMERA["match_start_y"], 0.8)
    log("Confirming match start...")
    click(bounds, PLANET_NAMEK_CAMERA["match_confirm_start_x"], PLANET_NAMEK_CAMERA["match_confirm_start_y"], 0.8)


def is_match_loaded(bounds):
    x = PLANET_NAMEK_CAMERA["match_loaded_check_x"]
    y = PLANET_NAMEK_CAMERA["match_loaded_check_y"]
    width = PLANET_NAMEK_CAMERA["match_loaded_check_w"]
    height = PLANET_NAMEK_CAMERA["match_loaded_check_h"]
    hdc = user32.GetDC(None)
    if not hdc:
        raise OSError("GetDC failed")

    matches = 0
    samples = 0
    try:
        for py in range(y, y + height, 5):
            for px in range(x, x + width, 5):
                sx, sy = screen_point(bounds, px, py)
                red, green, blue = colorref_to_rgb(gdi32.GetPixel(hdc, sx, sy))
                samples += 1
                is_match_panel_color = (
                    (green >= 115 and blue >= 115 and red <= 80)
                    or (red >= 140 and green <= 90 and blue <= 100)
                    or (red >= 150 and green >= 120 and blue <= 80)
                    or (blue >= 130 and red <= 100 and green <= 140)
                )
                if is_match_panel_color:
                    matches += 1
    finally:
        user32.ReleaseDC(None, hdc)

    score = matches / samples if samples else 0
    log(f"Match loaded score: {score:.2f}")
    return score >= PLANET_NAMEK_CAMERA["match_loaded_threshold"]


def wait_for_match_loaded(bounds):
    timeout = PLANET_NAMEK_CAMERA["match_load_timeout"]
    log("Waiting for match UI to load...")
    deadline = time.perf_counter() + timeout
    while time.perf_counter() < deadline:
        if is_match_loaded(bounds):
            log("Match loaded.")
            return
        sleep(1.0)
    raise RuntimeError("Timed out waiting for match UI to load.")


def click_vote_start(bounds):
    log("Clicking Vote Start yes...")
    click(bounds, PLANET_NAMEK_CAMERA["vote_start_yes_x"], PLANET_NAMEK_CAMERA["vote_start_yes_y"], 0.45)


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


def crop_rgb_rows(rows, x, y, width, height):
    return [row[x * 3 : (x + width) * 3] for row in rows[y : y + height]]


def scale_rgb_rows(rows, width, scale):
    if scale <= 1:
        return width, len(rows), rows

    scaled_rows = []
    for row in rows:
        scaled_row = bytearray()
        for index in range(width):
            pixel = row[index * 3 : index * 3 + 3]
            for _ in range(scale):
                scaled_row.extend(pixel)
        for _ in range(scale):
            scaled_rows.append(bytes(scaled_row))

    return width * scale, len(rows) * scale, scaled_rows


def high_contrast_ocr_rows(rows, width, mode="yellow"):
    processed = []
    for row in rows:
        output = bytearray()
        for index in range(width):
            offset = index * 3
            red = row[offset]
            green = row[offset + 1]
            blue = row[offset + 2]
            if mode == "dim-yellow":
                is_text = (
                    red >= 38
                    and green >= 25
                    and blue <= 70
                    and red >= green + 2
                    and green >= blue + 6
                    and not (red > 210 and green > 170 and blue < 90)
                )
            elif mode == "dark":
                is_text = red < 135 and green < 105 and blue < 70 and red + green + blue < 260
            else:
                is_yellow_text = red >= 135 and green >= 95 and blue <= 135 and red >= blue + 30
                is_white_text = red >= 170 and green >= 170 and blue >= 170
                is_text = is_yellow_text or is_white_text

            if is_text:
                output.extend((255, 255, 255))
            else:
                output.extend((0, 0, 0))
        processed.append(bytes(output))
    return processed


def write_scaled_crop(path, crop_rows, width, scale):
    scaled_width, scaled_height, scaled_rows = scale_rgb_rows(crop_rows, width, scale)
    write_png(path, scaled_width, scaled_height, scaled_rows)
    return path


def write_ocr_crop(name, width, height, rows, region, mode="yellow", scale=8):
    os.makedirs(HUD_DEBUG_DIR, exist_ok=True)
    crop_rows = crop_rgb_rows(rows, region["x"], region["y"], region["width"], region["height"])
    path = os.path.join(HUD_DEBUG_DIR, f"{name}_{mode}_{scale}x.png")
    if mode == "raw":
        return write_scaled_crop(path, crop_rows, region["width"], scale)

    ocr_rows = high_contrast_ocr_rows(crop_rows, region["width"], mode)
    return write_scaled_crop(path, ocr_rows, region["width"], scale)


def read_windows_ocr_text(image_path):
    if not os.path.exists(WIN_OCR_SCRIPT):
        raise RuntimeError(f"Missing OCR helper: {WIN_OCR_SCRIPT}")

    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            WIN_OCR_SCRIPT,
            "-ImagePath",
            image_path,
        ],
        capture_output=True,
        text=True,
        timeout=8,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Windows OCR failed.")
    return " ".join(result.stdout.split())


def parse_compact_number(text):
    spaced = text.upper().translate(str.maketrans({"O": "0", "I": "1", "L": "1"}))
    split_thousands = re.search(r"(\d{2})\s+(\d{2})(?=\D|$)", spaced)
    if split_thousands:
        return int(f"{split_thousands.group(1)}{split_thousands.group(2)}0")

    cleaned = spaced.replace(",", "").replace(" ", "")
    cleaned = re.sub(r"(?<=\d)[/\\|](?=\d)", "", cleaned)
    cleaned = re.sub(r"(?<=\d)[.](?=\d{3}\D|$)", "", cleaned)
    match = re.search(r"(\d+(?:\.\d+)?)([KMB])?", cleaned)
    if not match:
        return None

    value = float(match.group(1))
    suffix = match.group(2)
    has_decimal_short_scale = "." in match.group(1) and len(match.group(1).split(".", 1)[1]) <= 2
    if suffix is None and "." in match.group(1) and len(match.group(1).split(".", 1)[1]) <= 2:
        value = float(match.group(1).replace(".", ""))
    elif suffix == "K" and has_decimal_short_scale:
        value *= 1_000
    elif suffix == "M" and has_decimal_short_scale:
        value *= 1_000_000
    elif suffix == "B" and has_decimal_short_scale:
        value *= 1_000_000_000
    return int(value)


def parse_wave_text(text):
    text = text.upper().translate(str.maketrans({"O": "0", "I": "1", "L": "1", "A": "1", "S": "5"}))
    match = re.search(r"(\d+)\s*/\s*(\d+)", text)
    if match:
        return int(match.group(1)), int(match.group(2))

    match = re.search(r"(\d+)\D+(\d+)", text)
    if match:
        return int(match.group(1)), int(match.group(2))

    numbers = re.findall(r"\d+", text)
    if numbers:
        return int(numbers[0]), int(numbers[1]) if len(numbers) > 1 else None
    return None, None


def digit_count(text):
    return len(re.findall(r"\d", text))


def normalized_digit_count(text):
    normalized = text.upper().translate(str.maketrans({"O": "0", "I": "1", "L": "1"}))
    return len(re.findall(r"\d", normalized))


def choose_best_number(candidates, minimum=None):
    grouped = {}
    for candidate in candidates:
        value = candidate["value"]
        if value is None:
            continue
        if minimum is not None and value < minimum:
            continue
        grouped.setdefault(value, []).append(candidate)

    if not grouped:
        return None

    def score(item):
        value, matches = item
        best_digits = max(match["digits"] for match in matches)
        best_scale_score = max(20 - abs(match["scale"] - 10) for match in matches)
        best_mode_score = max({"raw": 30, "dim-yellow": 10, "dark": 0}.get(match["mode"], 0) for match in matches)
        support = len(matches)
        return support * 1000 + best_digits * 100 + best_scale_score + best_mode_score

    return max(grouped.items(), key=score)[0]


def read_region_number(name, width, height, rows, region, modes, minimum=None):
    raw_texts = {}
    candidates = []
    for mode in modes:
        for scale in region.get("scales", [8]):
            key = f"{mode}_{scale}x"
            path = write_ocr_crop(name, width, height, rows, region, mode=mode, scale=scale)
            text = read_windows_ocr_text(path)
            raw_texts[key] = text
            value = parse_compact_number(text)
            if value is None:
                continue
            candidates.append({"value": value, "digits": normalized_digit_count(text), "scale": scale, "mode": mode})
    return choose_best_number(candidates, minimum=minimum), raw_texts


def read_wave_number(width, height, rows):
    raw_texts = {}
    for mode in ("raw", "yellow"):
        for scale in HUD_OCR["wave"].get("scales", [8]):
            key = f"{mode}_{scale}x"
            path = write_ocr_crop("wave", width, height, rows, HUD_OCR["wave"], mode=mode, scale=scale)
            text = read_windows_ocr_text(path)
            raw_texts[key] = text
            wave, wave_max = parse_wave_text(text)
            if wave is not None:
                return wave, wave_max, raw_texts
    return None, None, raw_texts


def read_hud_state(bounds):
    width, height, rows = capture_viewport_pixels(bounds)
    full_path = os.path.join(HUD_DEBUG_DIR, "viewport.png")
    os.makedirs(HUD_DEBUG_DIR, exist_ok=True)
    write_png(full_path, width, height, rows)

    wave, wave_max, wave_texts = read_wave_number(width, height, rows)
    money, money_texts = read_region_number("money", width, height, rows, HUD_OCR["money"], ["raw"], minimum=1)

    unit_costs = {}
    unit_cost_text = {}
    for region in HUD_OCR["unit_costs"]:
        crop_name = normalize_name(region["slot"])
        cost, texts = read_region_number(crop_name, width, height, rows, region, ["raw", "dim-yellow", "dark"], minimum=1)
        unit_cost_text[region["slot"]] = texts
        unit_costs[region["slot"]] = cost

    return {
        "wave": wave,
        "wave_max": wave_max,
        "money": money,
        "unit_costs": unit_costs,
        "raw_text": {
            "wave": wave_texts,
            "money": money_texts,
            "unit_costs": unit_cost_text,
        },
        "debug_dir": HUD_DEBUG_DIR,
    }


def test_hud_ocr(bounds):
    log("Reading HUD with Windows OCR...")
    focus_roblox()
    state = read_hud_state(bounds)
    log(f"HUD wave: {state['wave']}/{state['wave_max']} raw={state['raw_text']['wave']!r}")
    log(f"HUD money: {state['money']} raw={state['raw_text']['money']!r}")
    for slot, cost in state["unit_costs"].items():
        raw = state["raw_text"]["unit_costs"][slot]
        log(f"HUD {slot} cost: {cost} raw={raw!r}")
    log(f"HUD OCR debug crops: {state['debug_dir']}")


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


def tap_scan_fast(scan_code):
    send_scan(scan_code, False)
    sleep(0.025)
    send_scan(scan_code, True)
    sleep(0.045)


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
    post_route_namek_setup=False,
    pitch_camera_down_enabled=False,
    test_unit_placement_enabled=False,
    test_hud_ocr_enabled=False,
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

    if pitch_camera_down_enabled:
        focus_roblox()
        pitch_camera_down(bounds)
        return

    if test_unit_placement_enabled:
        test_temporary_unit_placement(bounds)
        return

    if test_hud_ocr_enabled:
        test_hud_ocr(bounds)
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

    if post_route_namek_setup:
        click_match_start(bounds)
        wait_for_match_loaded(bounds)
        close_match_chat(bounds)
        click_vote_start(bounds)
        normalize_planet_namek_camera(bounds, spawn_template_map)
        play_movement(bounds)
        restart_match(bounds)


def main():
    parser = argparse.ArgumentParser(description="Open the Story area from the Anime Vanguards lobby.")
    parser.add_argument("--x", type=int, required=True)
    parser.add_argument("--y", type=int, required=True)
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--height", type=int, required=True)
    parser.add_argument("--mode", default="story")
    parser.add_argument("--map", default="Planet Namak")
    parser.add_argument("--act", default="Act 1")
    parser.add_argument("--sweep-routes", action="store_true")
    parser.add_argument("--normalize-namek-camera", action="store_true")
    parser.add_argument("--capture-namek-spawn-anchor", action="store_true")
    parser.add_argument("--spawn-template-map", default=PLANET_NAMEK_CAMERA["spawn_template_map"])
    parser.add_argument("--test-namek-spawn-detector", action="store_true")
    parser.add_argument("--spawn-test-attempts", type=int, default=100)
    parser.add_argument("--record-movement", action="store_true")
    parser.add_argument("--play-movement", action="store_true")
    parser.add_argument("--post-route-namek-setup", action="store_true")
    parser.add_argument("--pitch-camera-down", action="store_true")
    parser.add_argument("--test-unit-placement", action="store_true")
    parser.add_argument("--test-hud-ocr", action="store_true")
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
        args.post_route_namek_setup,
        args.pitch_camera_down,
        args.test_unit_placement,
        args.test_hud_ocr,
    )
    print("Started route flow.", flush=True)


if __name__ == "__main__":
    main()
