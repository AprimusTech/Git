CREATE TABLE dbo.PF_Accounts (
    AccountID INT IDENTITY(1,1) PRIMARY KEY,
    AccountName NVARCHAR(100) NOT NULL,
    AccountType NVARCHAR(40) NOT NULL,
    OpeningBalance DECIMAL(18,2) NOT NULL DEFAULT 0,
    Notes NVARCHAR(500) NULL,
    IsActive BIT NOT NULL DEFAULT 1
);
CREATE TABLE dbo.PF_Transactions (
    TransactionID INT IDENTITY(1,1) PRIMARY KEY,
    TransactionDate DATE NOT NULL,
    TransactionType NVARCHAR(20) NOT NULL,
    Category NVARCHAR(80) NOT NULL,
    Amount DECIMAL(18,2) NOT NULL,
    AccountName NVARCHAR(100) NULL,
    PaidBy NVARCHAR(80) NULL,
    Description NVARCHAR(500) NULL
);
CREATE TABLE dbo.PF_Loans (
    LoanID INT IDENTITY(1,1) PRIMARY KEY,
    Lender NVARCHAR(100) NOT NULL,
    LoanType NVARCHAR(60) NOT NULL,
    LoanStartDate DATE NULL,
    OriginalAmount DECIMAL(18,2) NOT NULL DEFAULT 0,
    OutstandingPrincipal DECIMAL(18,2) NOT NULL DEFAULT 0,
    InterestRate DECIMAL(9,4) NOT NULL DEFAULT 0,
    EMI DECIMAL(18,2) NOT NULL DEFAULT 0,
    DueDay INT NULL,
    TenureMonths INT NULL,
    Notes NVARCHAR(500) NULL
);
CREATE TABLE dbo.PF_CreditCards (
    CardID INT IDENTITY(1,1) PRIMARY KEY,
    CardName NVARCHAR(100) NOT NULL,
    Issuer NVARCHAR(100) NULL,
    CreditLimit DECIMAL(18,2) NOT NULL DEFAULT 0,
    Outstanding DECIMAL(18,2) NOT NULL DEFAULT 0,
    StatementDay INT NULL,
    DueDay INT NULL,
    Notes NVARCHAR(500) NULL
);
CREATE TABLE dbo.PF_Udhar (
    UdharID INT IDENTITY(1,1) PRIMARY KEY,
    Direction NVARCHAR(20) NOT NULL,
    PersonName NVARCHAR(100) NOT NULL,
    TransactionDate DATE NOT NULL,
    OriginalAmount DECIMAL(18,2) NOT NULL,
    Outstanding DECIMAL(18,2) NOT NULL,
    InterestRate DECIMAL(9,4) NOT NULL DEFAULT 0,
    ExpectedDate DATE NULL,
    Notes NVARCHAR(500) NULL
);
