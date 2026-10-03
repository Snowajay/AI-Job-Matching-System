# Live Demo

A browser front end for the AI Job Matching System. It drives the real backend: it saves a candidate profile, reads jobs from the database, and runs the match, all through the live API. Every score shown is computed by the server, not by the page.

Because it uses the real system, the backend and PostgreSQL must be running.

## Easiest way: the launcher (Windows)

Put `start_demo.ps1` in this folder (it already is) and run it:

- Right-click `start_demo.ps1` and choose **Run with PowerShell**, or run
  `powershell -ExecutionPolicy Bypass -File .\start_demo.ps1`

It asks for your PostgreSQL password, starts the backend and the page server in their own windows, seeds a few sample jobs, and opens the browser. Then just click **Find my matches**. Close the two windows to stop.

Edit the `$RepoPath` line at the top of the script if your backend code is not at `C:\Users\tjaym\Documents\AI-Job-Matching-System`.

## Manual way

1. Start the backend from the repo: `uvicorn app.main:app --reload`
2. Serve this folder: `python -m http.server 5174`
3. Open `http://localhost:5174/job_matcher_live.html` (use `localhost`).
4. Click **Seed sample jobs** once, then **Find my matches**.

## What it is and is not

This is the real system with a friendly face, used for demonstrating it live. It is **not** a standalone tool: it needs the backend and database running. There is no honest way to make a single file that both runs with zero setup and uses the real system, because the real system is the backend and the database.
