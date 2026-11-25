Code related to the web app goes in this folder.

to run app:
1. docker compose down
2. docker compose up --build

All IP addresses have been validated (0.0.0.0/0), so anyone should be able to set and retrieve data from the db.

If it's giving an error, there's a chance that your port is taken up by another program.
Check docker to confirm/make space.