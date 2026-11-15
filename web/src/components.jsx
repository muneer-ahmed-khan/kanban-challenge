import { useEffect, useMemo, useRef, useState } from 'react';
import {
  ArrowLeft, ArrowRight, CalendarDays,
  CircleAlert, Columns3, Ellipsis, FolderKanban, LogOut, Plus,
  Search, Settings2, Tag, Trash2, Users, X,
} from 'lucide-react';
import { formatDate, isOverdue } from './api.js';
import AppSelect from './AppSelect.jsx';

export const LABEL_COLORS = ['blue', 'red', 'green', 'purple', 'amber'];

export function IconButton({ icon: Icon, label, className = '', ...props }) {
  return <button type="button" className={`icon-button ${className}`} aria-label={label} title={label} {...props}><Icon size={18} strokeWidth={1.9} aria-hidden="true" /></button>;
}

export function Dialog({ title, subtitle, children, onClose, className = '' }) {
  const ref = useRef(null);
  useEffect(() => {
    const node = ref.current;
    node.showModal();
    return () => { if (node.open) node.close(); };
  }, []);
  return <dialog ref={ref} className={`app-dialog ${className}`} onCancel={(event) => { event.preventDefault(); onClose(); }} aria-labelledby="dialog-title">
    <div className="dialog-header">
      <div><h2 id="dialog-title">{title}</h2>{subtitle && <p>{subtitle}</p>}</div>
      <IconButton icon={X} label="Close dialog" onClick={onClose} />
    </div>
    {children}
  </dialog>;
}

export function BootScreen({ error, retry }) {
  return <div className="boot-screen" role="status" aria-live="polite">
    <div className="boot-mark"><Columns3 size={24} strokeWidth={2.2} aria-hidden="true" /></div>
    {error ? <><h1>Unable to open your workspace</h1><p>{error}</p><button className="button primary" onClick={retry}>Try again</button></> : <><div className="boot-line" /><span>Opening your workspace…</span></>}
  </div>;
}

export function AuthScreen({ onSubmit, busy, error }) {
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const signingUp = mode === 'signup';
  return <div className="auth-screen">
    <header className="auth-top"><span className="wordmark"><span className="wordmark-symbol"><Columns3 size={18} strokeWidth={2.4} aria-hidden="true" /></span>kanban</span><span>Make progress visible.</span></header>
    <main className="auth-main"><div className="auth-layout">
      <section className="auth-story" aria-label="How Kanban works">
        <p className="auth-story-title">See the work.<br />Move it forward.</p>
        <p>Bring the whole project into view, from the first idea to the final handoff.</p>
        <div className="preview-board" aria-hidden="true">
          <div className="preview-column"><span>To Do <b>2</b></span><i>Write the brief</i><i>Gather feedback</i></div>
          <div className="preview-column"><span>In Progress <b>1</b></span><i><em>Content</em>Design the page</i></div>
          <div className="preview-column"><span>Done <b>1</b></span><i>Set the direction</i></div>
        </div>
      </section>
      <div className="auth-panel">
      <div className="auth-intro"><h1>{signingUp ? 'Create your workspace' : 'Welcome back.'}</h1><p>{signingUp ? 'Create an account to start a board and bring your team along.' : 'Sign in to pick up where your team left off.'}</p></div>
      <form onSubmit={(event) => { event.preventDefault(); onSubmit(mode, email, password); }}>
        <label>Email address<input name="email" type="email" autoComplete="email" spellCheck="false" value={email} onChange={(event) => setEmail(event.target.value)} required placeholder="name@example.com" /></label>
        <label>Password<input name="password" type="password" autoComplete={signingUp ? 'new-password' : 'current-password'} value={password} onChange={(event) => setPassword(event.target.value)} required minLength={8} placeholder={signingUp ? 'At least 8 characters' : 'Enter your password'} /></label>
        {error && <p className="form-error" role="alert"><CircleAlert size={16} aria-hidden="true" />{error}</p>}
        <button className="button primary auth-submit" type="submit" disabled={busy}>{busy ? 'Please wait…' : signingUp ? 'Create account' : 'Sign in'}<ArrowRight size={17} aria-hidden="true" /></button>
      </form>
      <p className="auth-switch">{signingUp ? 'Already have an account?' : 'New to Kanban?'} <button type="button" onClick={() => setMode(signingUp ? 'login' : 'signup')}>{signingUp ? 'Sign in' : 'Create an account'}</button></p>
      </div>
    </div></main>
  </div>;
}

