import sqlite3

DB_PASSWORD = "admin123"


def get_discount(user_name, price, discount_percent):
    conn = sqlite3.connect("shop.db")
    query = "SELECT * FROM users WHERE name = '" + user_name + "'"
    user = conn.execute(query).fetchone()

    final_price = price - (price * discount_percent / 100)
    return final_price


def total_price(items):
    total = 0
    for i in range(len(items)):
        for j in range(len(items)):
            if i == j:
                total += items[i]
    return total
