# ui/app.py
import json
import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image # 👈 この行を追加
from .main_view import MainView
import os
import pyglet
import time
import threading
from core.pal_logic import PalLogic
from i18n import t
from core.utils import resource_path

# ▼▼▼【ここから下を丸ごと追加】▼▼▼
class InitialSetupDialog(ctk.CTkToplevel):
    """初回設定用のダイアログウィンドウ"""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.config = self.controller.get_config()

        self.title("Initial Setup")
        self.geometry("400x340")
        self.resizable(False, False)

        # このウィンドウが閉じるまで、他のウィンドウを操作できないようにする
        self.grab_set()
        # ウィンドウのxボタンを無効化し、必ず設定を完了させる
        self.protocol("WM_DELETE_WINDOW", lambda: None)

        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Welcome!", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, pady=(20, 10))
        ctk.CTkLabel(self, text="Please set your name and your AI's name.", wraplength=350).grid(row=1, column=0, pady=(0, 20), padx=20)

        ctk.CTkLabel(self, text="Your Name").grid(row=2, column=0, pady=(0, 5), padx=40, sticky="w")
        self.user_name_entry = ctk.CTkEntry(self)
        self.user_name_entry.grid(row=3, column=0, pady=(0, 15), padx=40, sticky="ew")

        ctk.CTkLabel(self, text="AI's Name").grid(row=4, column=0, pady=(0, 5), padx=40, sticky="w")
        self.ai_name_entry = ctk.CTkEntry(self)
        self.ai_name_entry.grid(row=5, column=0, pady=(0, 20), padx=40, sticky="ew")
        self.ai_name_entry.insert(0, self.config.get("ai_name", "Pal"))


        save_button = ctk.CTkButton(self, text="Save & Start", command=self.save_and_close)
        save_button.grid(row=6, column=0, pady=(0, 20), padx=40, sticky="ew")

    def save_and_close(self):
        """入力された名前を保存してウィンドウを閉じる"""
        user_name = self.user_name_entry.get().strip()
        ai_name = self.ai_name_entry.get().strip()

        if not user_name:
            # ユーザー名が空の場合は処理を中断
            return

        if not ai_name:
            # AI名が空の場合は処理を中断
            return

        self.config["user_name"] = user_name
        self.config["ai_name"] = ai_name
        self.controller.save_config(self.config)
        self.destroy() # ウィンドウを閉じる
# ▲▲▲【追加はここまで】▲▲▲


