from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from sqlalchemy.orm import joinedload
import pandas as pd

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://user:password@db/dbname"


db = SQLAlchemy(app)


class Article(db.Model):
    __tablename__ = "articles"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    stock_data = db.relationship("StockData", backref="article", lazy=True)


class StockData(db.Model):
    __tablename__ = "stock_data"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    ticker = db.Column(db.String(20), nullable=False)
    value = db.Column(db.Float, nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey("articles.id"), nullable=False)


@app.route("/article/<article_id>", methods=["GET"])
def article(article_id):
    article = Article.query.options(db.joinedload(Article.stock_data)).get(article_id)

    stock_data_list = [
        pd.DataFrame(
            [
                {
                    "Date": stock_data.date.strftime("%Y-%m-%d"),
                    "Ticker": stock_data.ticker,
                    "Value": stock_data.value,
                }
            ]
        )
        for stock_data in article.stock_data
    ]
    df = pd.concat(stock_data_list)
    df_pivot = df.pivot(index="Ticker", columns="Date", values="Value")

    return render_template("article.html", article=article, df=df_pivot)


@app.route("/")
def index():
    articles = Article.query.all()
    return render_template("index.html", articles=articles)


def create_tables():
    with app.app_context():
        db.create_all()
        db.session.commit()


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)

create_tables()
