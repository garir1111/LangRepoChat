import sys
import argparse
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import GitLoader
from langchain.indexes import VectorstoreIndexCreator
import os
from dotenv import load_dotenv
load_dotenv()

# 引数の設定
parser = argparse.ArgumentParser(description='Run LangChain with GitLoader.')
parser.add_argument('--clone_url', type=str, required=True, help='URL of the Git repository to clone.')
parser.add_argument('--branch', type=str, required=True, help='Branch of the Git repository to use.')
parser.add_argument('--filter_ext', type=str, required=True, nargs='+', help='File extensions to filter for loading.')
parser.add_argument('--lang', type=str, choices=['ja', 'en'], required=True, help='Language for response (ja: Japanese, en: English).')

args = parser.parse_args()

# 引数の検証
if not args.clone_url or not isinstance(args.branch, str) or not all(ext.startswith('.') for ext in args.filter_ext):
    print("invalid args")
    sys.stdout.flush()
    sys.exit(1)

# 環境の設定と初期化
openApiKey = os.getenv('OPENAI_API_KEY')
embedding = OpenAIEmbeddings(openai_api_key=openApiKey)
llm = OpenAI(temperature=0)

# Gitリポジトリのロード
loader = GitLoader(
    clone_url=args.clone_url,
    branch=args.branch,
    repo_path='./temp/',
    file_filter=lambda file_path: file_path.endswith(tuple(args.filter_ext)) and 'src/' in file_path,
)

# インデックス作成
index = VectorstoreIndexCreator(
    vectorstore_cls=Chroma,
    embedding=embedding,
).from_loaders([loader])

# 準備完了通知
print("ready!")
sys.stdout.flush()

# クエリを処理
while True:
    query = sys.stdin.readline().strip()
    if query.lower() == 'exit':
        break

    # 言語に応じたクエリを追加
    if args.lang == 'ja':
        localize_query = f"日本語で答えてください: {query}"
    elif args.lang == 'en':
        localize_query = f"Please answer in English: {query}"

    # LangChainでクエリを実行し結果を取得
    answer = index.query(localize_query, llm=llm)

    # 結果を出力
    print(f"{answer}")
    print("ready!")  # 次のクエリ受付のためにreadyを出力
    sys.stdout.flush()  # 結果とreadyを即座に出力

print("Processing... done!")
sys.stdout.flush()
