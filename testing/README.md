# Integration Testing Tools

Manual and end-to-end testing tools for the AI Job Matching System, maintained by the Integration Lead. These complement the automated `pytest` suite (`test_matches.py`) that runs in CI.

Start the backend first:

```
uvicorn app.main:app --reload
```

## smoke_test.py — automated end-to-end check

Runs the whole user flow against a running API (health, seed jobs, save a profile, run a match, and the 422/404 error paths) and prints PASS/FAIL for each check. Standard library only, nothing to install.

```
python testing/smoke_test.py
# or point it elsewhere:
python testing/smoke_test.py http://localhost:8000
```

Exit code is 0 if every check passes, 1 otherwise, so it can be wired into CI later.

## test_console.html — interactive browser console

A single-page console for driving the API by hand: add jobs, save a profile, run a match, and see the raw JSON. Serve it from an allowed origin so the browser permits the calls:

```
python -m http.server 5174
```

Then open `http://localhost:5174/test_console.html`. Set the API base URL at the top (use `http://127.0.0.1:8000` if `localhost` gives a connection error on Windows), then use the buttons.

## Notes

- The CORS configuration in `app/main.py` trusts `localhost` and `127.0.0.1` on any port, so both the React dev server and these tools work without edits.
- Known matching limitation: skills are matched by exact word (case-insensitive), so "JS" does not match "JavaScript". A skill-synonym layer is planned.
