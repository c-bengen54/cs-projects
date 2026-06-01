# CS Projects

## Would You Like to Play A Game? - WYLTPAG folder

## Java Independent Lab - project folder

# Exercise: Million Dollar Programmer! - Capital One Banking App

Independent lab program that will allow users to simulate using a banking and savings account with compound interest, live rate currency conversion, and an HTML + CSS frontend and Java server backend

---
### Programmer: 
## Christopher Bengen
### Date: 
## 5/29/2026
### Description:
```
This program simulates a simple banking application that allows users to check their balance, make deposits, and withdraw funds. The deposit function calculates the future value of the deposit using a fixed interest rate and a compounding frequency. The program continues to run until the user chooses to exit.
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


