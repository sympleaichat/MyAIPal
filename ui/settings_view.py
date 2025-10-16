# ui/settings_view.py
import customtkinter as ctk
import os
from tkinter import messagebox
from core.utils import resource_path

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller

        # --- ウィンドウ設定 ---
        self.title("Settings")
        self.geometry("480x600")
        self.resizable(True, True)
        self.configure(fg_color=self.controller.theme_colors["bg_color"])
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(7, weight=1) # 空きスペースの行

        self.config = self.controller.get_config()
        theme_colors = self.controller.theme_colors

        # --- ▼▼▼ 以下、ウィジェットのrow番号を整理 ▼▼▼ ---

        # Row 0: テーマ設定
        theme_frame = ctk.CTkFrame(self, fg_color="transparent")
        theme_frame.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="ew")
        ctk.CTkLabel(theme_frame, text="Appearance", font=ctk.CTkFont(weight="bold")).pack(side="left")
        self.theme_switcher = ctk.CTkSegmentedButton(
            theme_frame, values=["Light", "Dark"], command=self.switch_theme,
            selected_color=theme_colors["accent_color"], selected_hover_color=theme_colors["accent_color"],
        )
        self.theme_switcher.pack(side="right")
        self.theme_switcher.set(self.config.get("theme", "Dark").title())

        # Row 1-3: プロフィール設定
        ctk.CTkLabel(self, text="Your Name").grid(row=1, column=0, padx=20, pady=10, sticky="w")
        self.user_name_entry = ctk.CTkEntry(self)
        self.user_name_entry.grid(row=1, column=1, padx=20, pady=10, sticky="ew")
        self.user_name_entry.insert(0, self.config.get("user_name", "User"))

        ctk.CTkLabel(self, text="AI's Name").grid(row=2, column=0, padx=20, pady=10, sticky="w")
        self.ai_name_entry = ctk.CTkEntry(self)
        self.ai_name_entry.grid(row=2, column=1, padx=20, pady=10, sticky="ew")
        self.ai_name_entry.insert(0, self.config.get("ai_name", "Pal"))

        # ctk.CTkLabel(self, text="AI's Tone").grid(row=3, column=0, padx=20, pady=10, sticky="w")
        # self.ai_tone_menu = ctk.CTkComboBox(self, values=["Friendly", "Polite", "Concise"], button_color=theme_colors["accent_color"])
        # self.ai_tone_menu.grid(row=3, column=1, padx=20, pady=10, sticky="ew")
        # self.ai_tone_menu.set(self.config.get("ai_tone", "Friendly"))

        # Row 4: キャラクター設定
        ctk.CTkLabel(self, text="Character", font=ctk.CTkFont(weight="bold")).grid(row=4, column=0, padx=20, pady=10, sticky="w")
        # asset_path = "assets"
        asset_path = resource_path("assets")
        available_packs = [d for d in os.listdir(asset_path) if os.path.isdir(os.path.join(asset_path, d)) and d not in ["icons", "fonts"]]
        self.character_menu = ctk.CTkComboBox(
            self, values=[pack.title() for pack in available_packs],
            button_color=theme_colors["accent_color"]
        )
        self.character_menu.grid(row=4, column=1, padx=20, pady=10, sticky="ew")
        self.character_menu.set(self.config.get("character_pack", "pal").title())

        # Row 5: フォント設定
        ctk.CTkLabel(self, text="Font Face", font=ctk.CTkFont(weight="bold")).grid(row=5, column=0, padx=20, pady=10, sticky="w")
        # fonts_path = "assets/fonts"
        fonts_path = resource_path("assets/fonts")
        try:
            available_fonts = [f for f in os.listdir(fonts_path) if f.lower().endswith(('.ttf', '.otf'))]
            if not available_fonts: available_fonts = ["Default"]
        except FileNotFoundError:
            available_fonts = ["Default"]
        
        self.font_menu = ctk.CTkComboBox(self, values=available_fonts, button_color=theme_colors["accent_color"])
        self.font_menu.grid(row=5, column=1, padx=20, pady=10, sticky="ew")
        self.font_menu.set(self.config.get("font_face", "Default"))

        # Row 6: フォントサイズ設定
        ctk.CTkLabel(self, text="Font Size", font=ctk.CTkFont(weight="bold")).grid(row=6, column=0, padx=20, pady=10, sticky="w")
        font_size_frame = ctk.CTkFrame(self, fg_color="transparent")
        font_size_frame.grid(row=6, column=1, padx=20, pady=10, sticky="ew")
        font_size_frame.grid_columnconfigure(0, weight=1)
        self.font_size_slider = ctk.CTkSlider(font_size_frame, from_=10, to=24, number_of_steps=14, command=self.update_font_size_label)
        self.font_size_slider.grid(row=0, column=0, sticky="ew")
        self.font_size_slider.set(self.config.get("font_size", 16))
        self.font_size_label = ctk.CTkLabel(font_size_frame, width=20)
        self.font_size_label.grid(row=0, column=1, padx=(10, 0))
        self.update_font_size_label(self.font_size_slider.get())

        # Row 7: Proactive Chat設定 (重複を削除し、ここに配置)
        proactive_frame = ctk.CTkFrame(self, fg_color="transparent")
        proactive_frame.grid(row=7, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        ctk.CTkLabel(proactive_frame, text="Proactive Chat", font=ctk.CTkFont(weight="bold")).pack(side="left")
        self.proactive_switch = ctk.CTkSwitch(
            proactive_frame, text="", onvalue=True, offvalue=False,
            progress_color=theme_colors.get("accent_color")
        )
        self.proactive_switch.pack(side="right")
        if self.config.get("proactive_chat", True):
            self.proactive_switch.select()
        else:
            self.proactive_switch.deselect()

        # --- 保存ボタン ---
        save_button = ctk.CTkButton(
            self, text="Save & Close", command=self.save_and_close,
            fg_color=theme_colors["accent_color"], hover_color=theme_colors["hover_color"]
        )
        save_button.grid(row=8, column=0, columnspan=2, padx=20, pady=20, sticky="s")
    
    def update_font_size_label(self, value):
        self.font_size_label.configure(text=str(int(value)))

    def switch_theme(self, value):
        pass

    def save_and_close(self):
        old_config = self.controller.get_config()
        
        new_config = {
            "user_name": self.user_name_entry.get(),
            "ai_name": self.ai_name_entry.get(),
            # "ai_tone": self.ai_tone_menu.get(),
            "ai_tone": "Friendly",
            "theme": self.theme_switcher.get().lower(),
            "character_pack": self.character_menu.get().lower(),
            "font_face": self.font_menu.get(),
            "font_size": int(self.font_size_slider.get()),
            "proactive_chat": self.proactive_switch.get(),
            "width": self.config.get("width"),
            "height": self.config.get("height")
        }

        self.controller.save_config(new_config)

        if (old_config.get("theme") != new_config["theme"] or
            old_config.get("character_pack") != new_config["character_pack"] or
            old_config.get("font_face") != new_config["font_face"] or
            old_config.get("font_size") != new_config["font_size"]):
            messagebox.showinfo(
                "Restart Required",
                "Appearance settings have been changed.\nPlease restart the application to apply them."
            )
        
        self.destroy()