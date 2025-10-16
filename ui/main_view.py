# ui/main_view.py
import customtkinter as ctk
from i18n import t
from PIL import Image
from tkinterdnd2 import DND_FILES
import threading
import os
import json
from datetime import datetime
import random
import time # ★ timeをインポート
import webbrowser # ▼▼▼【ここを追加】▼▼▼
from .log_view import LogWindow
from .settings_view import SettingsWindow
from .help_view import HelpWindow
from .status_view import StatusWindow 
from PIL import Image, ImageTk
import pygame
from core.utils import resource_path


CHAT_LOG_FILE = "chat_log.json"


# main_view.py の上部 (import文の後あたり) にこのクラスを追加します
from PIL import Image, ImageTk

class AnimatedGifLabel(ctk.CTkLabel):
    """
    アニメーションGIFを再生するためのカスタムラベルクラス
    """
    def __init__(self, master, path, size=(180, 180)):
        super().__init__(master, text="")
        self.path = path
        self.size = size
        self.frames = []
        self.delays = []
        self._load_gif()
        self.frame_index = 0
        self.animation_id = None

    def _load_gif(self):
        """GIFを読み込み、フレームと遅延時間をリストに格納する"""
        with Image.open(self.path) as im:
            try:
                while True:
                    # CTkImageオブジェクトに変換してリストに追加
                    frame_image = ctk.CTkImage(im.copy().resize(self.size), size=self.size)
                    self.frames.append(frame_image)
                    self.delays.append(im.info.get('duration', 100)) # durationがなければ100ms
                    im.seek(len(self.frames))
            except EOFError:
                pass # フレームの終端

    def _animate(self):
        """フレームを更新し、次の更新を予約する"""


        # ▼▼▼ 変更後 ▼▼▼
        # 1. これから表示する「現在のフレーム」の表示時間を先に取得する
        delay = self.delays[self.frame_index]
        
        # 2. 現在のフレーム画像を表示する
        self.configure(image=self.frames[self.frame_index])
        
        # 3. 次に表示するフレームの番号を準備する
        self.frame_index = (self.frame_index + 1) % len(self.frames)
        
        # 4. 手順1で取得した「現在のフレームの表示時間」を使って、次の描画を予約する
        self.animation_id = self.after(delay, self._animate)

    def start(self):
        """アニメーションを開始する"""
        if self.animation_id is None:
            self._animate()

    def stop(self):
        """アニメーションを停止する"""
        if self.animation_id:
            self.after_cancel(self.animation_id)
            self.animation_id = None



