import sys
import os

def resource_path(relative_path):
    """ 
    実行可能ファイル（.exe）からの相対パスを取得します。
    PyInstallerでビルドした場合と、通常のPython環境で実行した場合の両方に対応します。
    """
    try:
        # PyInstallerで作成された一時フォルダのパスを取得
        base_path = sys._MEIPASS
    except Exception:
        # 通常のPython環境で実行している場合
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    return os.path.join(base_path, relative_path)