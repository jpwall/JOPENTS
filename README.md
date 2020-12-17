# JOPENTS - Jesse's Online PEN Testing Suite
## Local Installation
The local installation procedure is subject to differ by operating system and environment setup.

I do not recommend running JOPENTS locally to test out the software, instead go to [JOPENTS](https://jessewalling.com) directly.

The steps are as follows:
* Clone repo with `git clone https://github.com/jpwall/JOPENTS`
* Install `docker` and `docker-compose`
* `cd JOPENTS`
* Add missing directories: ```mkdir -p db/data/pg_notify db/data/pg_tblspc db/data/pg_replslot db/data/pg_twophase db/data/pg_stat db/data/pg_snapshots db/data/pg_commit_ts db/data/pg_logical/snapshots db/data/pg_logical/mappings```
* Change permissions of `db/data` with `sudo chown -R systemd-coredump:systemd-coredump db/data`
* Copy / move `secret.py` to `flask/scripts/`
* `[sudo] docker-compose build` (this will take a hefty amount of disk space and internet bandwidth, unfortunately)
* `[sudo] docker-compose up`
* At this point, it is very likely that you will encounter issues with connecting to the database. To fix this issue, please edit the `conn` variable in `flask/scripts/vendors.py` and `flask/app.py` to point to the correct subnet that Docker has created for the containers. I.e. `172.19.0.2` to `172.18.0.2`.
* If the Flask container complains about `pg_hba.conf`, edit the file under `db/data` to change IP address like you did before
* Open a web browser at `localhost:3100` to use JOPENTS!