--CREATE THE DATABASE MMU LIBRARY AND dbo.Accounts, dbo. Books, and dbo.BorrowHistory 

CREATE DATABASE MMU_Library;
GO

USE [MMU_Library];
GO

-- 1. CREATE ACCOUNTS TABLE (No Constraints)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Accounts]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Accounts](
        [AccountID] [int] IDENTITY(1,1) NOT NULL,
        [Username] [nvarchar](50) NOT NULL,
        [Password] [nvarchar](255) NOT NULL,
        [Role] [nvarchar](50) NOT NULL DEFAULT ('Reader'),
        [CreatedDate] [datetime] NOT NULL DEFAULT (getdate()),
        [FailedAttempts] [int] NOT NULL DEFAULT (0),
        [LockoutUntil] [datetime] NULL
    ) ON [PRIMARY];
END
GO

-- 2. CREATE BOOKS TABLE (No Constraints)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Books]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Books](
        [BookID] [int] IDENTITY(1,1) NOT NULL,
        [Title] [nvarchar](255) NOT NULL,
        [Author] [nvarchar](255) NOT NULL,
        [Category] [nvarchar](100) NULL,
        [Available] [int] NOT NULL DEFAULT (1),
        [DueDate] [datetime] NULL
    ) ON [PRIMARY];
END
GO

-- 3. CREATE BORROWHISTORY TABLE (No Constraints)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[BorrowHistory]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[BorrowHistory](
        [BorrowID] [int] IDENTITY(1,1) NOT NULL,
        [AccountID] [int] NOT NULL,
        [BookID] [int] NOT NULL,
        [BorrowDate] [datetime] NOT NULL DEFAULT (getdate()),
        [ReturnDate] [datetime] NULL,
        [Status] [nvarchar](50) NOT NULL
    ) ON [PRIMARY];
END
GO


USE MMU_Library;
GO

--Tiffany's part
-- ADD PRIMARY KEYS
ALTER TABLE [dbo].[Accounts] 
ADD CONSTRAINT [PK_Accounts] PRIMARY KEY CLUSTERED ([AccountID] ASC);

ALTER TABLE [dbo].[Books] 
ADD CONSTRAINT [PK_Books] PRIMARY KEY CLUSTERED ([BookID] ASC);

ALTER TABLE [dbo].[BorrowHistory] 
ADD CONSTRAINT [PK_BorrowHistory] PRIMARY KEY CLUSTERED ([BorrowID] ASC);

-- ADD FOREIGN KEYS
ALTER TABLE [dbo].[BorrowHistory] 
ADD CONSTRAINT [FK_BorrowHistory_Accounts] FOREIGN KEY ([AccountID]) 
REFERENCES [dbo].[Accounts] ([AccountID]);

ALTER TABLE [dbo].[BorrowHistory] 
ADD CONSTRAINT [FK_BorrowHistory_Books] FOREIGN KEY ([BookID]) 
REFERENCES [dbo].[Books] ([BookID]);
GO

--Tiffany's part
-- ALTER ABLE BorrowHistory TO PREVENT INVALID R=TRANSACTION VALUE
ALTER TABLE dbo.BorrowHistory
ADD CONSTRAINT CK_Borrow_Action
CHECK (Status IN ('borrow', 'return'));

AlTER TABLE dbo.Accounts
ADD CONSTRAINT UQ_Accounts_Username UNIQUE (Username);

--Joyce's part
USE MMU_Library;
GO

CREATE LOGIN transaction_login WITH PASSWORD = 'Pa$$w0rd';
CREATE USER transaction_service FOR LOGIN transaction_login;
CREATE ROLE transaction_role;
ALTER ROLE transaction_role ADD MEMBER transaction_service;


--Adibah's part
USE MMU_Library;
GO

CREATE LOGIN librarian_login WITH PASSWORD = 'pa$$w0rd';
CREATE USER librarian FOR LOGIN librarian_login;
CREATE ROLE librarian_role;
ALTER ROLE librarian_role ADD MEMBER librarian;

--Tiffanys part
USE MMU_Library;
GO

CREATE ROLE reader_role;

--Adibah's part
-- Create a schema named 'LibraryData'
CREATE SCHEMA LibraryData;
GO

-- Move the Books, Accounts and BorrowHistory table
ALTER SCHEMA LibraryData TRANSFER dbo.Books;
GO
ALTER SCHEMA LibraryData TRANSFER dbo.Accounts;
GO
ALTER SCHEMA LibraryData TRANSFER dbo.BorrowHistory;
GO

USE MMU_Library;
GO

-- Update your AddBook procedure to the new schema path
CREATE OR ALTER PROCEDURE LibraryData.AddBook
    @Title NVARCHAR(255),
    @Author NVARCHAR(255),
    @Category NVARCHAR(100)
