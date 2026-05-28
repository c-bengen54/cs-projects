/*
    Programmer: Christopher Bengen
    Date: 5/27/2026
    Description: 
        This program simulates a simple banking application where users can check their balance, 
        make deposits, and withdraw funds. The deposit function calculates the future value of the deposit based on a 
        fixed interest rate and compounding frequency. 
        The program continues to run until the user chooses to exit.
    Extra:
      - While True Loop: The program uses a while true loop to continuously display the menu until the user decides to exit.
      
      - Switch Statement: A switch statement is used to handle the user's menu selection and execute the corresponding actions 
        for checking balance, making deposits, withdrawing funds, or exiting the program.
      
      - Compound Interest Calculation: The program calculates the future value of a deposit using the compound interest formula,
        which takes into account the principal amount, interest rate, compounding frequency, and time period.
    
      - Input Validation: The program includes basic input validation to ensure that the user selects valid menu options and 
        does not attempt to withdraw more funds than available in the balance.

      - Currency Conversion: The program allows users to convert their USD balance into various foreign currencies using live exchange rates 
        fetched from an external API. It also keeps track of foreign currency balances and allows users to withdraw from those balances, 
        with the option to convert back to USD at the current exchange rate.
    
      - The program also keeps track of the total balance across all transactions, 
        allowing users to see their overall financial status.
    
*/

/*
    Citations

    - Compound Interest Formula: 
        The formula used to calculate the future value of a deposit is 
        based on the standard compound interest formula:

        A = P(1 + r/n)^(nt)
        Where:
        A = the future value of the investment/loan, including interest
        P = the principal investment amount (the initial deposit)
        r = the annual interest rate (decimal)
        n = the number of times that interest is compounded per year
        t = the time the money is invested for in years

    - While Loop
        Title: Java While Loop
        Author: W3Schools
        Date: Accessed on 5/27/2026
        Code Version: Java 8
        Availability: https://www.w3schools.com/java/java_while_loop.asp

    - Switch Statement
        Title: Java Switch
        Author: W3Schools
        Date: Accessed on 5/27/2026
        Code Version: Java 8
        Availability: https://www.w3schools.com/Java/java_switch.asp

    - Printf Method
    Title: Java Output printf() Method
    Author: W3Schools
    Date: Accessed on 5/27/2026
    Code Version: Java 8
    Availability: https://www.w3schools.com/JAVA/ref_output_printf.asp


    - HashMap Usage:
        Title: Java HashMap
        Author: W3Schools
        Date: Accessed May 27, 2026
        Code Version: Java 8
        Availability: https://www.w3schools.com/Java/java_hashmap.asp
    
    - HttpURLConnection:
        Title: Java HttpURLConnection
        Author: Oracle
        Date: Accessed May 27, 2026
        Code Version: Java 8
        Availability: https://docs.oracle.com/javase/8/docs/api/java/net/HttpURLConnection.html
 
    - Gson Library:
        Title: Gson User Guide
        Author: Google
        Date: Accessed May 27, 2026
        Code Version: 2.10.1
        Availability: https://github.com/google/gson
*/

import java.util.Scanner;
import java.net.URL;
import java.net.HttpURLConnection;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.util.Properties;
import java.io.FileInputStream;
import java.util.Map;
import java.util.HashMap;

public class menu {
    static Scanner sc = new Scanner(System.in);
    static double balance = 0.0;
    static double totalBalance = 0.0;
    static String apiKey = loadApiKey();
    static HashMap<String, Double> foreignBalances = new HashMap<>();

    public static String loadApiKey() {
        try {
            Properties props = new Properties();
            props.load(new FileInputStream("config.properties"));
            return props.getProperty("EXCHANGE_API_KEY");
        } catch (Exception e) {
            System.out.println("Error loading API key: " + e.getMessage());
            return null;
        }
    }

