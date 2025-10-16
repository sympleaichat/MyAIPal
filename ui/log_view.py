# ui/log_view.py
import customtkinter as ctk
import json
from datetime import datetime

CHAT_LOG_FILE = "chat_log.json"

class LogWindow(ctk.CTkToplevel):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller
        theme_colors = self.controller.theme_colors

        self.title("Conversation Log")
        self.geometry("640x720")
        self.configure(fg_color=theme_colors["bg_color"])

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.all_logs = []
        self.current_page = 0
        self.logs_per_page = 20
        self.bubble_widgets = []

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        self.scrollable_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        self.scrollable_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")

        self.page_label = ctk.CTkLabel(main_frame, text="Page 1/1")
        self.page_label.grid(row=1, column=0, columnspan=2, pady=(10,0))

        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.grid(row=2, column=0, columnspan=2)

        self.prev_button = ctk.CTkButton(button_frame, text="< Previous", command=self.prev_page, state="disabled")
        self.prev_button.pack(side="left", padx=10)

        self.next_button = ctk.CTkButton(button_frame, text="Next >", command=self.next_page, state="disabled")
        self.next_button.pack(side="left", padx=10)

        self.load_and_display_logs()

    def load_and_display_logs(self):
        """JSONから全てのログを読み込み、逆順にして最初のページを表示する"""
        try:
            with open(CHAT_LOG_FILE, "r", encoding="utf-8") as f:
                self.all_logs = json.load(f)
                self.all_logs.reverse()
        except (FileNotFoundError, json.JSONDecodeError):
            self.all_logs = []
        
        self.display_page()

    def display_page(self):
        """現在のページのログを表示する"""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.bubble_widgets = []

        start_index = self.current_page * self.logs_per_page
        end_index = start_index + self.logs_per_page
        logs_to_display = self.all_logs[start_index:end_index]

        for log_entry in logs_to_display:
            self.add_chat_bubble(log_entry)
        
        self.update_pagination_controls()

    def add_chat_bubble(self, message_data: dict):
        """スクロールフレームにチャットバブルを追加する"""
        role = message_data.get("role", "unknown")
        content = message_data.get("content", "")
        timestamp_str = message_data.get("timestamp")
        theme_colors = self.controller.theme_colors
        
        is_user = (role == "user")
        bubble_container = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        
        user_bubble_color = theme_colors.get("accent_color", "#4A90E2")
        pal_bubble_color = theme_colors.get("fg_color", "#3A3A3A")
        
        bubble_color = user_bubble_color if is_user else pal_bubble_color
        
        bubble = ctk.CTkFrame(bubble_container, fg_color=bubble_color, corner_radius=15)
        
        if timestamp_str:
            try:
                dt_object = datetime.fromisoformat(timestamp_str)
                formatted_time = dt_object.strftime("%Y-%m-%d %H:%M")
                time_label = ctk.CTkLabel(bubble, text=formatted_time, font=("Arial", 10), text_color=("#666666", "#AAAAAA"))
                # ユーザーの発言か否かでタイムスタンプの表示位置を変える
                anchor_side = "e" if is_user else "w"
                time_label.pack(padx=10, pady=(5, 0), anchor=anchor_side)
            except (ValueError, TypeError):
                pass

        text_color = "white" if is_user else theme_colors.get("text_color", "#E0E0E0")
        
        text_widget = ctk.CTkTextbox(
            bubble,
            wrap="word",
            text_color=text_color,
            fg_color="transparent",
            corner_radius=0,
            border_width=0,
            font=ctk.CTkFont(size=14)
        )
        text_widget.insert("1.0", content)
        text_widget.configure(state="disabled")

        text_widget.update_idletasks()
        num_lines = int(text_widget.index("end-1c").split('.')[0])
        height = max(40, min(num_lines * 20, 400))
        text_widget.configure(height=height)

        text_widget.pack(padx=10, pady=5, fill="x", expand=True)

        # 👈 変更点: レイアウトマネージャをpackからgridに変更し、バブルの幅と配置を制御
        bubble_container.grid_rowconfigure(0, weight=1)
        if is_user:
            # ユーザー（右寄せ）
            # 0列目（空きスペース）と1列目（バブル）の幅の比率を1:4に設定
            bubble_container.grid_columnconfigure(0, weight=1)
            bubble_container.grid_columnconfigure(1, weight=4)
            # バブルを1列目に配置し、横幅いっぱい(ew)に広げる
            bubble.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        else:
            # アシスタント（左寄せ）
            # 0列目（バブル）と1列目（空きスペース）の幅の比率を4:1に設定
            bubble_container.grid_columnconfigure(0, weight=4)
            bubble_container.grid_columnconfigure(1, weight=1)
            # バブルを0列目に配置し、横幅いっぱい(ew)に広げる
            bubble.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        bubble_container.pack(fill="x", pady=(0, 5))


    def on_frame_configure(self, event=None):
        """フレームのサイズが変更された際に呼び出される（現在は未使用）"""
        pass

    def update_pagination_controls(self):
        """ページネーションボタンの状態とラベルを更新する"""
        total_pages = (len(self.all_logs) + self.logs_per_page - 1) // self.logs_per_page
        if total_pages == 0: total_pages = 1
        self.page_label.configure(text=f"Page {self.current_page + 1} / {total_pages}")

        self.prev_button.configure(state="normal" if self.current_page > 0 else "disabled")
        self.next_button.configure(state="normal" if (self.current_page + 1) < total_pages else "disabled")

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.display_page()

    def next_page(self):
        total_pages = (len(self.all_logs) + self.logs_per_page - 1) // self.logs_per_page
        if (self.current_page + 1) < total_pages:
            self.current_page += 1
            self.display_page()