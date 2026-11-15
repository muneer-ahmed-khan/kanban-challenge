# Testing the Kanban board

## Automated checks

From this directory:

```sh
python3 -m unittest discover -s tests -v
npm --prefix web ci
npm --prefix web run build
```

The unit tests use temporary SQLite databases. They cover default columns and saved order, card title validation and movement, deletion of a board with cards, board-specific labels, and the owner/member/non-member boundary.

For the browser journey, install Playwright for Python in your own environment (`python3 -m pip install playwright`) and Google Chrome. The script uses a **visible Chrome window** and exits if Chrome is unavailable. Start a disposable local server in one terminal:

```sh
KANBAN_DEV_ORIGIN=http://127.0.0.1:5173 python3 kanban.py --port 8765 --db /tmp/kanban-browser-check.sqlite3
```

In another terminal, start Vite:

```sh
cd web
KANBAN_API_PORT=8765 npm run dev
```

In a third terminal, from the project root, run:

```sh
python3 tests/browser_visible.py
```

The browser script creates random `@example.com` test accounts in the disposable database, exercises the app in headed Chrome, and saves screenshots. Set `KANBAN_BROWSER` to your Chrome executable path if the macOS default does not apply. It checks:

| Area | Browser check |
| --- | --- |
| Access | Signed-out workspace hidden; sign-up, sign-out, sign-in |
| Boards and columns | Create board; add, reorder, rename and delete columns; delete board with cards |
| Cards | Required title; create, edit, delete; native drag and drop within/across columns; editor-based move |
| Due dates and labels | Overdue flag appears and clears; board label creation and card attachment |
| Finding cards | Case-insensitive description search; label and overdue filters together; no-match state |
| Teams | Member sees and changes cards; owner sees member changes; member board/column/label/member API changes receive 403; non-member board request receives 404 |
| Persistence and layout | Reload retains board and card positions; four complete columns at 1440px; sign-in, board, editor, settings and mobile screenshots; no page overflow at 320px; no browser page errors |

The screenshot account names are visual placeholders; test accounts have random addresses in the disposable database.

## Screenshots

- [Desktop board](screenshots/desktop.png) — 1440px viewport, first column visible.
- [Mobile board](screenshots/mobile.png) — 390px viewport.
- [Board settings](screenshots/settings.png) — member management.
- [Card editor](screenshots/editor.png) — card details and labels.
- [Sign-in](screenshots/auth.png) and [mobile sign-in](screenshots/auth-mobile.png) — account entry.

## Scope

The browser check verifies the local app and server authorization. Production deployment and assistive technology testing require separate work.
