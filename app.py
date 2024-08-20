from flask import Flask, Blueprint
from flask_sqlalchemy import SQLAlchemy

from flask_migrate import Migrate
# DBマイグレーションに使用する
# 詳細は下記ページを参照
# https://flask-migrate.readthedocs.io/en/latest/

import controller
from models import db

def create_app():

    # Flask applicationインスタンスの作成
    app = Flask(__name__)

    # 使用するDBの指定 (SQLiteでdata.dbファイルを使用する) 
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"

    # アプリケーションとデータベースを関連付ける
    db.init_app(app)

    # Flask-Migrateを使用するためMigrateインスタンスを作成
    migrate = Migrate(app, db)

    # APIのバージョン管理のためにBlueprintを作成
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
