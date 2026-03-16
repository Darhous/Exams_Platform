import sqlite3
import pandas as pd

DB_PATH = "exams.db"


def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def table_columns(table_name: str) -> list[str]:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    rows = cursor.fetchall()
    conn.close()
    return [row[1] for row in rows]


def ensure_column(table_name: str, column_name: str, ddl: str):
    cols = table_columns(table_name)
    if column_name not in cols:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {ddl}")
        conn.commit()
        conn.close()


def init_db():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            q_type TEXT NOT NULL,
            question TEXT NOT NULL,
            opt1 TEXT,
            opt2 TEXT,
            opt3 TEXT,
            opt4 TEXT,
            correct_answer TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            custom_name TEXT NOT NULL,
            file_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL,
            user_phone TEXT NOT NULL,
            subject TEXT NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            percent REAL NOT NULL,
            time_taken TEXT NOT NULL,
            warnings_count INTEGER DEFAULT 0,
            test_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS flagged_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER,
            question_text TEXT,
            subject TEXT,
            reported_by_name TEXT,
            reported_by_phone TEXT,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notification_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT,
            user_phone TEXT,
            channel TEXT,
            status TEXT,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

    ensure_column("users", "telegram_chat_id", "telegram_chat_id TEXT")
    ensure_column("users", "telegram_username", "telegram_username TEXT")
    ensure_column("users", "whatsapp_enabled", "whatsapp_enabled INTEGER DEFAULT 1")
    ensure_column("users", "last_notification_at", "last_notification_at TEXT")


def execute(query, params=()):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    conn.close()


def fetch_df(query, params=()):
    conn = get_conn()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def save_user(name, phone, is_admin=False):
    existing = fetch_df("SELECT * FROM users WHERE name=? AND phone=?", (name, phone))
    if existing.empty:
        execute(
            "INSERT INTO users (name, phone, is_admin, whatsapp_enabled) VALUES (?, ?, ?, ?)",
            (name, phone, 1 if is_admin else 0, 1),
        )


def update_user_telegram_link(phone: str, chat_id: str, username: str = ""):
    execute(
        """
        UPDATE users
        SET telegram_chat_id=?,
            telegram_username=COALESCE(NULLIF(?, ''), telegram_username)
        WHERE phone=?
        """,
        (str(chat_id), str(username or ""), phone),
    )


def get_user_contact_channels(phone: str):
    df = fetch_df(
        """
        SELECT id, name, phone, is_admin,
               COALESCE(telegram_chat_id, '') AS telegram_chat_id,
               COALESCE(telegram_username, '') AS telegram_username,
               COALESCE(whatsapp_enabled, 1) AS whatsapp_enabled
        FROM users
        WHERE phone=?
        ORDER BY id DESC
        LIMIT 1
        """,
        (phone,),
    )
    if df.empty:
        return {
            "exists": False,
            "telegram_chat_id": "",
            "telegram_username": "",
            "whatsapp_enabled": True,
        }

    row = df.iloc[0]
    return {
        "exists": True,
        "telegram_chat_id": str(row.get("telegram_chat_id", "") or "").strip(),
        "telegram_username": str(row.get("telegram_username", "") or "").strip(),
        "whatsapp_enabled": bool(int(row.get("whatsapp_enabled", 1) or 1)),
    }


def set_last_notification_at(phone: str, timestamp_text: str):
    execute(
        "UPDATE users SET last_notification_at=? WHERE phone=?",
        (timestamp_text, phone),
    )


def log_notification(user_name: str, user_phone: str, channel: str, status: str, details: str = ""):
    execute(
        """
        INSERT INTO notification_logs (user_name, user_phone, channel, status, details)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_name, user_phone, channel, status, details),
    )


def save_book(subject, custom_name, file_name):
    execute(
        "INSERT INTO books (subject, custom_name, file_name) VALUES (?, ?, ?)",
        (subject, custom_name, file_name),
    )


def save_result(user_name, user_phone, subject, score, total, percent, time_taken, warnings_count=0):
    execute(
        """
        INSERT INTO results (user_name, user_phone, subject, score, total, percent, time_taken, warnings_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_name, user_phone, subject, score, total, percent, time_taken, warnings_count),
    )


def save_flag(question_id, question_text, subject, reported_by_name, reported_by_phone, note):
    execute(
        """
        INSERT INTO flagged_questions (question_id, question_text, subject, reported_by_name, reported_by_phone, note)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (question_id, question_text, subject, reported_by_name, reported_by_phone, note),
    )


def get_books_by_subject(subject):
    return fetch_df(
        "SELECT id, custom_name, file_name, created_at FROM books WHERE subject=? ORDER BY id DESC",
        (subject,),
    )


def get_all_questions():
    return fetch_df("SELECT * FROM questions ORDER BY id DESC")


def delete_question(qid):
    execute("DELETE FROM questions WHERE id=?", (qid,))


def add_question(subject, q_type, question, opt1, opt2, opt3, opt4, correct_answer):
    execute(
        """
        INSERT INTO questions (subject, q_type, question, opt1, opt2, opt3, opt4, correct_answer)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (subject, q_type, question, opt1, opt2, opt3, opt4, correct_answer),
    )


def fetch_questions(subject=None, q_type=None, limit=10):
    query = "SELECT * FROM questions WHERE 1=1"
    params = []
    if subject:
        query += " AND subject=?"
        params.append(subject)
    if q_type and q_type != "ميكس":
        query += " AND q_type=?"
        params.append(q_type)
    query += " ORDER BY RANDOM() LIMIT ?"
    params.append(int(limit))
    return fetch_df(query, tuple(params))


def stats_counts():
    users = fetch_df("SELECT COUNT(*) AS c FROM users WHERE is_admin=0").iloc[0]["c"]
    tests = fetch_df("SELECT COUNT(*) AS c FROM results").iloc[0]["c"]
    books = fetch_df("SELECT COUNT(*) AS c FROM books").iloc[0]["c"]
    flags = fetch_df("SELECT COUNT(*) AS c FROM flagged_questions").iloc[0]["c"]
    return int(users), int(tests), int(books), int(flags)
