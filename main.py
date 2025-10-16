import logging
import traceback
import ctypes
import os
import sys
import tkinter as tk
from ctypes import wintypes
from ui.app import App
from tkinter import messagebox
from core.utils import resource_path

# (ログの設定は省略)

def show_error_and_exit(message):
    """エラーメッセージボックスを表示してプログラムを終了する関数"""
    root = tk.Tk()
    root.withdraw()  # 空白のウィンドウが表示されるのを防ぐ
    messagebox.showerror("Startup failure", message)
    root.destroy()



class SingleInstance:
    """ミューテックスを使用して二重起動を防止するクラス"""

    def __init__(self, name):
        self.mutex = None
        self.mutex_name = name

        kernel32 = ctypes.windll.kernel32
        
        # Win32 API関数の引数と戻り値の型を定義
        CreateMutexW = kernel32.CreateMutexW
        CreateMutexW.argtypes = [wintypes.LPCVOID, wintypes.BOOL, wintypes.LPCWSTR]
        CreateMutexW.restype = wintypes.HANDLE

        GetLastError = kernel32.GetLastError
        GetLastError.restype = wintypes.DWORD

        # ミューテックスを作成
        self.mutex = CreateMutexW(None, False, self.mutex_name)

        # すでにミューテックスが存在するかどうかを確認
        self.already_exists = GetLastError() == 183  # ERROR_ALREADY_EXISTS

    def __del__(self):
        # アプリ終了時にミューテックスを解放
        if self.mutex:
            kernel32 = ctypes.windll.kernel32
            CloseHandle = kernel32.CloseHandle
            CloseHandle.argtypes = [wintypes.HANDLE]
            CloseHandle.restype = wintypes.BOOL
            CloseHandle(self.mutex)

def main():


    # 世界中でユニークなミューテックス名を指定 (上記で生成したUUIDに置き換える)
    mutex_name = "MyAiPal-0accbca9-2415-482f-a0a6-56ddcea38158"
    instance = SingleInstance(mutex_name)

    if instance.already_exists:
        # 既存のインスタンスがすでに存在する場合
        print("アプリはすでに起動しています。")
        # お好みでメッセージボックスを表示しても良い
        # show_error_and_exit("アプリはすでに起動しています。") 
        return  # プログラムを終了


    steam_api = None
    try:
        # dll_path = os.path.join(os.path.dirname(__file__), "steam_api64.dll")
        dll_path = resource_path("steam_api64.dll")
        steam_api = ctypes.cdll.LoadLibrary(dll_path)

        init_func = steam_api.SteamAPI_InitFlat
        init_func.restype = ctypes.c_bool

        if init_func():
            try:
                print("Steamの利用資格があります。アプリを起動します。")
                app = App()
                print("start mainloop")
                app.mainloop()

            except Exception as e:
                # 予期せぬエラーが発生した場合、ログに詳細を記録
                logging.error("An unhandled exception occurred.")
                logging.error(traceback.format_exc()) # これがエラーの詳細

        else:
            try:
                print("Steamの利用資格があります。アプリを起動します。")
                app = App()
                print("start mainloop")
                app.mainloop()

            except Exception as e:
                # 予期せぬエラーが発生した場合、ログに詳細を記録
                logging.error("An unhandled exception occurred.")
                logging.error(traceback.format_exc()) # これがエラーの詳細
            # --- ここが変更点 ---
            # error_message = "Your Steam credentials could not be verified.\nPlease make sure Steam is running."
            # print(error_message)
            # show_error_and_exit(error_message)
            # return

    except FileNotFoundError:
        error_message = "steam_api64.dll not found."
        print(error_message)
        show_error_and_exit(error_message)
    except Exception as e:
        error_message = f"An unexpected error has occurred: {e}"
        print(error_message)
        logging.error(traceback.format_exc())
        show_error_and_exit(error_message)

    finally:
        if steam_api:
            shutdown_func = getattr(steam_api, 'SteamAPI_ShutdownFlat', getattr(steam_api, 'SteamAPI_Shutdown', None))
            if shutdown_func:
                print("Steamの後片付け処理を実行します。")
                shutdown_func()

if __name__ == "__main__":
    main()