# ▼▼▼【ここから下を丸ごと置き換え】▼▼▼
class SplashScreen(ctk.CTkToplevel):
    """ローディング画面（スプラッシュスクリーン）"""
    def __init__(self, parent, bg_color): # bg_color を受け取るように変更
        super().__init__(parent)

        self.geometry("400x250")
        self.overrideredirect(True)
        # ★★★ 透明設定を削除し、受け取った背景色を設定 ★★★
        self.configure(fg_color=bg_color)
        self.attributes("-topmost", True)

        try:
            # logo_image = ctk.CTkImage(Image.open("assets/icons/logo.png"), size=(360, 180))
            logo_image = ctk.CTkImage(Image.open(resource_path("assets/icons/logo.png")), size=(360, 180))
            logo_label = ctk.CTkLabel(self, image=logo_image, text="", bg_color="transparent")
            logo_label.pack(pady=(20, 10))

            loading_label = ctk.CTkLabel(self, text="Loading, please wait...", font=ctk.CTkFont(size=12), bg_color="transparent", text_color="white")
            loading_label.pack(pady=(0, 20))

        except Exception as e:
            print(f"Could not load logo.png: {e}")
            label = ctk.CTkLabel(self, text="Loading...")
            label.pack(expand=True)

        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - self.winfo_width()) // 2
        y = (screen_height - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
# ▲▲▲【置き換えはここまで】▲▲▲


# 透明にする色を定義（まず使われないであろう色を選ぶ）
TRANSPARENT_COLOR = '#010101' 
# CONFIG_FILE = "config.json"
# THEMES_FILE = "themes.json" # 👈 追加
CONFIG_FILE = resource_path("config.json")
THEMES_FILE = resource_path("themes.json")

class App(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        print("start app _init__")
        self.withdraw()
        self.start_time = time.time()
        self.logic = None # ロジックを一旦 None で初期化

        self.themes = self.load_themes()
        self.config = self.get_config()
        theme_name = self.config.get("theme", "dark").lower()
        bg_color = self.themes.get(theme_name, {}).get("bg_color", "#242424")

        self.splash = SplashScreen(self, bg_color=bg_color)

        # ★★★ 重いAIモデルの読み込みをバックグラウンドで開始 ★★★
        logic_loader_thread = threading.Thread(target=self._load_backend_logic, daemon=True)
        logic_loader_thread.start()


    def _load_backend_logic(self):
        """[バックグラウンド処理] 時間のかかるAIモデル(PalLogic)を初期化する"""
        print("AIモデルの読み込みを開始します...")
        # --- ここが時間のかかる処理 ---
        self.logic = PalLogic()
        # --- 処理ここまで ---
        print("AIモデルの読み込みが完了しました。")

        # 完了後、メイン画面の準備を予約する
        self.after(0, self._setup_ui)

    def _setup_ui(self):
        """[メイン処理] AIモデルの読み込み完了後に、UIの準備を行う"""
        if self.config.get("user_name") == "Any":
            dialog = InitialSetupDialog(self, self)
            self.wait_window(dialog)

        self.apply_theme()

        self.overrideredirect(True)
        self.configure(bg=TRANSPARENT_COLOR)
        self.wm_attributes("-transparentcolor", TRANSPARENT_COLOR)
        self.title(t("app_title"))
        self.geometry(str(self.config.get("width")) + "x" + str(self.config.get("height")))

        container = ctk.CTkFrame(self, fg_color=TRANSPARENT_COLOR)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        frame = MainView(parent=container, controller=self, app_font=self.app_font)
        self.frames[MainView] = frame
        frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame(MainView)
        
        # UIの準備が全て終わったら、ローディング画面を閉じる処理を呼び出す
        self.dismiss_splash_screen()

    def dismiss_splash_screen(self):
        """ローディング画面の最低表示時間を計算して閉じる"""
        def show_main_window():
            self.splash.destroy()
            self.deiconify()

        elapsed_time = time.time() - self.start_time
        min_display_time_sec = 2.0
        remaining_time_ms = int((min_display_time_sec - elapsed_time) * 1000)

        if remaining_time_ms > 0:
            self.after(remaining_time_ms, show_main_window)
        else:
            show_main_window()


    def __init__2(self):
        super().__init__()
        
        # --- 設定とテーマの読み込み ---
        self.themes = self.load_themes() # 👈 追加
        self.config = self.get_config()


        # ▼▼▼【ここから下を追加】▼▼▼
        # ユーザー名が初期値 "Any" の場合は初回設定ダイアログを表示
        if self.config.get("user_name") == "Any":
            self.withdraw() # 本体ウィンドウを一旦隠す
            dialog = InitialSetupDialog(self, self)
            self.wait_window(dialog) # ダイアログが閉じるまで待つ
            self.deiconify() # 本体ウィンドウを再表示
        # ▲▲▲【追加はここまで】▲▲▲

        self.apply_theme() # 👈 追加

        self.logic = PalLogic()

        # ウィンドウの枠を消す
        self.overrideredirect(True)
        # ウィンドウの背景色を設定し、その色を透明として指定
        self.configure(bg=TRANSPARENT_COLOR)
        self.wm_attributes("-transparentcolor", TRANSPARENT_COLOR)

        # ウィンドウをドラッグ可能にするためのイベント
        # self.bind("<Button-1>", self.on_press)
        # self.bind("<B1-Motion>", self.on_drag)

        # 👈 ctk.set_appearance_mode("System") を削除

        self.title(t("app_title"))
        self.geometry(str(self.config.get("width")) + "x" + str(self.config.get("height")))
        # self.geometry("340x500")

        # コンテナフレームの背景も透明色に設定
        container = ctk.CTkFrame(self, fg_color=TRANSPARENT_COLOR)
        container.pack(fill="both", expand=True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        
        # MainViewの背景も透明に設定
        frame = MainView(parent=container, controller=self, app_font=self.app_font)
        self.frames[MainView] = frame
        frame.grid(row=0, column=0, sticky="nsew")
        
        self.show_frame(MainView)

    def load_themes(self): # 👈 追加
        """themes.jsonを読み込む"""
        try:
            with open(THEMES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # ファイルがない場合はデフォルト値を返す
            return {
              "dark": {"bg_color": "#242424", "fg_color": "#2D2D2D", "hover_color": "#3A3A3A", "text_color": "#E0E0E0", "accent_color": "#4A90E2", "wordcloud_bg": "#333333"},
              "light": {"bg_color": "#EBEBEB", "fg_color": "#F5F5F5", "hover_color": "#DADADA", "text_color": "#1A1A1A", "accent_color": "#1A73E8",  "wordcloud_bg": "#E0E0E0"}
            }

    def apply_theme(self):
        """設定に基づいてアプリのテーマとフォントを適用する"""
        theme_name = self.config.get("theme", "dark").lower()
        ctk.set_appearance_mode(theme_name)
        self.theme_colors = self.themes.get(theme_name)

        # --- ▼▼▼ フォント読み込み処理の修正 ▼▼▼ ---
        font_face_filename = self.config.get("font_face", "Arial")
        font_size = self.config.get("font_size", 16)
        
        # フォントファイル名と、実際のフォントファミリー名の対応表
        font_map = {
            "PressStart2P-Regular.ttf": "Press Start 2P",
            "m5x7.ttf": "m5x7",
            "Silkscreen-Regular.ttf": "Silkscreen",
            "Inter-Regular.ttf": "Inter",
            "NotoSansJP-Regular.ttf": "Noto Sans JP"
        }
        
        # ファイル名から実際のフォント名を取得。見つからなければファイル名をそのまま使う
        font_family_name = font_map.get(font_face_filename, font_face_filename)

        try:
            # フォントファイルへのフルパスを生成
            # font_path = os.path.join("assets/fonts", font_face_filename)
            font_path = resource_path(os.path.join("assets/fonts", font_face_filename))
            # pygletを使ってフォントファイルを読み込む
            pyglet.font.add_file(font_path)
            print(f"Successfully loaded font: {font_path}")

        except Exception as e:
            print(f"Could not load font file {font_face_filename}: {e}")
            # ファイルが見つからない場合などは、フォント名をそのまま使う
            font_family_name = "Arial" # 安全なフォールバック

        # CTkFontオブジェクトを作成
        self.app_font = ctk.CTkFont(family=font_family_name, size=font_size)

    def get_config(self):
        """設定ファイルを読み込む"""
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    
                config = json.load(f)
                # 古い設定ファイルとの互換性のため、themeキーがなければ追加
                # if "theme" not in config:
                #     config["theme"] = "dark" # デフォルトはダークモード
                # print("get_config")
                return config
        except (FileNotFoundError, json.JSONDecodeError):
            # デフォルト設定を返す
  
            return {
                "user_name": "Any",
                "ai_name": "Pal",
                "ai_tone": "Friendly",
                "theme": "dark",
                "proactive_chat": True, 
                "character_pack": "imgset1",
                "font_face": "Inter_24pt-Regular.ttf",
                "font_size": 16,
                "width": 340,
                "height": 640
            }

    def save_config(self, new_config):
        """設定ファイルに保存する"""
        # 現在のテーマ設定を保持しつつ、新しい設定で更新
        # current_theme = self.config.get("theme", "dark")
        self.config = new_config
        # if "theme" not in self.config:
        #     self.config["theme"] = current_theme
        
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        
        self.apply_theme() # 👈 設定保存後にテーマを再適用
        print("Settings saved and theme applied.")


    def show_frame(self, page_class):
        frame = self.frames[page_class]
        frame.tkraise()

    def on_press(self, event):
        """マウスボタンが押された時の処理"""
        self._offset_x = event.x
        self._offset_y = event.y

    def on_drag(self, event):
        """マウスドラッグ中の処理"""
        x = self.winfo_pointerx() - self._offset_x
        y = self.winfo_pointery() - self._offset_y
        self.geometry(f"+{x}+{y}")