export function Sidebar({ boards, selectedId, me, onSelect, onCreate, onSignOut, mobileOpen, setMobileOpen }) {
  return <>
    {mobileOpen && <button className="sidebar-scrim" type="button" aria-label="Close navigation" onClick={() => setMobileOpen(false)} />}
    <aside className={`sidebar ${mobileOpen ? 'open' : ''}`}>
      <div className="sidebar-brand"><span className="wordmark"><span className="wordmark-symbol"><Columns3 size={18} strokeWidth={2.4} aria-hidden="true" /></span>kanban</span><IconButton className="mobile-close" icon={X} label="Close navigation" onClick={() => setMobileOpen(false)} /></div>
      <div className="sidebar-section"><div className="sidebar-section-head"><span>Boards</span></div>
        <nav aria-label="Boards" className="board-nav">{boards.map((item) => <a href={`/boards/${item.id}`} key={item.id} aria-current={selectedId === item.id ? 'page' : undefined} className={`nav-board ${selectedId === item.id ? 'active' : ''}`} onClick={(event) => { if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return; event.preventDefault(); onSelect(item.id); setMobileOpen(false); }}><FolderKanban size={17} strokeWidth={1.8} aria-hidden="true" /><span>{item.name}</span></a>)}
          {boards.length === 0 && <p className="sidebar-empty">Your boards will appear here.</p>}</nav>
        <button type="button" className="sidebar-create" onClick={onCreate}><Plus size={17} aria-hidden="true" />Create board</button>
      </div>
      <div className="sidebar-footer"><span className="avatar" aria-hidden="true">{me.email.slice(0, 1).toUpperCase()}</span><span className="account-email" title={me.email}>{me.email}</span><IconButton icon={LogOut} label="Sign out" onClick={onSignOut} /></div>
    </aside>
  </>;
}

export function BoardColumn({ column, index, cards, labels, owner, canMoveLeft, canMoveRight, onAdd, onQuickAdd, onEdit, onMove, onReorder, onRename, onDelete }) {
  const [menu, setMenu] = useState(false);
  const menuRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);
  const [adding, setAdding] = useState(false);
  const [draft, setDraft] = useState('');
  const [saving, setSaving] = useState(false);
  useEffect(() => {
    if (!menu) return;
    const closeOutside = (event) => { if (!menuRef.current?.contains(event.target)) setMenu(false); };
    const closeEscape = (event) => { if (event.key === 'Escape') setMenu(false); };
    document.addEventListener('pointerdown', closeOutside);
    document.addEventListener('keydown', closeEscape);
    return () => { document.removeEventListener('pointerdown', closeOutside); document.removeEventListener('keydown', closeEscape); };
  }, [menu]);
  const submitDraft = async (event) => {
    event.preventDefault();
    if (!draft.trim() || saving) return;
    setSaving(true);
    const saved = await onQuickAdd(column.id, draft.trim());
    setSaving(false);
    if (saved) setDraft('');
  };
  const drop = (event, index) => {
    event.preventDefault(); event.stopPropagation(); setDragOver(false);
    const id = Number(event.dataTransfer.getData('text/plain'));
    if (id) onMove(id, column.id, index);
  };
  return <section className={`board-column ${dragOver ? 'drop-target' : ''}`} aria-labelledby={`column-${column.id}`} onDragOver={(event) => { event.preventDefault(); setDragOver(true); }} onDragLeave={(event) => { if (!event.currentTarget.contains(event.relatedTarget)) setDragOver(false); }} onDrop={(event) => drop(event, column.cards.length)}>
    <div className="column-top"><div className="column-title"><span className="stage-index" aria-hidden="true">{String(index + 1).padStart(2, '0')}</span><h2 id={`column-${column.id}`}>{column.name}</h2><span className="count">{column.cards.length}</span></div>
      {owner && <div className="column-tools"><div className="menu-wrap" ref={menuRef}><IconButton icon={Ellipsis} label={`${column.name} options`} aria-expanded={menu} onClick={() => setMenu(!menu)} />{menu && <div className="mini-menu"><button type="button" disabled={!canMoveLeft} onClick={() => { setMenu(false); onReorder(column.id, -1); }}>Move {column.name} left</button><button type="button" disabled={!canMoveRight} onClick={() => { setMenu(false); onReorder(column.id, 1); }}>Move {column.name} right</button><button type="button" onClick={() => { setMenu(false); onRename(column); }}>Rename column</button><button type="button" className="danger-text" onClick={() => { setMenu(false); onDelete(column); }}>Delete column</button></div>}</div></div>}
    </div>
    <div className="column-cards">{column.cards.length === 0 && <p className="column-empty">Drop a card here, or add one below.</p>}{cards.map((card) => {
      const overdue = isOverdue(card.due_date);
      return <button type="button" key={card.id} className="task-card" draggable onClick={() => onEdit(card, column.id)} onDragStart={(event) => { event.dataTransfer.setData('text/plain', String(card.id)); event.dataTransfer.effectAllowed = 'move'; }} onDragEnd={() => setDragOver(false)} onDragOver={(event) => event.preventDefault()} onDrop={(event) => drop(event, column.cards.findIndex((item) => item.id === card.id))}>
        {card.label_ids.length > 0 && <span className="card-labels">{card.label_ids.map((id) => { const label = labels.find((item) => item.id === id); return label ? <span key={id} className={`label-chip ${label.color}`}>{label.name}</span> : null; })}</span>}
        <span className="card-title">{card.title}</span>
        {card.description && <span className="card-description">{card.description}</span>}
        {card.due_date && <span className={`card-due ${overdue ? 'overdue' : ''}`}><CalendarDays size={14} aria-hidden="true" />{overdue ? 'Overdue · ' : ''}{formatDate(card.due_date)}</span>}
      </button>;
    })}</div>
    {adding ? <form className="quick-add" onSubmit={submitDraft}>
      <label className="sr-only" htmlFor={`quick-add-${column.id}`}>Card title for {column.name}</label>
      <input id={`quick-add-${column.id}`} name="quick-card-title" autoComplete="off" autoFocus maxLength={200} placeholder="Card title" value={draft} onChange={(event) => setDraft(event.target.value)} onKeyDown={(event) => { if (event.key === 'Escape' && !draft.trim()) setAdding(false); }} />
      <div className="quick-add-actions"><button type="submit" className="button primary" disabled={!draft.trim() || saving}>{saving ? 'Adding…' : 'Add card'}</button><button type="button" className="button subtle" onClick={() => { setAdding(false); setDraft(''); }}>Cancel</button><button type="button" className="quick-add-details" onClick={() => { onAdd(column.id, draft); setAdding(false); setDraft(''); }}>More details</button></div>
    </form> : <button type="button" className="add-card" onClick={() => setAdding(true)}><Plus size={16} strokeWidth={2} aria-hidden="true" />Add card</button>}
  </section>;
}

