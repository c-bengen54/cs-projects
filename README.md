# CS Projects

# Would You Like to Play A Game? - WYLTPAG folder
# - Big B's Arcade

**Authors:** Christopher Bengen, Logan Down, Aaron Pichardo  
**Date:** November 5, 2025

---

## Overview

*Big B's Arcade Mystery* is a text-based adventure game set inside a haunted 1990s arcade. You play as one of a group of friends who stumble upon a mysterious arcade cabinet — and quickly find themselves trapped by the evil, soul-stealing wizard **Tobias**. To escape, you must navigate the dark and broken halls of Big B's Arcade, solve puzzles to restore power and unlock new areas, and confront the twisted versions of your friends that Tobias has corrupted.

Your choices throughout the game determine which of five possible endings you reach.

---

## Features

- **Branching story** with five distinct endings (True, Good, Bad, Secret, and Lame)
- **Boss battle system** with a purification mechanic that lets you spare corrupted friends instead of defeating them — and affects the ending you receive
- **Six puzzles** spanning voltage calibration, Python syntax repair, bootloader stabilization, file restoration, signal interruption, and EOF input
- **Dynamic atmosphere** via ANSI color, typewriter-style printing, glitch effects, and flickering text
- **Command tracker** that reacts when you repeat the same action too many times, with increasingly exasperated in-character responses
- **Error recovery** system that logs crashes and offers a clean restart without losing your character's name

---

## Requirements

- Python 3.x
- A terminal that supports ANSI escape codes (standard on macOS, Linux, and Windows Terminal)

No third-party libraries are needed — only Python's standard library (`random`, `time`, `sys`, `os`).

---

## How to Run

```bash
python would_you_like_to_play_a_game
```

You will be prompted to enter your character's name before the story begins.

---

## Commands

| Command | Description |
|---|---|
| `look` / `scan` | Describe your current room and list objects of interest |
| `examine <object>` | Read the description of a specific object |
| `interact` | Interact with an object (may trigger a puzzle) |
| `move <room>` | Travel to a connected room |
| `inventory` | List the items you are currently carrying |
| `map` | Display all rooms with their lock and power status |
| `help` | Show available commands |
| `quit` | Give up (leads to a bad ending) |

---

## Locations

The arcade comprises eight interconnected areas. Some require a key item to enter; others require the power to be restored first.

```
Lobby
├── Backroom (requires: key)
│   └── Control Room (requires: keycard + power)
├── Arcade Room Floor (requires: power)
│   ├── Big B Arena (requires: arcade token)
│   │   └── Maze (requires: maze_key)
│   │       └── Throne Room (requires: throne_key)
└── Cafeteria
```

---

## Bosses

Three of your corrupted friends guard key areas of the arcade. A fourth and final encounter waits in the Throne Room.

| Boss | Location | Health | Notes |
|---|---|---|---|
| Road-Boxer | Arcade Room Floor | 300 | First encounter; Chad transformed |
| Angry-Monkey | Big B Arena | 400 | Brad, who embraced the change |
| Pack-Dude | Maze | 350 | Arthur, who regrets his deal with Tobias |
| Tobias the Wizard | Throne Room | 500 | Final boss; form varies by ending |

In combat you may **attack**, **dodge** (dice roll required), **run** (forfeit the fight), or **use item**. If a boss's health drops to 20 or below and you are carrying **purified water**, you can attempt a purification ritual to spare them — though it requires a successful dice roll.

---

## Endings

The ending you receive depends on how many bosses you purified vs. defeated, and what items you are carrying when you reach the Throne Room.

| Ending | Condition |
|---|---|
| **True Ending** | All three friends purified (spared = 3) |
| **Good Ending** | At least one friend purified, rest defeated (spared > 0, total = 3) |
| **Secret Ending** | No purifications, carrying the arcade token but no purified water — then choose to join Tobias |
| **Bad Ending** | Defeated by Tobias, or choose "no" after the secret ending offer |
| **Lame Ending** | Reach the Throne Room without resolving any boss fights |

---

## Puzzles

All puzzles are accessed by using `interact` on specific objects in the world.

| Puzzle | Object | Location | Goal |
|---|---|---|---|
| **Generator** | Generator | Backroom | Set three voltage dials to sum to 100 — restores power to the arcade |
| **Syntax** | Monitor | Control Room | Fix a broken Python `for` loop to unlock Big B Arena |
| **File Restore** | Terminal | Control Room | Type the correct restored log line to receive the arcade token |
| **EOF Input** | Dispenser terminal | Arcade Room Floor | Terminate a connection by sending `EOF` or typing `eof` |
| **Signal Interrupt** | Maze Entrance | Arcade Room Floor | Interrupt an infinite loop to unlock the Maze |
| **Bootloader** | Dispenser | Cafeteria | Type `REPAIR` five times in sequence before sectors destabilize |

---

## Tips

- Read sticky notes carefully — they contain direct hints for the Generator and File Restore puzzles.
- Purified water can be found in multiple locations. You need it to attempt boss purifications.
- Solving all six puzzles is not required to finish the game, but some are necessary to progress to later areas.
- If you die in a boss fight, you are offered a retry — taking it resets both your HP and the boss's HP.

---

## Credits

Developed as a course project. Citations for specific Python standard library features used in the implementation are included in the source file header.

---

# Java Independent Lab - project folder
# - Exercise: Million Dollar Programmer! - Capital One Banking App

An independent lab program that will allow users to simulate using a banking and savings account with compound interest, 
live rate currency conversion, and an HTML + CSS frontend and Java server backend

