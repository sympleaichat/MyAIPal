# core/pal_logic.py (最終版)
import os
import re
import json
from datetime import datetime
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_community.vectorstores import Chroma
from langchain_chroma import Chroma
from langchain_community.llms import LlamaCpp
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from .utils import resource_path

class PalLogic:
    def __init__(self):
        # ... (以前の__init__のコードは変更なし) ...
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        embed_model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self.embeddings = HuggingFaceEmbeddings(model_name=embed_model_name)


        self.db_path = "./pal_db"
        self.chat_log_path = "chat_log.json"
        self.db = Chroma(
            persist_directory=self.db_path,
            embedding_function=self.embeddings
        )

        # model_path = "./models/qwen2-1_5b-instruct-q4_k_m.gguf"
        # model_path = "./models/qwen2-0_5b-instruct-q4_k_m.gguf"
        # model_path = "./models/gemma-2b-it.Q4_K_M.gguf"
        # model_path = "./models/Phi-3-mini-4k-instruct-q4.gguf"

        # model_path = resource_path("./models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")
        model_path = resource_path("./models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")
        self.llm = LlamaCpp(
            model_path=model_path, n_gpu_layers=-1, n_batch=512, n_ctx=4096, verbose=False,
        )

        # ▼▼▼ ここから追加 ▼▼▼
        # プロンプト設定ファイルを読み込む処理
        # self.prompt_config_path = "prompt_config.json"
        self.prompt_config_path = resource_path("prompt_config.json")
        self.prompt_config = self._load_prompt_config()
        # ▲▲▲ ここまで追加 ▲▲▲
        print("PalLogic initialized.")


    # ▼▼▼ ここから追加 ▼▼▼
    def _load_prompt_config(self) -> dict:
        """prompt_config.jsonを読み込む。失敗した場合はデフォルト値を返す。"""
        try:
            with open(self.prompt_config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            print(f"Prompt configuration loaded from '{self.prompt_config_path}'.")
            return config
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load '{self.prompt_config_path}' ({e}). Using default prompts.")
            # ファイル読み込みに失敗した場合のフォールバック
            return {
                "system_prompt": "You are a helpful AI assistant.",
                "prompt_no_history": "Context: {context}\nQuestion: {question}\nAnswer:",
                "prompt_with_history": "History: {history}\nContext: {context}\nQuestion: {question}\nAnswer:"
            }
    # ▲▲▲ ここまで追加 ▲▲▲

    def _load_and_split_document(self, file_path: str):
        # ... (変更なし) ...
        try:
            if file_path.lower().endswith(".pdf"): loader = PyPDFLoader(file_path)
            elif file_path.lower().endswith(".txt"): loader = TextLoader(file_path, encoding="utf-8")
            else: return []
            documents = loader.load()
            return self.text_splitter.split_documents(documents)
        except Exception as e:
            print(f"Error processing document {file_path}: {e}")
            return []

    def learn_from_document(self, file_path: str):
        # ... (変更なし) ...
        chunks = self._load_and_split_document(file_path)
        if not chunks: return "No content to learn."
        self.db.add_documents(chunks)
        self.db.persist()
        filename = os.path.basename(file_path)
        return f"Finished learning '{filename}'!"

    # --- ↓↓↓ ここから追加 ↓↓↓ ---
    def ask_question(self, query: str, history: list, config: dict) -> str:
        """
        【メインの質問応答メソッド】
        履歴の有無に応じてプロンプトを切り替えます。
        """
        print(f"Received question: {query}")
        retriever = self.db.as_retriever(search_kwargs={"k": 3})

        # --- configから設定値を取得 ---
        ai_name = config.get("ai_name", "Assistant")
        user_name = config.get("user_name", "User")
        
        # get_tone_descriptionは常に同じシンプルな指示を返す
        system_prompt = "You are a helpful AI assistant."

        # ▼▼▼ ここからが変更点 ▼▼▼
        # 設定ファイルからシステムプロンプトを取得
        system_prompt = self.prompt_config["system_prompt"]

        # もし会話履歴(history)が空っぽの場合
        system_prompt = self.prompt_config["system_prompt"]

        if not history:
            print("History is empty. Using a prompt without history section.")
            # 設定ファイルから履歴なしテンプレートを取得
            base_template = self.prompt_config["prompt_no_history"]
            # テンプレートにシステムプロンプトと変数名を埋め込む
            prompt_template = base_template.format(
                system_prompt=system_prompt, user_name=user_name, ai_name=ai_name
            )
            prompt = PromptTemplate.from_template(prompt_template)
            chain = (
                {"context": retriever, "question": RunnablePassthrough()}
                | prompt | self.llm | StrOutputParser()
            )
        else:
            print("History exists. Using a prompt with history section.")
            history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])
            # 設定ファイルから履歴ありテンプレートを取得
            base_template = self.prompt_config["prompt_with_history"]
            # テンプレートにシステムプロンプトと変数名を埋め込む
            prompt_template = base_template.format(
                system_prompt=system_prompt, user_name=user_name, ai_name=ai_name
            )
            prompt = PromptTemplate.from_template(prompt_template)
            chain = (
                {"context": retriever, "question": RunnablePassthrough(), "history": lambda x: history_str}
                | prompt | self.llm | StrOutputParser()
            )

        # ▲▲▲ ここまでが変更点 ▲▲▲

        # チェーンを実行して回答を生成
        try:
            answer = chain.invoke(query)
            print(f"Generated answer: {answer}")
            return answer
        except Exception as e:
            print(f"Error during chain execution: {e}")
            return "Sorry, an error occurred while generating the answer."

            
    def learn_from_history(self):
        """
        chat_log.jsonを読み込み、未学習の会話をDBに学習させる
        """
        # 1. ログファイルを読み込む
        try:
            with open(self.chat_log_path, "r", encoding="utf-8") as f:
                log_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return "No chat history found."

        # 2. 未学習のメッセージを抽出
        unlearned_entries = [entry for entry in log_data if not entry.get("learned")]
        
        if not unlearned_entries:
            return "No new conversations to learn."

        # 3. 未学習メッセージを1つのテキストに整形
        formatted_text = "\n".join(
            [f"{entry['role']}: {entry['content']}" for entry in unlearned_entries]
        )

        # 4. テキストをチャンク分割してDBに追加
        chunks = self.text_splitter.split_text(formatted_text)
        if not chunks:
            return "Failed to process chat history."
        
        # LangChainのDocument形式に変換
        from langchain_core.documents import Document
        documents_to_add = [Document(page_content=chunk) for chunk in chunks]

        self.db.add_documents(documents_to_add)
        self.db.persist()

        # 5. 学習済みフラグを更新
        for entry in log_data:
            if not entry.get("learned"):
                entry["learned"] = True
        
        # 6. JSONファイルを更新
        with open(self.chat_log_path, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        message = f"Learned from {len(unlearned_entries)} new messages."
        print(message)
        return message

    def get_tone_description(self, tone_name: str, ai_name: str) -> str:
        """口調の名前からシステムプロンプトを返す"""
        tones = {
        "Friendly": f"""You are {ai_name}, a friendly and caring AI companion. Your primary goal is to be helpful and supportive to the user.
**Personality:**
- Always be cheerful, positive, and encouraging.
- Speak in a simple, gentle, and easy-to-understand manner.
- Use friendly and casual language (e.g., "Hey there!", "Let's see...").
- You can use simple, positive emojis like :) or !.""",
        "Polite": f"""You are {ai_name}, a sophisticated and polite AI assistant. Your primary role is to serve the user with respect and efficiency.
**Personality:**
- Always use formal and respectful language (e.g., "Certainly," "At your service,").
- Maintain a calm, composed, and professional demeanor.
- Be proactive by offering suggestions.
- Avoid slang and casual language.""",
        "Concise": f"""You are {ai_name}, a professional and highly efficient AI assistant. Your purpose is to provide information and complete tasks as quickly and accurately as possible.
**Personality:**
- Be direct and to the point.
- Avoid greetings, apologies, and unnecessary conversational filler.
- Use clear, objective, and neutral language.
- Do not use emojis or emotional language."""
    }

        return tones.get(tone_name, "You are a helpful AI assistant.") # デフォルトも少し良くしました

    def get_db_size(self) -> float:
        """データベースディレクトリの合計サイズをMB単位で計算する"""
        total_size = 0
        if not os.path.exists(self.db_path):
            return 0.0
        for dirpath, dirnames, filenames in os.walk(self.db_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        return total_size / (1024 * 1024) # MBに変換

    def get_learning_stats(self) -> dict:
        """学習したドキュメントの統計情報を取得する"""
        if not os.path.exists(self.db_path):
            return {
                "doc_count": 0, "word_count": 0, "last_learned": "N/A",
                "all_text": "", "db_size": 0.0
            }
        
        # データベースからすべてのドキュメントとメタデータを取得
        db_content = self.db.get(include=["metadatas", "documents"])
        
        # ドキュメント数をカウント
        sources = [meta.get('source') for meta in db_content.get('metadatas', []) if meta]
        unique_sources = set(sources)
        doc_count = len(unique_sources)

        # 全テキストを結合し、単語数をカウント
        all_text = " ".join(db_content.get('documents', []))
        word_count = len(all_text.split())

        # 最後に学習した日を取得 (メタデータから最新の日付を探す)
        # ChromaDBはドキュメント追加日を保存しないため、ソースファイルの最終更新日時で代用
        last_learned_date = None
        if unique_sources:
            latest_time = 0
            for source_path in unique_sources:
                try:
                    mod_time = os.path.getmtime(source_path)
                    if mod_time > latest_time:
                        latest_time = mod_time
                except FileNotFoundError:
                    continue # ファイルが移動・削除された場合はスキップ
            if latest_time > 0:
                last_learned_date = datetime.fromtimestamp(latest_time).strftime("%Y-%m-%d")

        return {
            "doc_count": doc_count,
            "word_count": word_count,
            "last_learned": last_learned_date if last_learned_date else "Not available",
            "all_text": all_text,
            "db_size": self.get_db_size()
        }