import customtkinter as ctk
from i18n import t

# --- ヘルプの内容をここに定義 ---
# 後からこのリストを編集するだけで、ページ数や内容を変更できます
HELP_PAGES = [
    {
        "title": "Welcome to My AI Pal!",
        "content": "This is a personal AI assistant that learns from your documents.\n\nLet's see how to use it!"
    },
    {
        "title": "How to Teach Pal",
        "content": "Simply drag and drop your text files (.txt) or PDF files onto Pal's image.\n\nPal will read them and remember their content."
    },
    {
        "title": "How to Chat",
        "content": "Use the input box at the bottom to ask Pal questions.\n\nPal will use its learned knowledge and general knowledge to answer you."
    },
    {
        "title": "Other Features",
        "content": "You can check the chat log, Pal's status, and change settings using the icon buttons."
    }
]

class HelpWindow(ctk.CTkToplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Help")
        self.geometry("720x560")
        self.resizable(False, False)

        self.current_page_index = 0

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --- ウィジェットの作成 ---
        self.title_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=18, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.content_label = ctk.CTkLabel(self, text="", wraplength=500, justify="left")
        self.content_label.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

        # --- ナビゲーションボタン ---
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.grid(row=2, column=0, padx=20, pady=20, sticky="ew")
        nav_frame.grid_columnconfigure(1, weight=1)

        self.prev_button = ctk.CTkButton(nav_frame, text="< Prev", command=self.go_prev)
        self.prev_button.grid(row=0, column=0)

        self.page_number_label = ctk.CTkLabel(nav_frame, text="")
        self.page_number_label.grid(row=0, column=1)

        self.next_button = ctk.CTkButton(nav_frame, text="Next >", command=self.go_next)
        self.next_button.grid(row=0, column=2)
        
        # 最初のページを表示
        self.update_page()

    def update_page(self):
        """現在のページ番号に基づいて表示を更新する"""
        page_data = HELP_PAGES[self.current_page_index]
        self.title_label.configure(text=page_data["title"])
        self.content_label.configure(text=page_data["content"])
        self.page_number_label.configure(text=f"Page {self.current_page_index + 1} / {len(HELP_PAGES)}")

        # ボタンの有効/無効を切り替え
        self.prev_button.configure(state="normal" if self.current_page_index > 0 else "disabled")
        self.next_button.configure(state="normal" if self.current_page_index < len(HELP_PAGES) - 1 else "disabled")

    def go_next(self):
        if self.current_page_index < len(HELP_PAGES) - 1:
            self.current_page_index += 1
            self.update_page()

    def go_prev(self):
        if self.current_page_index > 0:
            self.current_page_index -= 1
            self.update_page()