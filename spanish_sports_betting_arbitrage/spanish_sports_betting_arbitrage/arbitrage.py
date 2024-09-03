import sqlite3
from pathlib import Path

# Define the root directory
ROOT_DIR = Path(__file__).resolve().parent

# Constants for the script
DATABASE_PATH = ROOT_DIR / 'odds.db'
AMOUNT_TO_BET = 100  # Fixed betting amount
MIN_ODDS = 1
MAX_ODDS = 10000
MIN_BETS = 2
MAX_BETS = 12

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
         WHERE OD2.OutcomeID = O.OutcomeID AND OD2.OfferedOdds = MAX(OD.OfferedOdds)) AS BookiesWithMaxOdds
    FROM 
        Events E
    JOIN 
        Outcomes O ON E.EventID = O.EventID
    JOIN 
        Odds OD ON O.OutcomeID = OD.OutcomeID
    GROUP BY 
        E.EventName, 
        O.OutcomeDescription
    """)

    results = cursor.fetchall()
    conn.close()

    max_odds_dict = {}
    for event_name, outcome_description, max_odds, bookies_with_max_odds in results:
        if event_name not in max_odds_dict:
            max_odds_dict[event_name] = {}
        max_odds_dict[event_name][outcome_description] = (max_odds, bookies_with_max_odds)
    return max_odds_dict

# Function to write the max odds to a file in the desired format
def write_max_odds_to_file(max_odds_dict, file_path):
    with open(file_path, 'w') as file:
        for event_name, outcomes in max_odds_dict.items():
            file.write("----------\n")
            file.write(f"{event_name}:\n")
            for outcome_desc, (max_odds, bookies) in outcomes.items():
                file.write(f"{outcome_desc}: {max_odds} --> {bookies}\n")
            file.write("----------")

# Function to calculate stakes for the equal pay strategy
def calculate_stakes_equal_pay(odds, probability, amount_to_bet):
    return [(probability / odd) * amount_to_bet for odd in odds]

# Function to calculate stakes for the max risk strategy
def calculate_stakes_max_risk(inverse_odds, odds, amount_to_bet):
    max_odd_index = inverse_odds.index(min(inverse_odds))
    sum_of_other_stakes = sum(inverse_odd * amount_to_bet for i, inverse_odd in enumerate(inverse_odds) if i != max_odd_index)
    
    stakes = [inverse_odd * amount_to_bet if i != max_odd_index else amount_to_bet - sum_of_other_stakes for i, inverse_odd in enumerate(inverse_odds)]
    return stakes

# Main function to control the program flow
def main():
    max_odds_dict = get_max_odds_from_db()

    # Write the max odds to maxodds.txt
    write_max_odds_to_file(max_odds_dict, ROOT_DIR / 'maxodds.txt')

    with open(ROOT_DIR / 'arbitrageable.txt', 'w') as file:
        for event_name, outcomes in max_odds_dict.items():
            odds = [info[0] for info in outcomes.values()]
            bookies = [info[1] for info in outcomes.values()]
            probability = arb_calculator(odds)

            if probability != "Not arbitrageable":
                file.write("-------------------------\n")
                file.write("-------------------------\n")
                file.write(f"{event_name}:\n")
                for outcome_desc, (max_odds, bookies) in outcomes.items():
                    file.write(f"{outcome_desc}: {max_odds} --> {bookies}\n")
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

# Helper function to write strategies to file
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

if __name__ == "__main__":
    main()
