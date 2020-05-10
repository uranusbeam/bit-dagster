import sqlalchemy as db

ScheduleStorageSqlMetadata = db.MetaData()

ScheduleTable = db.Table(
    'schedules',
    ScheduleStorageSqlMetadata,
    db.Column('id', db.Integer, primary_key=True, autoincrement=True),
    db.Column('repository_name', db.String(255)),
    db.Column('schedule_name', db.String),
    db.Column('status', db.String(63)),
    db.Column('schedule_body', db.String),
    db.Column('create_timestamp', db.DateTime, server_default=db.text('CURRENT_TIMESTAMP')),
    db.Column('update_timestamp', db.DateTime, server_default=db.text('CURRENT_TIMESTAMP')),
    db.UniqueConstraint('repository_name', 'schedule_name'),
)

ScheduleTickTable = db.Table(
    'schedule_ticks',
    ScheduleStorageSqlMetadata,
    db.Column('id', db.Integer, primary_key=True, autoincrement=True),
    db.Column('repository_name', db.String(255)),
    db.Column('schedule_name', db.String),
    db.Column('status', db.String(63)),
    db.Column('timestamp', db.types.TIMESTAMP),
    db.Column('tick_body', db.String),
    # The create and update timestamps are not used in framework code, are are simply
    # present for debugging purposes.
    db.Column('create_timestamp', db.DateTime, server_default=db.text('CURRENT_TIMESTAMP')),
    db.Column('update_timestamp', db.DateTime, server_default=db.text('CURRENT_TIMESTAMP')),
)
