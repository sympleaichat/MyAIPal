# ui/status_view.py
import customtkinter as ctk
from PIL import Image
import numpy as np
from wordcloud import WordCloud
import io
import threading
import random
from core.utils import resource_path

class StatusWindow(ctk.CTkToplevel):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.geometry("640x720") # Choose a good default size
        self.resizable(True, True)
        self.title("Pal's Status")

        # ウィンドウの背景色などを設定
        self.configure(fg_color=self.controller.theme_colors["bg_color"])

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1) # Word cloud area
        self.grid_rowconfigure(1, weight=0) # Stats area

        # --- ラベルと値の表示フレーム ---
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # --- ワードクラウド表示エリア ---
        self.wordcloud_label = ctk.CTkLabel(self.main_frame, text="Loading Knowledge Cloud...", fg_color=self.controller.theme_colors["wordcloud_bg"], corner_radius=10)
        self.wordcloud_label.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        self.main_frame.grid_rowconfigure(0, weight=1)

        # --- 統計情報表示エリア ---
        stats_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        stats_frame.grid(row=1, column=0, sticky="ew")
        stats_frame.grid_columnconfigure(1, weight=1)

        # 各統計情報のラベルと値
        self.doc_count_label = self._create_stat_row(stats_frame, 0, "Documents Learned:")
        self.word_count_label = self._create_stat_row(stats_frame, 1, "Total Knowledge:")
        self.last_learned_label = self._create_stat_row(stats_frame, 2, "Last Study Session:")
        self.db_size_label = self._create_stat_row(stats_frame, 3, "Memory Size:")

        # 閉じるボタン
        # close_button = ctk.CTkButton(self.main_frame, text="Close", command=self.destroy, fg_color="#555555", hover_color="#666666")
        # close_button.grid(row=2, column=0, sticky="ew", pady=(20, 0))

        # スレッドでデータ読み込みとUI更新を開始
        self.update_thread = threading.Thread(target=self.load_and_display_stats, daemon=True)
        self.update_thread.start()

    def _create_stat_row(self, parent, row, label_text):
        """統計情報の一行を作成するヘルパー関数"""
        label = ctk.CTkLabel(parent, text=label_text, anchor="w")
        label.grid(row=row, column=0, sticky="w", pady=2, padx=5)
        
        value_label = ctk.CTkLabel(parent, text="...", anchor="e")
        value_label.grid(row=row, column=1, sticky="e", pady=2, padx=5)
        return value_label

    def load_and_display_stats(self):
        """非同期で統計情報を取得し、UIを更新する"""
        try:
            stats = self.controller.logic.get_learning_stats()
            
            # メインスレッドでUIを更新
            self.after(0, self.update_ui, stats)
        except Exception as e:
            print(f"Error loading stats: {e}")
            self.after(0, self.wordcloud_label.configure, {"text": "Could not load stats."})

    def update_ui(self, stats):
        """取得した統計情報でUIを更新する"""
        if stats["doc_count"] == 0:
            self.wordcloud_label.configure(text="I haven't learned anything yet.\nDrag a file onto me to start!", image=None)
            self.doc_count_label.configure(text="0 documents")
            self.word_count_label.configure(text="0 words")
            self.last_learned_label.configure(text="N/A")
            self.db_size_label.configure(text="0.00 MB")
            return

        # 統計情報を更新
        self.doc_count_label.configure(text=f"{stats['doc_count']} documents")
        self.word_count_label.configure(text=f"{stats['word_count']:,} words") # 3桁カンマ区切り
        self.last_learned_label.configure(text=stats['last_learned'])
        self.db_size_label.configure(text=f"{stats['db_size']:.2f} MB")

        # ワードクラウドを生成
        self.generate_wordcloud(stats['all_text'])

    def generate_wordcloud(self, text):
        """ワードクラウド画像を生成して表示する"""
        try:
            # mask = np.array(Image.open("assets/brain_mask.png"))
            mask = np.array(Image.open(resource_path("assets/brain_mask.png")))

            # 修正箇所： colormap を color_func に変更
            wc = WordCloud(width=520, height=520, background_color=None, mode="RGBA",
                           max_words=100,
                           mask=mask,
                           color_func=self.theme_color_func).generate(text) # 👈 ここを変更

            pil_image = wc.to_image()
            ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(520, 520))
            self.wordcloud_label.configure(text="", image=ctk_image)
        except FileNotFoundError:
            self.wordcloud_label.configure(text="brain_mask.pngが見つかりません。", image=None)
            print("Error: brain_mask.png not found.")
        except Exception as e:
            self.wordcloud_label.configure(text="Error creating cloud.", image=None)
            print(f"Word cloud generation failed: {e}")


    def theme_color_func(self, word, font_size, position, orientation, **kwargs):
        """ワードクラウドの単語色をテーマカラーからランダムに選択する関数"""
        colors = [
            self.controller.theme_colors["accent_color"],
            self.controller.theme_colors["text_color"],
            self.controller.theme_colors["text_color"], # テキスト色を複数入れると出現頻度が上がる
            self.controller.theme_colors["text_color"],
        ]
        return random.choice(colors)