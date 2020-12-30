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

The order is:
1. wikis_parser.py
2. db_script.py
3. fetch_content.py 

### How to set up scripts as cron job


### How to use code remotely
