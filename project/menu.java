/*/
Programmer: Christopher Bengen
Date: 5/27/2026
Description: This program simulates a simple banking application where users can check their balance, 
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
*/

/*/
Citation

- Compound Interest Formula: The formula used to calculate the future value of a deposit is 
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
*/

import java.util.Scanner;

public class menu {
    static Scanner sc = new Scanner(System.in);
    static double balance = 0.0;
    static double totalBalance = 0.0;
    
    public static void main(String[] args) {
        while (true) {
            System.out.println("\nWelcome to the Capitol One 360 Perfomance App");
            System.out.println("1. Check Balance");
            System.out.println("2. Deposit");
            System.out.println("3. Withdraw");
            System.out.println("4. Exit");
            System.out.println("Please select an option:");
            int option = sc.nextInt();

            switch (option) {
                case 1: {
                    System.out.println("\nYour current balance is: $" + balance);
                    break;
                }

                case 2: {
                    System.out.println("\nEnter the amount to deposit:");
                    double depositAmount = sc.nextDouble();
                    
                    System.out.println("\nEnter the amount of years the deposit will be held:");
                    int years = sc.nextInt();
                    double r = 0.04; // 4% annual interest rate

                    System.out.println("\nHow many times will the interest be compounded per year?");
                    int n = sc.nextInt();

                    double accountValue = depositAmount * Math.pow(1+r/n, n*years);
                    System.out.printf("\nThe value of your account after " + years + " years will be: $%.2f", accountValue);

                    balance += accountValue;
                    totalBalance += accountValue;
                    System.out.printf("\nDeposit successful. Your new balance is: $%.2f", balance);
                    break;
                }

                case 3: {
                    System.out.println("\nEnter the amount to withdraw:");
                    double withdrawAmount = sc.nextDouble();

                    if (withdrawAmount > balance) {
                        System.out.printf("\nInsufficient funds. Your current balance is: $%.2f", balance);
                    } else {
                        balance -= withdrawAmount;
                        totalBalance -= withdrawAmount;
                        System.out.printf("\nWithdrawal successful. Your new balance is: $%.2f", balance);
                    }
                    break;
                }

                case 4: {
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