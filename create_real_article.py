from datetime import datetime, timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import yfinance as yf

from langchain.prompts import ChatPromptTemplate
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from dotenv import load_dotenv, find_dotenv

DATABASE_URI = f"postgres://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@db:5423/{os.environ['POSTGRES_DB']}"

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
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


class StockDataFetcher:
    def __init__(self, tickers):
        self.tickers = tickers

    def fetch(self):
        all_data = []
        end_date = datetime.today().strftime("%Y-%m-%d")
        start_date = (datetime.today() - timedelta(days=7)).strftime("%Y-%m-%d")

        for ticker in self.tickers:
            data = yf.download(ticker, start=start_date, end=end_date, interval="1d")
            data.reset_index(inplace=True)
            data["Ticker"] = ticker
            all_data.append(data[["Date", "Ticker", "Close"]])

        all_data = pd.concat(all_data)
        pivoted_data = all_data.pivot(index="Date", columns="Ticker", values="Close")
        pivoted_data.fillna("N/A", inplace=True)

        return pivoted_data


class StockDataAnalyzer:
    def __init__(self):
        self.llm = OpenAI()
        self.template = """
        "You are a financial expert specializing in analyzing trends in the stock market. Your role involves the weekly assessment of market performance, evaluating key indicators such as opening and closing prices, highs and lows, volumes of trade, and changes in percentages. You dissect this data to understand the market's sentiment, whether positive, neutral, or negative. You distill complex financial jargon into clear, digestible reports, helping others to understand the subject matter at hand. Utilizing your deep understanding of the market, you interpret these factors to provide a concise summary of the week's events in the financial world."
        Include the dates in your analysis and start with: In this week (startdate - enddate) ...
        Weekly Stock data: {data}
        """
        self.prompt_template = ChatPromptTemplate.from_template(template=self.template)
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt_template)

    def analyze(self, data):
        return self.chain.predict(data=data)


from sqlalchemy.exc import SQLAlchemyError


from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager


class ArticleDatabase:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)

    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations."""
        session = self.Session()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            print("Failed to commit transaction. Error: ", str(e))
            session.rollback()
            raise
        finally:
            session.close()

    def insert_article(self, title, content, author):
        with self.session_scope() as session:
            article = Article(
                title=title,
                content=content,
                author=author,
                date_posted=datetime.utcnow(),
            )
            session.add(article)
            session.commit()
            return article.id

    def insert_stock_data(self, article_id, stock_data):
        with self.session_scope() as session:
            for date, data_per_date in stock_data.iterrows():
                for ticker, value in data_per_date.items():
                    stock_data = StockData(
                        date=date, ticker=ticker, value=value, article_id=article_id
                    )
                    session.add(stock_data)

    def insert_article_with_stock_data(self, title, content, author, stock_data):
        try:
            article_id = self.insert_article(title, content, author)
            self.insert_stock_data(article_id, stock_data)
        except Exception as e:
            print(
                f"Failed to insert stock data because article insertion failed. Error: {str(e)}"
            )


import os

if __name__ == "__main__":
    load_dotenv(find_dotenv())

    tickers = ["AAPL", "MSFT", "AMZN", "GOOGL", "BRK-B", "V", "JNJ", "WMT", "PG"]
    article_title = "Weekly Stock Market Analysis"
    article_author = "Financial Expert"

    fetcher = StockDataFetcher(tickers)
    analyzer = StockDataAnalyzer()
    db_host = "db"  # as specified in your Docker Compose file

    db_url = "postgresql://user:password@db:5432/dbname"

    db = ArticleDatabase(db_url=db_url)

    stock_data = fetcher.fetch()
    analysis = analyzer.analyze(stock_data)
    db.insert_article_with_stock_data(
        article_title, analysis, article_author, stock_data
    )
