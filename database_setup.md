## Tables creation

Currently, the database is created inside Toolforge environment.
For that, the guide from [here](https://wikitech.wikimedia.org/wiki/Help:Toolforge/Database#Steps_to_create_a_user_database_on_tools.db.svc.eqiad.wmflabs)
was followed. Database name is <replica_username>__data.

Table creation scripts:
```mysql
create table Sources(
    dbname varchar(32) not null,
    url text,
    update_time datetime,
    primary key (dbname)
);

create table Scripts(
    page_id int unsigned not null,
    title text,
    length int unsigned,
    sourcecode text,
    content_model varbinary(32),
    touched datetime,
    dbname varchar(32) not null,
    in_database bool default 0,
    in_api bool default 0,
    lastrevid int unsigned,
    url text,
    is_missed bool default 0,
    edits int,
    minor_edits int,
    first_edit datetime,
    last_edit datetime,
    anonymous_edit int,
    editors int,
    iwls int,
    pls int,
    langs int,
    transcluded_in int,
    transclusions int,
    categories int,
    pr_level_edit varchar(32),
    pr_level_move varchar(32),
    tags text,
    primary key (page_id, dbname),
    foreign key (dbname) references Sources(dbname)
);

create table Interwiki(
    prefix varchar(32) not null,
    url text,
    primary key (prefix)
);

```


## How to access

To access the created database, open the port:
`ssh -N <username>@dev.toolforge.org -L 1147:tools.db.svc.eqiad.wmflabs:3306
`

Then enter
`mysql --user=<replica_user> --host=127.0.0.1 --port=1147 --password <replica_user>__data`

or copy *replica.my.cnf* to your PC and use `mysql --defaults-file=replica.my.cnf --host=127.0.0.1 --port=1147
<replica_user>__data
`