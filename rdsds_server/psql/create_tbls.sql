CREATE TABLE dataset(
    Dataset_id SERIAL NOT NULL,
    Dataset_pid VARCHAR,
    DatasetName VARCHAR,
    SourceSiteName VARCHAR,
    TransferSource VARCHAR,
    Protocol VARCHAR,
    Hostname VARCHAR,
    Port INTEGER,
    FilePath VARCHAR,
    CreatorName VARCHAR,
    CreatorEmail VARCHAR,
    Version INTEGER,
    Status VARCHAR,
    UpdatedTime TEXT,
    FolderPath INTEGER,
    Owner_id VARCHAR,
    PRIMARY KEY(Dataset_id)
    );

CREATE TABLE file(
    File_id SERIAL NOT NULL,
    Dataset_pid VARCHAR,
    FileName VARCHAR,
    FileBits VARCHAR,
    FileChecksum VARCHAR,
    UpdatedTime TEXT,
    Version INTEGER,
    Deleted INTEGER,
    Gridftp_time VARCHAR,
    PRIMARY KEY(File_id)
    );

CREATE TABLE sessions(
    Session_id SERIAL NOT NULL,
    Access_token VARCHAR,
    Subscriber_id VARCHAR,
    Timestamp VARCHAR,
    PRIMARY KEY(Session_id)
    );

CREATE TABLE subscriber(
    Subscriber_id SERIAL NOT NULL,
    FullName  VARCHAR,
    Email VARCHAR,
    Organisation VARCHAR,
    HostName VARCHAR,
    Port INTEGER,
    FilePath VARCHAR,
    UserName VARCHAR,
    Status VARCHAR,
    CreatedTime TEXT,
    UpdatedTime TEXT,
    PRIMARY KEY(Subscriber_id)
    );

CREATE TABLE subscription(
    Subs_id SERIAL NOT NULL,
    Subscriber_id VARCHAR,
    Dataset_id VARCHAR,
    Status VARCHAR,
    UpdatedTime TEXT,
    CreatedTime TEXT,
    PRIMARY KEY(Subs_id)
    );

