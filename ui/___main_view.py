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
from .log_view import LogWindow
from .settings_view import SettingsWindow
from .help_view import HelpWindow
from .status_view import StatusWindow 
from PIL import Image, ImageTk


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


class ChatBubble(ctk.CTkFrame):
    """
    プレビューと全文表示を切り替えられる、ふきだし風のUIを管理するクラス
    """
    def __init__(self, master, app_font, theme_colors):
        super().__init__(master, fg_color="transparent")
        
        self.app_font = app_font
        self.full_text = ""
        self.theme_colors = theme_colors

        # ふきだしの本体となるFrame
        self.bubble_frame = ctk.CTkFrame(
            self,
            corner_radius=15,
            border_width=2,
            border_color=theme_colors.get("accent_color", "#555555"),
            fg_color=theme_colors.get("fg_color", "#3A3A3A")
        )
        self.bubble_frame.pack(expand=True, fill="both")

    def show_message(self, text):
        """外部からメッセージを受け取り、長さに応じて表示を切り替える"""
        self.full_text = text
        
        # 80文字以上の場合はプレビュー、それ未満は全文表示
        if len(text) > 80:
            self._show_preview()
        else:
            self._show_full()
            
        self.grid(row=0, column=0, sticky="nsew", padx=20, pady=(10, 0))

    def _clear_bubble(self):
        """ふきだしの中身を空にする"""
        for widget in self.bubble_frame.winfo_children():
            widget.destroy()

    def _show_preview(self):
        """プレビュー表示（短いテキスト + 続きを読むボタン）"""
        self._clear_bubble()
        
        preview_text = self.full_text[:80] + "..."
        
        lbl_preview = ctk.CTkLabel(
            self.bubble_frame,
            text=preview_text,
            font=self.app_font,
            wraplength=380,
            justify="left"
        )
        lbl_preview.pack(pady=10, padx=10, anchor="w", expand=True, fill="x")

        btn_read_more = ctk.CTkButton(
            self.bubble_frame,
            text="続きを読む...",
            font=self.app_font,
            command=self._show_full
        )
        btn_read_more.pack(pady=5, padx=10, anchor="e")

    def _show_full(self):
        """全文表示（スクロール可能なTextbox）"""
        self._clear_bubble()
        
        textbox = ctk.CTkTextbox(
            self.bubble_frame,
            wrap="word",
            font=self.app_font,
            fg_color="transparent" # Frameの色を活かす
        )
        textbox.pack(expand=True, fill="both", padx=5, pady=5)
        textbox.insert("1.0", self.full_text)
        textbox.configure(state="disabled")

    def hide(self):
        """ふきだしを非表示にする"""
        self.grid_remove()


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

        theme_colors = self.controller.theme_colors

        # --- グリッドレイアウトの設定 ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)

        # --- 回答表示エリア ---
        # self.answer_textbox = ctk.CTkTextbox(
        #     self, corner_radius=15, border_width=2,
        #     border_color=theme_colors.get("accent_color", "#555555"),
        #     fg_color=theme_colors.get("fg_color", "#3A3A3A"),
        #     wrap="word", state="disabled",
        #     font=self.app_font
        # )
        self.bubble = ChatBubble(self, self.app_font, theme_colors)       

        # --- キャラクター表示エリア --

        try:

            current_pack = self.controller.get_config().get("character_pack", "pal")
            pack_path = f"assets/{current_pack}"

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
        self.chat_entry = ctk.CTkEntry(self.control_frame, placeholder_text=t("chat_hint"), font=self.app_font )
        self.chat_entry.grid(row=0, column=0, sticky="ew", padx=20, pady=(10,0))
        self.chat_entry.bind("<Return>", self.send_question)
        icon_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        icon_frame.grid(row=1, column=0, pady=10)
        try:
            ICON_SIZE = (24, 24)
            chat_icon = ctk.CTkImage(Image.open("assets/icons/chat_icon.png"), size=ICON_SIZE)
            status_icon = ctk.CTkImage(Image.open("assets/icons/status_icon.png"), size=ICON_SIZE)
            settings_icon = ctk.CTkImage(Image.open("assets/icons/settings_icon.png"), size=ICON_SIZE)
            help_icon = ctk.CTkImage(Image.open("assets/icons/help_icon.png"), size=ICON_SIZE)
            close_icon = ctk.CTkImage(Image.open("assets/icons/close_icon.png"), size=ICON_SIZE)
            hover_color = theme_colors.get("hover_color", "#999999")
            ctk.CTkButton(icon_frame, image=chat_icon, text="", fg_color="transparent", width=40, hover_color=hover_color, command=self.open_log_window).pack(side="left", expand=True, padx=5)
            ctk.CTkButton(icon_frame, image=status_icon, text="", fg_color="transparent", width=40, hover_color=hover_color, command=self.open_status_window).pack(side="left", expand=True, padx=5)
            ctk.CTkButton(icon_frame, image=settings_icon, text="", fg_color="transparent", width=40, hover_color=hover_color, command=self.open_settings_window).pack(side="left", expand=True, padx=5)
            ctk.CTkButton(icon_frame, image=help_icon, text="", fg_color="transparent", width=40, hover_color=hover_color, command=self.open_help_window).pack(side="left", expand=True, padx=5)
            ctk.CTkButton(icon_frame, image=close_icon, text="", fg_color="transparent", width=40, hover_color=hover_color, command=self.controller.destroy).pack(side="left", expand=True, padx=5)
        except FileNotFoundError as e:
            ctk.CTkLabel(icon_frame, text=f"アイコン画像が見つかりません:\n{e.filename}").pack()
        self._setup_dnd()

        # --- AIからの語りかけ機能 ---
        self.proactive_chat_id = None # タイマーID
        self.schedule_proactive_chat() # 最初のタイマーをセット


    # ▼▼▼【このメソッドをMainViewクラス内に追加】▼▼▼
    def _load_character_size(self, character_pack):
        """
        キャラクターパックのフォルダからサイズ設定(config.json)を読み込みます。
        ファイルが存在しない、または読み込めない場合はデフォルトサイズを返します。
        """
        default_size = (180, 180)
        config_path = f"assets/{character_pack}/config.json"
        
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
        
        # self.answer_textbox.configure(state="normal")
        # self.answer_textbox.delete("1.0", "end")
        # self.answer_textbox.insert("1.0", random.choice(learning_messages))
        # self.answer_textbox.configure(state="disabled")
        # self.answer_textbox.grid(row=0, column=0, sticky="nsew", padx=20, pady=(10, 0))

        self.bubble.show_message(random.choice(learning_messages))

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
        # self.answer_textbox.configure(state="normal")
        # self.answer_textbox.delete("1.0", "end")
        # self.answer_textbox.insert("1.0", f"Learning completed！\nI learned the data that '{filename}' gave me.")
        # self.answer_textbox.configure(state="disabled")
        # self.answer_textbox.grid(row=0, column=0, sticky="nsew", padx=20, pady=(10, 0))
        message = f"Learning completed！\nI learned the data that '{filename}' gave me."
        self.bubble.show_message(message)

        self.set_pal_state("idle")


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

        query = self.chat_entry.get()
        if not query: return
        # self.answer_textbox.grid_remove() 
        self.bubble.hide() # ★変更点
        self.chat_entry.delete(0, 'end')
        self.chat_entry.configure(state="disabled", placeholder_text="Thinking...")
        self.set_pal_state("thinking") 
        self.current_user_message = { "role": "user", "content": query, "timestamp": datetime.now().isoformat(), "learned": False }
        thread = threading.Thread(target=self.run_chatting, args=(query,))
        thread.start()

    def on_chat_complete(self, answer):
        self.chat_entry.configure(state="normal", placeholder_text=t("chat_hint"))

        # self.set_pal_state("talking")
        # self.answer_textbox.configure(state="normal")
        # self.answer_textbox.delete("1.0", "end")
        # self.answer_textbox.grid(row=0, column=0, sticky="nsew", padx=20, pady=(10, 0))
        # self.stream_and_animate(answer)
        # ★★★ ここからが大きな変更点 ★★★
        # talking状態のアニメーションを少しだけ再生して、すぐにidleに戻す
        self.set_pal_state("talking")
        self.after(1000, lambda: self.set_pal_state("idle")) # 1秒後に待機状態へ

        # 新しいふきだしにメッセージを表示させる
        self.bubble.show_message(answer)

        assistant_message = { "role": "assistant", "content": answer, "timestamp": datetime.now().isoformat(), "learned": False }
        log = self._load_chat_log()
        if self.current_user_message: log.append(self.current_user_message); self.current_user_message = None
        log.append(assistant_message)
        self._save_chat_log(log)
        print(f"'{CHAT_LOG_FILE}' has been updated.")

    # def stream_and_animate(self, text, index=0):
        # talking状態を開始
    #     if index == 0:
    #         self.set_pal_state("talking")

    #     if index >= len(text):
    #         self.set_pal_state("idle") # 会話が終わったら待機状態に戻す
    #         return

    #     self.answer_textbox.insert("end", text[index])
    #     self.answer_textbox.see("end")
    #     typing_speed_ms = 50
        
        # afterのID管理が不要になる
    #     self.after(typing_speed_ms, self.stream_and_animate, text, index + 1)

        
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

    def reset_proactive_chat_timer(self):
        """ユーザーの操作時にタイマーをリセットする"""
        self.schedule_proactive_chat()

    def trigger_proactive_chat(self):
        """AIが話しかけるのを実行する"""
        print("Triggering proactive chat...")

        
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