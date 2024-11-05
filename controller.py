from flask import jsonify, request, abort, make_response
from models import db, Stock, Sales


# ----------------API のエンドポイントを定義----------------
# route()については下記ページなどを参照
# https://flask.palletsprojects.com/en/3.0.x/quickstart/#routing

# それぞれのURLについて、HTTPリクエストを受け取ったときの
# HTTPレスポンスを返す関数を定義する


# 在庫チェック
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

# 在庫の更新、作成
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

# 販売
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

# 売上チェック
def check_sales_v1():
    
    # salesテーブルのname="sales"行データを取得
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
def remove_stocks_v1():
    # stocks テーブルのデータを全削除
    Stock.query.delete()
    db.session.commit()
    
    # sales テーブルのデータを全削除
    Sales.query.delete()
    db.session.commit()
    
    # 空の JSON データを返す
    return jsonify(
        {}
    ), 200

# クライアントからのリクエストが不正な場合
def bad_request_v1(error):
    return jsonify({'message': "ERROR"}), 400

# リクエストされたリソースが見つからない
def not_found_v1(error):
    return jsonify({'message': "ERROR"}), 404

# 許可されていないメソッド
def method_not_allowed_v1(error):
    return jsonify({'message': "ERROR"}), 405