---
### Programmer: 
## Christopher Bengen
### Date: 
## 5/29/2026
### Description:
```
This program simulates a simple banking application that allows users to check their balance,
make deposits, and withdraw funds. The deposit function calculates the deposit's
future value using a fixed interest rate and a compounding frequency.
The program continues to run until the user chooses to exit.
```

### Extras
- **While True Loop**: The program uses a while true loop to continuously display the menu until the user decides to exit.
      
- **Switch Statements and If Statements**: A switch statement is used to handle the user's menu selection and execute the corresponding actions for checking balance, making deposits, withdrawing funds, or exiting the program. Various other if statements are used to differentiate between certain logic operations.
      
- **Compound Interest Calculation**: The program calculates the future value of a deposit using the compound interest formula, which takes into account the principal amount, interest rate, compounding frequency, and time period.
    
- **Input Validation**: The program includes basic input validation to ensure that the user selects valid menu options and does not attempt to withdraw more funds than available in the balance.

- **Currency Conversion**: The program allows users to convert their USD balance into various foreign currencies using live exchange rates fetched from an external API. It also keeps track of foreign currency balances.
    
- **Transaction History**: The program also keeps track of the total balance across all transactions, allowing users to see their overall financial status.

- **Password Hashing and Login System**: The program allows users to log in using differentiated accounts with hashed passwords that use SHA-256.

- **Java backend and HTML frontend**: The program uses an HTML frontend to display to users the program's functionality, while the Java backend handles frontend -> server interaction.

---

### Project Structure
```
cs-projects/
├── .vscode/
│    └── settings.json
├── lib/
│   ├── gson-2.10.1.jar
│   ├── javax.servlet-api-3.1.0.jar
│   ├── jetty-http-9.4.31.v20200723.jar
│   ├── jetty-io-9.4.31.v20200723.jar
│   ├── jetty-server-9.4.31.v20200723.jar
│   ├── jetty-servlet-9.4.31.v20200723.jar
│   ├── jetty-util-9.4.31.v20200723.jar
│   ├── slf4j-api-1.7.36.jar
│   ├── slf4j-simple-1.7.36.jar
│   └── spark-core-2.9.4.jar
├── project/                  #This is where the Java lab program lives
│   ├── data/
│   │   ├── accounts/
│   ├── frontend/
│   │   ├── dashboard.html
│   │   ├── login.html
│   │   └── styles.css
│   ├── .env
│   ├── .gitignore
│   ├── config.properties
│   ├── menu.class            #Compiled Java file for menu.java
│   ├── menu.java             
│   ├── Server.class          #Compiled Java file for Server.java
│   └── Server.java           
└── WYLTPAG/                  #Would You Like To Play A Game? Game Jam Submission
```

## To run the Java project, use this compiler bash command

```
cd /workspaces/cs-projects/project
javac -cp .:/workspaces/cs-projects/lib/* Server.java menu.java && java -cp .:/workspaces/cs-projects/lib/* Server
```
---

## To access the frontend
After running the server, open the forwarded port 4567 in your browser.
The app will automatically redirect to the login page.

## Citations

### 1. Compound Interest Formula: 
The formula used to calculate the future value of a deposit is based on the 
standard compound interest formula:

    A = P(1 + r/n)^(nt)
    Where:
    - A = the future value of the investment/loan, including interest
    - P = the principal investment amount (the initial deposit)
    - r = the annual interest rate (decimal)
    - n = the number of times that interest is compounded per year
    - t = the time the money is invested for in years

---

### 2. While Loop
    Title: Java While Loop
    Author: W3Schools
    Date: Accessed on 5/27/2026
    Code Version: Java 8
    Availability: https://www.w3schools.com/java/java_while_loop.asp

---

### 3. Switch Statement
    Title: Java Switch
    Author: W3Schools
    Date: Accessed on 5/27/2026
    Code Version: Java 8
    Availability: https://www.w3schools.com/Java/java_switch.asp

---

### 4. Printf Method
    Title: Java Output printf() Method
    Author: W3Schools
    Date: Accessed on 5/27/2026
    Code Version: Java 8
    Availability: https://www.w3schools.com/JAVA/ref_output_printf.asp


### 5. HashMap Usage:
    Title: Java HashMap
    Author: W3Schools
    Date: Accessed May 27, 2026
    Code Version: Java 8
    Availability: https://www.w3schools.com/Java/java_hashmap.asp
    
### 6. HttpURLConnection:
    Title: Java HttpURLConnection
    Author: Oracle
    Date: Accessed May 27, 2026
    Code Version: Java 8
    Availability: https://docs.oracle.com/javase/8/docs/api/java/net/HttpURLConnection.html
 
### 7. Gson Library:
    Title: Gson User Guide
    Author: Google
    Date: Accessed May 27, 2026
    Code Version: 2.10.1
    Availability: https://github.com/google/gson

### 8. Spark Java Framework
    Title: Spark Framework Documentation
    Author: Per Wendel
    Date: Accessed May 29, 2026
    Code Version: 2.9.4
    Availability: https://sparkjava.com/documentation

### 9. SHA-256 Hashing
    Title: Java MessageDigest
    Author: Oracle
    Date: Accessed May 29, 2026
    Code Version: Java 8
    Availability: https://docs.oracle.com/javase/8/docs/api/java/security/MessageDigest.html

### 10. ExchangeRate API
    Title: ExchangeRate-API Documentation
    Author: ExchangeRate-API
    Date: Accessed May 29, 2026
    Code Version: N/A
    Availability: https://www.exchangerate-api.com/docs/overview


