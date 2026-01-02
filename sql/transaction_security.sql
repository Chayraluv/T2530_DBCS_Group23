
CREATE LOGIN transaction_login WITH PASSWORD = 'Pa$$w0rd';
GO

CREATE USER transaction_service FOR LOGIN transaction_login;
GO


CREATE ROLE transaction_role;
ALTER ROLE transaction_role ADD MEMBER transaction_service;
GO

--Borrow Book--
CREATE PROCEDURE BorrowBook
    @user_id INT,
    @book_id INT
AS
BEGIN
    SET NOCOUNT ON;

    IF EXISTS (
        SELECT 1 FROM Books
        WHERE book_id = @book_id AND available = 1
    )
    BEGIN
        INSERT INTO BorrowHistory(user_id, book_id, action, action_date)
        VALUES (@user_id, @book_id, 'BORROW', GETDATE());

        UPDATE Books SET available = 0 WHERE book_id = @book_id;
    END
    ELSE
    BEGIN
        RAISERROR ('Book is not available', 16, 1);
    END
END;
GO

--Return Book--
CREATE PROCEDURE ReturnBook
    @user_id INT,
    @book_id INT
AS
BEGIN
    SET NOCOUNT ON;

    INSERT INTO BorrowHistory(user_id, book_id, action, action_date)
    VALUES (@user_id, @book_id, 'RETURN', GETDATE());

    UPDATE Books SET available = 1 WHERE book_id = @book_id;
END;
GO

--Permission--
GRANT EXECUTE ON BorrowBook TO transaction_role;
GRANT EXECUTE ON ReturnBook TO transaction_role;

DENY INSERT, UPDATE, DELETE ON Books TO transaction_role;
DENY SELECT ON Users TO transaction_role;
GO
