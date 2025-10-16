# i18n.py

STRINGS = {
    "ja": {
        "app_title": "My AI Pal",
        "chat_hint": "Palに話しかける...",
        "status_title": "Palのステータス",
        "learning_timeline_title": "学習のきろく",
        "drop_accepted": "{} を読み込みました！",
        "tooltip_status": "学習内容",
        "tooltip_log": "会話ログ",
        "tooltip_setting": "設定",
        "tooltip_back": "戻る",
        "tooltip_showlog": "クリックして会話ログを表示",
        "tooltip_mascothint": "PalにテキストやPDFファイルをドラッグアンドドロップしよう",
    },
    "en": {
        "app_title": "My AI Pal",
        "chat_hint": "Talk to Pal...",
        "status_title": "Pal's Status",
        "learning_timeline_title": "Learning Timeline",
        "drop_accepted": "Loaded {}!",
        "tooltip_status": "status",
        "tooltip_log": "chat log",
        "tooltip_setting": "setting",
        "tooltip_back": "back",
        "tooltip_showlog": "Click to view conversation log",
    }
}

PROMPTS = {
    "en": "Use the following context to answer the question. Context: {context} Question: {question} Answer:",
    "ja": "以下のコンテキスト情報だけを使って、質問に日本語で答えてください。コンテキスト: {context} 質問: {question} 回答:"
}

# 現在の言語
current_lang = "en"

def t(key):
    """指定されたキーの翻訳テキストを取得します。"""
    return STRINGS[current_lang].get(key, key)