AS
BEGIN
    INSERT INTO LibraryData.Books (Title, Author, Category, Available)
    VALUES (@Title, @Author, @Category, 1);
END;
GO

USE MMU_Library;
GO
-- EditBook
CREATE OR ALTER PROCEDURE LibraryData.EditBook
    @BookID INT,
    @Title NVARCHAR(255),
    @Author NVARCHAR(255),
    @Category NVARCHAR(100)
AS
BEGIN
    UPDATE LibraryData.Books
    SET Title = @Title,
        Author = @Author,
        Category = @Category
    WHERE BookID = @BookID;
END;
GO

USE MMU_Library;
GO
-- EditBook
CREATE OR ALTER PROCEDURE LibraryData.DeleteBook
    @BookID INT
AS
BEGIN
    SET NOCOUNT ON;

    DELETE FROM LibraryData.Books
    WHERE BookID = @BookID;
END;
GO

USE MMU_Library;
GO
-- adjust toggle book
CREATE OR ALTER PROCEDURE LibraryData.ToggleBookStatus
    @BookID INT
AS
BEGIN
    SET NOCOUNT ON;
    -- Updated to use the LibraryData schema
    UPDATE LibraryData.Books
    SET Available = CASE 
        WHEN Available = 1 THEN 0 
        ELSE 1 
    END
    WHERE BookID = @BookID;
END;
GO

USE MMU_Library;
GO
--Create reader account
CREATE OR ALTER PROCEDURE LibraryData.CreateReaderAccount
    @Username NVARCHAR(50),
    @Password NVARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;
    -- Reference the new schema-based table
    INSERT INTO LibraryData.Accounts (Username, Password, Role)
    VALUES (@Username, @Password, 'Reader');
END;
GO

USE MMU_Library;
GO
--Reset user password
CREATE OR ALTER PROCEDURE LibraryData.ResetUserPassword
    @Username NVARCHAR(50),
    @HashedPassword NVARCHAR(255)
AS
BEGIN
    UPDATE LibraryData.Accounts
    SET Password = @HashedPassword,
        FailedAttempts = 0,
        LockoutUntil = NULL,
        CreatedDate = GETDATE()
    WHERE Username = @Username;
END;
GO

USE MMU_Library;
GO
--Delete user account
CREATE OR ALTER PROCEDURE LibraryData.DeleteUser
    @Username NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;
    -- Logic protection for the specific 'librarian' account
    IF LOWER(@Username) = 'librarian'
        THROW 50001, 'Cannot delete main librarian account', 1;

    -- Reference the new schema-based table
    DELETE FROM LibraryData.Accounts
    WHERE Username = @Username;
END;
GO


--Joyce's part
USE MMU_Library;
GO
--Borrow Book
CREATE OR ALTER PROCEDURE LibraryData.BorrowBook
    @AccountID INT,
    @BookID INT
AS
BEGIN
    SET NOCOUNT ON;

    -- 1. Check if the book exists and is available in the LibraryData schema
    IF EXISTS (
        SELECT 1 FROM LibraryData.Books
        WHERE BookID = @bookID AND Available = 1
    )
    BEGIN
        -- 2. Mark the book as borrowed and set a 14-day due date
        UPDATE LibraryData.Books
        SET Available = 0, 
            DueDate = DATEADD(day, 14, GETDATE())
        WHERE BookID = @bookID;

        -- 3. Log the transaction using the new 'AccountID', 'BorrowDate', and 'Status' columns
        INSERT INTO LibraryData.BorrowHistory (AccountID, BookID, BorrowDate, Status)
        VALUES (@AccountID, @bookID, GETDATE(), 'borrow');
        
        PRINT 'Book borrowed successfully.';
    END
    ELSE
    BEGIN
        -- 4. Handle cases where the book is already out or doesn't exist
        PRINT 'Book not available or does not exist.';
    END
END;
GO

USE MMU_Library;
GO
-- Return Book
CREATE OR ALTER PROCEDURE LibraryData.ReturnBook
    @AccountID INT,
    @BookID INT
AS
BEGIN
    SET NOCOUNT ON;

    -- Ensure the book is currently marked as borrowed
    IF EXISTS (
        SELECT 1 FROM LibraryData.Books
        WHERE BookID = @bookID AND Available = 0
    )
    BEGIN
        -- Make the book available again
        UPDATE LibraryData.Books
        SET Available = 1, DueDate = NULL
        WHERE BookID = @bookID;

        -- Log the action using 'return' and record return date 
        INSERT INTO LibraryData.BorrowHistory (AccountID, BookID, ReturnDate, Status)
        VALUES (@AccountID, @bookID, GETDATE(), 'return');
    END
    ELSE
    BEGIN
        PRINT 'Book was not borrowed or does not exist';
    END
END;
GO

