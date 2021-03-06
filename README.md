# Abstract Wikipedia Data Science

Repository for fetching and analyzing community functions across all wiki projects. 

Visit [this link](https://abstract-wiki-ds.toolforge.org/) to access the results!

This project is Outreachy 21 task, more info can be found in [phabricator](https://phabricator.wikimedia.org/T263678) and our wiki page [meta:Abstract_Wikipedia/Data](https://meta.wikimedia.org/wiki/Abstract_Wikipedia/Data).

## Documentation

- [Overview](#overview)
- [Description](#description)
- [How to use](#how-to-use)
- [How to re-create](#how-to-re-create)
   + [Step by step algorithm](#step-by-step-algorithm)
   + [Function of python files](#function-of-python-files)
   + [How to use code remotely](#how-to-use-code-remotely)
   + [How to schedule the scripts](#how-to-schedule-the-scripts)
-  [Further improvements](#further-improvements)

## Overview
Across various wiki projects (Wikipedia, Wikibooks, Wiktionary, etc) and across languages are numerous Lua functions, we call wikifunctions or modules, performing operations that reflect in templates or wiki pages. With the goal towards Abstract Wikipedia - a language-independent Wikipedia that generates wiki pages and articles of different languages from a pool of knowledge - it is now necessary to pool the community authored functions as well. This project gives users and contributors a place to analyze and start merging wikifunctions starting with *important* modules and then merging or refactoring *similar* modules.

## Description

This project aims to find important Scibunto modules with similar functions on different Wikimedia's wikis.
Highlighting such modules would allow storing them in more centralized manner, so the users wouldn't
have to copy-paste them from one wiki to another, or "reinvent the wheel" trying to make a script with wanted
functionality.

For reaching this goal, first all the Scribunto modules should be fetched from all the wikis and stored in more
centralized fashion, along with additional data for analysis. Then through comparing different data, such as titles,
usages and source codes, we expect to distinguish modules, which can be centralized for better.

## How to use

While working on this project, we had two goals in mind: to help detect important functions in Wikimedia projects 
and also detect similar ones. This information can be viewed in [our site](https://abstract-wiki-ds.toolforge.org/).

It is hard to determine, which parameters we consider important when working with Lua scripts. 
That's the reason why the first step in working with the site is to set up weights for different parameters,
such as number of unique editors, number of edits, number of pages a module is transcluded in, and so on.
This is done through the corresponding fields on the top of the page. The weights can be any values, just give higher values for features that you want more focus in. They are normalised anyways.

Additionally, you can filter results you want 
to get by using tabs in light blue box: filtering by Wikimedia project family (wiktionary, wikipedia, wikiversity etc.),
filtering by the language the project uses and excluding modules, which only store data, but don't process it, 
is available. By default, all Wikimedia projects and all languages are chosen and filtering for "data modules" is off.

Clicking "request" sends the request to the server, which returns top 50 functions, corresponding to set filters 
and features weights. The titles of these functions are clickable links, which lead to the corresponding pages 
for viewing information of the those modules. This page in its header contains module's title, name of the wiki, 
where it was fetched from, and page ID in this wiki; grey box shows the source code of this module, 
and on the right links to the functions, which are considered to be similar to current module, are displayed. 

This way the website allows working with both functions "importance" through setting up weights 
and shows scripts, which were detected as similar, through "similar entries" block on script's page.  

## How to re-create

### Step by step algorithm

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

_4. Set up a web service (optional)_

For accessing analytics results in a more clear way, the web application was created. 
Full application is stored in `web` folder of the project. It should be considered a different project,
as it relies only on one file from the previous step - `data_distribution.csv`, generated by `get_distribution` script.
Because of that, all the actions, described below, should be done from `web` folder, if not explicitly told otherwise.

To set it up in local environment:
 - if needed, install npm and Node.js;
 - go to `client` folder and install front-end libraries with `npm install`;
 - build the front-end part of web service with `npm run build`;
 - install all python requirements with `pip install -r requirements.txt`;
 - open 2 ssh ports: to _meta_ database and to _user's_ database (more info [here](#how-to-use-code-remotely));
 - add these ports as parameters to some function calls in the `app.py`:
   + port of connection to _meta db_ to `get_language_family_linkage()`,
   + port of connection to _user's db_ to `get_sourcecode_from_database(wiki, id)`, 
     `get_close_sourcecodes(wiki, id, ser.loc['cluster'], eps=0)`, `get_scripts_titles(data)` as 
     `user_db_port= <port number>`;
 - in `app.py` add path to `data_distribution.csv` as a parameter `csv_address` to 
   `get_score(weights=weights)` call;   
 - run `app.py`.

After these steps, the web server should be accessible by default on `http://localhost:5000/` address.

Toolforge allows setting up websites for tools, which can be used in our case. To set up the site in Toolforge:
 - follow [this guide](https://wikitech.wikimedia.org/wiki/Help:Toolforge/Web/Python#Creating_a_virtual_environment) 
   on creating python virtual environment for this tool (`requirements.txt` for it are stored in `web` folder);
 - go to `shell_scripts` folder of the main project and do `./web_toolforge_setup.sh`;
 - after copying some scripts, it will be interrupted by opening another interactive shell. In this shell, go to 
   `shell_scripts` folder again and do `./web_toolforge_setup_container.sh`. 
   Exit the interactive shell when script finishes by typing `exit`;
 - go to `$HOME/www/python/src/` folder and open `config.yml` in text editor; modify values there 
   (user and password refer to the values in tool's `replica.my.cnf`);
 - run in command line `webservice --backend=kubernetes python3.7 restart`.

After these steps, your tool's web-site should be available on _<tool's name>.toolforge.org_.

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

   Clusters similar modules together and stores cluster-ids in Scripts table in the `cluster` field. It also performs clustering only on non-data modules (`is_data` = 0) and stores cluster-ids in `cluster_wo_data` field. Clustering can be performed with word-embedding features with `-we` tag or document embedding. It uses OPTICS algorithm to perform clustering.

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

## Further improvements

- Improve clustering: Test code2vec or other similar code-based methods to create embeddings.
- Add pageviews as a feature (Find a way to use page dumps. APIs were tested but take too long).
- Provide *diffs* among similar modules (shows users parts of code to modularize or merge).
- Create a new workaround for ssh tunneling for acessible local development.
- Add proper description and a few examples of interestiong weight combinations onto the website.
- Add to the website sortable list of all functions, accessible without working with weights.
- Add pagination in list of important modules on the website.
- Add to the website a possibility to look not only at the modules in the same cluster, but also show ones in close clusters.
