import sqlite3

conn = sqlite3.connect("usage.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS usage_logs(
    ip TEXT,
    executions INTEGER
)
""")

conn.commit()


def check_usage(ip):

    cursor.execute(
        "SELECT executions FROM usage_logs WHERE ip=?",
        (ip,)
    )

    row = cursor.fetchone()

    if row is None:
        return True

    return row[0] < 2


def register_usage(ip):

    cursor.execute(
        "SELECT executions FROM usage_logs WHERE ip=?",
        (ip,)
    )

    row = cursor.fetchone()

    if row is None:

        cursor.execute(
            "INSERT INTO usage_logs VALUES (?,1)",
            (ip,)
        )

    else:

        cursor.execute(
            "UPDATE usage_logs SET executions=? WHERE ip=?",
            (row[0] + 1, ip)
        )

    conn.commit()