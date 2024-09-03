import sqlite3
from pathlib import Path

# Define the root directory
ROOT_DIR = Path(__file__).resolve().parent

# Connect to the SQLite database (the file will be created if it does not exist)
conn = sqlite3.connect(ROOT_DIR / 'odds.db')

# Create a cursor object using the cursor() method
cursor = conn.cursor()

# Create EventMatches table
cursor.execute('''
CREATE TABLE EventMatches (
    EventMatchID INTEGER PRIMARY KEY AUTOINCREMENT,
    UniversalEventName TEXT NOT NULL
);
''')

# Create Events table
cursor.execute('''
CREATE TABLE Events (
    EventID INTEGER PRIMARY KEY AUTOINCREMENT,
    EventName TEXT NOT NULL,
    EventMatchID INTEGER,
    FOREIGN KEY (EventMatchID) REFERENCES EventMatches(EventMatchID)
);
''')

# Modify Outcomes table to include EventLink
cursor.execute('''
CREATE TABLE Outcomes (
    OutcomeID INTEGER PRIMARY KEY AUTOINCREMENT,
    EventID INTEGER NOT NULL,
    OutcomeDescription TEXT NOT NULL,
    EventLink TEXT,
    FOREIGN KEY (EventID) REFERENCES Events(EventID)
);
''')

# Modify Odds table to include EventLink
cursor.execute('''
CREATE TABLE Odds (
    OddsID INTEGER PRIMARY KEY AUTOINCREMENT,
    OutcomeID INTEGER NOT NULL,
    BookieName TEXT NOT NULL,
    OfferedOdds REAL NOT NULL,
    EventLink TEXT,
    FOREIGN KEY (OutcomeID) REFERENCES Outcomes(OutcomeID)
);
''')

# Commit the changes
conn.commit()

# Close the database connection
conn.close()
