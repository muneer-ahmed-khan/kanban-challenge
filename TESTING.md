# Test record

## Automated checks

From this directory:

```sh
python3 -m unittest discover -s tests -v
node --check app.js
```

The unit tests use temporary SQLite databases. They cover default columns and saved order, card title validation and movement, deletion of a board with cards, board-specific labels, and the owner/member/non-member boundary.

For the browser journey, start a disposable local server in one terminal:

```sh
python3 kanban.py --port 8765 --db /tmp/kanban-browser-check.sqlite3
```

In another terminal, with Playwright installed, run:

```sh
python3 tests/browser_smoke.py
```

The browser script creates fresh test accounts, exercises the app, and saves the screenshots below. It checks:

| Area | Browser check |
| --- | --- |
| Access | Signed-out workspace hidden; sign-up, sign-out, sign-in |
| Boards and columns | Create board; add, reorder, rename and delete columns; delete board with cards |
| Cards | Required title; create, edit, delete, move across columns, reorder within a column |
| Due dates and labels | Overdue flag appears and clears; board label creation and card attachment |
| Finding cards | Case-insensitive description search; label and overdue filters together; no-match state |
| Teams | Member sees and changes cards; owner sees member changes; member board/column/label/member API changes receive 403; non-member board request receives 404 |
| Persistence and layout | Reload retains board and card positions; first column is visible on load; desktop screenshot; 390px mobile screenshot; no page overflow at 320px; no browser page errors |

The screenshot account names are visual placeholders; test accounts have random addresses in the disposable database.

## Screenshots

- [Desktop board](screenshots/desktop.png) — 1920px viewport, first column visible.
- [Mobile board](screenshots/mobile.png) — 390px viewport, edited card's destination column visible.

## Scope

The browser check uses headless Chrome on macOS when available, or an installed Playwright Chromium elsewhere. It verifies the local app and server authorization; it does not establish production deployment readiness or accessibility conformance from assistive technology testing.
