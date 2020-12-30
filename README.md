# Abstract Wikipedia Data Science

Repository for fetching and analyzing community functions from different Wikipedias.

This project is Outreachy 21 task, more info can be found in [phabricator](https://phabricator.wikimedia.org/T263678). 

### How to use

*1. Create Wikimedia developer account and create a new tool in Toolforge.*

The scripts get a lot of information from Wikimedia table replicas, and these replicas are accessed from the 
Toolforge. Please follow [this page](https://wikitech.wikimedia.org/wiki/Portal:Toolforge/Quickstart) 
to create an account, and a new tool to use this project in.

*2. Create user database*

Fetched data is stored into the database, created by user. To create the user's database, please follow 
[this guide](database_setup.md). Scripts use this database, fetching the name stored in `DATABASE_NAME` constant.

*3. Run the scripts*

To run the scripts from Toolforge tool's account, first you need to initiate Python environment and 
install requirements. For this, do the following:
```shell
$ chmod +x init.sh
$ ./init.sh
```

This will set up Python environment (and get some work done for 
[setting up cron jobs](#how-to-schedule-the-scripts)). After that, ypu can run Python code.

Some scripts require positional arguments to run correctly, especially if you want to run them from local PC
(more info [here](#how-to-use-code-remotely)). To find out more on which exactly arguments the program needs, 
help is available by running `python3 <script-name> -h`.

In short, right now only *fetch_content.py* has obligatory parameters *start_idx* and *end_idx*, which are used
to let you choose, which exactly wikis you are fetching modules from (indexes start with 0, and the order of them
is based on *Sources* table order).

The order to run the scripts is:
1. wikis_parser.py
2. fetch_content.py 
3. db_script.py
4. get_db_pages.py

As running some scripts require quite a lot of time and computations, whe in Toolforge environment, 
it is recommended to use [jsub](https://wikitech.wikimedia.org/wiki/Help:Toolforge/Grid#Submitting_simple_one-off_jobs_using_'jsub').
You can submit a jsub job by using corresponding script from *shell_scripts* folder.

#### What python files are doing

1. wikis_parser.py

   Collects all the names of wikis' databases and their urls from meta database and saves them to Sources table. 

3. fetch_content.py
   
   Collects full info about Scribunto modules from the list of the wikis, stored in Sources, using Wikimedia API; 
   saves this info to Scripts table.

3. db_script.py
   
   Collects basic info (page_id, title) about Scribunto modules from the list of the wikis, stored in Sources,
   using database replicas; saves this info to Scripts table or updates in_database flag, if the same thing 
   was obtained through API requests.
   
4. get_db_pages.py

   Collects additional info about Scribunto modules, whose info was fetched from database replicas, but didn't appear
   in API request results; saves this info to Scripts table.

### How to use code remotely

You can run python scripts, mentioned previously, from your local PC - but you still have to establish
connection to the Toolforge. This requires you to use [ssh tunneling to Toolforge databases](https://wikitech.wikimedia.org/wiki/Help:Toolforge/Database#SSH_tunneling_for_local_testing_which_makes_use_of_Wiki_Replica_databases).
Most likely, you'd need to open the tunnel to two databases: any wiki on *analytics.db.svc.eqiad.wmflabs*
(for example, *enwiki.analytics.db.svc.eqiad.wmflabs*) and *tools.db.svc.eqiad.wmflabs*. 
The ssh port of 1st connection is referred to as *replicas port*, as it allows connecting to the Wikimedia database replicas,
the ssh port of 2nd connection is referred to as *user db port*, as user's database is stored in Tools.

Additionally, you'll need to know the username and password of the tool, where you created the user's database. 
This info is stored into *$HOME/replica.my.cnf* so get this file's content, for example, 
with `$ nano $HOME/replica.my.cnf`

To run scripts from local environment, you need to use flags and parameters. 
For example, this is how to get *wikis_parser.py* working from local environment:
```shell
$ python3 wikis_parser.py -l -r=<replicas-port> -udb=<user-db-port> -u=<username> -p=<password>
```

+ `-l` or `--local` states that the connection should be handled through ssh tunneling.
All the other info is not used, if this argument is missed.
  
+ `-r` or `--replicas-port` requires the port of the ssh tunnel, connected to any database on
*analytics.db.svc.eqiad.wmflabs*, as discussed before.
  
+ `-udb` or `--user-db-port` requires the port of the ssh tunnel, connected to user's database on
*tools.db.svc.eqiad.wmflabs*, as discussed before.
  
+ `-u` or `--user` requires username from the tool's *replica.my.cnf*.

+ `-p` or `--password` requires password from the tool's *replica.my.cnf*.

Missing any of these parameters will result in error.

In other Python scripts the same arguments are utilized to use ssh. But some of the scripts don't need connection
to the replicas, so they don't have `-r` as argument. Check `--help` to see if it's required.

### How to schedule the scripts

Scheduling script work is useful to automatically update contents of user's database. This can be done by using cron.

Use `crontab -e` and add to the end something like 
`0 0 * * * jsub abstract-wikipedia-data-science/shell_scripts/fetch_content.sh 0 10`.
This example will run every day at the midnight - more detailed explanation is available after running `crontab -e`.

