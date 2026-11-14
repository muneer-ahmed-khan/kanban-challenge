# Sharing drafts

## Bluesky

Rebuilt my collaborative Kanban board for Coding Challenge #146. It has drag-and-drop cards, persistent ordering, due dates, board-specific labels, combined search filters, and owner/member permissions enforced by the server. The new React interface has a cleaner layout and no sign-in flash on reload. React + Vite + Python + SQLite.

Code: https://github.com/muneer-ahmed-khan/kanban-challenge

#CodingChallenges #React #Python

## Substack Note

I built a Kanban board for John Crickett’s Coding Challenge #146.

The visible part is familiar: boards, columns, cards, drag and drop, due dates, labels and search. The more interesting part was deciding where the rules live. A board member can create, edit and move cards, while only the owner can change columns, labels or membership. The server checks those permissions on every request, including requests made directly to the API.

I used React, Vite and Lucide icons for the interface, Python’s standard library for the API, and SQLite for persistence. The README includes local setup, development and API details. I tested the complete flow in a visible Chrome window with a disposable database, including three accounts and direct API permission checks. The app is designed for local exploration; production hosting would need HTTPS, rate limiting and an account recovery flow.

Code: https://github.com/muneer-ahmed-khan/kanban-challenge
Challenge: https://codingchallenges.substack.com/p/coding-challenge-146-kanban

#CodingChallenges #React #Python #BuildInPublic
