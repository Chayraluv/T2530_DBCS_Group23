USE MMU_Library;
GO

CREATE ROLE librarian_role;

CREATE LOGIN librarian_login WITH PASSWORD = 'pa$$w0rd';

CREATE USER librarian FOR LOGIN librarian_login;

GRANT SELECT, INSERT, UPDATE ON dbo.Books TO librarian_role;
GRANT SELECT ON dbo.BorrowHistory TO librarian_role;

ALTER ROLE librarian_role ADD MEMBER [librarian];

USE MMU_Library;
GO

-- Create a new Reader account
CREATE PROCEDURE dbo.CreateReaderAccount
    @Username NVARCHAR(50),
    @Password NVARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO dbo.Accounts (Username, Password, Role)
    VALUES (@Username, @Password, 'Reader');
END;
GO

-- Reset a user's password
CREATE PROCEDURE dbo.ResetUserPassword
    @Username NVARCHAR(50),
    @NewPassword NVARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.Accounts
    SET Password = @NewPassword,
        CreatedDate = GETDATE()
    WHERE Username = @Username;
END;
GO

-- Delete a user (with protection for the main librarian account)
CREATE PROCEDURE dbo.DeleteUser
    @Username NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;
    IF LOWER(@Username) = 'librarian'
        THROW 50001, 'Cannot delete main librarian account', 1;

    DELETE FROM dbo.Accounts
    WHERE Username = @Username;
END;
GO

USE MMU_Library;
GO

-- Add a new book to the inventory
CREATE PROCEDURE dbo.AddBook
    @Title NVARCHAR(255),
    @Author NVARCHAR(255)
AS
BEGIN
    INSERT INTO dbo.Books (Title, Author, Available)
    VALUES (@Title, @Author, 1);
END;
GO

-- Edit an existing book's details
CREATE PROCEDURE dbo.EditBook
    @BookID INT,
    @Title NVARCHAR(255),
    @Author NVARCHAR(255)
AS
BEGIN
    UPDATE dbo.Books
    SET Title = @Title,
        Author = @Author
    WHERE BookID = @BookID;
END;
GO

-- Remove a book from the inventory
CREATE PROCEDURE dbo.DeleteBook
    @BookID INT
AS
BEGIN
    DELETE FROM dbo.Books
    WHERE BookID = @BookID;
END;
GO

-- Toggle the availability status of a book
CREATE PROCEDURE dbo.ToggleBookStatus
    @BookID INT
AS
BEGIN
    UPDATE dbo.Books
    SET Available = CASE 
        WHEN Available = 1 THEN 0 
        ELSE 1 
    END
    WHERE BookID = @BookID;
END;
GO

USE MMU_Library;
GO

-- Grant execution permissions for all procedures to the librarian role
GRANT EXECUTE ON dbo.CreateReaderAccount TO librarian_role;
GRANT EXECUTE ON dbo.ResetUserPassword TO librarian_role;
GRANT EXECUTE ON dbo.DeleteUser TO librarian_role;
GRANT EXECUTE ON dbo.AddBook TO librarian_role;
GRANT EXECUTE ON dbo.EditBook TO librarian_role;
GRANT EXECUTE ON dbo.DeleteBook TO librarian_role;
GRANT EXECUTE ON dbo.ToggleBookStatus TO librarian_role;
GO

-- Deny direct table access to ensure users must use procedures
DENY SELECT, INSERT, UPDATE, DELETE ON dbo.Accounts TO librarian_role;
DENY SELECT, INSERT, UPDATE, DELETE ON dbo.Books TO librarian_role;

DENY SELECT, INSERT, UPDATE, DELETE ON dbo.Accounts TO reader_role;
DENY SELECT, INSERT, UPDATE, DELETE ON dbo.Books TO reader_role;
GO

CREATE SERVER AUDIT AccountAudit
TO FILE (FILEPATH = 'C:\sem 2 year 3\database and cloud security\combine CCS6344 Database Assignment\audit\accountaudit');

