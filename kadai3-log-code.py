project_v2/
│
├── app.py          # Flaskアプリケーションインスタンスの定義
├── models.py       # データベースモデル
├── controller.py   # 関数等
└── main.py         # エントリーポイント



・アプリケーションの設定（app.py）

def create_app():

    # Flask applicationインスタンスの作成
    app = Flask(__name__)

    # 使用するDBの指定 (SQLiteでdata.dbファイルを使用する) 
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"

    # アプリケーションとデータベースを関連付ける
    db.init_app(app)

    # DBマイグレーションに使用する。詳細は下記ページを参照
    # https://flask-migrate.readthedocs.io/en/latest/
    # Flask-Migrateを使用するためMigrateインスタンスを作成
    # これにより、データベースのスキーマ変更が容易に行えるようになる
    migrate = Migrate(app, db)

    # APIのバージョン管理のためにBlueprintを作成
    # 古いバージョンのAPIを使っているクライアントに対して後方互換性を維持したまま、
    # 新しいバージョンを提供することが可能になる
    v1 = Blueprint('v1', __name__, url_prefix='/v1')

    # URLルールを追加し、それぞれのURLに対応するコントローラの関数を指定
    v1.add_url_rule('/stocks', 'retrieve_stocks_v1', controller.retrieve_stocks_v1, methods=['GET'])
    v1.add_url_rule('/stocks/<string:name>', 'retrieve_stock_v1', controller.retrieve_stock_v1, methods=['GET'])
    v1.add_url_rule('/stocks', 'add_stocks_v1', controller.add_stocks_v1, methods=['POST'])
    v1.add_url_rule('/sales', 'sale_stocks_v1', controller.sale_stocks_v1, methods=['POST'])
    v1.add_url_rule('/sales', 'check_sales_v1', controller.check_sales_v1, methods=['GET'])
    v1.add_url_rule('/stocks', 'remove_stocks_v1', controller.remove_stocks_v1, methods=['DELETE'])

    # 作成したBlueprintをアプリケーションに登録
    app.register_blueprint(v1)

    # ERROR 処理
    # エラーハンドラーについては下記ページなどを参照
    # https://flask.palletsprojects.com/en/3.0.x/errorhandling/
    # https://flask.palletsprojects.com/en/3.0.x/api/#flask.Flask.errorhandler

    # クライアントからのリクエストが不正な場合
    @app.errorhandler(400)
    def bad_request(error):
        return controller.bad_request_v1(error)

    # リクエストされたリソースが見つからない
    @app.errorhandler(404)
    def not_found(error):
        return controller.not_found_v1(error)

    # 許可されていないメソッド
    @app.errorhandler(405)
    def method_not_allowed(error):
        return controller.method_not_allowed_v1(error)

    return app



・データベースモデルの定義（models.py）

from flask_sqlalchemy import SQLAlchemy
# DB接続にはflask_sqlalchemyを使用する
# Flask SQLAlchemyについては下記ページを参照
# https://pypi.org/project/Flask-SQLAlchemy/
# https://flask-sqlalchemy.palletsprojects.com/en/3.1.x/

# SQLAlchemyインスタンスの作成
db = SQLAlchemy()

# ----------------DBモデルの定義----------------
# stocksテーブルとsalesテーブルを定義する
# テーブル含まれるカラムのタイプなどを指定する

# モデル定義については下記ページなど参照
# https://flask-sqlalchemy.palletsprojects.com/en/3.1.x/quickstart/#define-models
class Stock(db.Model):
    __tablename__ = 'stocks'
    name = db.Column(db.String(8), primary_key=True)
    amount = db.Column(db.Integer, default=0)

    def format(self):
        return {
            self.name: self.amount,
        }
    
class Sales(db.Model):
    __tablename__ = 'sales'
    name = db.Column(db.String, primary_key=True)
    sales = db.Column(db.REAL, default=0)
    
    def format(self):
        return {
            # "sales"行のデータを小数点第2位までの表示にフォーマットする(四捨五入する)
            "sales": float("{:.2f}".format(self.sales)),
        }



・在庫チェックの関数（controller.py）

def retrieve_stocks_v1():
    if request.method == 'GET':
        # nameをキーにして昇順ソートする
        all_stocks = Stock.query.order_by(Stock.name).all()
        
        # stocksテーブルの全てのデータをリストとしてJSON化してレスポンスとして返す
        # レスポンス ステータスを200に設定
        response_data = {}
        for stock in all_stocks:
            response_data.update(stock.format())
        return jsonify(response_data), 200

