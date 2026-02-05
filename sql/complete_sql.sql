/* =========================================================
   MMU LIBRARY DATABASE (MySQL / Amazon RDS Compatible)
   Converted from SQL Server (T-SQL) to MySQL
   ========================================================= */

/* -----------------------------
   1. CREATE DATABASE
------------------------------*/
CREATE DATABASE IF NOT EXISTS mmu_library;
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
USE mmu_library;

/* -----------------------------
   2. ACCOUNTS TABLE
------------------------------*/
CREATE TABLE IF NOT EXISTS accounts (
    account_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'Reader',
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    failed_attempts INT DEFAULT 0,
    lockout_until DATETIME NULL
);

/* -----------------------------
   3. BOOKS TABLE
------------------------------*/
CREATE TABLE IF NOT EXISTS books (
    book_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    available TINYINT DEFAULT 1,
    due_date DATETIME NULL
);

/* -----------------------------
   4. BORROW HISTORY TABLE
------------------------------*/
CREATE TABLE IF NOT EXISTS borrow_history (
    borrow_id INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT NOT NULL,
    book_id INT NOT NULL,
    borrow_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    return_date DATETIME NULL,
    status ENUM('borrow','return') NOT NULL,

    CONSTRAINT fk_borrow_account
        FOREIGN KEY (account_id) REFERENCES accounts(account_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_borrow_book
        FOREIGN KEY (book_id) REFERENCES books(book_id)
        ON DELETE CASCADE
);

/* -----------------------------
   5. INDEXES (PERFORMANCE)
------------------------------*/
CREATE INDEX idx_accounts_username ON accounts(username);
CREATE INDEX idx_borrow_account ON borrow_history(account_id);
CREATE INDEX idx_borrow_book ON borrow_history(book_id);

/* -----------------------------
   6. STORED PROCEDURES
------------------------------*/
DELIMITER $$

/* Add Book */
CREATE PROCEDURE add_book (
    IN p_title VARCHAR(255),
    IN p_author VARCHAR(255),
    IN p_category VARCHAR(100)
)
BEGIN
    INSERT INTO books (title, author, category, available)
    VALUES (p_title, p_author, p_category, 1);
END$$

/* Edit Book */
CREATE PROCEDURE edit_book (
    IN p_book_id INT,
    IN p_title VARCHAR(255),
    IN p_author VARCHAR(255),
    IN p_category VARCHAR(100)
)
BEGIN
    UPDATE books
    SET title = p_title,
        author = p_author,
        category = p_category
    WHERE book_id = p_book_id;
END$$

/* Delete Book */
CREATE PROCEDURE delete_book (
    IN p_book_id INT
)
BEGIN
    DELETE FROM books
    WHERE book_id = p_book_id;
END$$

/* Toggle Book Availability */
CREATE PROCEDURE toggle_book_status (
    IN p_book_id INT
)
BEGIN
    UPDATE books
    SET available = IF(available = 1, 0, 1)
    WHERE book_id = p_book_id;
END$$

/* Create Reader Account */
CREATE PROCEDURE create_reader_account (
    IN p_username VARCHAR(50),
    IN p_password VARCHAR(255)
)
BEGIN
    INSERT INTO accounts (username, password, role)
    VALUES (p_username, p_password, 'Reader');
END$$

/* Borrow Book */
CREATE PROCEDURE borrow_book (
    IN p_account_id INT,
    IN p_book_id INT
)
BEGIN
    IF EXISTS (
        SELECT 1 FROM books
        WHERE book_id = p_book_id AND available = 1
    ) THEN
        UPDATE books
        SET available = 0,
            due_date = DATE_ADD(NOW(), INTERVAL 14 DAY)
        WHERE book_id = p_book_id;

        INSERT INTO borrow_history (account_id, book_id, status)
        VALUES (p_account_id, p_book_id, 'borrow');
    ELSE
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Book not available';
    END IF;
END$$

/* Return Book */
CREATE PROCEDURE return_book (
    IN p_account_id INT,
    IN p_book_id INT
)
BEGIN
    UPDATE books
    SET available = 1,
        due_date = NULL
    WHERE book_id = p_book_id;

    INSERT INTO borrow_history (account_id, book_id, return_date, status)
    VALUES (p_account_id, p_book_id, NOW(), 'return');
END$$

DELIMITER ;

/* -----------------------------
   7. INITIAL DATA
------------------------------*/

/* Librarian Account */
INSERT INTO accounts (username, password, role)
VALUES (
    'librarian',
    '$2b$12$TguWcPbjDKl3g/eI2B6T8OZZu7bkHRpkF2nAk0y9fsDIDwciYteHe',
    'Librarian'
);

/* Sample Books */
INSERT INTO books (title, author, category, available)
VALUES
('The Great Gatsby', 'F. Scott Fitzgerald', 'Fiction', 1),
('1984', 'George Orwell', 'Science Fiction', 1),
('The Hobbit', 'J.R.R. Tolkien', 'Fantasy', 1),
('Python Programming', 'MMU Press', 'Technology', 1);

/* -----------------------------
   8. VERIFICATION QUERIES
------------------------------*/
SELECT * FROM accounts;
SELECT * FROM books;
SELECT * FROM borrow_history;

/* =========================================================
   END OF FILE
   ========================================================= */
