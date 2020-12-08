import sqlite3

sql_con = sqlite3.connect('math_training.db')
sql_cur = sql_con.cursor()

sql_cur.execute("""
CREATE TABLE Users (
    id       INTEGER PRIMARY KEY AUTOINCREMENT
                     NOT NULL
                     UNIQUE,
    login    STRING  NOT NULL
                     UNIQUE,
    password STRING  NOT NULL,
    name     STRING  NOT NULL,
    surname  STRING  NOT NULL,
    remember INTEGER DEFAULT (0) 
)
""")

sql_cur.execute("""
CREATE TABLE Settings (
    id    INTEGER PRIMARY KEY AUTOINCREMENT
                  NOT NULL
                  UNIQUE,
    name  STRING  NOT NULL,
    value INTEGER NOT NULL
)
""")

sql_cur.execute("""
CREATE TABLE Results (
    id                    INTEGER  PRIMARY KEY AUTOINCREMENT
                                   NOT NULL
                                   UNIQUE,
    user_id               INTEGER  NOT NULL,
    datetime              DATETIME NOT NULL,
    difficult             INTEGER  NOT NULL,
    solve_duration        INTEGER  NOT NULL,
    tasks_count           INTEGER  NOT NULL,
    correct_answers_count INTEGER  NOT NULL,
    coefficient           DECIMAL  NOT NULL
)
""")

sql_cur.execute("""
INSERT INTO Settings(name, value) VALUES ('countdown_duration', 5), ('show_count', 2)
""")

sql_con.commit()
