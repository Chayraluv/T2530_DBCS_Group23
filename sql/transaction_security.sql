
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

--Adjust the procedure based on schema
USE MMU_Library;
GO

-- Adjusted BorrowBook
CREATE OR ALTER PROCEDURE dbo.BorrowBook
    @username NVARCHAR(100),
    @bookID INT
AS
BEGIN
    SET NOCOUNT ON;

    -- Look in the NEW schema
    IF EXISTS (
        SELECT 1 FROM LibraryData.Books
        WHERE BookID = @bookID AND Available = 1
    )
    BEGIN
        UPDATE LibraryData.Books
        SET Available = 0, DueDate = DATEADD(day, 14, GETDATE())
        WHERE BookID = @bookID;

        INSERT INTO LibraryData.BorrowHistory (Username, BookID, Action)
        VALUES (@username, @bookID, 'Borrowed');
    END
    ELSE
    BEGIN
        PRINT 'Book not available';
    END
END;
GO

-- Adjusted ReturnBook
CREATE OR ALTER PROCEDURE dbo.ReturnBook
    @username NVARCHAR(100),
    @bookID INT
AS
BEGIN
    SET NOCOUNT ON;

    -- Look in the NEW schema
    IF EXISTS (
        SELECT 1 FROM LibraryData.Books
        WHERE BookID = @bookID AND Available = 0
    )
    BEGIN
        UPDATE LibraryData.Books
        SET Available = 1, DueDate = NULL
        WHERE BookID = @bookID;

        INSERT INTO LibraryData.BorrowHistory (Username, BookID, Action)
        VALUES (@username, @bookID, 'Returned');
    END
    ELSE
    BEGIN
        PRINT 'Book was not borrowed or does not exist';
    END
END;
GO

-- Grant least privilege back

-- Grant execution on the procedures (this remains the same)
GRANT EXECUTE ON dbo.BorrowBook TO transaction_role;
GRANT EXECUTE ON dbo.ReturnBook TO transaction_role;

-- NEW: Deny access to the entire LibraryData schema
-- This ensures the transaction_role CANNOT touch the tables directly
DENY SELECT, INSERT, UPDATE, DELETE ON SCHEMA::LibraryData TO transaction_role;
GO


