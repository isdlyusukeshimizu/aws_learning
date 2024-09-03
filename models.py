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
