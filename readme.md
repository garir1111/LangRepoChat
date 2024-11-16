# langRepoChat

## メンテナンス方針

本プロジェクトは現状のまま提供されており、今後のバグ修正やアップデートを保証しません。  
フォークや独自改変を自由に行ってください。

## 必須環境

- pipenv
- Python 3.10.5

## 推奨環境

- pyenv

## 使用方法

pipenv を導入したうえで、後述する 2 点の設定ファイルを準備し、下記コマンドを実行する．

```bash
pipenv install
pipenv run dev
```

## 各種設定ファイル

### .env

ルートディレクトリに新規作成し、下記形式で OpenAI のキー情報を入力する．

```env
OPENAI_API_KEY="..."
```

### config.yml

下記を書き換えてください．

```yml
# 必須の設定
CLONE_URL: "git@github.com:garir1111/langRepoChat.git" # クローンするリポジトリ
BRANCH: "main" # ブランチの指定

# オプションの設定
FILTER_EXT: "src" # 複数の拡張子をカンマ区切りで指定（半角スペースも許容）
DIR: "py" # ディレクトリをカンマ区切りで指定
LANG: "ja" # 言語設定（'ja' または 'en'）
```

CLONE_URL は、使用者がアクセス可能なリポジトリの URL を指定する．  
※private リポジトリでも、アクセス権さえあれば問題ない．

## 参考文献

1. [LangChain による「GitHub リポジトリを学習させる方法」](https://zenn.dev/umi_mori/books/prompt-engineer/viewer/github_repository_langchain_chatgpt)
2. [pyenv と pipenv の導入方法をまとめる(Windows 版)](https://zenn.dev/tikita/articles/f7a5bc16c36101)
3. [Pipenv を使った Python 開発まとめ - Qiita](https://qiita.com/y-tsutsu/items/54c10e0b2c6b565c887a)
4. [[Python].env ファイルで環境変数を設定する[python-dotenv] - Qiita](https://qiita.com/shown_it/items/2b85434e4e2658c484f4)
