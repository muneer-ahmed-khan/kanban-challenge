# Kanban — Coding Challenge #146

A collaborative Kanban board with private accounts, owner-managed boards, and card editing for team members. The interface uses React, Vite and Lucide icons. Python serves the API and stores data in SQLite.

## Stack and challenge fit

| Part | Technology |
| --- | --- |
| Server and API | Python 3 standard library (`http.server`) |
| Database | SQLite (`sqlite3`) |
| Frontend | React 19, Vite 8, CSS, Lucide React |
| Browser checks | Playwright in visible Google Chrome |

Challenge #146 permits any web or mobile stack. OutSystems is an optional route, not a requirement. This implementation is a web app with persistent local storage and server-enforced permissions.

## Run locally

Requires Python 3.10+ and Node.js 20.19+ or 22.12+. From this directory:

```sh
npm --prefix web ci
npm --prefix web run build
python3 kanban.py
```

Open [http://localhost:8000](http://localhost:8000). Sign up, create a board and start adding cards. The database is created as `kanban.sqlite3` in this folder. Use `python3 kanban.py --port 8001 --db /path/to/board.sqlite3` to change the port or database location. Stop with Ctrl+C. Existing SQLite data from the earlier interface remains compatible.

### Frontend development

Run the API and Vite in separate terminals:

```sh
KANBAN_DEV_ORIGIN=http://127.0.0.1:5173 python3 kanban.py --port 8000
```

```sh
cd web
npm ci
npm run dev
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173). Vite proxies `/api` to port 8000. If the API uses another port, set `KANBAN_API_PORT` for the Vite command. Rebuild after frontend changes when using the single-server mode.

## Use the board

- New boards start with To Do, In Progress and Done. Owners can add, rename, reorder and delete columns, and manage board labels and members.
- Use **Add card** in a column to capture a title inline, then keep adding without leaving the board. Choose **More details** to carry the title into the full editor for a description, due date, labels and placement. Click a card to edit it. Drag a card onto another card or empty part of a column to move it, or choose its column and position in the editor. Reload to verify saved order.
- Search titles and descriptions without case sensitivity. Label and overdue filters combine with search.
- A board-level attention cue opens overdue cards in one click; the main New card action starts a card in the first column.
- Open a card to edit or delete it. A column with cards cannot be deleted until they are moved or deleted.
- Closing a card with unsaved edits asks whether to keep editing or discard the changes.
- Use **Board settings** to rename or delete a board, create or remove labels, and add or remove members.
- The session is verified before showing the workspace on reload, so a signed-in user does not see a sign-in flash.

## API

Authentication uses a seven-day HTTP-only session cookie. `POST /api/signup` and `/api/login` take `email` and `password`; `POST /api/logout` ends the session. All other endpoints require sign-in.

| Endpoint | Methods | Purpose |
| --- | --- | --- |
| `/api/boards` | GET, POST | List accessible boards; create board |
| `/api/boards/{id}` | GET, PATCH, DELETE | Read, rename or delete board |
| `/api/boards/{id}/columns` | POST | Add column |
| `/api/boards/{id}/columns/order` | PATCH | Reorder with `{"ids":[...]}` |
| `/api/boards/{id}/columns/{column_id}` | PATCH, DELETE | Rename or delete column |
| `/api/boards/{id}/labels` | POST | Add label with name and color |
| `/api/boards/{id}/labels/{label_id}` | DELETE | Delete label |
| `/api/boards/{id}/members` | POST | Add existing user by email |
| `/api/boards/{id}/members/{user_id}` | DELETE | Remove member |
| `/api/boards/{id}/cards` | POST | Add card with column ID and title |
| `/api/boards/{id}/cards/{card_id}` | PATCH, DELETE | Edit or delete card |
| `/api/boards/{id}/cards/move` | PATCH | Move with card ID, column ID and zero-based index |

Owner-only endpoints check ownership in the server. Card endpoints check board membership, and IDs from another board are rejected. Passwords use salted PBKDF2 hashes; sessions are stored server-side. The server binds to loopback for local use and does not include production HTTPS, rate limits, or account recovery.

## Check

Run `python3 -m unittest discover -s tests -v`. The test suite uses temporary SQLite databases and checks the owner/member boundary, card moves, board deletion and persistence behavior.

For the visible Chrome walkthrough and screenshots, follow [TESTING.md](TESTING.md).

## Contributing

Issues and pull requests are welcome. Fork the repository, run the unit and visible browser checks, and describe the behavior you changed. Keep test accounts and personal data out of commits. The frontend source is in `web/src`; the API is in `kanban.py`.

Licensed under [MIT](LICENSE).
