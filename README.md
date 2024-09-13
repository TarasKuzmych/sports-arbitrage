# Spanish Sports Betting Arbitrage Script

**[Leer en Español](readme-es.md)**

## Brief Description

This project is my attempt to develop a Python tool that extracts and analyzes betting odds from all licensed Spanish sportsbooks (39 in total) to identify arbitrage opportunities on **Non-Live winner-loser bets** for events involving up to 4 participants. 
The development of this tool occurred intermittently from November 2023 to May 2024. Despite the ambitious scope, the complexity and rapid changes in the betting landscape led me to discontinue the project after successfully arbitraging 12 betting houses, covering approximately 30% of the national market. 

The tool uses asynchronous requests to efficiently scrape odds data, which are then parsed through custom-built parsers and stored in a SQLite database. Utilizing natural language processing and a matching algorithm, it harmonizes event names across different sources and identifies the most profitable odds discrepancies. This script is modular, consisting of distinct components for data scraping, database management, and arbitrage analysis, making it adaptable for users looking to customize or expand its capabilities.

If you are aspiring to develop a similar tool without an engineering background, I energetically encourage you to reconsider. The challenges are substantial, and the likelihood of success without specialized knowledge can be low. This project may be better suited for a team rather than an individual.

**Open Collaboration and Use:** My primary goal with this project is to aid others in developing their own tools and projects. Feel free to copy, adapt, and use any part of this script as you see fit. I hope that by sharing my work openly, it will foster learning and innovation, encouraging everyone to utilize these resources to enhance their understanding and capabilities in their respective fields.

