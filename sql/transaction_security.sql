
CREATE LOGIN transaction_login WITH PASSWORD = 'Pa$$w0rd';
GO

CREATE USER transaction_service FOR LOGIN transaction_login;
GO


CREATE ROLE transaction_role;
ALTER ROLE transaction_role ADD MEMBER transaction_service;
GO

CREATE PROCEDURE BorrowBook
    @username NVARCHAR(100),
    @bookID INT
AS
BEGIN
    SET NOCOUNT ON;

    IF EXISTS (
        SELECT 1 FROM Books
        WHERE BookID = @bookID AND Available = 1
    )
    BEGIN
        -- Mark book as borrowed
        UPDATE Books
        SET Available = 0, DueDate = DATEADD(day, 14, GETDATE())
        WHERE BookID = @bookID;

        -- Log the borrowing action
        INSERT INTO BorrowHistory (Username, BookID, Action)
        VALUES (@username, @bookID, 'Borrowed');
    END
    ELSE
    BEGIN
        PRINT 'Book not available';
    END
END


CREATE PROCEDURE ReturnBook
    @username NVARCHAR(100),
    @bookID INT
AS
BEGIN
    SET NOCOUNT ON;

    IF EXISTS (
        SELECT 1 FROM Books
        WHERE BookID = @bookID AND Available = 0
    )
    BEGIN
        -- Mark book as returned
        UPDATE Books
        SET Available = 1, DueDate = NULL
        WHERE BookID = @bookID;

        -- Log the returning action
        INSERT INTO BorrowHistory (Username, BookID, Action)
        VALUES (@username, @bookID, 'Returned');
    END
    ELSE
    BEGIN
        PRINT 'Book was not borrowed or does not exist';
    END
END


--Permission--
GRANT EXECUTE ON BorrowBook TO transaction_role;
GRANT EXECUTE ON ReturnBook TO transaction_role;

DENY INSERT, UPDATE, DELETE ON Books TO transaction_role;
DENY SELECT ON Users TO transaction_role;
GO
