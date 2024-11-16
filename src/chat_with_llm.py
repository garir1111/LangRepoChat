import shutil
import asyncio
import os
import yaml
import flet as ft
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import GitLoader
from langchain.indexes import VectorstoreIndexCreator
import datetime
from dotenv import load_dotenv
import stat

config_path = 'config.yml'

# .env からAPIキーを読み込む
dotenv_loaded = load_dotenv(override=True)
openApiKey = os.getenv('OPENAI_API_KEY')


def load_config():
    with open(config_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)


config = load_config()


def show_error_and_exit(page, message):
    def close_app(e):
        page.window_close()
    page.dialog = ft.AlertDialog(
        title=ft.Text("Error"),
        content=ft.Text(message),
        actions=[ft.TextButton("OK", on_click=close_app)]
    )
    page.dialog.open = True
    page.update()


if not dotenv_loaded:
    ft.app(target=lambda page: show_error_and_exit(page, ".envファイルが読み込めません"))
    exit()

if not config:
    ft.app(target=lambda page: show_error_and_exit(page, "config.ymlファイルが読み込めません"))
    exit()

clone_url = config.get('CLONE_URL')
branch = config.get('BRANCH')
filter_ext = [f".{ext.strip()}" for ext in config.get('FILTER_EXT', '').split(',')]
dir = config.get('DIR', '').split(',') if config.get('DIR') else []
lang = config.get('LANG', 'ja')

if not clone_url or not branch:
    ft.app(target=lambda page: show_error_and_exit(page, "CLONE_URL または BRANCH が config.yml に設定されていません"))
    exit()

if not openApiKey:
    print("Error: OPENAI_API_KEY is not set.")
    ft.app(target=lambda page: show_error_and_exit(page, "OPENAI_API_KEY が .env に設定されていません"))
    exit()

embedding = OpenAIEmbeddings(openai_api_key=openApiKey)
llm = OpenAI(temperature=0)
repo_path = "./temp/"
filter_ext = tuple(filter_ext) if filter_ext else None

# チャットログ用フォルダの設定
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'chatlog')
os.makedirs(log_dir, exist_ok=True)
log_file_path = os.path.join(log_dir, f'chatlog_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.txt')


# パーミッションエラー時にファイルのアクセス権を変更して再試行する
def handle_remove_readonly(func, path, excinfo):
    # エラーがパーミッションエラーの場合、ファイルを再度書き込み可能にする
    if isinstance(excinfo[1], PermissionError):
        os.chmod(path, stat.S_IWRITE)
        func(path)


async def initialize_app(page):
    # tempディレクトリが存在する場合は削除して再クローンできるようにする
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path, onerror=handle_remove_readonly)

    loader = GitLoader(
        clone_url=clone_url,
        branch=branch,
        repo_path=repo_path,
        file_filter=lambda file_path: (
            (file_path.endswith(filter_ext) if filter_ext else True) and (any(directory in file_path for directory in dir) if dir else True)
        ),
    )

    global index
    index = VectorstoreIndexCreator(
        vectorstore_cls=Chroma,
        embedding=embedding,
    ).from_loaders([loader])

    page.clean()  # 読み込み画面をクリア
    load_main_ui(page)  # メインUIを読み込む


def load_main_ui(page: ft.Page):
    chat_box = ft.Column()
    scrollable_chat_box = ft.Column(
        controls=[chat_box],
        scroll="auto",
        expand=True
    )

    initial_message = f"{clone_url}の{branch}ブランチで、{dir}にある拡張子が{filter_ext}のファイルを学習済みです\n" if lang == 'ja' else f"{filter_ext} files in {dir} on the {branch} branch from {clone_url}\n"
    chat_box.controls.append(ft.Text(f"{initial_message}", color=ft.colors.BLUE, size=18))  # フォントサイズ18
    page.update()

    with open(log_file_path, 'a', encoding='utf-8') as log_file:
        log_file.write(initial_message)

    user_input = ft.TextField(
        hint_text="質問を入力してください..." if lang == 'ja' else "Enter your Question...",
        expand=True
    )

    def send_message(e):
        query = user_input.value
        timestamp = datetime.datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
        if query.strip().lower() == "exit":
            page.window_close()
            return
        if query:
            sanitized_query = query.replace("\n", "")
            chat_box.controls.append(ft.Text(f"Q: {sanitized_query}", color=ft.colors.GREEN, size=16))  # フォントサイズ16
            page.update()
            localize_query = f"{'日本語で答えてください' if lang == 'ja' else 'Please answer in English'}: {sanitized_query}"

            answer = index.query(localize_query, llm=llm)
            sanitized_answer = answer.replace("\n", "")
            chat_box.controls.append(ft.Text(f"A: {sanitized_answer}", color=ft.colors.BLUE, size=16))  # フォントサイズ16
            chat_box.controls.append(ft.Divider())

            with open(log_file_path, 'a', encoding='utf-8') as log_file:
                log_file.write(f"Q:, {timestamp}, {sanitized_query}, A:, {sanitized_answer}\n")

            user_input.value = ""
            page.update()

    submit_text = "送信" if lang == 'ja' else "Submit"
    send_button = ft.ElevatedButton(submit_text, on_click=send_message)

    page.add(
        ft.Column([
            scrollable_chat_box,
            ft.Row([
                user_input,
                send_button
            ], alignment=ft.MainAxisAlignment.CENTER)
        ], alignment=ft.MainAxisAlignment.END, expand=True)
    )


async def main(page: ft.Page):
    page.title = "Chat with LLM"

    # プログレスリングとテキストを表示するコンテナ
    loading_text = ft.Text("読み込み中です...", color=ft.colors.BLUE, size=20)  # フォントサイズ20
    loading_spinner = ft.ProgressRing(width=50, height=50)
    loading_container = ft.Column(
        [loading_spinner, loading_text],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )

    # 中央揃えを行うためにContainerでラップ
    centered_container = ft.Container(
        content=loading_container,
        alignment=ft.alignment.center,  # 水平方向と垂直方向両方を中央に揃える
        expand=True
    )

    # ページに読み込み中のUIを追加して更新
    page.add(centered_container)
    page.update()

    # ちょっとした待機を追加して確実に表示
    await asyncio.sleep(0.1)

    # 非同期でアプリの初期化を実行
    await initialize_app(page)


# アプリケーションを実行
if __name__ == "__main__":
    try:
        ft.app(target=main)
    finally:
        pass