export function FilterBar({ search, setSearch, labelId, setLabelId, overdueOnly, setOverdueOnly, labels, onClear, hasFilters }) {
  return <div className="filter-bar"><label className="search-field"><Search size={18} aria-hidden="true" /><span className="sr-only">Search card titles and descriptions</span><input name="search" type="search" autoComplete="off" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search cards" /></label>
    <AppSelect label="Filter by label" value={labelId || 'all'} onValueChange={(next) => setLabelId(next === 'all' ? '' : next)} icon={Tag} className="filter-select" options={[{ value: 'all', label: 'All labels' }, ...labels.map((label) => ({ value: label.id, label: label.name, color: label.color }))]} />
    <label className="overdue-filter"><input type="checkbox" checked={overdueOnly} onChange={(event) => setOverdueOnly(event.target.checked)} />Overdue only</label>
    {hasFilters && <button type="button" className="clear-filters" onClick={onClear}>Clear filters</button>}
  </div>;
}

export function NameDialog({ title, label, initial = '', submitLabel, onSave, onClose, busy, error }) {
  const [name, setName] = useState(initial);
  return <Dialog title={title} onClose={onClose}><form className="dialog-body" onSubmit={(event) => { event.preventDefault(); onSave(name.trim()); }}><label className="field-label">{label}<input name="name" autoComplete="off" autoFocus={window.matchMedia('(pointer: fine)').matches} value={name} onChange={(event) => setName(event.target.value)} required maxLength={100} /></label>{error && <p className="form-error" role="alert">{error}</p>}<div className="dialog-actions"><button type="button" className="button secondary" onClick={onClose}>Cancel</button><button className="button primary" type="submit" disabled={busy || !name.trim()}>{submitLabel}</button></div></form></Dialog>;
}

export function ConfirmDialog({ title, message, confirmLabel, onConfirm, onClose, busy, error }) {
  return <Dialog title={title} onClose={onClose}><div className="dialog-body"><p className="confirm-message">{message}</p>{error && <p className="form-error" role="alert">{error}</p>}<div className="dialog-actions"><button type="button" className="button secondary" onClick={onClose}>Cancel</button><button type="button" className="button danger" onClick={onConfirm} disabled={busy}>{confirmLabel}</button></div></div></Dialog>;
}

