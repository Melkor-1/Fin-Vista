#   Fin-Vista - A Portfolio Management Web App

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://https://github.com/Melkor-1/Fin-Vista/edit/main/LICENSE)

Fin-Vista is a simple web application for managing stock portfolios, checking 
real-time stock prices, buying and selling stocks, and viewing transaction 
history. It's built using Flask and SQlite for database management.

##  Table of Contents:

*   [Installation](#installation)
*   [Usage](#usage)
*   [Database Schema](#database-schema)
##  Installation: 

1.  Clone the repository:
    ```bash
    git clone https://github.com/Melkor-1/Fin-Vista
    cd Fin-Vista
    ```

2.  Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

3.  Set up the SQLite database:
*   Create a SQlite database `finance.db`:
    ```bash
    touch finance.db
    ```
*   Add the tables to the database. You can find the schema below.

4.  Start the application:
    ```bash
    flask run
    ```

5.  Access the app in your web browser at `http://127.0.0.1:5000/`.

##  Usage
*   Register or log in to your account.
*   Navigate to different sections for buying, selling, portfolio management, 
    and transaction history.

##  Contributing
    Contributions are welcome! If you'd like to contribute to this project, 
    please follow these guidelines:

1.  Fork the project.
2.  Create your feature branch (`git checkout -b feature/YourFeature`).
3.  Commit your changes (`git commit -m 'Add some feature'`).
4.  Push to the branch (`git push origin feature/YourFeature`).
5.  Open a pull request.

##  Database Schema
    Fin-Vista uses a SQLite database named `finance.db`. It contains the 
    following tables:

### `users` Table
*   `id` (INTEGER): A unique identifier for each user.
*   `username` (TEXT): The username associated with the user.
*   `hash` (TEXT):  The hashed password for the user.
*   `cash` (NUMERIC): The cash balance for the user, with a default of $10,000.

### `transactions` Table
*   `user_id` (INTEGER): A reference to the user who made the transaction.
*   `transaction_id` (INTEGER): A unique identifier for each transaction.
*	`symbol` (TEXT): The symbol of the stock involved in the transaction.
*	`shares_amount` (INTEGER): The number of shares bought or sold.
*	`price` (NUMERIC): The price of the stock at the time of the transaction.
*	`date` (DATETIME): The date and time when the transaction occurred.
*	`type` (TEXT): The type of transaction (e.g., "buy" or "sell").

	This schema is used to store user information and transaction history for
	the Fin-Vista application.