CREATE SERVER AUDIT LibraryAudit
TO FILE (FILEPATH = 'C:\sem 2 year 3\database and cloud security\combine CCS6344 Database Assignment\audit\bookaudit');

CREATE DATABASE AUDIT SPECIFICATION LibraryAuditSpec
FOR SERVER AUDIT LibraryAudit
ADD (INSERT, UPDATE, DELETE ON dbo.Books BY librarian_role);

CREATE DATABASE AUDIT SPECIFICATION AccountAuditSpec
FOR SERVER AUDIT AccountAudit
ADD (INSERT, UPDATE, DELETE ON dbo.Accounts BY librarian_role);

USE MMU_Library;
GO

-- Create a schema named 'LibraryData'
CREATE SCHEMA LibraryData;
GO

-- Move the Books table
ALTER SCHEMA LibraryData TRANSFER dbo.Books;
GO

-- Move the Accounts table
ALTER SCHEMA LibraryData TRANSFER dbo.Accounts;
GO

ALTER SCHEMA LibraryData TRANSFER dbo.BorrowHistory;
GO

-- Grant the librarian role full control over everything inside this schema
GRANT SELECT, INSERT, UPDATE, DELETE ON SCHEMA::LibraryData TO librarian_role;
GO

-- Update your AddBook procedure to the new schema path
CREATE OR ALTER PROCEDURE dbo.AddBook
    @Title NVARCHAR(255),
    @Author NVARCHAR(255)
AS
BEGIN
    INSERT INTO LibraryData.Books (Title, Author, Available)
    VALUES (@Title, @Author, 1);
END;
GO

USE MMU_Library;
GO

-- 1. Adjusted EditBook Procedure
CREATE OR ALTER PROCEDURE dbo.EditBook
    @BookID INT,
    @Title NVARCHAR(255),
    @Author NVARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;
    -- Updated to use the LibraryData schema
    UPDATE LibraryData.Books
    SET Title = @Title,
        Author = @Author
    WHERE BookID = @BookID;
END;
GO

-- 2. Adjusted DeleteBook Procedure
CREATE OR ALTER PROCEDURE dbo.DeleteBook
    @BookID INT
AS
BEGIN
    SET NOCOUNT ON;
    -- Updated to use the LibraryData schema
    DELETE FROM LibraryData.Books
    WHERE BookID = @BookID;
END;
GO

-- 3. Adjusted ToggleBookStatus Procedure
CREATE OR ALTER PROCEDURE dbo.ToggleBookStatus
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

-- 1. Adjusted CreateReaderAccount Procedure
CREATE OR ALTER PROCEDURE dbo.CreateReaderAccount
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

-- 2. Adjusted ResetUserPassword Procedure
CREATE OR ALTER PROCEDURE dbo.ResetUserPassword
    @Username NVARCHAR(50),
    @NewPassword NVARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;
    -- Reference the new schema-based table
    UPDATE LibraryData.Accounts
    SET Password = @NewPassword,
        CreatedDate = GETDATE()
    WHERE Username = @Username;
END;
GO

-- 3. Adjusted DeleteUser Procedure
CREATE OR ALTER PROCEDURE dbo.DeleteUser
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

-- 1. Deny direct table access to the librarian
DENY SELECT, INSERT, UPDATE, DELETE ON SCHEMA::LibraryData TO librarian_role;

-- 2. Grant execution of the updated procedures
GRANT EXECUTE ON dbo.AddBook TO librarian_role;
GRANT EXECUTE ON dbo.EditBook TO librarian_role;
GRANT EXECUTE ON dbo.DeleteBook TO librarian_role;
GRANT EXECUTE ON dbo.ToggleBookStatus TO librarian_role;
GRANT EXECUTE ON dbo.CreateReaderAccount TO librarian_role;
GRANT EXECUTE ON dbo.ResetUserPassword TO librarian_role;
GRANT EXECUTE ON dbo.DeleteUser TO librarian_role;
GO