export function CardEditor({ card, initialTitle = '', initialColumnId, board, onSave, onDelete, onClose, busy, error }) {
  const initialColumn = board.columns.find((column) => column.id === (card?.column_id || initialColumnId)) || board.columns[0];
  const initialPosition = card ? initialColumn.cards.findIndex((item) => item.id === card.id) : initialColumn.cards.length;
  const [title, setTitle] = useState(card?.title || initialTitle);
  const [description, setDescription] = useState(card?.description || '');
  const [dueDate, setDueDate] = useState(card?.due_date || '');
  const [labelIds, setLabelIds] = useState(card?.label_ids || []);
  const [columnId, setColumnId] = useState(initialColumn.id);
  const [position, setPosition] = useState(initialPosition);
  const [confirmDiscard, setConfirmDiscard] = useState(false);
  const target = board.columns.find((column) => column.id === columnId);
  const maxPosition = target.cards.length + (!card || card.column_id !== columnId ? 1 : 0);
  const toggleLabel = (id) => setLabelIds((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]);
  const dirty = title !== (card?.title || '') || description !== (card?.description || '') || dueDate !== (card?.due_date || '') || columnId !== initialColumn.id || position !== initialPosition || [...labelIds].sort().join(',') !== [...(card?.label_ids || [])].sort().join(',');
  const requestClose = () => { if (dirty) setConfirmDiscard(true); else onClose(); };
  useEffect(() => {
    if (!dirty) return;
    const warn = (event) => { event.preventDefault(); event.returnValue = ''; };
    window.addEventListener('beforeunload', warn);
    return () => window.removeEventListener('beforeunload', warn);
  }, [dirty]);
  return <Dialog title={card ? 'Edit card' : 'New card'} subtitle={card ? 'Update the details and place this card where it belongs.' : `Adding to ${initialColumn.name}`} onClose={requestClose} className="card-dialog">
    <form className="dialog-body card-form" onSubmit={(event) => { event.preventDefault(); onSave({ title: title.trim(), description, due_date: dueDate || null, label_ids: labelIds, column_id: columnId, position }); }}>
      <label className="field-label">Title<input name="title" autoComplete="off" autoFocus={window.matchMedia('(pointer: fine)').matches} value={title} onChange={(event) => setTitle(event.target.value)} required maxLength={200} placeholder="What needs to get done?" /></label>
      <label className="field-label"><span className="field-heading">Description <span className="optional">Optional</span></span><textarea name="description" autoComplete="off" value={description} onChange={(event) => setDescription(event.target.value)} rows={4} placeholder="Add useful context for your team" /></label>
      <div className="form-row"><label className="field-label"><span className="field-heading">Due date <span className="optional">Optional</span></span><input name="due-date" type="date" value={dueDate} onChange={(event) => setDueDate(event.target.value)} /></label>
        <div className="field-label">Column<AppSelect label="Column" value={columnId} onValueChange={(next) => { const id = Number(next); setColumnId(id); const destination = board.columns.find((column) => column.id === id); setPosition(destination.cards.length); }} options={board.columns.map((column) => ({ value: column.id, label: column.name }))} /></div></div>
      <div className="field-label position-field">Position<AppSelect label="Position" value={Math.min(position, maxPosition - 1)} onValueChange={(next) => setPosition(Number(next))} options={Array.from({ length: maxPosition }, (_, index) => ({ value: index, label: `${index + 1} of ${maxPosition}` }))} /></div>
      <fieldset className="label-picker"><legend>Labels</legend>{board.labels.length ? <div className="label-options">{board.labels.map((label) => <label key={label.id} className="label-option"><input type="checkbox" checked={labelIds.includes(label.id)} onChange={() => toggleLabel(label.id)} /><span className={`label-chip ${label.color}`}>{label.name}</span></label>)}</div> : <p>No labels yet. A board owner can add them in Board settings.</p>}</fieldset>
      {error && <p className="form-error" role="alert"><CircleAlert size={16} aria-hidden="true" />{error}</p>}
      {confirmDiscard && <div className="discard-prompt" role="alert"><div><strong>Discard your changes?</strong><span>The card has unsaved edits.</span></div><div className="action-group"><button type="button" className="button secondary" onClick={() => setConfirmDiscard(false)}>Keep editing</button><button type="button" className="button danger-outline" onClick={onClose}>Discard changes</button></div></div>}
      <div className="dialog-actions"><div>{card && <button type="button" className="button text-danger" onClick={onDelete}><Trash2 size={16} aria-hidden="true" />Delete card</button>}</div><div className="action-group"><button type="button" className="button secondary" onClick={requestClose}>Cancel</button><button type="submit" className="button primary" disabled={busy || !title.trim()}>{busy ? 'Saving…' : card ? 'Save changes' : 'Create card'}</button></div></div>
    </form>
  </Dialog>;
}

