CREATE TABLE [dbo].[Users] (
    [id] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    [name] NVARCHAR(120) NOT NULL,
    [email] NVARCHAR(255) NOT NULL UNIQUE,
    [password_hash] NVARCHAR(255) NOT NULL,
    [subjects] NVARCHAR(MAX) NOT NULL CONSTRAINT [DF_Users_subjects] DEFAULT (''),
    [skill_level] NVARCHAR(50) NOT NULL CONSTRAINT [DF_Users_skill_level] DEFAULT ('Beginner'),
    [availability] NVARCHAR(MAX) NOT NULL CONSTRAINT [DF_Users_availability] DEFAULT (''),
    [created_at] DATETIME2 NOT NULL CONSTRAINT [DF_Users_created_at] DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT [CK_Users_SkillLevel] CHECK ([skill_level] IN ('Beginner', 'Intermediate', 'Advanced')),
    CONSTRAINT [CK_Users_NameNotBlank] CHECK (LEN(LTRIM(RTRIM([name]))) > 0)
);

CREATE INDEX [IX_Users_Email] ON [dbo].[Users]([email]);

CREATE TABLE [dbo].[StudyGroups] (
    [id] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    [subject] NVARCHAR(120) NOT NULL,
    [description] NVARCHAR(MAX) NOT NULL,
    [schedule] NVARCHAR(255) NOT NULL,
    [max_members] INT NOT NULL CONSTRAINT [DF_StudyGroups_max_members] DEFAULT (5),
    [is_private] BIT NOT NULL CONSTRAINT [DF_StudyGroups_is_private] DEFAULT (0),
    [invite_token] NVARCHAR(64) NOT NULL UNIQUE,
    [creator_id] INT NOT NULL,
    [created_at] DATETIME2 NOT NULL CONSTRAINT [DF_StudyGroups_created_at] DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT [CK_StudyGroups_MaxMembers] CHECK ([max_members] >= 2),
    CONSTRAINT [CK_StudyGroups_SubjectNotBlank] CHECK (LEN(LTRIM(RTRIM([subject]))) > 0),
    CONSTRAINT [FK_StudyGroups_Users] FOREIGN KEY ([creator_id]) REFERENCES [dbo].[Users]([id])
);

CREATE INDEX [IX_StudyGroups_Subject] ON [dbo].[StudyGroups]([subject]);

CREATE TABLE [dbo].[GroupMembers] (
    [user_id] INT NOT NULL,
    [group_id] INT NOT NULL,
    [role] NVARCHAR(20) NOT NULL CONSTRAINT [DF_GroupMembers_role] DEFAULT ('member'),
    [joined_at] DATETIME2 NOT NULL CONSTRAINT [DF_GroupMembers_joined_at] DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT [PK_GroupMembers] PRIMARY KEY ([user_id], [group_id]),
    CONSTRAINT [CK_GroupMembers_Role] CHECK ([role] IN ('admin', 'moderator', 'member')),
    CONSTRAINT [FK_GroupMembers_Users] FOREIGN KEY ([user_id]) REFERENCES [dbo].[Users]([id]),
    CONSTRAINT [FK_GroupMembers_StudyGroups] FOREIGN KEY ([group_id]) REFERENCES [dbo].[StudyGroups]([id])
);

CREATE INDEX [IX_GroupMembers_GroupRole] ON [dbo].[GroupMembers]([group_id], [role]);

CREATE TABLE [dbo].[GroupSessions] (
    [id] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    [group_id] INT NOT NULL,
    [title] NVARCHAR(160) NOT NULL,
    [starts_at] DATETIME2 NOT NULL,
    [duration_minutes] INT NOT NULL CONSTRAINT [DF_GroupSessions_duration] DEFAULT (60),
    [notes] NVARCHAR(MAX) NOT NULL CONSTRAINT [DF_GroupSessions_notes] DEFAULT (''),
    [created_at] DATETIME2 NOT NULL CONSTRAINT [DF_GroupSessions_created_at] DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT [CK_GroupSessions_Duration] CHECK ([duration_minutes] >= 15),
    CONSTRAINT [FK_GroupSessions_StudyGroups] FOREIGN KEY ([group_id]) REFERENCES [dbo].[StudyGroups]([id])
);

CREATE INDEX [IX_GroupSessions_GroupStarts] ON [dbo].[GroupSessions]([group_id], [starts_at]);

CREATE TABLE [dbo].[Subscriptions] (
    [id] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    [user_id] INT NOT NULL,
    [plan_type] NVARCHAR(20) NOT NULL CONSTRAINT [DF_Subscriptions_plan_type] DEFAULT ('free'),
    [start_date] DATETIME2 NOT NULL CONSTRAINT [DF_Subscriptions_start_date] DEFAULT (SYSUTCDATETIME()),
    [end_date] DATETIME2 NOT NULL,
    [status] NVARCHAR(20) NOT NULL CONSTRAINT [DF_Subscriptions_status] DEFAULT ('active'),
    [stripe_subscription_id] NVARCHAR(255) NULL,
    [created_at] DATETIME2 NOT NULL CONSTRAINT [DF_Subscriptions_created_at] DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT [CK_Subscriptions_PlanType] CHECK ([plan_type] IN ('free', 'premium')),
    CONSTRAINT [CK_Subscriptions_Status] CHECK ([status] IN ('active', 'expired')),
    CONSTRAINT [CK_Subscriptions_DateWindow] CHECK ([end_date] > [start_date]),
    CONSTRAINT [FK_Subscriptions_Users] FOREIGN KEY ([user_id]) REFERENCES [dbo].[Users]([id])
);

CREATE INDEX [IX_Subscriptions_UserEnd] ON [dbo].[Subscriptions]([user_id], [end_date]);

CREATE TABLE [dbo].[ChatMessages] (
    [id] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    [group_id] INT NOT NULL,
    [user_id] INT NOT NULL,
    [content] NVARCHAR(MAX) NOT NULL,
    [created_at] DATETIME2 NOT NULL CONSTRAINT [DF_ChatMessages_created_at] DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT [CK_ChatMessages_Content] CHECK (LEN(LTRIM(RTRIM([content]))) > 0),
    CONSTRAINT [FK_ChatMessages_Groups] FOREIGN KEY ([group_id]) REFERENCES [dbo].[StudyGroups]([id]),
    CONSTRAINT [FK_ChatMessages_Users] FOREIGN KEY ([user_id]) REFERENCES [dbo].[Users]([id])
);

CREATE INDEX [IX_ChatMessages_GroupCreated] ON [dbo].[ChatMessages]([group_id], [created_at]);
