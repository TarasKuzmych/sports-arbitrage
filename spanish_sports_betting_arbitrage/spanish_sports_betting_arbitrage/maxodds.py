import sqlite3
import time
from collections import defaultdict
from nltk.tokenize import word_tokenize
from fuzzywuzzy import fuzz
from phonetics import metaphone
import nltk
from pathlib import Path

# Define the root directory
ROOT_DIR = Path(__file__).resolve().parent

# Download required NLTK resources
nltk.download('punkt')

# Adjust the threshold based on your specific needs
SIMILARITY_THRESHOLD = 77

def metaphone_tokenized(event_name):
    tokens = word_tokenize(event_name.lower())
    phonetic_tokens = [metaphone(token) for token in tokens]
    return set(phonetic_tokens)

def match_events(event_phonetics, new_event_phonetics, event_names, new_event_name, threshold=SIMILARITY_THRESHOLD):
    for existing_event, phonetics_set in event_phonetics.items():
        if phonetics_set & new_event_phonetics:
            similarity = fuzz.token_sort_ratio(event_names[existing_event], new_event_name)
            if similarity > threshold:
                return existing_event
    return None

start_time = time.time()

conn = sqlite3.connect(ROOT_DIR / 'odds.db')
cursor = conn.cursor()

# Updated SQL query to consider the EventLink for each Odds entry
cursor.execute("""
SELECT 
    E.EventName,
    O.OutcomeDescription,
    OD.EventLink,
    OD.OfferedOdds,
    OD.BookieName
FROM 
    Events E
JOIN 
    Outcomes O ON E.EventID = O.EventID
JOIN 
    Odds OD ON O.OutcomeID = OD.OutcomeID
""")

results = cursor.fetchall()
conn.close()

event_phonetics = {}
event_names = {}
max_odds_dict = defaultdict(lambda: defaultdict(lambda: (0, '', '')))
grouped_events = defaultdict(set)

for event_name, outcome_description, event_link, offered_odds, bookie_name in results:
    event_phonetic_tokens = metaphone_tokenized(event_name)
    best_match = match_events(event_phonetics, event_phonetic_tokens, event_names, event_name)

    if best_match:
        unified_event_name = best_match
    else:
        unified_event_name = event_name
        event_phonetics[unified_event_name] = event_phonetic_tokens
        event_names[unified_event_name] = event_name

    grouped_events[unified_event_name].add(event_name)

    offered_odds_float = float(offered_odds)
    outcome_description_str = str(outcome_description)

    current_max_odds, current_bookie, current_link = max_odds_dict[unified_event_name][outcome_description_str]
    if offered_odds_float > current_max_odds:
        max_odds_dict[unified_event_name][outcome_description_str] = (offered_odds_float, bookie_name, event_link)

with open(ROOT_DIR / 'maxodds.txt', 'w', encoding='utf-8') as file:
    for unified_event_name, associated_events in grouped_events.items():
        sorted_associated_events = sorted(list(associated_events))
        file.write(f"{unified_event_name} (Grouped Events: {', '.join(sorted_associated_events)}):\n")
        sorted_outcomes = sorted(max_odds_dict[unified_event_name].items(), key=lambda x: x[0])
        for outcome_desc, (max_odds, bookie, link) in sorted_outcomes:
            if max_odds > 0:  # Only write outcomes with odds
                outcome_number = outcome_desc if outcome_desc.isdigit() else outcome_desc
                file.write(f"{outcome_number}: {max_odds} --> {bookie} -> {link}\n")
        file.write("----------\n")

end_time = time.time()
elapsed_time = end_time - start_time
print(f"Script executed in {elapsed_time:.2f} seconds.")
