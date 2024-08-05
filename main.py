from app import create_app

# create_app関数を呼び出してFlaskアプリケーションインスタンスを作成する
app = create_app()

if __name__ == '__main__':
    app.run(host="54.65.196.247", port=80)
