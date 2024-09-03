import sqlite3
import os
import re  # Import the regular expressions module
from pathlib import Path

# Define the root directory
ROOT_DIR = Path(__file__).resolve().parent

# Function to extract the event link from a block of text
def extract_event_link(block):
    match = re.search(r'link -> (.+)', block)
    return match.group(1) if match else None

# Function to get or create an event match and return its ID
def get_or_create_event_match(cursor, event_name):
    try:
        # Check if the event match already exists
        cursor.execute("SELECT EventMatchID FROM EventMatches WHERE UniversalEventName = ?", (event_name,))
        match = cursor.fetchone()
        if match:
            return match[0]  # Return the existing EventMatchID
        else:
            # If not, create a new event match record
            cursor.execute("INSERT INTO EventMatches (UniversalEventName) VALUES (?)", (event_name,))
            return cursor.lastrowid  # Return the new EventMatchID
    except sqlite3.DatabaseError as e:
        print(f"Database error: {e}")
        return None


# Insert event record and return its ID
def get_or_create_event(cursor, event_name, event_match_id):
    try:
        # Check if the event already exists with the same EventMatchID
        cursor.execute("SELECT EventID FROM Events WHERE EventName = ? AND EventMatchID = ?", (event_name, event_match_id))
        event = cursor.fetchone()
        if event:
            return event[0]  # Return the existing EventID
        else:
            # If not, create a new event record without the link
            cursor.execute("INSERT INTO Events (EventName, EventMatchID) VALUES (?, ?)", (event_name, event_match_id))
            return cursor.lastrowid  # Return the new EventID
    except sqlite3.DatabaseError as e:
        print(f"Database error: {e}")
        return None


# Insert outcomes and odds with event link
def insert_outcomes_and_odds(cursor, event_id, outcomes, bookie_name, event_link):
    try:
        for outcome_desc, odds in outcomes:
            # Insert into Outcomes with the EventLink
            cursor.execute("INSERT INTO Outcomes (EventID, OutcomeDescription, EventLink) VALUES (?, ?, ?)", 
                           (event_id, outcome_desc, event_link))
            outcome_id = cursor.lastrowid
            # Insert into Odds with the EventLink
            cursor.execute("INSERT INTO Odds (OutcomeID, BookieName, OfferedOdds, EventLink) VALUES (?, ?, ?, ?)", 
                           (outcome_id, bookie_name, odds, event_link))
    except sqlite3.DatabaseError as e:
        print(f"Database error: {e}")


def process_bookie_file(filepath, cursor):
    bookie_name = os.path.splitext(os.path.basename(filepath))[0]
    with open(filepath, 'r', encoding='utf-8') as file:
        event_blocks = file.read().strip().split('-----')
        for block in event_blocks:
            if not block.strip():  # Skip empty blocks
                continue
            parts = block.strip().split('\nlink ->', 1)  # Split the block to separate the link
            event_block = parts[0].strip()
            event_lines = event_block.split('\n')
            event_name = event_lines[0]
            event_link = extract_event_link(block) if len(parts) == 2 else "No link provided"
            event_match_id = get_or_create_event_match(cursor, event_name)
            event_id = get_or_create_event(cursor, event_name, event_match_id)
            if event_id is not None:
                outcomes = []  # Initialize outcomes for this event
                for line in event_lines[1:]:  # Iterate over the lines excluding the event name
                    try:
                        split_line = line.split(':')
                        if len(split_line) != 2 or not split_line[1].strip():
                            print(f"Line format error in {line}: {bookie_name}")
                            continue

                        outcome_num, odd = split_line
                        outcome_desc = f"{outcome_num.strip()}"
                        odd = float(odd.strip())
                        outcomes.append((outcome_desc, odd))  # Append outcome to the outcomes list
                    except ValueError as e:
                        print(f"Error parsing line {line}: {e} {bookie_name}")
                        continue
                insert_outcomes_and_odds(cursor, event_id, outcomes, bookie_name, event_link)

def clear_existing_data(cursor):
    try:
        cursor.execute("DELETE FROM Odds")
        cursor.execute("DELETE FROM Outcomes")
        cursor.execute("DELETE FROM Events")
        cursor.execute("DELETE FROM EventMatches")
    except sqlite3.DatabaseError as e:
        print(f"Database error while clearing data: {e}")


# Main function to walk through the directories and process files
def process_directories(root_dir):
    with sqlite3.connect(ROOT_DIR / 'odds.db') as conn:
        cursor = conn.cursor()
        clear_existing_data(cursor)  # Clear existing data before processing new files
        for subdir, dirs, files in os.walk(root_dir):
            folder_name = os.path.basename(subdir)
            for filename in files:
                if filename.endswith('.txt') and os.path.splitext(filename)[0] == folder_name:
                    filepath = os.path.join(subdir, filename)
                    try:
                        process_bookie_file(filepath, cursor)
                    except Exception as e:
                        print(f"An error occurred while processing file {filepath}: {e}")
        conn.commit()

# Call the main function with the path to your top root directory
process_directories(ROOT_DIR)
