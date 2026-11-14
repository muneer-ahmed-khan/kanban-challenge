# Kanban — Coding Challenge #146

A small collaborative Kanban board built with Python, SQLite and plain browser JavaScript. Boards, columns, cards, due dates, labels, search and team sharing persist in SQLite. Board owners manage structure and members; members can manage cards. Access checks run on every API request.

## Run locally

Requires Python 3.10 or newer. No packages or build tools are needed.

```sh
cd 146-kanban
python3 kanban.py
```

Open [http://localhost:8000](http://localhost:8000). Sign up, create a board and start adding cards. The database is created as `kanban.sqlite3` in this folder. Use `python3 kanban.py --port 8001 --db /path/to/board.sqlite3` to change the port or database location. Stop with Ctrl+C.

## Use the board

- New boards start with To Do, In Progress and Done. Owners can add, rename, reorder and delete columns, and manage board labels and members.
- Add cards with a title, description, due date and labels. Click a card to edit it. Drag a card onto another card or empty part of a column to move it. Reload to verify saved order.
- Search titles and descriptions without case sensitivity. Label and overdue filters combine with search.
- Open a card to edit or delete it. A column with cards cannot be deleted until they are moved or deleted.
- The board settings button accepts `rename`, `delete`, `label`, `remove label`, `invite`, and `remove member`. It shows the IDs needed for removal.

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

Run `python3 -m unittest discover -s tests -v`. The test suite uses an in-memory database and checks the owner/member boundary, card moves and persistence behavior.