--LEAST PRIVILEGE
--Adibah's part
USE MMU_Library;
GO

-- 1. Deny direct table access to the librarian
DENY SELECT, INSERT, UPDATE, DELETE ON SCHEMA::LibraryData TO librarian_role;

-- 2. Grant execution of the updated procedures
GRANT EXECUTE ON LibraryData.AddBook TO librarian_role;
GRANT EXECUTE ON LibraryData.EditBook TO librarian_role;
GRANT EXECUTE ON LibraryData.DeleteBook TO librarian_role;
GRANT EXECUTE ON LibraryData.ToggleBookStatus TO librarian_role;
GRANT EXECUTE ON LibraryData.CreateReaderAccount TO librarian_role;
GRANT EXECUTE ON LibraryData.ResetUserPassword TO librarian_role;
GRANT EXECUTE ON LibraryData.DeleteUser TO librarian_role;
GO

--Joyce's part
USE MMU_Library;
GO

-- 1. Grant Execution on the Adjusted Procedures
-- These procedures now live in the LibraryData schema
GRANT EXECUTE ON LibraryData.BorrowBook TO transaction_role;
GRANT EXECUTE ON LibraryData.ReturnBook TO transaction_role;
GO

-- 2. Apply Deny Restrictions
-- We deny access to the entire LibraryData schema to prevent any manual edits
-- This replaces the individual DENY on Books and Users
DENY INSERT, UPDATE, DELETE, SELECT ON SCHEMA::LibraryData TO transaction_role;
GO

--Tiffany's part
USE MMU_Library;
GO
-- 1. Grant visibility to the entire book catalog
GRANT SELECT ON LibraryData.Books TO reader_role;
-- 2. Grant visibility to their own history
GRANT SELECT ON LibraryData.BorrowHistory TO reader_role;
-- 3. Block all editing to prevent tampering
DENY INSERT, UPDATE, DELETE ON SCHEMA::LibraryData TO reader_role;
-- 4. Specifically deny selection of the Accounts table for privacy
DENY SELECT ON LibraryData.Accounts TO reader_role;
GO

--GUIDANCE
--INPUT THE LIBRARIAN DATA, BOOKS DATA AND READER DATA
USE MMU_Library;
GO

INSERT INTO LibraryData.Accounts (Username, [Password], [Role], CreatedDate, FailedAttempts)
VALUES (
    'librarian', 
    '$2b$12$TguWcPbjDKl3g/eI2B6T8OZZu7bkHRpkF2nAk0y9fsDIDwciYteHe', -- Your provided hash -- "pa$$w0rd"
    'Librarian', 
    GETDATE(), 
    0
);

COMMIT;
GO

--Check whether librarian data already insert or not
--Open the website,Log in as librarian, add reader and add books
--Log in as reader, borrow the books and return
select * from LibraryData.Accounts;
select * from LibraryData.Books;
select * from LibraryData.BorrowHistory;

--APPLY ADVANCE SECURITY
--Adibah's part
--TDE
USE master;
GO
CREATE MASTER KEY ENCRYPTION BY PASSWORD = 'pa$$w0rd';
CREATE CERTIFICATE TDECert WITH SUBJECT = 'Library Data Protection';
GO

USE MMU_Library;
GO
CREATE DATABASE ENCRYPTION KEY
WITH ALGORITHM = AES_256
ENCRYPTION BY SERVER CERTIFICATE TDECert;
GO
ALTER DATABASE MMU_Library SET ENCRYPTION ON;
GO

USE master;
GO

-- Export the certificate and private key to a secure folder
-- Ensure the folder path exists on your computer
BACKUP CERTIFICATE TDECert
TO FILE = 'C:\sem 2 year 3\database and cloud security\combine CCS6344 Database Assignment\Backup\TDE_Certificate.cer'
WITH PRIVATE KEY (
    FILE = 'C:\sem 2 year 3\database and cloud security\combine CCS6344 Database Assignment\Backup\TDE_PrivateKey.pvk',
    ENCRYPTION BY PASSWORD = 'pa$$w0rd'
);
GO

--Backup key in C:
USE master;
GO
BACKUP CERTIFICATE TDECert 
TO FILE = 'C:\sem 2 year 3\database and cloud security\Backupkey\TDE_Backup_Cert.cer'
WITH PRIVATE KEY (
    FILE = 'C:\sem 2 year 3\database and cloud security\Backupkey\TDE_Key_Backup.pvk',
    ENCRYPTION BY PASSWORD = 'pa$$w0rd'
);
GO

-- Masking
USE MMU_Library;
GO

-- Apply the mask to the table in the NEW schema
ALTER TABLE LibraryData.Accounts
ALTER COLUMN [Password] ADD MASKED WITH (FUNCTION = 'partial(0, "XXXX", 0)');
GO

