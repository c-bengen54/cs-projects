/*
 * Title: Capital One 360 Banking App - Web Server
 * Programmer: Christopher Bengen
 * Date: 5/28/2026
 * Description: This file creates a web server using Spark Java
 *              that serves the frontend and handles all banking
 *              operations via HTTP endpoints.
 */

import static spark.Spark.*;
import com.google.gson.JsonObject;
import com.google.gson.JsonArray;
import com.google.gson.JsonParser;
import com.google.gson.Gson;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

public class Server {

    // path constants so we never hardcode paths twice
    static final String DATA_DIR      = "data/";
    static final String ACCOUNTS_DIR  = "data/accounts/";
    static final String USERS_FILE    = "data/users.json";
    static Gson gson = new Gson();

    // -------------------------------------------------------
    // MAIN — starts the server and registers all endpoints
    // -------------------------------------------------------
    public static void main(String[] args) {

        // serve frontend files from the frontend/ folder
        staticFiles.externalLocation("/workspaces/cs-projects/project/frontend");

        // allow browser to talk to our server (CORS)
        before((req, res) -> {
            res.header("Access-Control-Allow-Origin", "*");
            res.header("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
            res.header("Access-Control-Allow-Headers", "Content-Type");
            res.type("application/json");
        });

        // handle browser preflight requests
        options("/*", (req, res) -> {
            res.status(200);
            return "OK";
        });

        // register all endpoints
        post("/register", Server::handleRegister);
        post("/login",    Server::handleLogin);
        get("/balance",   Server::handleBalance);
        post("/deposit",  Server::handleDeposit);
        post("/withdraw", Server::handleWithdraw);
        post("/convert",  Server::handleConvert);
        get("/history",   Server::handleHistory);
        get("/", (req, res) -> {
        res.redirect("/login.html");
        return null;
    });

        get("/rates", (req, res) -> {
        JsonObject data  = menu.fetchRates();
        if (data == null) return gson.toJson(Map.of("error", "Could not fetch rates"));
        return data.getAsJsonObject("conversion_rates").toString();
    });

        System.out.println("Server started at http://localhost:4567");
    }

    // -------------------------------------------------------
    // REGISTER — creates a new user account
    // -------------------------------------------------------
    public static Object handleRegister(spark.Request req, spark.Response res) {
        try {
            // parse the incoming JSON body
            JsonObject body     = JsonParser.parseString(req.body()).getAsJsonObject();
            String username     = body.get("username").getAsString().toLowerCase();
            String password     = body.get("password").getAsString();

            // load existing users
            JsonObject users    = loadUsers();

            // check if username already exists
            if (users.has(username)) {
                res.status(409);
                return gson.toJson(Map.of("error", "Username already exists"));
            }

            // hash the password before saving
            String hashedPassword = hashPassword(password);
            users.addProperty(username, hashedPassword);
            saveUsers(users);

            // create a blank account file for this user
            createAccount(username);

            return gson.toJson(Map.of("success", true));

        } catch (Exception e) {
            res.status(500);
            return gson.toJson(Map.of("error", e.getMessage()));
        }
    }

    // -------------------------------------------------------
    // LOGIN — validates credentials
    // -------------------------------------------------------
    public static Object handleLogin(spark.Request req, spark.Response res) {
        try {
            JsonObject body     = JsonParser.parseString(req.body()).getAsJsonObject();
            String username     = body.get("username").getAsString().toLowerCase();
            String password     = body.get("password").getAsString();

            JsonObject users    = loadUsers();

            // check user exists and password matches
            if (!users.has(username)) {
                res.status(401);
                return gson.toJson(Map.of("error", "Invalid username or password"));
            }

            String storedHash   = users.get(username).getAsString();
            if (!storedHash.equals(hashPassword(password))) {
                res.status(401);
                return gson.toJson(Map.of("error", "Invalid username or password"));
            }

            return gson.toJson(Map.of("success", true, "username", username));

        } catch (Exception e) {
            res.status(500);
            return gson.toJson(Map.of("error", e.getMessage()));
        }
    }

    // -------------------------------------------------------
    // BALANCE — returns current balances for a user
    // -------------------------------------------------------
    public static Object handleBalance(spark.Request req, spark.Response res) {
        try {
            String username     = req.queryParams("username");
            JsonObject account  = loadAccount(username);
            return account.toString();

        } catch (Exception e) {
            res.status(500);
            return gson.toJson(Map.of("error", e.getMessage()));
        }
    }

    // -------------------------------------------------------
    // DEPOSIT — adds money with compound interest
    // -------------------------------------------------------
    public static Object handleDeposit(spark.Request req, spark.Response res) {
        try {
            JsonObject body     = JsonParser.parseString(req.body()).getAsJsonObject();
            String username     = body.get("username").getAsString();
            double amount       = body.get("amount").getAsDouble();
            int years           = body.get("years").getAsInt();
            int compounds       = body.get("compounds").getAsInt();
            double r            = 0.04;

            // compound interest formula
            double finalValue   = amount * Math.pow(1 + r / compounds, compounds * years);

            // load account, update balance, save
            JsonObject account  = loadAccount(username);
            double balance      = account.get("balance").getAsDouble();
            balance            += finalValue;
            account.addProperty("balance", balance);

            // log the transaction
            logTransaction(account, "Deposit", amount, finalValue, balance,
                          years + "yr @ " + compounds + "x/yr compounding");

            saveAccount(username, account);
            return gson.toJson(Map.of(
                "success",    true,
                "finalValue", String.format("%.2f", finalValue),
                "balance",    String.format("%.2f", balance)
            ));

        } catch (Exception e) {
            res.status(500);
            return gson.toJson(Map.of("error", e.getMessage()));
        }
    }

    // -------------------------------------------------------
    // WITHDRAW — removes money from USD balance
    // -------------------------------------------------------
    public static Object handleWithdraw(spark.Request req, spark.Response res) {
        try {
            JsonObject body     = JsonParser.parseString(req.body()).getAsJsonObject();
            String username     = body.get("username").getAsString();
            double amount       = body.get("amount").getAsDouble();

            JsonObject account  = loadAccount(username);
            double balance      = account.get("balance").getAsDouble();

            // insufficient funds check
            if (amount > balance) {
                res.status(400);
                return gson.toJson(Map.of("error", "Insufficient funds"));
            }

            balance            -= amount;
            account.addProperty("balance", balance);

            logTransaction(account, "Withdrawal", amount, amount, balance, "USD");

            saveAccount(username, account);
            return gson.toJson(Map.of(
                "success", true,
                "balance", String.format("%.2f", balance)
            ));

        } catch (Exception e) {
            res.status(500);
            return gson.toJson(Map.of("error", e.getMessage()));
        }
    }

    // -------------------------------------------------------
    // CONVERT — converts USD to foreign currency
    // -------------------------------------------------------
    public static Object handleConvert(spark.Request req, spark.Response res) {
        try {
            JsonObject body         = JsonParser.parseString(req.body()).getAsJsonObject();
            String username         = body.get("username").getAsString();
            double amount           = body.get("amount").getAsDouble();
            String currencyCode     = body.get("currencyCode").getAsString().toUpperCase();
            double rate             = body.get("rate").getAsDouble();

            JsonObject account      = loadAccount(username);
            double balance          = account.get("balance").getAsDouble();

            if (amount > balance) {
                res.status(400);
                return gson.toJson(Map.of("error", "Insufficient funds"));
            }

            // update USD balance
            balance                -= amount;
            account.addProperty("balance", balance);

            // update foreign balance
            JsonObject foreign      = account.getAsJsonObject("foreignBalances");
            double current          = foreign.has(currencyCode)
                                      ? foreign.get(currencyCode).getAsDouble() : 0;
            double converted        = amount * rate;
            foreign.addProperty(currencyCode, current + converted);

            logTransaction(account, "Conversion", amount, converted, balance,
                          "USD → " + currencyCode + " @ " + rate);

            saveAccount(username, account);
            return gson.toJson(Map.of(
                "success",   true,
                "converted", String.format("%.2f", converted),
                "balance",   String.format("%.2f", balance)
            ));

        } catch (Exception e) {
            res.status(500);
            return gson.toJson(Map.of("error", e.getMessage()));
        }
    }

    // -------------------------------------------------------
    // HISTORY — returns transaction log
    // -------------------------------------------------------
    public static Object handleHistory(spark.Request req, spark.Response res) {
        try {
            String username     = req.queryParams("username");
            JsonObject account  = loadAccount(username);
            return account.getAsJsonArray("transactions").toString();

        } catch (Exception e) {
            res.status(500);
            return gson.toJson(Map.of("error", e.getMessage()));
        }
    }

    // -------------------------------------------------------
    // HELPERS — file I/O and utilities
    // -------------------------------------------------------

    // loads users.json or returns empty object if missing
    static JsonObject loadUsers() throws IOException {
        File f = new File(USERS_FILE);
        if (!f.exists()) return new JsonObject();
        return JsonParser.parseString(
            new String(Files.readAllBytes(f.toPath()))
        ).getAsJsonObject();
    }

    // saves users.json
    static void saveUsers(JsonObject users) throws IOException {
        Files.write(Paths.get(USERS_FILE),
            new Gson().toJson(users).getBytes());
    }

    // loads a user's account JSON file
    static JsonObject loadAccount(String username) throws IOException {
        File f = new File(ACCOUNTS_DIR + username + ".json");
        if (!f.exists()) createAccount(username);
        return JsonParser.parseString(
            new String(Files.readAllBytes(f.toPath()))
        ).getAsJsonObject();
    }

    // saves a user's account JSON file
    static void saveAccount(String username, JsonObject account) throws IOException {
        Files.write(
            Paths.get(ACCOUNTS_DIR + username + ".json"),
            new Gson().toJson(account).getBytes()
        );
    }

    // creates a blank account file for a new user
    static void createAccount(String username) throws IOException {
        new File(ACCOUNTS_DIR).mkdirs();
        JsonObject account = new JsonObject();
        account.addProperty("username", username);
        account.addProperty("balance", 0.0);
        account.add("foreignBalances", new JsonObject());
        account.add("transactions", new JsonArray());
        saveAccount(username, account);
    }

    // logs a transaction to the account's history
    static void logTransaction(JsonObject account, String type,
                                double inputAmount, double outputAmount,
                                double runningBalance, String note) {
        JsonArray transactions  = account.getAsJsonArray("transactions");
        JsonObject tx           = new JsonObject();
        DateTimeFormatter fmt   = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

        tx.addProperty("type",           type);
        tx.addProperty("inputAmount",    String.format("%.2f", inputAmount));
        tx.addProperty("outputAmount",   String.format("%.2f", outputAmount));
        tx.addProperty("runningBalance", String.format("%.2f", runningBalance));
        tx.addProperty("note",           note);
        tx.addProperty("timestamp",      LocalDateTime.now().format(fmt));

        transactions.add(tx);
    }

    // simple password hashing using SHA-256
    static String hashPassword(String password) throws Exception {
        java.security.MessageDigest md =
            java.security.MessageDigest.getInstance("SHA-256");
        byte[] hash = md.digest(password.getBytes("UTF-8"));
        StringBuilder sb = new StringBuilder();
        for (byte b : hash) sb.append(String.format("%02x", b));
        return sb.toString();
    }
}