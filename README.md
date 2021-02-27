# Abstract Wikipedia Data Science

Repository for fetching and analyzing community functions across all wiki projects.

This project is Outreachy 21 task, more info can be found in [phabricator](https://phabricator.wikimedia.org/T263678).

## Description

This project aims to find important Scibunto modules with similar functions on different Wikimedia's wikis.
Highlighting such modules would allow storing them in more centralized manner, so the users wouldn't
have to copy-paste them from one wiki to another, or "reinvent the wheel" trying to make a script with wanted
functionality.

For reaching this goal, first all the Scribunto modules should be fetched from all the wikis and stored in more
centralized fashion, along with additional data for analysis. Then through comparing different data, such as titles,
usages and source codes, we expect to distinguish modules, which can be centralized for better.

## How to use

## How to re-create

_1. Create Wikimedia developer account and create a new tool in Toolforge._

The scripts get a lot of information from Wikimedia database replicas, and these replicas are accessed from
Toolforge. Please follow [this page](https://wikitech.wikimedia.org/wiki/Portal:Toolforge/Quickstart)
to create an account, and a new tool to use this project in.

_2. Create user database_

Fetched data is stored into the database, created by user. To create the user's database, please follow
[this guide](database_setup.md). Scripts use this database, fetching the name stored in `DATABASE_NAME` constant.
To modify it, change the value in _constants.py_.

_3. Run the scripts_

To run the scripts from Toolforge tool's account, first you need to initiate Python environment and
install requirements. For this, do the following:

```shell
$ chmod +x init.sh
$ ./init.sh
```

This will set up Python environment (and get some work done for
[setting up cron jobs](#how-to-schedule-the-scripts)). After that, you can run Python code.

Some scripts require positional arguments to run correctly, especially if you want to run them from local PC
(more info [here](#how-to-use-code-remotely)). To find out more on which exactly arguments the program needs,
help is available by running `python3 <script-name> -h`.

The order to run the scripts is:

1. wikis_parser.py
2. fetch_content.py
3. db_script.sh

   - db_script.py
   - get_db_pages.py
   - remove_missed.py

4. fetch_db_info.py
5. get_pageviews.py
6. get_distribution.py
7. detect_data_modules.py
8. detect_similarity.py

As running some scripts require quite a lot of time and computations, when in Toolforge environment,
it is recommended to use [jsub](https://wikitech.wikimedia.org/wiki/Help:Toolforge/Grid#Submitting_simple_one-off_jobs_using_'jsub').
You can submit a jsub job by using corresponding script from _shell_scripts_ folder. For single python scripts, a convenience script is `py_script.sh`, e.g `py_script.sh python/script/name.py --python-args`.

We run these scripts as cronjobs. A list of all jobs set up for cron can be found in [cronjobs.txt](cronjobs.txt). It is recommended to view this file to see how exactly the scripts are run.

### Function of python files

1. wikis_parser.py

   Collects all the names of wikis' databases and their urls from meta database and saves them to Sources table.

2. fetch_content.py

   Collects source code of Scribunto modules from the list of the wikis, stored in Sources, using Wikimedia API;
   saves this info to Scripts table.

3. db_script.py

   Collects basic info (page_id) about Scribunto modules from the list of the wikis, stored in Sources,
   using database replicas; saves this info to Scripts table or updates `in_database` flag, if the same thing
   was obtained through API requests.

4. get_db_pages.py

   Collects source code of Scribunto modules, whose info was fetched from database replicas, but didn't appear
   in API request results; saves this info to Scripts table.

5. remove_missed.py

   Remove pages from Scripts table with incomplete information (i.e. page is missing from either API or database).

6. fetch_db_info.py

   Collect statistical data about the pages from various database tables. For example number of edits, number of editors, pages module is transcluded in etc.

7. get_distribution.py

   Calculates scores for given features and stores them as a csv file for future use.

8. detect_data_modules.py

   Tries to detect so-called "data functions" - functions, which are used only for storing data, without any processing - using regular expressions on their sourcecodes; the results are saved into the database `is_data` field. Current implementation _does not_ promise that all the data functions are marked as such, but it does sort out most of the cases.

9. detect_similarity.py

   Clusters similar modules together and stores cluster-ids in Scripts table in the `cluster` field. It also performs clustering only on non-data modules (`is_data` = 0) and stores cluster-ids in `cluster_wo_data` field. Clustering can be performed with word-embedding features with `-we` tag or document embedding. It uses OPTICS algorithm to perform clutering.

10. get_pageviews.py

    Fetch and sum pageviews of all pages that transclude a module, for all modules.

### How to use code remotely

You can run python scripts, mentioned previously, from your local PC - but you still have to establish
connection to the Toolforge. This requires you to use [ssh tunneling to Toolforge databases](https://wikitech.wikimedia.org/wiki/Help:Toolforge/Database#SSH_tunneling_for_local_testing_which_makes_use_of_Wiki_Replica_databases).
Most likely, you'd need to open the tunnel to two databases: any wiki on _analytics.db.svc.eqiad.wmflabs_
(for example, _enwiki.analytics.db.svc.eqiad.wmflabs_) and _tools.db.svc.eqiad.wmflabs_.
The ssh port of 1st connection is referred to as _replicas port_, as it allows connecting to the Wikimedia database replicas,
the ssh port of 2nd connection is referred to as _user db port_, as user's database is stored in Tools.

Additionally, you'll need to know the username and password of the tool, where you created the user's database.
This info is stored into _$HOME/replica.my.cnf_ to get this file's content, for example,
with `$ cat $HOME/replica.my.cnf`

To run scripts from local environment, you need to use some parameters.
For example, this is how to get _wikis_parser.py_ working from local environment:

```shell
$ python3 wikis_parser.py -r=<replicas-port> -udb=<user-db-port> -u=<username> -p=<password>
```

- `-r` or `--replicas-port` requires the port of the ssh tunnel, connected to any database on
  _analytics.db.svc.eqiad.wmflabs_, as discussed before.
- `-udb` or `--user-db-port` requires the port of the ssh tunnel, connected to user's database on
  _tools.db.svc.eqiad.wmflabs_, as discussed before.
- `-u` or `--user` requires username from the tool's _replica.my.cnf_.

- `-p` or `--password` requires password from the tool's _replica.my.cnf_.

Missing any of these parameters will result in error.

In other Python scripts the same arguments are utilized to use ssh. But some of the scripts don't need connection
to the replicas, so they don't have `-r` as argument. Check `--help` to see if it's required.

### How to schedule the scripts

Scheduling script work is useful to automatically update contents of user's database. This can be done by using cron.

Use `crontab -e` and add to the end something like
`0 0 * * * jsub abstract-wikipedia-data-science/shell_scripts/fetch_content.sh 0 10`.
This example will run every day at the midnight - more detailed explanation is available after running `crontab -e`.

A list of all jobs set up for cron can be found in [cronjobs.txt](cronjobs.txt).
