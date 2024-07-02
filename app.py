from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
# DB 接続には flask_sqlalchemy を使用する
# Flask SQLAlchemy については下記ページを参照
# https://pypi.org/project/Flask-SQLAlchemy/
# https://flask-sqlalchemy.palletsprojects.com/en/3.1.x/

from flask_migrate import Migrate
# DB マイグレーション に使用する
# 詳細は下記ページを参照
# https://flask-migrate.readthedocs.io/en/latest/

from flask import abort
from flask import make_response

# Flask application インスタンスの作成
app = Flask(__name__)

# 使用するDB の指定 (SQLite で data.db ファイルを使用する) 
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"

# SQLAlchemy インスタンスの作成
db = SQLAlchemy(app)

# Flask-Migrate を使用するため Migrate インスタンスを作成
migrate = Migrate(app, db)

# -------- API のエンドポイントを定義 ------------------------------
# route() については下記ページなどを参照
# https://flask.palletsprojects.com/en/3.0.x/quickstart/#routing

# それぞれのURLについて、HTTPリクエストを受け取ったときの
# HTTPレスポンスを返す関数を定義する

# 在庫チェック
@app.route("/v1/stocks", methods=['GET']) # URLパス: /v1/stocks に GET リクエストが
def retrieve_stocks():                    # 送られたときのレスポンスを定義する
    if request.method == 'GET':
        # name をキーにして昇順ソートする
        all_stocks = Stock.query.order_by(Stock.name).all()
        
        # stocks テーブルの全てのデータをリストとして JSON 化してレスポンスとして返す
        # レスポンス ステータスを 200 に設定
        return jsonify(
            [stock.format() for stock in all_stocks]
        ), 200

# URLパス: /v1/stocks/<name> に GET リクエストが送られたときのレスポンスを定義する
# <name> の部分はパラメーター: name として関数中で使用できる
@app.route("/v1/stocks/<string:name>", methods=['GET'])                                                         
def retrieve_stock(name):                           
    if request.method == 'GET':
        
        # URL の <name> 部分で指定した名前の商品を stocks テーブルから探す
        stock = Stock.query.filter_by(name=name).first()
        if stock:
            # 在庫がある場合
            # テーブルから見つけたデータをJSONレスポンスとして返す
            return jsonify(
                stock.format()
            ), 200
        else:
            # 在庫がない場合
            # amount を 0 としてJSONレスポンスを返す
            return jsonify(
                {name: 0}
            ), 200

# 在庫の更新、作成
@app.route("/v1/stocks", methods=['POST'])
def add_stocks():
    if request.method == 'POST':
        
        # リクエストボディから name と amount の値を取得する
        name = request.get_json().get('name')
        amount = request.get_json().get('amount')
        
        # name の値チェック
        # ERROR となる場合は 400 エラーとする
        if name is None or not isinstance(name, str) or\
           not name.isalpha() or len(name) > 8:
            abort(400)
        
        # 上にあるので不要
        # amount = request.get_json().get('amount')
        
        # amount の値チェック
        # amount が リクエストボディに含まれない場合 amount = 1 とする
        if amount is None:
            amount = 1
        # ERROR となる場合 400 エラーとする
        if not isinstance(amount, int) or not amount > 0:
            abort(400)
            
        # 指定した名前の商品を stocks テーブルから探す
        stock = Stock.query.filter_by(name=name).first()
        if stock:
            # 存在する場合更新する
            # amount をプラスする
            stock.amount += amount

        else:
            # 存在しない場合作成する
            # 指定した amount でテーブルにデータを追加する
            stock = Stock(name=name, amount=amount)
            db.session.add(stock)
        # DBテーブルの更新を実行
        db.session.commit()
        
        # response インスタンスをつくる
        # リクエストボディの JSON と同じデータに設定する
        response = make_response(
            request.get_json()
        )
        
        # レスポンスヘッダの設定
        response.headers["Location"] = request.base_url + "/" + name
        return response
        
# 販売
@app.route("/v1/sales", methods=['POST'])
def sale_stocks():
    
    # リクエストボディから name, amount, price のデータを取得
    name = request.get_json().get('name')
    amount = request.get_json().get('amount')
    price = request.get_json().get('price')
    
    # amount が指定されていない場合は 1 に設定する
    if amount is None:
        amount = 1
    
    # name の値の条件チェック
    # 商品名は8文字以内であること、アルファベット小文字または大文字のみを含むこと
    if name is None or not isinstance(name, str) or\
    not name.isalpha() or len(name) > 8:
        abort(400)
    
    # amount の値の条件チェック
    # 整数であること、0より大きいこと
    if not isinstance(amount, int) or not amount > 0:
        abort(400)
    
    # 指定商品の在庫があるかどうかチェック
    # 在庫数が不足の場合 400 エラー
    stock = Stock.query.filter_by(name=name).first()
    if stock is None or stock.amount < amount:
        abort(400)

    # price が指定されていない場合
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
        
    # price の値の条件チェック
    # float タイプであること、0より大きいこと
    if not isinstance(price, float) or not price > 0:
        abort(400)
        
    # 販売分だけ在庫を減らす    
    stock.amount -= amount
    db.session.commit()
    
    # sales テーブルの "sales" データの取得
    sales = Sales.query.filter_by(name="sales").first()
    
    # データがない場合はテーブルに追加する
    if sales is None:
        sales = Sales(name="sales")
        db.session.add(sales)
        db.session.commit()
    
    # 売上に 販売価格 x 数量 を加算
    #sales.sales += Decimal(price * amount)
    sales.sales += price * amount
    db.session.commit()
    
    # レスポンスのボディをリクエストボディと同じ内容にする
    response = make_response(
        request.get_json()
    )
    
    # レスポンスヘッダーの設定
    response.headers["Location"] = request.base_url + "/" + name
    return response
    
# 売上チェック
@app.route("/v1/sales", methods=['GET'])
def check_stocks():
    
    # sales テーブルの name="sales"行データを取得
    sales = Sales.query.filter_by(name="sales").first()
    
    # データがない場合は"sales"行データを作成する
    if sales is None:
        sales = Sales(name="sales")
        db.session.add(sales)
        db.session.commit()
    
    # "sales"行のデータを JSON 化して返す
    return jsonify(
        sales.format()
    ), 200

# 全削除
@app.route("/v1/stocks", methods=['DELETE'])
def remove_stocks():
    # stocks テーブルのデータを全削除
    Stock.query.delete()
    db.session.commit()
    
    # sales テーブルのデータを全削除
    Sales.query.delete()
    db.session.commit()
    
    # 空の JSON データを返す
    return jsonify(
        {}
    ), 204

# ERROR 処理
# エラーハンドラーについては下記ページなどを参照
# https://flask.palletsprojects.com/en/3.0.x/errorhandling/
# https://flask.palletsprojects.com/en/3.0.x/api/#flask.Flask.errorhandler
@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        'message': "ERROR"
    }), 400
# --------------------------------------
# DBモデルの定義
# stocks テーブルと sales テーブルを定義する
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
    #sales = db.Column(db.Numeric(scale=2), default=0)
    sales = db.Column(db.REAL, default=0)
    
    def format(self):
        return {
            # "sales"行のデータを小数点第2位までの表示にフォーマットする(四捨五入する)
            "sales": float("{:.2f}".format(self.sales)),
        }
