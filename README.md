# IDS Project - Notes App

## Setup

This project is meant to be ran as a docker compose stack. From the root of the project run the following code to turn on the app.

```sh
docker compose up -d --build
```

The project requires the ports `16000` and `18000` to be free. This is because the main Notes app will use port 16000 and the dashboard app will use the port 18000.

## Access

After all containers started, visit [Notes App](http://localhost:16000) on port 16000 or [Logs Dashboard](http://localhost:18000) on port 18000

## Project Notes

1. The attacker will prove suspicious urls every second and make a note with an SQL injection every 6 seconds. The SQL is stored by the API as plaintext so it doesn't actually execute but it's used as an example of attempted attack.
2. The Notes app allows for account registration and login.
3. JWT is used so I don't need to store session data in the db, and the database will contain just basic user information and notes.
4. api/schema.sql stores the schema of the database.

## AI Declaration

Generative AI was NOT used to generate code included in the submission.

Google search AI was used to answer queries such as "How does docker manage internal networks?", or "Can suricata detect SQL injections?". This was used purely to get summarative clarification on concepts to get a better idea on how to approach the third-party library documentation.
