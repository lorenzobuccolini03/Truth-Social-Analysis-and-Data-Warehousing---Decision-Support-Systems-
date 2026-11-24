
SET XACT_ABORT ON;

IF DB_NAME() IN (N'master', N'model', N'msdb', N'tempdb')
BEGIN
    THROW 50001, 'Seleziona il database del tuo gruppo.', 1;
END;

BEGIN TRY
    BEGIN TRANSACTION;

    -- Tabelle _python
    CREATE TABLE dbo.DimDate_python (
        DateKey INT IDENTITY(1,1) NOT NULL,
        FullDate DATE NULL,
        [Day] TINYINT NULL,
        [Month] TINYINT NULL,
        [Year] SMALLINT NULL,
        DayofWeek TINYINT NULL,
        Season VARCHAR(10) NOT NULL,
        CONSTRAINT PK_DimDate_python PRIMARY KEY (DateKey),
        CONSTRAINT UQ_DimDate_python_Source UNIQUE (FullDate)
    );

    CREATE TABLE dbo.DimTime_python (
        TimeKey SMALLINT IDENTITY(1,1) NOT NULL,
        [Hour] TINYINT NULL,
        [Minute] TINYINT NULL,
        DayPeriod VARCHAR(10) NOT NULL,
        CONSTRAINT PK_DimTime_python PRIMARY KEY (TimeKey),
        CONSTRAINT UQ_DimTime_python_Source UNIQUE ([Hour], [Minute])
    );

    CREATE TABLE dbo.DimEventType_python (
        EventTypeKey TINYINT IDENTITY(1,1) NOT NULL,
        EventTypeCode VARCHAR(3) NOT NULL,
        EventTypeName VARCHAR(20) NOT NULL,
        CONSTRAINT PK_DimEventType_python PRIMARY KEY (EventTypeKey),
        CONSTRAINT UQ_DimEventType_python_Code UNIQUE (EventTypeCode)
    );

    CREATE TABLE dbo.DimUser_python (
        UserKey INT IDENTITY(1,1) NOT NULL,
        SourceUserID BIGINT NULL,
        Username NVARCHAR(255) NULL,
        FollowersCount BIGINT NULL,
        FollowingCount BIGINT NULL,
        AccountCreationDate DATE NULL,
        IsDonaldTrump BIT NOT NULL,
        CONSTRAINT PK_DimUser_python PRIMARY KEY (UserKey),
        CONSTRAINT UQ_DimUser_python_SourceUserID UNIQUE (SourceUserID)
    );

    CREATE TABLE dbo.DimPost_python (
        PostKey INT IDENTITY(1,1) NOT NULL,
        IntegratedPostID BIGINT NULL,
        PublicationDate DATE NULL,
        PublicationTime TIME(0) NULL,
        Category NVARCHAR(255) NOT NULL,
        Is_Retruth BIT NULL,
        Is_Reply BIT NULL,
        RetruthedPostKey INT NULL,
        TextLength INT NULL,
        WordCount INT NULL,
        EstimatedMediaSize INT NULL, -- KB
        CONSTRAINT PK_DimPost_python PRIMARY KEY (PostKey),
        CONSTRAINT UQ_DimPost_python_IntegratedPostID UNIQUE (IntegratedPostID)
    );

    CREATE TABLE dbo.FactEvent_python (
        EventKey BIGINT IDENTITY(1,1) NOT NULL,
        SourceEventID BIGINT NOT NULL,
        PostKey INT NOT NULL,
        ActorUserKey INT NOT NULL,
        PostAuthorUserKey INT NOT NULL,
        EventDateKey INT NOT NULL,
        EventTimeKey SMALLINT NOT NULL,
        EventTypeKey TINYINT NOT NULL,
        CONSTRAINT PK_FactEvent_python PRIMARY KEY (EventKey),
        CONSTRAINT UQ_FactEvent_python_SourceEventID UNIQUE (SourceEventID),
        CONSTRAINT FK_FactEvent_python_Post
            FOREIGN KEY (PostKey) REFERENCES dbo.DimPost_python (PostKey),
        CONSTRAINT FK_FactEvent_python_Actor
            FOREIGN KEY (ActorUserKey) REFERENCES dbo.DimUser_python (UserKey),
        CONSTRAINT FK_FactEvent_python_PostAuthor
            FOREIGN KEY (PostAuthorUserKey) REFERENCES dbo.DimUser_python (UserKey),
        CONSTRAINT FK_FactEvent_python_Date
            FOREIGN KEY (EventDateKey) REFERENCES dbo.DimDate_python (DateKey),
        CONSTRAINT FK_FactEvent_python_Time
            FOREIGN KEY (EventTimeKey) REFERENCES dbo.DimTime_python (TimeKey),
        CONSTRAINT FK_FactEvent_python_Type
            FOREIGN KEY (EventTypeKey) REFERENCES dbo.DimEventType_python (EventTypeKey)
    );

    -- Tabelle _IS
    CREATE TABLE dbo.DimDate_IS (
        DateKey INT IDENTITY(1,1) NOT NULL,
        FullDate DATE NULL,
        [Day] TINYINT NULL,
        [Month] TINYINT NULL,
        [Year] SMALLINT NULL,
        DayofWeek TINYINT NULL,
        Season VARCHAR(10) NOT NULL,
        CONSTRAINT PK_DimDate_IS PRIMARY KEY (DateKey),
        CONSTRAINT UQ_DimDate_IS_Source UNIQUE (FullDate)
    );

    CREATE TABLE dbo.DimTime_IS (
        TimeKey SMALLINT IDENTITY(1,1) NOT NULL,
        [Hour] TINYINT NULL,
        [Minute] TINYINT NULL,
        DayPeriod VARCHAR(10) NOT NULL,
        CONSTRAINT PK_DimTime_IS PRIMARY KEY (TimeKey),
        CONSTRAINT UQ_DimTime_IS_Source UNIQUE ([Hour], [Minute])
    );

    CREATE TABLE dbo.DimEventType_IS (
        EventTypeKey TINYINT IDENTITY(1,1) NOT NULL,
        EventTypeCode VARCHAR(3) NOT NULL,
        EventTypeName VARCHAR(20) NOT NULL,
        CONSTRAINT PK_DimEventType_IS PRIMARY KEY (EventTypeKey),
        CONSTRAINT UQ_DimEventType_IS_Code UNIQUE (EventTypeCode)
    );

    CREATE TABLE dbo.DimUser_IS (
        UserKey INT IDENTITY(1,1) NOT NULL,
        SourceUserID BIGINT NULL,
        Username NVARCHAR(255) NULL,
        FollowersCount BIGINT NULL,
        FollowingCount BIGINT NULL,
        AccountCreationDate DATE NULL,
        IsDonaldTrump BIT NOT NULL,
        CONSTRAINT PK_DimUser_IS PRIMARY KEY (UserKey),
        CONSTRAINT UQ_DimUser_IS_SourceUserID UNIQUE (SourceUserID)
    );

    CREATE TABLE dbo.DimPost_IS (
        PostKey INT IDENTITY(1,1) NOT NULL,
        IntegratedPostID BIGINT NULL,
        PublicationDate DATE NULL,
        PublicationTime TIME(0) NULL,
        Category NVARCHAR(255) NOT NULL,
        Is_Retruth BIT NULL,
        Is_Reply BIT NULL,
        RetruthedPostKey INT NULL,
        TextLength INT NULL,
        WordCount INT NULL,
        EstimatedMediaSize INT NULL, -- KB
        CONSTRAINT PK_DimPost_IS PRIMARY KEY (PostKey),
        CONSTRAINT UQ_DimPost_IS_IntegratedPostID UNIQUE (IntegratedPostID)
    );

    CREATE TABLE dbo.FactEvent_IS (
        EventKey BIGINT IDENTITY(1,1) NOT NULL,
        SourceEventID BIGINT NOT NULL,
        PostKey INT NOT NULL,
        ActorUserKey INT NOT NULL,
        PostAuthorUserKey INT NOT NULL,
        EventDateKey INT NOT NULL,
        EventTimeKey SMALLINT NOT NULL,
        EventTypeKey TINYINT NOT NULL,
        CONSTRAINT PK_FactEvent_IS PRIMARY KEY (EventKey),
        CONSTRAINT UQ_FactEvent_IS_SourceEventID UNIQUE (SourceEventID),
        CONSTRAINT FK_FactEvent_IS_Post
            FOREIGN KEY (PostKey) REFERENCES dbo.DimPost_IS (PostKey),
        CONSTRAINT FK_FactEvent_IS_Actor
            FOREIGN KEY (ActorUserKey) REFERENCES dbo.DimUser_IS (UserKey),
        CONSTRAINT FK_FactEvent_IS_PostAuthor
            FOREIGN KEY (PostAuthorUserKey) REFERENCES dbo.DimUser_IS (UserKey),
        CONSTRAINT FK_FactEvent_IS_Date
            FOREIGN KEY (EventDateKey) REFERENCES dbo.DimDate_IS (DateKey),
        CONSTRAINT FK_FactEvent_IS_Time
            FOREIGN KEY (EventTimeKey) REFERENCES dbo.DimTime_IS (TimeKey),
        CONSTRAINT FK_FactEvent_IS_Type
            FOREIGN KEY (EventTypeKey) REFERENCES dbo.DimEventType_IS (EventTypeKey)
    );

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0
        ROLLBACK TRANSACTION;
    THROW;
END CATCH;

-- Elenco delle tabelle create nel database selezionato.
SELECT SCHEMA_NAME(t.schema_id) AS NomeSchema, t.name AS NomeTabella
FROM sys.tables AS t
WHERE t.schema_id = SCHEMA_ID(N'dbo')
  AND t.name IN (
      N'DimDate_python', N'DimTime_python', N'DimEventType_python', N'DimUser_python',
      N'DimPost_python', N'FactEvent_python',
      N'DimDate_IS', N'DimTime_IS', N'DimEventType_IS', N'DimUser_IS',
      N'DimPost_IS', N'FactEvent_IS'
  )
ORDER BY NomeTabella;