--Tiffany's part
--RLS for reader to check their own account
USE MMU_Library;
GO

CREATE SCHEMA Security;
GO

-- 1. Create the Security Function (Based on image_e8ade0.png)
CREATE OR ALTER FUNCTION Security.fn_reader_rls (@AccountID INT)
    RETURNS TABLE WITH SCHEMABINDING
AS
RETURN (
    SELECT 1 AS accessResult
    WHERE @AccountID = CAST(SESSION_CONTEXT(N'UserID') AS INT) -- Match ID from Flask
       OR IS_MEMBER('db_owner') = 1                             -- Admin see all
);
GO

-- 2. Apply the policy to both tables (Based on image_e8adfd.png)
-- We drop the old one first to prevent Msg 33264
IF EXISTS (SELECT * FROM sys.security_policies WHERE name = 'AccountFilter')
    DROP SECURITY POLICY Security.AccountFilter;
GO

CREATE SECURITY POLICY Security.ReaderBorrowPolicy
ADD FILTER PREDICATE Security.fn_reader_rls(AccountID) ON LibraryData.Accounts,
ADD FILTER PREDICATE Security.fn_reader_rls(AccountID) ON LibraryData.BorrowHistory
WITH (STATE = ON);
GO

--Audit LOG
--Tiffany's and Adibah's part
--Audit login failed
USE master;
GO

-- Create the Audit container
CREATE SERVER AUDIT FailedLoginAudit
TO FILE (FILEPATH = 'C:\sem 2 year 3\database and cloud security\combine CCS6344 Database Assignment\audit\auditlog');
GO

-- Enable the Audit
ALTER SERVER AUDIT FailedLoginAudit WITH (STATE = ON);
GO

-- Track failed logins specifically
CREATE SERVER AUDIT SPECIFICATION FailedLogin_Spec
FOR SERVER AUDIT FailedLoginAudit
ADD (FAILED_LOGIN_GROUP);
GO

ALTER SERVER AUDIT SPECIFICATION FailedLogin_Spec WITH (STATE = ON);
GO

--Audit for Data Modification Audit (The "Who Changed What" Log)
USE master;
GO

-- 1. Create the Audit container pointing to your assignment folder
CREATE SERVER AUDIT ProcessAudit
TO FILE (FILEPATH = 'C:\sem 2 year 3\database and cloud security\combine CCS6344 Database Assignment\audit\processaudit\'); 
GO

-- 2. Enable the Audit
ALTER SERVER AUDIT ProcessAudit WITH (STATE = ON);
GO

USE MMU_Library;
GO

-- 3. Create a specification to track data changes in LibraryData
CREATE DATABASE AUDIT SPECIFICATION Audit_Library_Data_Changes
FOR SERVER AUDIT ProcessAudit 
ADD (INSERT, UPDATE, DELETE ON SCHEMA::LibraryData BY public)
WITH (STATE = ON);
GO

--Security Audit (The "Who Changed the Rules" Log)
USE master;
GO

-- 1. Create the Audit container pointing to your assignment folder
CREATE SERVER AUDIT SecurityAudit
TO FILE (FILEPATH = 'C:\sem 2 year 3\database and cloud security\combine CCS6344 Database Assignment\audit\SecurityAudit'); 
GO

-- 2. Enable the Audit
ALTER SERVER AUDIT SecurityAudit WITH (STATE = ON);
GO

USE master;
GO

-- Track if someone tries to drop the TDE Certificate or change RLS policies
CREATE SERVER AUDIT SPECIFICATION Audit_Security_Changes
FOR SERVER AUDIT SecurityAudit
ADD (SCHEMA_OBJECT_CHANGE_GROUP),    -- Tracks changes to RLS functions/policies
ADD (DATABASE_PERMISSION_CHANGE_GROUP), -- Tracks GRANT/REVOKE actions
ADD (DATABASE_ROLE_MEMBER_CHANGE_GROUP) -- Tracks if someone makes themselves an Admin
WITH (STATE = ON);
GO

--USING INDEX METHOD
USE MMU_Library;
GO

-- 1. Index for RLS on the Accounts table
CREATE INDEX IX_LibraryData_Accounts_AccountID 
ON LibraryData.Accounts(AccountID);
GO

-- 2. Index for RLS on the BorrowHistory table
CREATE INDEX IX_LibraryData_BorrowHistory_AccountID 
ON LibraryData.BorrowHistory(AccountID);
GO

-- 3. Index for Login Performance (speed up Username lookups)
CREATE INDEX IX_LibraryData_Accounts_Username 
ON LibraryData.Accounts(Username);
GO

-- Index for Book searches in BorrowHistory
CREATE INDEX IX_LibraryData_BorrowHistory_BookID 
ON LibraryData.BorrowHistory(BookID);
GO





