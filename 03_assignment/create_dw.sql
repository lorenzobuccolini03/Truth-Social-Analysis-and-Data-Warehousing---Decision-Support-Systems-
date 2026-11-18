
SET XACT_ABORT ON;

IF DB_NAME() IN (N'master', N'model', N'msdb', N'tempdb')
BEGIN
    THROW 50001, 'Seleziona il database del tuo gruppo.', 1;
END;

BEGIN TRY
    BEGIN TRANSACTION;

    -- Tabelle _python
    CREATE TABLE dbo.DimDate_python (
        DateKey INT NOT NULL,
        FullDate DATE NULL,
        [Day] TINYINT NULL,
        [Month] TINYINT NULL,
        [Year] SMALLINT NULL,
        DayofWeek TINYINT NULL,
        IsWeekend BIT NULL,
        Season VARCHAR(10) NOT NULL,
        CONSTRAINT PK_DimDate_python PRIMARY KEY (DateKey)
    );

    CREATE TABLE dbo.DimTime_python (
        TimeKey SMALLINT NOT NULL,
        [Hour] TINYINT NULL,
        [Minute] TINYINT NULL,
        DayPeriod VARCHAR(10) NOT NULL,
        CONSTRAINT PK_DimTime_python PRIMARY KEY (TimeKey)
    );

    CREATE TABLE dbo.DimEventType_python (
        EventTypeKey TINYINT NOT NULL,
        EventTypeCode VARCHAR(3) NOT NULL,
        EventTypeName VARCHAR(20) NOT NULL,
        CONSTRAINT PK_DimEventType_python PRIMARY KEY (EventTypeKey),
        CONSTRAINT UQ_DimEventType_python_Code UNIQUE (EventTypeCode)
    );

    CREATE TABLE dbo.DimUser_python (
        UserKey INT NOT NULL,
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
        PostKey INT NOT NULL,
        IntegratedPostID BIGINT NULL,
        PostAuthorUserKey INT NOT NULL,
        PublicationDate DATE NULL,
        PublicationTime TIME(0) NULL,
        Category NVARCHAR(255) NOT NULL,
        Is_Retruth BIT NULL,
        Is_Reply BIT NULL,
        RetruthedPostKey INT NULL,
        HasMedia BIT NULL,
        HasHashtags BIT NULL,
        HasExternalURLS BIT NULL,
        HasMentions BIT NULL,
        TextLength INT NULL,
        WordCount INT NULL,
        HasQuotes BIT NULL,
        CONSTRAINT PK_DimPost_python PRIMARY KEY (PostKey),
        CONSTRAINT UQ_DimPost_python_IntegratedPostID UNIQUE (IntegratedPostID),
        CONSTRAINT FK_DimPost_python_Author
            FOREIGN KEY (PostAuthorUserKey) REFERENCES dbo.DimUser_python (UserKey),
        CONSTRAINT FK_DimPost_python_RetruthedPost
            FOREIGN KEY (RetruthedPostKey) REFERENCES dbo.DimPost_python (PostKey)
    );

    CREATE TABLE dbo.DimMedia_python (
        MediaKey INT NOT NULL,
        SourceMediaID BIGINT NOT NULL,
        MediaURL NVARCHAR(2048) NULL,
        MediaFormat VARCHAR(10) NOT NULL,
        EstimatedSize INT NULL, -- KB
        CONSTRAINT PK_DimMedia_python PRIMARY KEY (MediaKey),
        CONSTRAINT UQ_DimMedia_python_SourceMediaID UNIQUE (SourceMediaID)
    );

    CREATE TABLE dbo.BridgePostMedia_python (
        PostKey INT NOT NULL,
        MediaKey INT NOT NULL,
        CONSTRAINT PK_BridgePostMedia_python PRIMARY KEY (PostKey, MediaKey),
        CONSTRAINT FK_BridgePostMedia_python_Post
            FOREIGN KEY (PostKey) REFERENCES dbo.DimPost_python (PostKey),
        CONSTRAINT FK_BridgePostMedia_python_Media
            FOREIGN KEY (MediaKey) REFERENCES dbo.DimMedia_python (MediaKey)
    );

    CREATE TABLE dbo.FactEvent_python (
        EventKey BIGINT NOT NULL,
        SourceEventID BIGINT NOT NULL,
        PostKey INT NOT NULL,
        ActorUserKey INT NOT NULL,
        PostAuthorUserKey INT NOT NULL,
        EventDateKey INT NOT NULL,
        EventTimekey SMALLINT NOT NULL,
        EventTypeKey TINYINT NOT NULL,
        EventCount TINYINT NOT NULL,
        CONSTRAINT PK_FactEvent_python PRIMARY KEY (EventKey),
        CONSTRAINT UQ_FactEvent_python_SourceEventID UNIQUE (SourceEventID),
        CONSTRAINT CK_FactEvent_python_EventCount CHECK (EventCount = 1),
        CONSTRAINT FK_FactEvent_python_Post
            FOREIGN KEY (PostKey) REFERENCES dbo.DimPost_python (PostKey),
        CONSTRAINT FK_FactEvent_python_Actor
            FOREIGN KEY (ActorUserKey) REFERENCES dbo.DimUser_python (UserKey),
        CONSTRAINT FK_FactEvent_python_PostAuthor
            FOREIGN KEY (PostAuthorUserKey) REFERENCES dbo.DimUser_python (UserKey),
        CONSTRAINT FK_FactEvent_python_Date
            FOREIGN KEY (EventDateKey) REFERENCES dbo.DimDate_python (DateKey),
        CONSTRAINT FK_FactEvent_python_Time
            FOREIGN KEY (EventTimekey) REFERENCES dbo.DimTime_python (TimeKey),
        CONSTRAINT FK_FactEvent_python_Type
            FOREIGN KEY (EventTypeKey) REFERENCES dbo.DimEventType_python (EventTypeKey)
    );

    -- Tabelle _IS
    CREATE TABLE dbo.DimDate_IS (
        DateKey INT NOT NULL,
        FullDate DATE NULL,
        [Day] TINYINT NULL,
        [Month] TINYINT NULL,
        [Year] SMALLINT NULL,
        DayofWeek TINYINT NULL,
        IsWeekend BIT NULL,
        Season VARCHAR(10) NOT NULL,
        CONSTRAINT PK_DimDate_IS PRIMARY KEY (DateKey)
    );

    CREATE TABLE dbo.DimTime_IS (
        TimeKey SMALLINT NOT NULL,
        [Hour] TINYINT NULL,
        [Minute] TINYINT NULL,
        DayPeriod VARCHAR(10) NOT NULL,
        CONSTRAINT PK_DimTime_IS PRIMARY KEY (TimeKey)
    );

    CREATE TABLE dbo.DimEventType_IS (
        EventTypeKey TINYINT NOT NULL,
        EventTypeCode VARCHAR(3) NOT NULL,
        EventTypeName VARCHAR(20) NOT NULL,
        CONSTRAINT PK_DimEventType_IS PRIMARY KEY (EventTypeKey),
        CONSTRAINT UQ_DimEventType_IS_Code UNIQUE (EventTypeCode)
    );

    CREATE TABLE dbo.DimUser_IS (
        UserKey INT NOT NULL,
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
        PostKey INT NOT NULL,
        IntegratedPostID BIGINT NULL,
        PostAuthorUserKey INT NOT NULL,
        PublicationDate DATE NULL,
        PublicationTime TIME(0) NULL,
        Category NVARCHAR(255) NOT NULL,
        Is_Retruth BIT NULL,
        Is_Reply BIT NULL,
        RetruthedPostKey INT NULL,
        HasMedia BIT NULL,
        HasHashtags BIT NULL,
        HasExternalURLS BIT NULL,
        HasMentions BIT NULL,
        TextLength INT NULL,
        WordCount INT NULL,
        HasQuotes BIT NULL,
        CONSTRAINT PK_DimPost_IS PRIMARY KEY (PostKey),
        CONSTRAINT UQ_DimPost_IS_IntegratedPostID UNIQUE (IntegratedPostID),
        CONSTRAINT FK_DimPost_IS_Author
            FOREIGN KEY (PostAuthorUserKey) REFERENCES dbo.DimUser_IS (UserKey),
        CONSTRAINT FK_DimPost_IS_RetruthedPost
            FOREIGN KEY (RetruthedPostKey) REFERENCES dbo.DimPost_IS (PostKey)
    );

    CREATE TABLE dbo.DimMedia_IS (
        MediaKey INT NOT NULL,
        SourceMediaID BIGINT NOT NULL,
        MediaURL NVARCHAR(2048) NULL,
        MediaFormat VARCHAR(10) NOT NULL,
        EstimatedSize INT NULL, -- KB
        CONSTRAINT PK_DimMedia_IS PRIMARY KEY (MediaKey),
        CONSTRAINT UQ_DimMedia_IS_SourceMediaID UNIQUE (SourceMediaID)
    );

    CREATE TABLE dbo.BridgePostMedia_IS (
        PostKey INT NOT NULL,
        MediaKey INT NOT NULL,
        CONSTRAINT PK_BridgePostMedia_IS PRIMARY KEY (PostKey, MediaKey),
        CONSTRAINT FK_BridgePostMedia_IS_Post
            FOREIGN KEY (PostKey) REFERENCES dbo.DimPost_IS (PostKey),
        CONSTRAINT FK_BridgePostMedia_IS_Media
            FOREIGN KEY (MediaKey) REFERENCES dbo.DimMedia_IS (MediaKey)
    );

    CREATE TABLE dbo.FactEvent_IS (
        EventKey BIGINT NOT NULL,
        SourceEventID BIGINT NOT NULL,
        PostKey INT NOT NULL,
        ActorUserKey INT NOT NULL,
        PostAuthorUserKey INT NOT NULL,
        EventDateKey INT NOT NULL,
        EventTimekey SMALLINT NOT NULL,
        EventTypeKey TINYINT NOT NULL,
        EventCount TINYINT NOT NULL,
        CONSTRAINT PK_FactEvent_IS PRIMARY KEY (EventKey),
        CONSTRAINT UQ_FactEvent_IS_SourceEventID UNIQUE (SourceEventID),
        CONSTRAINT CK_FactEvent_IS_EventCount CHECK (EventCount = 1),
        CONSTRAINT FK_FactEvent_IS_Post
            FOREIGN KEY (PostKey) REFERENCES dbo.DimPost_IS (PostKey),
        CONSTRAINT FK_FactEvent_IS_Actor
            FOREIGN KEY (ActorUserKey) REFERENCES dbo.DimUser_IS (UserKey),
        CONSTRAINT FK_FactEvent_IS_PostAuthor
            FOREIGN KEY (PostAuthorUserKey) REFERENCES dbo.DimUser_IS (UserKey),
        CONSTRAINT FK_FactEvent_IS_Date
            FOREIGN KEY (EventDateKey) REFERENCES dbo.DimDate_IS (DateKey),
        CONSTRAINT FK_FactEvent_IS_Time
            FOREIGN KEY (EventTimekey) REFERENCES dbo.DimTime_IS (TimeKey),
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
      N'DimPost_python', N'DimMedia_python', N'BridgePostMedia_python', N'FactEvent_python',
      N'DimDate_IS', N'DimTime_IS', N'DimEventType_IS', N'DimUser_IS',
      N'DimPost_IS', N'DimMedia_IS', N'BridgePostMedia_IS', N'FactEvent_IS'
  )
ORDER BY NomeTabella;