    public static JsonObject fetchRates(){
        try {
            URL url = new URL("https://v6.exchangerate-api.com/v6/" + apiKey + "/latest/USD");
            HttpURLConnection con = (HttpURLConnection) url.openConnection();
            con.setRequestMethod("GET");

            BufferedReader reader = new BufferedReader(new InputStreamReader(con.getInputStream()));

            StringBuilder response = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                response.append(line);
            }

            reader.close();

            return JsonParser.parseString(response.toString()).getAsJsonObject();
        } catch (Exception e) {
            System.out.println("\n Error fetching exchange rates: " + e.getMessage());
            return null;
        }
    }

    public static void convertCurrency(){
        System.out.println("\n--- Currency Conversion ---");
        System.out.println("Fetching latest exchange rates...");
        JsonObject data = fetchRates();

        if (data == null) {
            return;
        }

        JsonObject rates = data.getAsJsonObject("conversion_rates");

        System.out.println("How much money would you like to convert?");
        double amount = sc.nextDouble();

        if (amount > balance) {
            System.out.printf("\nInsufficient funds. Your current balance is: $%.2f", balance);
            return;
        }

        balance -= amount;

        System.out.printf("%nConverting balance of: $%.2f USD%n", amount);
        System.out.println("1. Euro        (EUR)");
        System.out.println("2. British Pound (GBP)");
        System.out.println("3. Japanese Yen  (JPY)");
        System.out.println("4. Canadian Dollar (CAD)");
        System.out.println("5. Mexican Peso  (MXN)");
        System.out.println("Select a currency:");

        int choice = sc.nextInt();
        String currencyCode = "";
        String currencyName = "";

        switch (choice) {
            case 1: currencyCode = "EUR"; currencyName = "Euro"; break;
            case 2: currencyCode = "GBP"; currencyName = "British Pound"; break;
            case 3: currencyCode = "JPY"; currencyName = "Japanese Yen"; break;
            case 4: currencyCode = "CAD"; currencyName = "Canadian Dollar"; break;
            case 5: currencyCode = "MXN"; currencyName = "Mexican Peso"; break;
            default: System.out.println("Invalid choice. Returning to main menu."); return;
        }

        double rate = rates.get(currencyCode).getAsDouble();
        double converted = amount * rate;

        if (foreignBalances.containsKey(currencyCode)) {
            foreignBalances.put(currencyCode, foreignBalances.get(currencyCode) + converted);
        } else {
            foreignBalances.put(currencyCode, converted);
        }


        System.out.printf("%nBalance:    $%.2f USD%n", amount);
        System.out.printf("Converts to: %.2f %s (%s)%n", converted, currencyName, currencyCode);
        System.out.printf("Live Rate:   1 USD = %.4f %s%n", rate, currencyCode);
    }

    public static void displayAllBalances() {
        System.out.printf("%nUSD Balance: $%.2f%n", balance);
        
            if (foreignBalances.isEmpty()) {
                System.out.println("No foreign currency balances.");
            } else {
                System.out.println("\n--- Foreign Currency Balances ---");
                // loop through every currency in the HashMap
                for (Map.Entry<String, Double> entry : foreignBalances.entrySet()) {
                    String code = entry.getKey();     // EUR, JPY etc
                    double amount = entry.getValue(); // the balance
                    System.out.printf("%s Balance: %.2f%n", code, amount);
                }
            }
    }

    public static void withdrawForeign() {
        // if no foreign balances exist, stop here
        if (foreignBalances.isEmpty()) {
            System.out.println("\nYou have no foreign currency balances to withdraw.");
            return;
        }

        // show all current foreign balances
        System.out.println("\n--- Foreign Currency Withdrawal ---");
        System.out.println("Your current foreign balances:");
        for (Map.Entry<String, Double> entry : foreignBalances.entrySet()) {
            System.out.printf("%s: %.2f%n", entry.getKey(), entry.getValue());
        }

        // ask which currency they want to withdraw from
        System.out.println("\nEnter the currency code you want to withdraw from (e.g. EUR, JPY):");
        String code = sc.next().toUpperCase(); // toUpperCase handles lowercase input

        // check if they actually have that currency
        if (!foreignBalances.containsKey(code)) {
            System.out.println("\nYou have no balance in " + code + ". Returning to menu.");
            return;
        }

        // show current balance in that currency
        double foreignBalance = foreignBalances.get(code);
        System.out.printf("%nYour %s balance: %.2f%n", code, foreignBalance);
        System.out.println("How much would you like to withdraw?");
        double withdrawAmount = sc.nextDouble();

        // check sufficient funds
        if (withdrawAmount > foreignBalance) {
            System.out.printf("%nInsufficient funds. Your %s balance is: %.2f%n", 
                            code, foreignBalance);
            return;
        }

        // subtract from foreign balance
        double newForeignBalance = foreignBalance - withdrawAmount;

        // remove currency from HashMap entirely if balance hits zero
        if (newForeignBalance == 0) {
            foreignBalances.remove(code);
        } else {
            foreignBalances.put(code, newForeignBalance);
        }

        // ask if they want it converted back to USD
        System.out.println("\nWould you like to convert this back to USD?");
        System.out.println("1. Yes");
        System.out.println("2. No");
        int choice = sc.nextInt();

        if (choice == 1) {
            // fetch live rates to convert back
            System.out.println("Fetching live rates...");
            JsonObject data = fetchRates();

            if (data == null) {
                System.out.println("Could not fetch rates. Withdrawal processed without conversion.");
                return;
            }

            // get the rate for this currency
            JsonObject rates = data.getAsJsonObject("conversion_rates");
            double rateToUSD = 1.0 / rates.get(code).getAsDouble(); // inverse of USD->foreign
            double convertedBack = withdrawAmount * rateToUSD;

            // add back to USD balance
            balance += convertedBack;

            System.out.printf("%nWithdrew %.2f %s%n", withdrawAmount, code);
            System.out.printf("Converted back to: $%.2f USD%n", convertedBack);
            System.out.printf("Live Rate: 1 %s = $%.4f USD%n", code, rateToUSD);
            System.out.printf("New USD Balance: $%.2f%n", balance);
        } else {
            // just confirm the withdrawal without USD conversion
            System.out.printf("%nWithdrew %.2f %s successfully.%n", withdrawAmount, code);
        }

        // show updated balances
        System.out.println("\n--- Updated Balances ---");
        displayAllBalances();
    }
    
    public static void deposit() {
        System.out.println("\nEnter the amount to deposit:");
        double depositAmount = sc.nextDouble();
        
        System.out.println("\nEnter the amount of years:");
        int years = sc.nextInt();
        double r = 0.04;

        System.out.println("\nHow many times compounded per year?");
        int n = sc.nextInt();

        double accountValue = depositAmount * Math.pow(1+r/n, n*years);
        balance += accountValue;
        totalBalance += accountValue;

        System.out.printf("\nValue of the account after %d years: $%.2f%n", years, accountValue);
        System.out.printf("New Balance: $%.2f%n", balance);
    }

    public static void withdraw() {
        System.out.println("\nEnter the amount to withdraw:");
        double withdrawAmount = sc.nextDouble();

        if (withdrawAmount > balance) {
            System.out.printf("\nInsufficient funds. Your current balance is: $%.2f", balance);
            return;
        }

        balance -= withdrawAmount;
        System.out.printf("\nWithdrawal successful. New Balance: $%.2f%n", balance);
    }

    public static void main(String[] args) {
        while (true) {
            System.out.println("\nWelcome to the Capitol One 360 Performance App");
            System.out.println("1. Check Balance");
            System.out.println("2. Deposit");
            System.out.println("3. Withdraw");
            System.out.println("4. Convert Currency");
            System.out.println("5. Withdraw Foreign Currency");
            System.out.println("6. Exit");
            System.out.println("Please select an option:");
            int option = sc.nextInt();

            switch (option) {
                case 1: {
                    displayAllBalances();
                    break;
                }

                case 2: {
                    deposit();
                    break;
                }

                case 3: {
                    withdraw();
                    break;
                }

                case 4: {
                    convertCurrency();
                    break;
                }
                
                case 5: {
                    withdrawForeign();
                    break;
                }

                case 6: {
                    System.out.println("\n--- Final Account Summary ---");
                    displayAllBalances();
                    System.out.println("\nThank you for using the Capitol One 360 Performance App. Goodbye!");
                    return;
                }

                default: {
                    System.out.println("\nInvalid option. Please try again.");
                    break;
                }
            }
        }
    }
}