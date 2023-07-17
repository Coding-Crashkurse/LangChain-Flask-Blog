import sqlite3
from datetime import datetime
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from langchain.prompts import ChatPromptTemplate
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from dotenv import load_dotenv, find_dotenv


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

        print(pivoted_data)
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


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
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
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def insert_article(self, title, content, author):
        with self.session_scope() as session:
            sql = """
            INSERT INTO articles (title, content, author, date_posted) VALUES (:title, :content, :author, :date_posted);
            """
            current_date = datetime.now()
            article_data = {
                "title": title,
                "content": content,
                "author": author,
                "date_posted": current_date,
            }
            session.execute(sql, article_data)
            session.flush()
            article_id = session.execute("SELECT LASTVAL();").scalar()

            return article_id

    def insert_stock_data(self, article_id, stock_data):
        with self.session_scope() as session:
            for date, data_per_date in stock_data.iterrows():
                for ticker, value in data_per_date.items():
                    sql = """
                    INSERT INTO stock_data (date, ticker, value, article_id) VALUES (:date, :ticker, :value, :article_id);
                    """
                    date_str = date.strftime("%Y-%m-%d")  # convert the date to a string
                    stock_data = {
                        "date": date_str,
                        "ticker": ticker,
                        "value": value,
                        "article_id": article_id,
                    }
                    session.execute(sql, stock_data)

    def insert_article_with_stock_data(self, title, content, author, stock_data):
        try:
            article_id = self.insert_article(title, content, author)
            self.insert_stock_data(article_id, stock_data)
            print("Successfully inserted data.")
        except Exception as e:
            print(f"An error occurred: {e}")


if __name__ == "__main__":
    load_dotenv(find_dotenv())

    tickers = ["AAPL", "MSFT", "AMZN", "GOOGL", "BRK-B", "V", "JNJ", "WMT", "PG"]
    db_path = "app.db"
    article_title = "Weekly Stock Market Analysis"
    article_author = "Financial Expert"

    fetcher = StockDataFetcher(tickers)
    analyzer = StockDataAnalyzer()
    db_url = "postgresql://user:password@localhost:5432/mydatabase"
    db = ArticleDatabase(db_url)

    stock_data = fetcher.fetch()
    analysis = analyzer.analyze(stock_data)
    db.insert_article_with_stock_data(
        article_title, analysis, article_author, stock_data
    )