def retrieve_stock_v1(name):
    if request.method == 'GET':

        # nameの値チェック
        # ERRORとなる場合は400エラーとする
        if name is None or not isinstance(name, str) or\
           not name.isalpha() or len(name) > 8:
            abort(400)
        
        # URLの<name>部分で指定した名前の商品をstocksテーブルから探す
        stock = Stock.query.filter_by(name=name).first()
        if stock:
            # 在庫がある場合
            # テーブルから見つけたデータをJSONレスポンスとして返す
            return jsonify(
                stock.format()
            ), 200
        else:
            # 在庫がない場合
            # amountを0としてJSONレスポンスを返す
            return jsonify(
                {name: 0}
            ), 200



・在庫の更新・作成の関数（controller.py）

def add_stocks_v1():
    if request.method == 'POST':
        
        # リクエストボディからnameとamountの値を取得する
        name = request.get_json().get('name')
        amount = request.get_json().get('amount')
        
        # nameの値チェック
        # ERRORとなる場合は400エラーとする
        if name is None or not isinstance(name, str) or\
           not name.isalpha() or len(name) > 8:
            abort(400)
        
        # amountの値チェック
        # amountがリクエストボディに含まれない場合amount = 1とする
        if amount is None:
            amount = 1
        # ERRORとなる場合400エラーとする
        if not isinstance(amount, int) or not amount > 0:
            abort(400)
            
        # 指定した名前の商品をstocksテーブルから探す
        stock = Stock.query.filter_by(name=name).first()
        if stock:
            # 存在する場合更新する
            # amountをプラスする
            stock.amount += amount

        else:
            # 存在しない場合作成する
            # 指定したamountでテーブルにデータを追加する
            stock = Stock(name=name, amount=amount)
            db.session.add(stock)
        # DBテーブルの更新を実行
        db.session.commit()
        
        # responseインスタンスをつくる
        # リクエストボディのJSONと同じデータに設定する
        response = make_response(
            request.get_json()
        )
        
        # レスポンスヘッダの設定
        response.headers["Location"] = request.base_url + "/" + name
        return response



・販売の関数（controller.py）

def sale_stocks_v1():
    
    # リクエストボディからname, amount, priceのデータを取得
    name = request.get_json().get('name')
    amount = request.get_json().get('amount')
    price = request.get_json().get('price')
    
    # amountが指定されていない場合は1に設定する
    if amount is None:
        amount = 1
    
    # nameの値の条件チェック
    # 商品名は8文字以内であること、アルファベット小文字または大文字のみを含むこと
    if name is None or not isinstance(name, str) or\
    not name.isalpha() or len(name) > 8:
        abort(400)
    
    # amountの値の条件チェック
    # 整数であること、0より大きいこと
    if not isinstance(amount, int) or not amount > 0:
        abort(400)
    
    # priceの値の条件チェック
    # None、整数、浮動小数点のいずれかであること
    if price is not None and not (isinstance(price, int) or isinstance(price, float)):
        abort(400)
    
    # 指定商品の在庫があるかどうかチェック
    # 在庫数が不足の場合400エラー
    stock = Stock.query.filter_by(name=name).first()
    if stock is None or stock.amount < amount:
        abort(400)

    # priceが指定されていない場合
    if price is None:
        # 販売分だけ在庫を減らす    
        stock.amount -= amount
        db.session.commit()
        
        # レスポンスのボディをリクエストボディと同じ内容にする
        response = make_response(
            request.get_json()
        )
        # ヘッダーを指定してレスポンスを返す
        response.headers["Location"] = request.base_url + "/" + name
        return response
    else:
        price = float(price)
        
    # priceの値の条件チェック
    # floatタイプであること、0より大きいこと
    if not isinstance(price, float) or not price > 0:
        abort(400)
        
    # 販売分だけ在庫を減らす    
    stock.amount -= amount
    db.session.commit()
    
    # salesテーブルの"sales"データの取得
    sales = Sales.query.filter_by(name="sales").first()
    
    # データがない場合はテーブルに追加する
    if sales is None:
        sales = Sales(name="sales")
        db.session.add(sales)
        db.session.commit()
    
    # 売上に販売価格 x 数量 を加算
    sales.sales += price * amount
    db.session.commit()
    
    # レスポンスのボディをリクエストボディと同じ内容にする
    response = make_response(
        request.get_json()
    )
    
    # レスポンスヘッダーの設定
    response.headers["Location"] = request.base_url + "/" + name
    return response



※売上チェックと全削除のAPIは他APIと類似した構造を持っているため省略



・アプリケーションのエントリーポイント（main.py）

from app import create_app

# app.pyのcreate_app関数を呼び出してFlaskアプリケーションインスタンスを作成
app = create_app()

if __name__ == '__main__':
    app.run(host="54.65.196.247", port=80)
