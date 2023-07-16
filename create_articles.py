import sqlite3
from datetime import datetime


def create_fake_articles():
    conn = sqlite3.connect("app.db")
    cur = conn.cursor()

    sql = """
    INSERT INTO articles (title, content, author, date_posted) VALUES (?, ?, ?, ?);
    """

    current_date = datetime.now().strftime("%Y-%m-%d")

    data1 = (
        "Fake Article 1",
        "This is a fake article for testing.",
        "Author 1",
        current_date,
    )
    data2 = (
        "Fake Article 2",
        "This is another fake article for testing.",
        "Author 2",
        current_date,
    )

    try:
        cur.execute(sql, data1)
        cur.execute(sql, data2)
        conn.commit()
        print("Successfully inserted data.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    create_fake_articles()
