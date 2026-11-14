import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ArrowLeft, ArrowRight, Columns3, Menu, Plus, Settings2, SlidersHorizontal } from 'lucide-react';
import { api, isOverdue } from './api.js';
import { AuthScreen, BoardColumn, BoardSettings, BootScreen, CardEditor, ConfirmDialog, FilterBar, IconButton, NameDialog, Sidebar } from './components.jsx';

const savedBoardKey = 'kanban:selected-board';

function requestedBoardId() {
  const match = window.location.pathname.match(/^\/boards\/(\d+)\/?$/);
  return match ? Number(match[1]) : null;
}

export default function App() {
  const [booting, setBooting] = useState(true);
  const [bootError, setBootError] = useState('');
  const [me, setMe] = useState(null);
  const [authError, setAuthError] = useState('');
  const [boards, setBoards] = useState([]);
  const [board, setBoard] = useState(null);
  const [boardError, setBoardError] = useState('');
  const [boardLoading, setBoardLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [dialog, setDialog] = useState(null);
  const [dialogError, setDialogError] = useState('');
  const [toast, setToast] = useState('');
  const [search, setSearch] = useState('');
  const [labelId, setLabelId] = useState('');
  const [overdueOnly, setOverdueOnly] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [scrollState, setScrollState] = useState({ left: false, right: false });
  const boardRef = useRef(null);

  const notify = useCallback((message) => { setToast(message); window.setTimeout(() => setToast(''), 4500); }, []);
  const clearFilters = () => { setSearch(''); setLabelId(''); setOverdueOnly(false); };
  const closeDialog = () => { setDialog(null); setDialogError(''); };
  const openDialog = (next) => { setDialogError(''); setDialog(next); };

  const applySnapshot = (snapshot) => {
    setBoard(snapshot);
    setBoards((current) => current.map((item) => item.id === snapshot.id ? { ...item, name: snapshot.name } : item));
  };

  const hydrate = useCallback(async () => {
    setBooting(true);
    setBootError('');
    try {
      const user = await api('/me');
      const list = await api('/boards');
      const routeId = requestedBoardId();
      const storedId = Number(localStorage.getItem(savedBoardKey));
      const id = routeId || (list.some((item) => item.id === storedId) ? storedId : list[0]?.id);
      let selected = null;
      let accessError = '';
      if (id) {
        try { selected = await api(`/boards/${id}`); }
        catch (error) { accessError = error.status === 404 ? 'You do not have access to this board.' : error.message; }
      }
      setMe(user); setBoards(list); setBoard(selected); setBoardError(accessError);
      if (selected) localStorage.setItem(savedBoardKey, String(selected.id));
    } catch (error) {
      if (error.status === 401) { setMe(null); setBoards([]); setBoard(null); }
      else setBootError(error.message);
    } finally { setBooting(false); }
  }, []);

  useEffect(() => { hydrate(); }, [hydrate]);

  async function run(action) {
    setBusy(true); setDialogError('');
    try { await action(); return true; }
    catch (error) { setDialogError(error.message); notify(error.message); return false; }
    finally { setBusy(false); }
  }

  async function signIn(mode, email, password) {
    setBusy(true); setAuthError('');
    try {
      const user = await api(mode === 'signup' ? '/signup' : '/login', 'POST', { email, password });
      const list = await api('/boards');
      const first = list[0] || null;
      const selected = first ? await api(`/boards/${first.id}`) : null;
      setMe(user); setBoards(list); setBoard(selected); setBoardError(''); clearFilters();
      if (selected) { localStorage.setItem(savedBoardKey, String(selected.id)); window.history.replaceState({}, '', `/boards/${selected.id}`); }
      else window.history.replaceState({}, '', '/');
    } catch (error) { setAuthError(error.message); }
    finally { setBusy(false); }
  }

  async function signOut() {
    await run(async () => {
      await api('/logout', 'POST');
      setMe(null); setBoards([]); setBoard(null); setBoardError(''); clearFilters();
      localStorage.removeItem(savedBoardKey);
      window.history.replaceState({}, '', '/');
    });
  }

  async function selectBoard(id, push = true) {
    if (board?.id === id && !boardError) return;
    setBoardLoading(true); setBoardError(''); clearFilters();
    try {
      const selected = await api(`/boards/${id}`);
      setBoard(selected); localStorage.setItem(savedBoardKey, String(id));
      if (push) window.history.pushState({}, '', `/boards/${id}`);
    } catch (error) { setBoard(null); setBoardError(error.status === 404 ? 'You do not have access to this board.' : error.message); }
    finally { setBoardLoading(false); }
  }

  useEffect(() => {
    const onPop = () => { const id = requestedBoardId(); if (id) selectBoard(id, false); else { setBoard(null); setBoardError(''); } };
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  });

  async function createBoard(name) {
    await run(async () => {
      const snapshot = await api('/boards', 'POST', { name });
      const list = await api('/boards');
      setBoards(list); setBoard(snapshot); clearFilters(); closeDialog();
      localStorage.setItem(savedBoardKey, String(snapshot.id));
      window.history.pushState({}, '', `/boards/${snapshot.id}`);
      notify('Board created.');
    });
  }

  async function mutate(path, method, body, message, close = false) {
    return run(async () => {
      const snapshot = await api(path, method, body);
      applySnapshot(snapshot);
      if (close) closeDialog();
      if (message) notify(message);
    });
  }

  async function saveCard(values) {
    const id = board.id;
    await run(async () => {
      let snapshot;
      if (dialog.card) {
        snapshot = await api(`/boards/${id}/cards/${dialog.card.id}`, 'PATCH', values);
        const source = snapshot.columns.find((column) => column.cards.some((card) => card.id === dialog.card.id));
        const currentIndex = source.cards.findIndex((card) => card.id === dialog.card.id);
        if (source.id !== values.column_id || currentIndex !== values.position) {
          snapshot = await api(`/boards/${id}/cards/move`, 'PATCH', { card_id: dialog.card.id, column_id: values.column_id, index: values.position });
        }
      } else {
        snapshot = await api(`/boards/${id}/cards`, 'POST', { column_id: values.column_id, title: values.title, description: values.description });
        const created = snapshot.columns.find((column) => column.id === values.column_id).cards.at(-1);
        if (values.due_date || values.label_ids.length) snapshot = await api(`/boards/${id}/cards/${created.id}`, 'PATCH', values);
        if (values.position < snapshot.columns.find((column) => column.id === values.column_id).cards.length - 1) {
          snapshot = await api(`/boards/${id}/cards/move`, 'PATCH', { card_id: created.id, column_id: values.column_id, index: values.position });
        }
      }
      applySnapshot(snapshot); closeDialog(); notify(dialog.card ? 'Card updated.' : 'Card created.');
    });
  }

  async function moveCard(cardId, columnId, index) {
    await mutate(`/boards/${board.id}/cards/move`, 'PATCH', { card_id: cardId, column_id: columnId, index }, 'Card moved.');
  }

  async function reorderColumn(columnId, direction) {
    const ids = board.columns.map((column) => column.id);
    const from = ids.indexOf(columnId), to = from + direction;
    if (to < 0 || to >= ids.length) return;
    [ids[from], ids[to]] = [ids[to], ids[from]];
    await mutate(`/boards/${board.id}/columns/order`, 'PATCH', { ids }, 'Columns reordered.');
  }

  async function deleteBoard() {
    await run(async () => {
      await api(`/boards/${board.id}`, 'DELETE');
      const list = await api('/boards');
      const next = list[0] ? await api(`/boards/${list[0].id}`) : null;
      setBoards(list); setBoard(next); closeDialog();
      if (next) { localStorage.setItem(savedBoardKey, String(next.id)); window.history.replaceState({}, '', `/boards/${next.id}`); }
      else { localStorage.removeItem(savedBoardKey); window.history.replaceState({}, '', '/'); }
      notify('Board deleted.');
    });
  }

  const visibleCards = useMemo(() => {
    if (!board) return new Map();
    const query = search.trim().toLocaleLowerCase();
    return new Map(board.columns.map((column) => [column.id, column.cards.filter((card) =>
      (!query || `${card.title} ${card.description}`.toLocaleLowerCase().includes(query)) &&
      (!labelId || card.label_ids.includes(Number(labelId))) &&
      (!overdueOnly || isOverdue(card.due_date))
    )]));
  }, [board, search, labelId, overdueOnly]);
  const visibleCount = [...visibleCards.values()].reduce((count, cards) => count + cards.length, 0);
  const totalCount = board?.columns.reduce((count, column) => count + column.cards.length, 0) || 0;
  const hasFilters = !!(search || labelId || overdueOnly);

  useEffect(() => {
    const rail = boardRef.current;
    if (!rail) return;
    rail.scrollLeft = 0;
    const measure = () => setScrollState({ left: rail.scrollLeft > 4, right: rail.scrollLeft + rail.clientWidth < rail.scrollWidth - 4 });
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(rail);
    return () => observer.disconnect();
  }, [board?.id, board?.columns.length]);

  if (booting || bootError) return <BootScreen error={bootError} retry={hydrate} />;
  if (!me) return <AuthScreen onSubmit={signIn} busy={busy} error={authError} />;

  return <div className="app-shell">
    <a className="skip-link" href="#main-content">Skip to main content</a>
    <Sidebar boards={boards} selectedId={board?.id} me={me} onSelect={selectBoard} onCreate={() => openDialog({ type: 'createBoard' })} onSignOut={signOut} mobileOpen={mobileOpen} setMobileOpen={setMobileOpen} />
    <main id="main-content" className="workspace" tabIndex={-1}>
      <div className="mobile-header"><IconButton icon={Menu} label="Open navigation" onClick={() => setMobileOpen(true)} /><span className="wordmark"><span className="wordmark-symbol"><Columns3 size={17} strokeWidth={2.4} aria-hidden="true" /></span>kanban</span></div>
      {boardLoading ? <div className="board-loading" role="status">Loading board…</div> : boardError ? <div className="empty-workspace"><div className="empty-icon"><SlidersHorizontal size={26} aria-hidden="true" /></div><h1>Board unavailable</h1><p>{boardError}</p><button className="button secondary" onClick={() => { setBoardError(''); window.history.replaceState({}, '', '/'); }}>Back to boards</button></div> : !board ? <div className="empty-workspace"><div className="empty-icon"><FolderKanbanIcon /></div><h1>Bring your work together.</h1><p>Create a board to organize the next thing your team is building.</p><button className="button primary" onClick={() => openDialog({ type: 'createBoard' })}><Plus size={18} aria-hidden="true" />Create your first board</button></div> : <>
        <header className="workspace-header"><div className="header-copy"><p className="breadcrumb">Workspace <span>/</span> Boards</p><h1>{board.name}</h1><p className="board-meta">{board.columns.length} {board.columns.length === 1 ? 'column' : 'columns'} <span>·</span> {totalCount} {totalCount === 1 ? 'card' : 'cards'}</p></div>{board.owner && <button className="button secondary manage-button" onClick={() => openDialog({ type: 'settings' })}><Settings2 size={17} aria-hidden="true" />Board settings</button>}</header>
        <FilterBar search={search} setSearch={setSearch} labelId={labelId} setLabelId={setLabelId} overdueOnly={overdueOnly} setOverdueOnly={setOverdueOnly} labels={board.labels} hasFilters={hasFilters} onClear={clearFilters} />
        <div className="board-tools"><p>{hasFilters ? `${visibleCount} of ${totalCount} cards shown` : 'Drag cards to move them, or open a card for more options.'}</p><div className="board-navigation"><IconButton icon={ArrowLeft} label="Scroll columns left" disabled={!scrollState.left} onClick={() => boardRef.current?.scrollBy({ left: -350, behavior: 'smooth' })} /><IconButton icon={ArrowRight} label="Scroll columns right" disabled={!scrollState.right} onClick={() => boardRef.current?.scrollBy({ left: 350, behavior: 'smooth' })} /></div></div>
        {hasFilters && visibleCount === 0 && <div className="filter-empty"><SlidersHorizontal size={19} aria-hidden="true" /><span>No cards match these filters.</span><button type="button" onClick={clearFilters}>Clear filters</button></div>}
        <div className="board-scroll" ref={boardRef} onScroll={(event) => { const rail = event.currentTarget; setScrollState({ left: rail.scrollLeft > 4, right: rail.scrollLeft + rail.clientWidth < rail.scrollWidth - 4 }); }} tabIndex={0} aria-label="Board columns">
          <div className="board-columns">{board.columns.map((column) => <BoardColumn key={column.id} column={column} cards={visibleCards.get(column.id) || []} labels={board.labels} owner={board.owner} onAdd={(columnId) => openDialog({ type: 'card', columnId })} onEdit={(card, columnId) => openDialog({ type: 'card', card, columnId })} onMove={moveCard} onReorder={reorderColumn} onRename={(target) => openDialog({ type: 'renameColumn', column: target })} onDelete={(target) => openDialog({ type: 'deleteColumn', column: target })} />)}{board.owner && <button className="add-column" onClick={() => openDialog({ type: 'createColumn' })}><Plus size={18} aria-hidden="true" />Add column</button>}</div>
        </div>
      </>}
    </main>
    {toast && <div className="toast" role="status" aria-live="polite">{toast}</div>}
    {dialog?.type === 'createBoard' && <NameDialog title="Create board" label="Board name" submitLabel="Create board" onSave={createBoard} onClose={closeDialog} busy={busy} error={dialogError} />}
    {dialog?.type === 'createColumn' && <NameDialog title="Add column" label="Column name" submitLabel="Add column" onSave={(name) => mutate(`/boards/${board.id}/columns`, 'POST', { name }, 'Column added.', true)} onClose={closeDialog} busy={busy} error={dialogError} />}
    {dialog?.type === 'renameColumn' && <NameDialog title="Rename column" label="Column name" initial={dialog.column.name} submitLabel="Save name" onSave={(name) => mutate(`/boards/${board.id}/columns/${dialog.column.id}`, 'PATCH', { name }, 'Column renamed.', true)} onClose={closeDialog} busy={busy} error={dialogError} />}
    {dialog?.type === 'card' && <CardEditor card={dialog.card} initialColumnId={dialog.columnId} board={board} onSave={saveCard} onDelete={() => openDialog({ type: 'deleteCard', card: dialog.card })} onClose={closeDialog} busy={busy} error={dialogError} />}
    {dialog?.type === 'settings' && <BoardSettings board={board} onClose={closeDialog} onRename={(name) => mutate(`/boards/${board.id}`, 'PATCH', { name }, 'Board renamed.')} onAddLabel={(name, color) => mutate(`/boards/${board.id}/labels`, 'POST', { name, color }, 'Label added.')} onRemoveLabel={(label) => openDialog({ type: 'deleteLabel', label })} onAddMember={(email) => mutate(`/boards/${board.id}/members`, 'POST', { email }, 'Member added.')} onRemoveMember={(member) => openDialog({ type: 'removeMember', member })} onDeleteBoard={() => openDialog({ type: 'deleteBoard' })} busy={busy} error={dialogError} />}
    {dialog?.type === 'deleteCard' && <ConfirmDialog title="Delete card?" message={`“${dialog.card.title}” will be removed from this board.`} confirmLabel="Delete card" onConfirm={() => mutate(`/boards/${board.id}/cards/${dialog.card.id}`, 'DELETE', undefined, 'Card deleted.', true)} onClose={closeDialog} busy={busy} error={dialogError} />}
    {dialog?.type === 'deleteColumn' && <ConfirmDialog title="Delete column?" message={dialog.column.cards.length ? `Move the ${dialog.column.cards.length} cards out of “${dialog.column.name}” first.` : `“${dialog.column.name}” will be removed from this board.`} confirmLabel="Delete column" onConfirm={() => mutate(`/boards/${board.id}/columns/${dialog.column.id}`, 'DELETE', undefined, 'Column deleted.', true)} onClose={closeDialog} busy={busy} error={dialogError} />}
    {dialog?.type === 'deleteLabel' && <ConfirmDialog title="Delete label?" message={`“${dialog.label.name}” will be removed from every card on this board.`} confirmLabel="Delete label" onConfirm={() => mutate(`/boards/${board.id}/labels/${dialog.label.id}`, 'DELETE', undefined, 'Label deleted.', true)} onClose={closeDialog} busy={busy} error={dialogError} />}
    {dialog?.type === 'removeMember' && <ConfirmDialog title="Remove member?" message={`${dialog.member.email} will no longer have access to this board.`} confirmLabel="Remove member" onConfirm={() => mutate(`/boards/${board.id}/members/${dialog.member.id}`, 'DELETE', undefined, 'Member removed.', true)} onClose={closeDialog} busy={busy} error={dialogError} />}
    {dialog?.type === 'deleteBoard' && <ConfirmDialog title="Delete board?" message={`“${board.name}” and all of its cards will be permanently removed.`} confirmLabel="Delete board" onConfirm={deleteBoard} onClose={closeDialog} busy={busy} error={dialogError} />}
  </div>;
}

function FolderKanbanIcon() { return <Columns3 size={28} strokeWidth={1.7} aria-hidden="true" />; }
