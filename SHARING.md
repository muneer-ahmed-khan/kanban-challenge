# Sharing drafts

## Bluesky

Built a collaborative Kanban board for Coding Challenge #146. It has drag-and-drop cards, saved ordering, due dates, board-specific labels, combined search filters, and owner/member permissions enforced by the server. Python + SQLite, no install step.

Code: https://github.com/muneer-ahmed-khan/kanban-challenge

#CodingChallenges #Python

## Substack Note

I built a Kanban board for John Crickett’s Coding Challenge #146.

The visible part is familiar: boards, columns, cards, drag and drop, due dates, labels and search. The more interesting part was deciding where the rules live. A board member can create, edit and move cards, while only the owner can change columns, labels or membership. The server checks those permissions on every request, including requests made directly to the API.

I used Python’s standard library, SQLite and plain JavaScript so the project is easy to run locally. The README includes setup and API details. The app is designed for local exploration; production hosting would need HTTPS, rate limiting and an account recovery flow.

Code: https://github.com/muneer-ahmed-khan/kanban-challenge
Challenge: https://codingchallenges.substack.com/p/coding-challenge-146-kanban

#CodingChallenges #Python #BuildInPublic