export function BoardSettings({ board, onClose, onRename, onAddLabel, onRemoveLabel, onAddMember, onRemoveMember, onDeleteBoard, busy, error }) {
  const [tab, setTab] = useState('general');
  const tabs = [['general', Settings2, 'General'], ['labels', Tag, 'Labels'], ['people', Users, 'People']];
  const [name, setName] = useState(board.name);
  const [labelName, setLabelName] = useState('');
  const [color, setColor] = useState('blue');
  const [email, setEmail] = useState('');
  return <Dialog title="Board settings" subtitle={board.name} onClose={onClose} className="settings-dialog">
    <div className="settings-tabs" role="tablist" aria-label="Board settings sections">
      {tabs.map(([id, Icon, text], index) => <button key={id} id={`settings-tab-${id}`} type="button" role="tab" aria-selected={tab === id} aria-controls="settings-panel" tabIndex={tab === id ? 0 : -1} className={tab === id ? 'active' : ''} onClick={() => setTab(id)} onKeyDown={(event) => { const next = event.key === 'ArrowRight' ? (index + 1) % tabs.length : event.key === 'ArrowLeft' ? (index + tabs.length - 1) % tabs.length : event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : -1; if (next >= 0) { event.preventDefault(); setTab(tabs[next][0]); event.currentTarget.parentElement.children[next].focus(); } }}><Icon size={16} aria-hidden="true" />{text}</button>)}
    </div>
    <div id="settings-panel" className="settings-panel" role="tabpanel" aria-labelledby={`settings-tab-${tab}`}>
      {tab === 'general' && <><form onSubmit={(event) => { event.preventDefault(); onRename(name.trim()); }}><h3>Board name</h3><p>The name your team sees in their board list.</p><label className="field-label"><span className="sr-only">Board name</span><input value={name} onChange={(event) => setName(event.target.value)} required maxLength={100} /></label><button type="submit" className="button primary" disabled={busy || !name.trim()}>Save name</button></form><div className="settings-danger"><div><h3>Delete board</h3><p>Remove this board and all of its cards. This cannot be undone.</p></div><button className="button danger-outline" type="button" onClick={onDeleteBoard}><Trash2 size={16} aria-hidden="true" />Delete board</button></div></>}
      {tab === 'labels' && <><div className="settings-heading"><h3>Labels</h3><p>Labels are available only on this board.</p></div><div className="settings-list">{board.labels.map((label) => <div key={label.id} className="settings-item"><span className={`label-chip ${label.color}`}>{label.name}</span><IconButton icon={Trash2} label={`Delete ${label.name} label`} onClick={() => onRemoveLabel(label)} /></div>)}{!board.labels.length && <p className="list-empty">No labels yet.</p>}</div><form className="settings-add-form" onSubmit={async (event) => { event.preventDefault(); if (await onAddLabel(labelName.trim(), color)) setLabelName(''); }}><label className="field-label">Label name<input value={labelName} onChange={(event) => setLabelName(event.target.value)} maxLength={40} required placeholder="e.g. Content" /></label><div className="field-label">Color<AppSelect label="Color" value={color} onValueChange={setColor} options={LABEL_COLORS.map((item) => ({ value: item, label: item[0].toUpperCase() + item.slice(1), color: item }))} /></div><button type="submit" className="button primary" disabled={busy || !labelName.trim()}><Plus size={16} aria-hidden="true" />Add label</button></form></>}
      {tab === 'people' && <><div className="settings-heading"><h3>Board members</h3><p>Members can create, edit and move cards. Only you can manage this board.</p></div><div className="settings-list">{board.members.map((member) => <div key={member.id} className="settings-item"><span className="member-row"><span className="mini-avatar">{member.email.slice(0, 1).toUpperCase()}</span>{member.email}</span><IconButton icon={X} label={`Remove ${member.email}`} onClick={() => onRemoveMember(member)} /></div>)}{!board.members.length && <p className="list-empty">Only you have access right now.</p>}</div><form className="settings-add-form" onSubmit={async (event) => { event.preventDefault(); if (await onAddMember(email)) setEmail(''); }}><label className="field-label">Add an existing user by email<input type="email" spellCheck="false" value={email} onChange={(event) => setEmail(event.target.value)} required placeholder="name@example.com" /></label><button type="submit" className="button primary" disabled={busy || !email.trim()}><Plus size={16} aria-hidden="true" />Add member</button></form></>}
      {error && <p className="form-error" role="alert"><CircleAlert size={16} aria-hidden="true" />{error}</p>}
    </div>
  </Dialog>;
}
