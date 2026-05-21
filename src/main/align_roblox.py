import argparse
import ctypes
import os
from ctypes import wintypes


SW_RESTORE = 9
HWND_TOP = 0
SWP_SHOWWINDOW = 0x0040
GWL_STYLE = -16
GWL_EXSTYLE = -20
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]

user32.EnumWindows.argtypes = [EnumWindowsProc, wintypes.LPARAM]
user32.EnumWindows.restype = wintypes.BOOL
user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
user32.GetWindowTextLengthW.restype = ctypes.c_int
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowTextW.restype = ctypes.c_int
user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetClassNameW.restype = ctypes.c_int
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.IsWindowVisible.restype = wintypes.BOOL
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD
user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
user32.GetWindowLongW.restype = ctypes.c_long
user32.AdjustWindowRectEx.argtypes = [ctypes.POINTER(RECT), ctypes.c_long, wintypes.BOOL, ctypes.c_long]
user32.AdjustWindowRectEx.restype = wintypes.BOOL
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.ShowWindow.restype = wintypes.BOOL
user32.BringWindowToTop.argtypes = [wintypes.HWND]
user32.BringWindowToTop.restype = wintypes.BOOL
user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.SetForegroundWindow.restype = wintypes.BOOL
user32.SetWindowPos.argtypes = [
    wintypes.HWND,
    wintypes.HWND,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_uint,
]
user32.SetWindowPos.restype = wintypes.BOOL
kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.QueryFullProcessImageNameW.argtypes = [
    wintypes.HANDLE,
    wintypes.DWORD,
    wintypes.LPWSTR,
    ctypes.POINTER(wintypes.DWORD),
]
kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL


def get_window_text(hwnd):
    length = user32.GetWindowTextLengthW(hwnd)
    if length <= 0:
        return ""

    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, length + 1)
    return buffer.value


def get_class_name(hwnd):
    buffer = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buffer, len(buffer))
    return buffer.value


def get_window_process_id(hwnd):
    process_id = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
    return process_id.value


def get_process_image_name(process_id):
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, process_id)
    if not handle:
        return ""

    try:
        size = wintypes.DWORD(1024)
        buffer = ctypes.create_unicode_buffer(size.value)
        ok = kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size))
        return buffer.value if ok else ""
    finally:
        kernel32.CloseHandle(handle)


def is_roblox_window(hwnd):
    process_id = get_window_process_id(hwnd)
    image_name = get_process_image_name(process_id)
    executable = os.path.basename(image_name).lower()
    return executable == "robloxplayerbeta.exe"


def find_roblox_window():
    matches = []

    @EnumWindowsProc
    def callback(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True

        if is_roblox_window(hwnd):
            matches.append(hwnd)
            return False

        return True

    user32.EnumWindows(callback, 0)
    return matches[0] if matches else None


def align_window(hwnd, x, y, width, height):
    user32.ShowWindow(hwnd, SW_RESTORE)
    style = user32.GetWindowLongW(hwnd, GWL_STYLE)
    ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    outer_rect = RECT(x, y, x + width, y + height)

    adjusted = user32.AdjustWindowRectEx(ctypes.byref(outer_rect), style, False, ex_style)
    if not adjusted:
        error_code = ctypes.get_last_error()
        raise OSError(error_code, "AdjustWindowRectEx failed")

    moved = user32.SetWindowPos(
        hwnd,
        HWND_TOP,
        outer_rect.left,
        outer_rect.top,
        outer_rect.right - outer_rect.left,
        outer_rect.bottom - outer_rect.top,
        SWP_SHOWWINDOW,
    )
    if not moved:
        error_code = ctypes.get_last_error()
        raise OSError(error_code, "SetWindowPos failed")

    user32.BringWindowToTop(hwnd)
    user32.SetForegroundWindow(hwnd)


def main():
    parser = argparse.ArgumentParser(description="Align the Roblox client area to a target rectangle.")
    parser.add_argument("--x", type=int, required=True)
    parser.add_argument("--y", type=int, required=True)
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--height", type=int, required=True)
    args = parser.parse_args()

    hwnd = find_roblox_window()
    if not hwnd:
        raise SystemExit("Roblox window was not found.")

    align_window(hwnd, args.x, args.y, args.width, args.height)
    print(f"Aligned Roblox client area to {args.x},{args.y} {args.width} x {args.height}")


if __name__ == "__main__":
    main()