-- Disable the audit spec first
ALTER DATABASE AUDIT SPECIFICATION LibraryAuditSpec WITH (STATE = OFF);

-- Update the action to point to the new schema
ALTER DATABASE AUDIT SPECIFICATION LibraryAuditSpec
FOR SERVER AUDIT LibraryAudit
ADD (INSERT, UPDATE, DELETE ON LibraryData.Books BY librarian_role);

-- Re-enable
ALTER DATABASE AUDIT SPECIFICATION LibraryAuditSpec WITH (STATE = ON);
GO

ALTER DATABASE AUDIT SPECIFICATION AccountAuditSpec WITH (STATE = OFF);
GO

ALTER DATABASE AUDIT SPECIFICATION AccountAuditSpec
FOR SERVER AUDIT AccountAudit
ADD (INSERT, UPDATE, DELETE ON LibraryData.Accounts BY librarian_role);
GO

ALTER DATABASE AUDIT SPECIFICATION AccountAuditSpec WITH (STATE = ON);
GO

--CREATE TDE
USE master;
GO
CREATE MASTER KEY ENCRYPTION BY PASSWORD = 'Pa$$w0rd';
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

-- Masking
USE MMU_Library;
GO

-- Apply the mask to the table in the NEW schema
ALTER TABLE LibraryData.Accounts
ALTER COLUMN [Password] ADD MASKED WITH (FUNCTION = 'partial(0, "XXXX", 0)');
GO

--check masking
USE MMU_Library;
GO

-- Create a login and user for testing
CREATE LOGIN ReaderTestUser WITH PASSWORD = 'CNY';
CREATE USER ReaderTestUser FOR LOGIN ReaderTestUser;

-- Grant basic select permissions on the schema
GRANT SELECT ON SCHEMA::LibraryData TO ReaderTestUser;
GO

-- Switch to the Reader user
EXECUTE AS USER = 'ReaderTestUser';

-- Try to see the passwords
SELECT Username, [Password] 
FROM LibraryData.Accounts;

-- Switch back to your admin account
REVERT;
GO

-- Adjust procedure, add, edit 


-- Add Book
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

-- Edit Book
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

CREATE OR ALTER PROCEDURE LibraryData.DeleteBook
    @BookID INT
AS
BEGIN
    SET NOCOUNT ON;

    DELETE FROM LibraryData.Books
    WHERE BookID = @BookID;
END;
GO

--RLS for reader to check their own account

USE MMU_Library;
GO

-- Create a schema for security functions to keep them organized
CREATE SCHEMA Security;
GO

CREATE FUNCTION Security.fn_securitypredicate(@Username AS sysname)
    RETURNS TABLE
WITH SCHEMABINDING
AS
    RETURN SELECT 1 AS fn_securitypredicate_result
    WHERE USER_NAME() = @Username  -- User can see their own row
       OR IS_MEMBER('db_owner') = 1; -- Admins can see everything
GO

CREATE SECURITY POLICY Security.AccountFilter
ADD FILTER PREDICATE Security.fn_securitypredicate(Username)
ON LibraryData.Accounts
WITH (STATE = ON);
GO

USE MMU_Library;
GO
REVERT; -- Ensure you are back to Admin
GO

-- 1. Fix the data so RLS can find a match
-- Make sure a row actually exists for 'ReaderTestUser'
UPDATE LibraryData.Accounts 
SET Username = 'ReaderTestUser', 
    [Password] = 'MyNewSecret123' -- Set a real password as Admin
WHERE Username = 'adibah'; -- Or whichever row you want to test
GO

-- 2. Test the RLS again
EXECUTE AS USER = 'ReaderTestUser';
SELECT * FROM LibraryData.Accounts; -- Now you should see EXACTLY 1 row
REVERT;
GO

-- Create index
CREATE INDEX IX_Books_Title 
ON LibraryData.Books(Title);
GO

--CREATE INDEX IX_Books_Title 
--ON LibraryData.Books(Title);
--GO


--Reset user password since have problem
CREATE PROCEDURE LibraryData.ResetUserPassword
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
END