class MainView(ctk.CTkFrame):

    def __init__(self, parent, controller, app_font):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.app_font = app_font
        self.current_user_message = None
        self.log_window = None
        self.settings_window = None
        self.help_window = None
        self.status_window = None
        self.active_animation_id = None
        self.learning_start_time = None # ★ 学習開始時刻を保持する変数を追加
        self.current_state = None

        # ▼▼▼【ここを追加】▼▼▼
        self.stream_animation_id = None # ストリーミングアニメーションのID
        # ▲▲▲【追加はここまで】▲▲▲

        # ▼▼▼【ここから追加】▼▼▼
        self.typing_sound = None
        try:
            pygame.mixer.init()
            # 用意したサウンドファイルのパスを指定
            # sound_path = "assets/sounds/typing3.mp3" 
            sound_path = resource_path("assets/sounds/typing3.mp3") 
            if os.path.exists(sound_path):
                self.typing_sound = pygame.mixer.Sound(sound_path)
                print("Typing sound loaded successfully.")
            else:
                print(f"Warning: Sound file not found at '{sound_path}'")
        except Exception as e:
            print(f"Error initializing pygame mixer or loading sound: {e}")
        # ▲▲▲【追加はここまで】▲▲▲


        theme_colors = self.controller.theme_colors

        # --- グリッドレイアウトの設定 ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0) # ▼▼▼【行の設定を追加】▼▼▼

        # --- 回答表示エリア ---
        self.answer_textbox = ctk.CTkTextbox(
            self, corner_radius=0, border_width=3,
            border_color=theme_colors.get("text_color", "#555555"),
            fg_color=theme_colors.get("fg_color", "#3A3A3A"),
            wrap="word", state="disabled",
            font=self.app_font
        )
        # ▼▼▼【ここを追加】▼▼▼
        # テキストボックスがクリックされたらskip_animationを呼ぶ
        self.answer_textbox.bind("<Button-1>", self.skip_animation) 
        self.full_answer_text = None # スキップ用の全文を保持する変数
        # ▲▲▲【追加はここまで】▲▲▲
        
        # --- キャラクター表示エリア --

        try:

            current_pack = self.controller.get_config().get("character_pack", "pal")
            # pack_path = f"assets/{current_pack}"
            pack_path = resource_path(f"assets/{current_pack}")

            # 1. キャラクターの表示サイズを設定ファイルから読み込む
            character_size = self._load_character_size(current_pack)

            # 2. 読み込んだサイズを使用してアニメーションを初期化する
            self.pal_animations = {
                "idle": AnimatedGifLabel(self, path=f"{pack_path}/idle.gif", size=character_size),
                "thinking": AnimatedGifLabel(self, path=f"{pack_path}/thinking.gif", size=character_size),
                "learning": AnimatedGifLabel(self, path=f"{pack_path}/learning.gif", size=character_size),
                "talking": AnimatedGifLabel(self, path=f"{pack_path}/talking.gif", size=character_size),
            }

            self.active_pal_animation = None # 現在表示中のアニメーションを保持





            # 各アニメーションラベルにイベントをバインド
            for anim_label in self.pal_animations.values():
                anim_label.bind("<Button-1>", self.controller.on_press)
                anim_label.bind("<B1-Motion>", self.controller.on_drag)





            self.set_pal_state("idle")


        except FileNotFoundError as e:
            self.anim_label = ctk.CTkLabel(self, text=f"Facial expression image not found in assets folder:\n{e.filename}")
            self.anim_label.grid(row=1, column=0, expand=True)
            self.pal_images = None
        
        # --- 操作エリア ---
        self.control_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.control_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(10, 20))
        self.control_frame.grid_columnconfigure(0, weight=1)
        self.chat_entry = ctk.CTkEntry(
                                    self.control_frame, 
                                    placeholder_text=t("chat_hint"), 
                                    font=self.app_font, corner_radius=0,
                                    border_width=3,         # ★ 枠の太さを指定 (例: 2ピクセル)
                                    border_color=theme_colors.get("text_color", "#555555")  # ★ 枠の色を指定 (例: 明るい青色)   
                                        )
        self.chat_entry.grid(row=0, column=0, sticky="ew", padx=20, pady=(10,0))
        self.chat_entry.bind("<Return>", self.send_question)
        icon_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        icon_frame.grid(row=1, column=0, pady=10)
        try:
            ICON_SIZE = (24, 24)
            # chat_icon = ctk.CTkImage(Image.open("assets/icons/chat_icon.png"), size=ICON_SIZE)
            # status_icon = ctk.CTkImage(Image.open("assets/icons/status_icon.png"), size=ICON_SIZE)
            # settings_icon = ctk.CTkImage(Image.open("assets/icons/settings_icon.png"), size=ICON_SIZE)
            # help_icon = ctk.CTkImage(Image.open("assets/icons/help_icon.png"), size=ICON_SIZE)
            # close_icon = ctk.CTkImage(Image.open("assets/icons/close_icon.png"), size=ICON_SIZE)

            chat_icon = ctk.CTkImage(Image.open(resource_path("assets/icons/chat_icon.png")), size=ICON_SIZE)
            status_icon = ctk.CTkImage(Image.open(resource_path("assets/icons/status_icon.png")), size=ICON_SIZE)
            settings_icon = ctk.CTkImage(Image.open(resource_path("assets/icons/settings_icon.png")), size=ICON_SIZE)
            help_icon = ctk.CTkImage(Image.open(resource_path("assets/icons/help_icon.png")), size=ICON_SIZE)
            close_icon = ctk.CTkImage(Image.open(resource_path("assets/icons/close_icon.png")), size=ICON_SIZE)


            hover_color = theme_colors.get("hover_color", "#999999")
            ctk.CTkButton(icon_frame, image=chat_icon, text="", fg_color="transparent", width=36, hover_color=hover_color, command=self.open_log_window).pack(side="left", expand=True, padx=3)
            ctk.CTkButton(icon_frame, image=status_icon, text="", fg_color="transparent", width=36, hover_color=hover_color, command=self.open_status_window).pack(side="left", expand=True, padx=3)
            ctk.CTkButton(icon_frame, image=settings_icon, text="", fg_color="transparent", width=36, hover_color=hover_color, command=self.open_settings_window).pack(side="left", expand=True, padx=3)
            ctk.CTkButton(icon_frame, image=help_icon, text="", fg_color="transparent", width=36, hover_color=hover_color, command=self.open_help_window).pack(side="left", expand=True, padx=3)
            ctk.CTkButton(icon_frame, image=close_icon, text="", fg_color="transparent", width=36, hover_color=hover_color, command=self.controller.destroy).pack(side="left", expand=True, padx=3)
        except FileNotFoundError as e:
            ctk.CTkLabel(icon_frame, text=f"アイコン画像が見つかりません:\n{e.filename}").pack()

        # ▼▼▼【ここから追加】▼▼▼
        # --- Steam告知エリア ---
        self.steam_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.steam_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(5, 15))
        self.steam_frame.grid_columnconfigure(0, weight=1) # 中央寄せのため

        # 注意書きラベル
        # フォントサイズを少し小さく設定
        notice_font = ctk.CTkFont(family=self.app_font.cget("family"), size=self.app_font.cget("size") - 3)
        notice_text = "This is a demo version using a speed-focused model.\nThe full version will allow model selection."
        self.notice_label = ctk.CTkLabel(
            self.steam_frame,
            text=notice_text,
            font=notice_font,
            text_color="#A9A9A9" # ダークグレー
        )
        self.notice_label.grid(row=0, column=0, pady=(0, 8))

        # Wishlistボタン
        self.wishlist_button = ctk.CTkButton(
            self.steam_frame,
            text="Add to Wishlist on Steam",
            command=self.open_wishlist,
            fg_color="#1E365C", # Steamっぽい緑色
            hover_color="#1E5886"
        )
        self.wishlist_button.grid(row=1, column=0)
        # ▲▲▲【追加はここまで】▲▲▲

        self._setup_dnd()

        # --- AIからの語りかけ機能 ---
        self.proactive_chat_id = None # タイマーID
        self.schedule_proactive_chat() # 最初のタイマーをセット

    # ▼▼▼【このメソッドをMainViewクラス内に追加】▼▼▼
    def open_wishlist(self):
        """Steamのウィッシュリストページをブラウザで開く"""
        # ★★★ TODO: ここにあなたのアプリの実際のSteamストアページのURLを入力してください ★★★
        steam_url = "https://store.steampowered.com/app/3878310/"  # 例: "https://store.steampowered.com/app/YOUR_APP_ID"
        print(f"Opening Steam page: {steam_url}")
        try:
            webbrowser.open_new_tab(steam_url)
        except Exception as e:
            print(f"Error: Failed to open web browser. {e}")
    # ▲▲▲【メソッドの追加はここまで】▲▲▲

    # ▼▼▼【このメソッドをMainViewクラス内に追加】▼▼▼
    def _load_character_size(self, character_pack):
        """
        キャラクターパックのフォルダからサイズ設定(config.json)を読み込みます。
        ファイルが存在しない、または読み込めない場合はデフォルトサイズを返します。
        """
        default_size = (180, 180)
        # config_path = f"assets/{character_pack}/config.json"
        config_path = resource_path(f"assets/{character_pack}/config.json")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                # config.get() を使い、キーが存在しない場合でもエラーにならないようにする
                width = int(config.get("width", default_size[0]))
                height = int(config.get("height", default_size[1]))
                print(f"Loaded character size from '{config_path}': ({width}, {height})")
                return (width, height)
        except (FileNotFoundError, json.JSONDecodeError, TypeError, ValueError) as e:
            # エラーが発生した場合はコンソールに出力し、デフォルト値を返す
            print(f"Could not load or parse '{config_path}'. Using default size {default_size}. Reason: {e}")
            return default_size
    # ▲▲▲【メソッドの追加はここまで】▲▲▲

    def on_drop(self, event):
        self.reset_proactive_chat_timer() # ★タイマーリセット

        filepaths = self.tk.splitlist(event.data)
        if not filepaths: return

        # ▼▼▼ 修正点: 学習開始時刻を記録 ▼▼▼
        self.learning_start_time = time.time()

        # English learning messages
        learning_messages = [
            "Om nom nom... this document is delicious!",
            "Absorbing knowledge... munch munch...",
            "Reading a lot to get smarter!",
            "Wonder what this one tastes like...?"
        ]
        self.answer_textbox.configure(state="normal")
        self.answer_textbox.delete("1.0", "end")
        self.answer_textbox.insert("1.0", random.choice(learning_messages))
        self.answer_textbox.configure(state="disabled")
        # self.answer_textbox.grid(row=0, column=0, sticky="nsew", padx=20, pady=(10, 0))
        self.answer_textbox.grid(row=0, column=0, sticky="ew", padx=20, pady=(10, 0))


        # ▼▼▼【ここを追加】▼▼▼
        # チャット入力欄を再度有効化し、プレースホルダーを元に戻す
        self.chat_entry.configure(state="normal", placeholder_text=t("chat_hint"))
        # ▲▲▲【追加はここまで】▲▲▲

        file_path = filepaths[0]
        self.set_pal_state("learning")
        
        thread = threading.Thread(target=self.run_learning, args=(file_path,))
        thread.start()


    def on_learning_complete(self, filename):
        # ▼▼▼ 修正点: 経過時間を計算し、遅延処理を行う ▼▼▼
        elapsed_time = time.time() - self.learning_start_time
        min_duration = 2.0  # 最低でも2秒間表示する

        if elapsed_time < min_duration:
            delay_ms = int((min_duration - elapsed_time) * 1000)
            # 足りない時間分、待ってから完了表示を出す
            self.after(delay_ms, self._show_learning_complete_ui, filename)
        else:
            # 2秒以上かかっていたら、すぐに完了表示を出す
            self._show_learning_complete_ui(filename)

    def _show_learning_complete_ui(self, filename):
        """学習完了のUI更新を行う実際のメソッド"""
        self.answer_textbox.configure(state="normal")
        self.answer_textbox.delete("1.0", "end")
        self.answer_textbox.insert("1.0", f"Learning completed！\nI learned the data that '{filename}' gave me.")
        self.answer_textbox.configure(state="disabled")
        self.answer_textbox.grid(row=0, column=0, sticky="nsew", padx=20, pady=(10, 0))
        self.set_pal_state("idle")

        # ▼▼▼【ここを追加】▼▼▼
        # チャット入力欄を再度有効化し、プレースホルダーを元に戻す
        self.chat_entry.configure(state="normal", placeholder_text=t("chat_hint"))
        # ▲▲▲【追加はここまで】▲▲▲


    def set_pal_state(self, state):
        if not self.pal_animations: return

        self.current_state = state

        # 現在のアニメーションを停止して非表示にする
        if self.active_pal_animation:
            self.active_pal_animation.stop()
            self.active_pal_animation.grid_remove()

        # 新しい状態のアニメーションを取得
        # 'talking'はストリーミング処理で個別に制御するため、ここでは'idle'に戻すなど調整可能
        # 今回はtalking.gifがあると仮定します。
        new_state_key = state if state in self.pal_animations else "idle"
        self.active_pal_animation = self.pal_animations[new_state_key]

        # 新しいアニメーションを表示して開始
        self.active_pal_animation.grid(row=1, column=0, pady=(10, 0), sticky="s")
        self.active_pal_animation.start()

    def send_question(self, event=None):
        self.reset_proactive_chat_timer()

        # 既存の回答ストリーミングが実行中であればキャンセルする
        if self.stream_animation_id:
            self.after_cancel(self.stream_animation_id)
            self.stream_animation_id = None

        query = self.chat_entry.get()
        if not query: return
        self.answer_textbox.grid_remove() 
        self.chat_entry.delete(0, 'end')
        self.chat_entry.configure(state="disabled", placeholder_text="Thinking...")
        self.set_pal_state("thinking") 
        self.current_user_message = { "role": "user", "content": query, "timestamp": datetime.now().isoformat(), "learned": False }
        thread = threading.Thread(target=self.run_chatting, args=(query,))
        thread.start()

    def on_chat_complete(self, answer):
        self.chat_entry.configure(state="normal", placeholder_text=t("chat_hint"))
        self.set_pal_state("talking")
        self.answer_textbox.configure(state="normal")
        self.answer_textbox.delete("1.0", "end")
        self.answer_textbox.grid(row=0, column=0, sticky="nsew", padx=20, pady=(10, 0))
        self.stream_and_animate(answer)
        assistant_message = { "role": "assistant", "content": answer, "timestamp": datetime.now().isoformat(), "learned": False }
        log = self._load_chat_log()
        if self.current_user_message: log.append(self.current_user_message); self.current_user_message = None
        log.append(assistant_message)
        self._save_chat_log(log)
        print(f"'{CHAT_LOG_FILE}' has been updated.")


    # ▼▼▼【このメソッドを丸ごと追加】▼▼▼
    def skip_animation(self, event=None):
        """テキスト表示アニメーションをスキップして全文を表示する"""
        # アニメーション実行中かつ、全文テキストが保持されている場合のみ実行
        if self.stream_animation_id and self.full_answer_text:
            print("Skipping animation.")
            # 1. 進行中のアニメーション(after)をキャンセル
            self.after_cancel(self.stream_animation_id)
            self.stream_animation_id = None

            # 2. テキストボックスを一度クリアし、全文を挿入
            self.answer_textbox.configure(state="normal")
            self.answer_textbox.delete("1.0", "end")
            self.answer_textbox.insert("1.0", self.full_answer_text)
            self.answer_textbox.configure(state="disabled")

            # 3. 状態を待機モードに戻す
            self.set_pal_state("idle")
            
            # 4. 全文テキスト変数をクリア
            self.full_answer_text = None
    # ▲▲▲【追加はここまで】▲▲▲



    def stream_and_animate(self, text, index=0):
        # talking状態を開始
        if index == 0:
            self.set_pal_state("talking")
            # ▼▼▼【ここを追加】▼▼▼
            self.full_answer_text = text # アニメーション開始時に全文を保持
            # ▲▲▲【追加はここまで】▲▲▲

        if index >= len(text):
            self.set_pal_state("idle") # 会話が終わったら待機状態に戻す
            # ▼▼▼【ここを追加】▼▼▼
            self.full_answer_text = None # 正常終了時もクリア
            # ▲▲▲【追加はここまで】▲▲▲
            return

        self.answer_textbox.insert("end", text[index])
        self.answer_textbox.see("end")

        # ▼▼▼【ここを追加】▼▼▼
        # 効果音を再生
        # if self.typing_sound:
        #     self.typing_sound.play()
        # ▲▲▲【追加はここまで】▲▲▲

        typing_speed_ms = 30
        
        # afterのID管理が不要になる
        # self.after(typing_speed_ms, self.stream_and_animate, text, index + 1)
        # ▼▼▼【ここを変更】▼▼▼
        # afterのIDをインスタンス変数に保存する
        self.stream_animation_id = self.after(typing_speed_ms, self.stream_and_animate, text, index + 1)
        # ▲▲▲【変更はここまで】▲▲▲

        
    def _load_chat_log(self):
        try:
            with open(CHAT_LOG_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError): return []

    def _save_chat_log(self, log_data):
        with open(CHAT_LOG_FILE, "w", encoding="utf-8") as f: json.dump(log_data, f, indent=2, ensure_ascii=False)

    def run_chatting(self, query):
        log = self._load_chat_log()
        history = log[-6:] if len(log) > 6 else log
        answer = self.controller.logic.ask_question(query, history, self.controller.get_config())
        self.after(0, self.on_chat_complete, answer)
    
    def _setup_dnd(self):


        if self.pal_animations: # アニメーションが正常に読み込めた場合のみ実行
            for anim_label in self.pal_animations.values():
                anim_label.drop_target_register(DND_FILES)
                anim_label.dnd_bind('<<Drop>>', self.on_drop)

    def run_learning(self, file_path):
        self.controller.logic.learn_from_document(file_path)
        self.after(0, self.on_learning_complete, os.path.basename(file_path))

    def open_log_window(self):
        if self.log_window is None or not self.log_window.winfo_exists(): self.log_window = LogWindow(self, self.controller); self.log_window.grab_set()
        else: self.log_window.focus()

    def run_history_learning(self):
        print("Starting to learn from chat history...")
        self.answer_textbox.grid_remove() 
        self.set_pal_state("learning")
        thread = threading.Thread(target=self.controller.logic.learn_from_history)
        thread.start()

    def open_help_window(self):
        if self.help_window is None or not self.help_window.winfo_exists(): self.help_window = HelpWindow(self); self.help_window.grab_set()
        else: self.help_window.focus()

    def open_status_window(self):
        if self.status_window is None or not self.status_window.winfo_exists(): self.status_window = StatusWindow(self, self.controller); self.status_window.grab_set()
        else: self.status_window.focus()

    def open_settings_window(self):
        if self.settings_window is None or not self.settings_window.winfo_exists():
            self.settings_window = SettingsWindow(self, self.controller)
            self.settings_window.grab_set()
        else:
            self.settings_window.focus()

    def schedule_proactive_chat(self):
        """設定がONの場合、一定時間後にAIが話しかけるように予約する"""
        # 既存のタイマーがあればキャンセル
        if self.proactive_chat_id:
            self.after_cancel(self.proactive_chat_id)

        # 設定を確認し、ONの場合のみタイマーをセット
        if self.controller.get_config().get("proactive_chat", True):
            # 300000ミリ秒 = 5分
            self.proactive_chat_id = self.after(300000, self.trigger_proactive_chat)
            # self.proactive_chat_id = self.after(10000, self.trigger_proactive_chat)

    def reset_proactive_chat_timer(self):
        """ユーザーの操作時にタイマーをリセットする"""
        self.schedule_proactive_chat()

    def trigger_proactive_chat(self):
        """AIが話しかけるのを実行する"""
        print("Triggering proactive chat...")
        
        # 待機状態でない場合は何もしない

        
        if self.current_state != 'idle':
            print(f"Not idle (current state: {self.current_state}), skipping proactive chat.")
            self.schedule_proactive_chat() # 次のタイマーだけ予約
            return


        # Get the current user name from the config
        config = self.controller.get_config()
        user_name = config.get("user_name", "friend")

        # English proactive phrases using the user's name
        proactive_phrases = [
            f"Hey {user_name}, anything interesting happen today?",
            f"Just letting you know I'm here if you need anything, {user_name}!",
            "Getting a little bored... Do you have any documents for me to read?",
            f"How's the weather over there, {user_name}?",
            "It feels like a while since I last learned something..."
        ]
        message = random.choice(proactive_phrases)
        
        # 会話ストリーミング機能を使ってメッセージを表示
        self.on_chat_complete(message)
        
        # メッセージを表示した後、次のタイマーを予約
        self.schedule_proactive_chat()