## Table of Contents
1. [Legal Warning](#legal-warning)
2. [How to Use It](#how-to-use-it)
3. [What is (Probably) More Re-usable](#whats-probably-more-useful)
4. [How does it work](#how-does-it-work)
5. [Folder Structure](#folder-structure)
6. [Troubleshooting](#troubleshooting)
7. [Progress and Accuracy per Sportsbook](#progress-and-accuracy-per-sportsbook)
8. [Contact Information](#contact-information)
9. [Why I Started This Project (might be relevant if you are considering hiring me)](#why-i-started)
10. [Why I Left The Project Unfinished (mbriyachm)](#why-i-stopped-the-project)

## Legal Warning
### Compliance with `robots.txt`
This script may not adhere to the `robots.txt` file of each sportsbook website, which is meant to regulate automated access to their data. Users are responsible for verifying and respecting the `robots.txt` directives of each website they intend to scrape. Some components of the script have been developed theoretically (have not been tested) to respect `robots.txt` guidelines; however, they may still function effectively despite these constraints.


### Ethical and Legal Use
The functionality provided by this script should be used ethically and within the bounds of the law. Before deploying or utilizing this script, users should ensure that their activities are compliant with all applicable laws and terms of service agreements.

### Disclaimer
This tool is provided as-is without any guarantees or warranties. The creator of this script is not responsible for any actions taken by its users, including any potential legal consequences or damages arising from its use. Users should consult with legal counsel to understand the potential risks and legalities of using web scraping technologies in their region.

Use of this script implies acceptance of these terms and an understanding that you, as the user, are solely responsible for any legal implications of your actions.

## How to Use It
Just make sure to download all the libraries imported in `scrape_v7` or any other script you might try, and execute it. For convenience, you can refer to the `requirements.txt` file, which lists the dependencies. 

**Important:** The requirements.txt file may include additional libraries not strictly required for this specific project, as it includes dependencies from other projects I am currently working on. While I apologize for any inconvenience, I recommend installing all listed packages to avoid any issues.

## What is (Probably) More Re-Usable. Just copy it. 

### Data Parsing Tools
Basically the most reusable part. These are the only tools that I do not think will need much updates as sportsbooks rarely change the nature of their HTMLs while they do change from time to time the way you interact with the webpage (which makes gathering the HTMLs highly costly). You can find these labeled as "parser" in the folder of each sportsbook. 

### Arbitrage Detection
The scripts involved in identifying arbitrage opportunities are `maxodds.py` and `arbitrage.py`. They not only show how to process and analyze odds from the database but also make all the calculations on how much to bet to maximize the return. It is EXTREMELY reusable for somebody starting this project as most events / teams / players are named differently in order to avoid comparing odds programmatically. My approach may NOT be perfect, but it is a great way of starting and testing other functionalities.

###
For a deeper understanding of how these components work together to provide a comprehensive solution, refer to the [How Does it work](#how-does-it-work) section.

## How does it Work

This section serves as a quick guide to explore the project folders and their functionalities. I have developed everything modularly, allowing you to inspect each component either within individual sportsbook folders or via the `scrape_v7` script.

### Common practices
The entire process done simultaneously for each sportsbook involves:
1. **Data Scraping**: Utilizing `requests` to download HTML content from sportsbook websites, through different approaches adapted to each webpage structure.
2. **Data Parsing**: Extracting and processing data from the HTMLs using custom parsing scripts tailored to the structure of each sportsbook's webpage. A `.txt` file named after the folder of each sportsbook is then created. 
- In order to facilitate further steps the team names are "cleaned" or normalized to facilitate linking events named differently across various sportsbooks.
3. **Data Storage**: Storing and managing the parsed data in a SQLite database using `SQL.py` and `odds.py` for efficient retrieval and analysis from the previously created `.txt` files.

### Arbitrage Detection
The main foundation lies in reading the centralized database to identify the best odds for each event. In order to do so, I have managed to apply a pre-existing algorithm that uses natural language simulation techniques (NLTK) to try and link the same events named slightly differently by each sportsbook. This can be closely analyzed and optimized in **`maxodds.py`**, even though the configuration that is already set has already been excruciatingly tested and determined to be the best. The main output of this process is `maxodds.txt`, pretty self-explanatory.

Finally, **`arbitrage.py`** extends the functionality of `maxodds.py` by adding the capability to filter and display only those events where arbitrage opportunities exist. It calculates the stakes for each bet to guarantee a profit regardless of the outcome. The main output of this process is `arbitrageable.txt`, which is also self-explanatory.

## Folder Structure
The project is organized into several directories and files, each serving a specific function in the workflow of the script. 

### Root Directory
- `README.md`: Provides an overview of the project, including installation, usage, and legal warning.
- `requirements.txt`: Lists all Python libraries necessary to run the scripts, simplifying the setup process with a single command.

### Sportsbook Folders
Each sportsbook analyzed by the script has its own folder named after the sportsbook. These folders contain:
- **Scraping scripts**: Tailored to each sportsbook, handling the specific intricacies of scraping data from their websites.
- **Requester scripts**: These manage the requests sent to the sportsbook’s web servers. They handle tasks such as managing HTTP sessions, retrying failed requests, and conforming to rate limits, ensuring that the scraping activities remain efficient. 
- **Parser scripts**: Extract and format the data from the scraping scripts into a structured and analyzable format. 
- **Data files (`*.txt`)**: Output from the scraping scripts, storing the processed data ready for analysis.

### Central Scripts
- `scrape_v7.py`: The main script that orchestrates the scraping process across all sportsbooks simultaneously in order to simply run the script and get the information on what to arbitrage.
- `maxodds.py`: Analyzes data to identify the best betting odds across sportsbooks.
- `arbitrage.py`: Identifies and calculates arbitrage opportunities, outputting potential bets into `arbitrageable.txt`.

### Database Files
- `SQL.py`: Manages all interactions with the SQLite database, setting up the database schema.
- `odds.py`: Handles inserting and querying data within the database, facilitating efficient data management.

### Output Files
- `maxodds.txt`: Contains the results from `maxodds.py`, listing the best odds found for each event.
- `arbitrageable.txt`: Generated by `arbitrage.py`, it lists all events where arbitrage opportunities have been found along with suggested stakes.

## Troubleshooting
Well, when running `scrape_v7` lots of things could go wrong. I tried to minimize all possible errors, but there are always errors related to the asynchronous approach, which I have no idea how to fix. GL with those! 

A more complete list could be;

- **Database Connectivity Issues**: Ensure the SQLite database path in `SQL.py` and `odds.py` is correct. Verify that the database file is accessible and not being used by another process.

- **Parsing Errors**: If parsing fails due to updates in a sportsbook’s HTML structure, update the respective parsing scripts in the sportsbook's folder with the correct HTML elements. It will take you from a couple of hours to days depending on the complexity of the HTML structure. 

- **Missing Data in Output Files**: Ensure all scripts completed successfully without errors. Check for errors in the console output and verify the integrity of the database and output files.

## Progress and Accuracy per Sportsbook

The table below details the progress and accuracy of data scraping for each sportsbook involved in this project. Each entry is rated on a scale from 1 to 10, where the score represents the percentage of offered events that were successfully covered by this tool.

| Sportsbook  | Progress (1-10) | Last Scrape Date | Remarks |
|-------------|-----------------|------------------|---------|
| Betfair     | 9               | 28/08/2024 | |
| Interwetten | 9              | Sudden Error 403; 21/05/2024                | Up until the last scrape, more than 95% of events were covered. |
| Marca       | 9               | 28/08/2024                 | |
| MarathonBet        | 9              | Sudden Error; 26/05/2024               | |
| PokerStars  | 9               | 28/08/2024                 | |
| Zebet       | 10              | 28/08/2024                 | The best scraper so far. |
| Bet777      | 8.5               | 28/08/2024                 | |
| TonyBet     | 3               | 28/08/2024                 | Initially functional but later issues arose (I messed up the requester); covers only about 25% of events. Further development needed, but I hope my work might be useful to somebody. |
| Dafabet     | 7            | 28/08/2024                 | Still  |
| 1xBet       | 6.5              | Sudden Error; MAY 2024                 | Previous issues; winning odds where messed up with other types of bets for; ufc, boxing, live and table tennis.
| Winamax    | 6               | Sudden error 403; 25/11/2023                | Not running on `scrape_v7`. Active for `scrape_v1`. Lots of events covered; check `parser.` Development was not continued due to `requester` constraints related to the 403 error. |
| Bwin        | 8               | 28/08/2024                 | Parser errors; selecting "set" bets instead of winner bets. I would not include it when runnning the whole `scrape_v7` as it results on numerous false positives in `arbitrageable.txt`.|

**Note:** Remember that this tool only scrapes **winner-loser nature bets**. The following are **EXCLUDED**:
- **Sports including more than 4 participants**: you'll rarely arbitrage all possible outcomes on a 20 participants event without assuming some of those are negligible to win. So you end up taking some risks. Sports arbitrage consists on taking NO RISKS. 
- **Live events**: More complex to develop; requires automation of the betting account used, which is beyond the scope of this script.

## Contact Information
Just send an email to TarasKuzmych@proton.me with the subject "Bets Arbitrage" and your message. Otherwise I will NOT answer. 

## Why I Started This Project (might be relevant if you are considering hiring me)

The origin of this project was rooted in a conviction I had very present whilst completing my first *programming with Python* course (prior to that I had no experience in programming): the real value of such courses isn't just in acquiring knowledge, but in applying it to create tangible outcomes. Motivated by this insight and with the course already completed, I began searching for a side project that could not only leverage my new skills but also potentially generate some extra cash flow for me at the end of the day. Considering some potential project ideas, one day, while coming back home from class, on the train, I realized there was a concept I had known for months already where people were allegedly making profits by exploiting tools enabling them to arbitrage sports bets. Which at one point, a couple of months before, I even considered paying for one myself. So in that train, I questioned why I should pay for such a service when I could potentially build it myself. "If they *could* build it, why *wouldn't* I?" And that's how this project started. 

## Why I Left The Project Unfinished (mbriyachm)

I embarked on this project back in November 2023 and worked on it intermittently until May 2024. At that point, three sportsbooks suddenly stopped functioning within the script due to changes they implemented. By then, I had only managed to get 10 sportsbooks running concurrently, and not even fully for arbitrage purposes. Considering the escalating complexity, fully integrating the remaining sportsbooks seemed an overwhelming task, likely demanding over two years—if the difficulty curve remained constant, which it certainly did not. In addition to that, it would have required constant updates of the already "finished" sub-projects which seemed unfeasible for me. 

The project faced two major technical hurdles: 
- First, the technical difficulty of bypassing web protections to successfully request and download HTML from sportsbooks’ webpages.
- Secondly, and more dauntingly, matching events named slightly differently across sportsbooks. Despite my best efforts throughout months, the latter problem persisted, highlighting perhaps a gap in my skills or the challenge’s complexity beyond my intelligence.

At one point, I considered selling the arbitrage opportunities I discovered. However, this plan required broader coverage of sportsbooks and a solution to the event-matching issue. Realizing the limited potential for generating short-term cash flow, coupled with the diminishing educational value and daunting technical challenges, led me to reassess my priorities. As my inner child stop playing with this project, the enthusiasm faded and it began to feel more like an obligation rather than a pastime. I had to adopt a more pragmatic approach, acknowledging that the marginal returns were much lower than other potential paths I might explore in the coming months.

Thus, I think it is best to leave this project aside, and move forward. I had the opportunity to learn valuable lessons and even though I failed miserably I hope to help someone with the progress made (and possibly differentiate myself in a hiring process!). 
###
***See you on the next one.***
