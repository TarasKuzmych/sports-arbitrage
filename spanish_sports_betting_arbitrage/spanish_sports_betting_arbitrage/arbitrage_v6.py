import sqlite3
import time
from collections import defaultdict
from nltk.tokenize import word_tokenize
from fuzzywuzzy import fuzz
from phonetics import metaphone
import nltk
from multiprocessing import Pool, cpu_count
import os
from pathlib import Path

# Determine the root directory dynamically
ROOT_DIR = Path(__file__).resolve().parent

# Constants for the script
DATABASE_PATH = ROOT_DIR / "odds.db"
AMOUNT_TO_BET = 100  # Fixed betting amount
MIN_ODDS = 1
MAX_ODDS = 10000
MIN_BETS = 2
MAX_BETS = 12
N_PROCESSES = cpu_count()  # Number of processes to us

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

# Function to query the database and process the results into a dictionary
def get_max_odds_from_db():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT 
        E.EventName,
        O.OutcomeDescription,
        MAX(OD.OfferedOdds) AS MaxOfferedOdds,
        (SELECT GROUP_CONCAT(OD2.BookieName) 
        FROM Odds OD2 
        WHERE OD2.OutcomeID = O.OutcomeID AND OD2.OfferedOdds = MAX(OD.OfferedOdds)) AS BookiesWithMaxOdds,
        OD.EventLink  
    FROM 
        Events E
    JOIN 
        Outcomes O ON E.EventID = O.EventID
    JOIN 
        Odds OD ON O.OutcomeID = OD.OutcomeID
    GROUP BY 
        E.EventName, 
        O.OutcomeDescription
    ORDER BY 
        E.EventName
    """)

    results = cursor.fetchall()
    conn.close()
    return results

def process_chunk(chunk):
    event_phonetics = {}
    event_names = {}
    grouped_events = defaultdict(list)
    unified_results = []

    for event_name, outcome_description, max_odds, bookies_with_max_odds, event_link in chunk:
        event_phonetic_tokens = metaphone_tokenized(event_name)
        best_match = match_events(event_phonetics, event_phonetic_tokens, event_names, event_name)

        if best_match:
            unified_event_name = best_match
        else:
            unified_event_name = event_name
            event_phonetics[unified_event_name] = event_phonetic_tokens
            event_names[unified_event_name] = event_name

        grouped_events[unified_event_name].append(event_name)
        unified_results.append((unified_event_name, outcome_description, max_odds, bookies_with_max_odds, event_link))  # Add the event_link here

    return unified_results, grouped_events


def chunk_data(results):
    chunks = []
    current_chunk = []
    current_letter = None

    for result in results:
        event_name = result[0]
        if current_letter is None or event_name[0].lower() == current_letter:
            current_chunk.append(result)
        else:
            chunks.append(current_chunk)
            current_chunk = [result]
        current_letter = event_name[0].lower()

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

def unify_event_names_parallel(results):
    chunks = chunk_data(results)

    with Pool(N_PROCESSES) as pool:
        results = pool.map(process_chunk, chunks)

    # Combine results from all chunks
    unified_results = []
    grouped_events = defaultdict(list)
    for result in results:
        unified_chunk_results, grouped_chunk_events = result
        unified_results.extend(unified_chunk_results)
        for event_name, events in grouped_chunk_events.items():
            grouped_events[event_name].extend(events)

    return unified_results, grouped_events

# Function to write the max odds to a file in the desired format
def write_max_odds_to_file(max_odds_dict, grouped_events, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        for unified_event_name, associated_events in grouped_events.items():
            file.write(f"{unified_event_name} (Grouped Events: {', '.join(associated_events)}):\n")
            for outcome_desc, (max_odds, bookies, link) in max_odds_dict[unified_event_name].items():  # Expect a tuple with the link now
                file.write(f"{outcome_desc}: {max_odds} --> {bookies} -> {link}\n")  # Output the link
            file.write("----------\n")

# Function to calculate stakes for the equal pay strategy
def calculate_stakes_equal_pay(odds, probability, amount_to_bet):
    return [(probability / odd) * amount_to_bet for odd in odds]

# Function to calculate stakes for the max risk strategy
def calculate_stakes_max_risk(inverse_odds, odds, amount_to_bet):
    max_odd_index = inverse_odds.index(min(inverse_odds))
    sum_of_other_stakes = sum(inverse_odd * amount_to_bet for i, inverse_odd in enumerate(inverse_odds) if i != max_odd_index)
    
    stakes = [inverse_odd * amount_to_bet if i != max_odd_index else amount_to_bet - sum_of_other_stakes for i, inverse_odd in enumerate(inverse_odds)]
    return stakes

def write_strategy_to_file(file, stakes, total_profit, strategy_title):
    file.write(strategy_title + "\n")
    for i, stake in enumerate(stakes):
        file.write(f"Stake for bet {i+1}: {stake:,.2f}$\n")
    file.write(f"Total profit: {total_profit:,.2f}$\n")
    file.write("-------------------------\n")

# Function to calculate the arbitrage probability
def arb_calculator(odds):
    odds_probability = sum(1/odd for odd in odds)
    return 1 / odds_probability if odds_probability < 1 else "Not arbitrageable"

if __name__ == '__main__':
    # Start timing for processing directories to write_max_odds_to_file
    processing_start_time = time.time()

    results = get_max_odds_from_db()
    unified_results, grouped_events = unify_event_names_parallel(results)

    max_odds_dict = {}
    for unified_event_name, outcome_description, max_odds, bookies_with_max_odds, event_link in unified_results:  # Include the event_link
        if unified_event_name not in max_odds_dict:
            max_odds_dict[unified_event_name] = {}
        max_odds_dict[unified_event_name][outcome_description] = (max_odds, bookies_with_max_odds, event_link)  # Include the event_link here

    # Write the max odds to maxodds.txt
    write_max_odds_to_file(max_odds_dict, grouped_events, ROOT_DIR / 'maxodds.txt')
    processing_end_time = time.time()
    print(f"Time taken from processing directories to write_max_odds_to_file: {processing_end_time - processing_start_time:.2f} seconds.")

    # Start timing for remaining part of the script
    remaining_part_start_time = time.time()

    with open(ROOT_DIR / 'arbitrageable.txt', 'w') as file:
        for event_name, outcomes in max_odds_dict.items():
            odds = [info[0] for info in outcomes.values()]
            bookies = [info[1] for info in outcomes.values()]
            links = [info[2] for info in outcomes.values()]
            probability = arb_calculator(odds)

            if probability != "Not arbitrageable":
                file.write("-------------------------\n")
                file.write("-------------------------\n")
                file.write(f"{event_name}:\n")
                for i, (outcome_desc, (max_odds, bookies, event_link)) in enumerate(outcomes.items()):
                    file.write(f"{outcome_desc}: {max_odds} --> {bookies} -> {event_link}\n") 
                file.write("-------------------------\n")
                
                stakes_equal_pay = calculate_stakes_equal_pay(odds, probability, AMOUNT_TO_BET)
                total_profit_equal_pay = (probability - 1) * AMOUNT_TO_BET
                write_strategy_to_file(file, stakes_equal_pay, total_profit_equal_pay, "For equal pay strategy:")

                inverse_odds = [1/odd for odd in odds]
                stakes_max_risk = calculate_stakes_max_risk(inverse_odds, odds, AMOUNT_TO_BET)
                total_profit_max_risk = sum((stake * odd) - AMOUNT_TO_BET for stake, odd in zip(stakes_max_risk, odds))
                write_strategy_to_file(file, stakes_max_risk, total_profit_max_risk, "For max risk strategy:")
                file.write("-------------------------\n")
                file.write("\n")

    remaining_part_end_time = time.time()
    print(f"Time taken for remaining part of the script: {remaining_part_end_time - remaining_part_start_time:.2f} seconds.")
