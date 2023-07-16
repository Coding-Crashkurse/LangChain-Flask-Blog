from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "app.db")

db = SQLAlchemy(app)


class Article(db.Model):
    __tablename__ = "articles"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


@app.route("/article/<int:article_id>")
def article(article_id):
    article = Article.query.get(article_id)
    if article is None:
        return "Article not found", 404
    return render_template("article.html", article=article)


@app.route("/")
def index():
    articles = Article.query.all()
    return render_template("index.html", articles=articles)


def create_tables():
    with app.app_context():
        db.create_all()
        db.session.commit()


if __name__ == "__main__":
    create_tables()
    app.run(debug=True)
