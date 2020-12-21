## Tables creation

Currently, the database is created inside Toolforge environment.
For that, the guide from [here](https://wikitech.wikimedia.org/wiki/Help:Toolforge/Database#Steps_to_create_a_user_database_on_tools.db.svc.eqiad.wmflabs)
was followed. Database name is <replica_username>__data.

Table creation scripts:
```mysql
create table Sources(
    dbname varchar(32) not null,
    url text not null,
    update_time datetime,
    primary key (dbname)
);

create table Scripts(
    id int unsigned not null auto_increment,
    title text,
    page_id int unsigned not null,
    length int unsigned,
    sourcecode text,
    content_model varbinary(32),
    touched datetime,
    dbname varchar(32) not null,
    in_database bool,
    in_api bool,
    primary key (id),
    foreign key (dbname) references Sources(dbname)
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