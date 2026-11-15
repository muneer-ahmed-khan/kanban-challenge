"""Visible Chrome walkthrough against a disposable Vite + Python local setup."""

import os
from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4

from playwright.sync_api import sync_playwright

BASE = os.environ.get('KANBAN_TEST_URL', 'http://127.0.0.1:5173')
CHROME = os.environ.get('KANBAN_BROWSER', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
SHOTS = Path(__file__).resolve().parents[1] / 'screenshots'


def step(message):
    print(f'✓ {message}', flush=True)


def create_account(page, email):
    page.goto(BASE, wait_until='networkidle')
    page.get_by_role('button', name='Create an account').click()
    page.get_by_label('Email address').fill(email)
    page.get_by_label('Password').fill('password123')
    page.get_by_role('button', name='Create account').click()
    page.get_by_text('Your boards will appear here.').wait_for(timeout=15000)


def column(page, name):
    return page.locator('.board-column').filter(has=page.locator('h2').filter(has_text=name))


def card(page, title):
    return page.locator('.task-card').filter(has_text=title)


def open_settings(page, tab=None):
    page.get_by_role('button', name='Board settings').click()
    page.get_by_role('heading', name='Board settings').wait_for()
    if tab:
        page.get_by_role('tab', name=tab).click()


def close_dialog(page):
    page.get_by_role('button', name='Close dialog').click()


with sync_playwright() as playwright:
    if not Path(CHROME).is_file():
        raise SystemExit(f'Visible Chrome executable missing: {CHROME}. Set KANBAN_BROWSER.')
    browser = playwright.chromium.launch(headless=False, executable_path=CHROME, slow_mo=110)
    alice_context = browser.new_context(viewport={'width': 1440, 'height': 900})
    alice = alice_context.new_page()
    page_errors = []
    alice.on('pageerror', lambda error: page_errors.append(str(error)))
    suffix = uuid4().hex[:8]
    alice_email = f'alice-{suffix}@example.com'
    bob_email = f'bob-{suffix}@example.com'
    carol_email = f'carol-{suffix}@example.com'

    SHOTS.mkdir(exist_ok=True)
    alice.goto(BASE, wait_until='networkidle')
    alice.get_by_role('heading', name='Welcome back.').wait_for()
    alice.screenshot(path=str(SHOTS / 'auth.png'), full_page=True)
    create_account(alice, alice_email)
    alice.bring_to_front()
    step('Signed-out screen, account creation and empty workspace')

    alice.get_by_role('button', name='Create your first board').click()
    alice.get_by_label('Board name').fill('Website Relaunch')
    alice.get_by_role('button', name='Create board', exact=True).last.click()
    alice.get_by_role('heading', name='Website Relaunch').wait_for()
    board_id = int(alice.url.rstrip('/').split('/')[-1])
    assert [item.inner_text() for item in alice.locator('.board-column h2').all()] == ['To Do', 'In Progress', 'Done']
    assert column(alice, 'In Progress').locator('h2').evaluate('(node) => node.scrollWidth <= node.clientWidth && node.scrollHeight <= node.clientHeight')
    step('Board creation and three default columns')

    alice.get_by_role('button', name='Board settings').click()
    assert alice.locator('.app-dialog').evaluate('(node) => parseFloat(getComputedStyle(node).animationDuration) > 0.1')
    close_dialog(alice)
    alice.emulate_media(reduced_motion='reduce')
    alice.get_by_role('button', name='Board settings').click()
    assert alice.locator('.app-dialog').evaluate('(node) => parseFloat(getComputedStyle(node).animationDuration) < 0.01')
    close_dialog(alice)
    alice.emulate_media(reduced_motion='no-preference')
    step('Dialog motion respects reduced-motion preference')

    alice.get_by_role('button', name='New card').click()
    alice.get_by_role('textbox', name='Title', exact=True).fill('Quick task')
    alice.get_by_role('button', name='Create card').click()
    card(alice, 'Quick task').click()
    alice.get_by_role('button', name='Delete card').click()
    alice.get_by_role('button', name='Delete card').last.click()
    assert card(alice, 'Quick task').count() == 0
    step('Primary New card action opens the first column')

    alice.add_init_script("""window.__authFlash = false;
      document.addEventListener('DOMContentLoaded', () => {
        const inspect = () => { if (document.body?.textContent.includes('Welcome back.')) window.__authFlash = true; };
        new MutationObserver(inspect).observe(document.body, {subtree: true, childList: true});
        inspect();
      });""")
    alice.reload(wait_until='networkidle')
    alice.get_by_role('heading', name='Website Relaunch').wait_for()
    assert not alice.evaluate('window.__authFlash')
    assert alice.locator('.board-scroll').evaluate('(node) => node.scrollLeft') == 0
    step('Reload preserves the board without a sign-in flash or clipped first column')

    alice.get_by_role('button', name='Add column').click()
    alice.get_by_label('Column name').fill('Review')
    alice.get_by_role('button', name='Add column').last.click()
    column(alice, 'Review').wait_for()
    column(alice, 'Review').get_by_role('button', name='Review options').click()
    column(alice, 'Review').get_by_role('button', name='Move Review left').click()
    alice.locator('.board-column').nth(2).get_by_role('heading', name='Review').wait_for()
    column(alice, 'To Do').get_by_role('button', name='To Do options').click()
    alice.keyboard.press('Escape')
    assert alice.get_by_role('button', name='Rename column').count() == 0
    column(alice, 'To Do').get_by_role('button', name='To Do options').click()
    alice.locator('.workspace-header h1').click()
    assert alice.get_by_role('button', name='Rename column').count() == 0
    column(alice, 'To Do').get_by_role('button', name='To Do options').click()
    alice.get_by_role('button', name='Rename column').click()
    alice.get_by_label('Column name').fill('Backlog')
    alice.get_by_role('button', name='Save name').click()
    column(alice, 'Backlog').wait_for()
    step('Add, reorder and rename columns')

    column(alice, 'Backlog').get_by_role('button', name='Add card').click()
    assert column(alice, 'Backlog').get_by_role('button', name='Add card').is_disabled()
    column(alice, 'Backlog').get_by_label('Card title for Backlog').fill('Write copy')
    column(alice, 'Backlog').get_by_role('button', name='More details').click()
    assert alice.get_by_role('textbox', name='Title', exact=True).input_value() == 'Write copy'
    alice.locator('.card-form textarea').fill('Homepage headline and navigation')
    alice.get_by_role('button', name='Create card').click()
    card(alice, 'Write copy').wait_for()
    column(alice, 'Backlog').get_by_role('button', name='Add card').click()
    for title in ['Design hero image', 'Set up hosting']:
        column(alice, 'Backlog').get_by_label('Card title for Backlog').fill(title)
        column(alice, 'Backlog').get_by_role('button', name='Add card').click()
        card(alice, title).wait_for()
    column(alice, 'Backlog').get_by_role('button', name='Cancel').click()
    card(alice, 'Set up hosting').click()
    alice.get_by_label('Position').select_option('0')
    alice.get_by_role('button', name='Save changes').click()
    alice.locator('.board-column').first.locator('.task-card').first.get_by_text('Set up hosting').wait_for()
    step('Required card title, card creation and same-column reorder')

    card(alice, 'Design hero image').click()
    alice.get_by_role('textbox', name='Title', exact=True).fill('Unpublished draft')
    alice.get_by_role('button', name='Cancel').click()
    alice.get_by_text('Discard your changes?').wait_for()
    alice.get_by_role('button', name='Keep editing').click()
    assert alice.get_by_role('textbox', name='Title', exact=True).input_value() == 'Unpublished draft'
    alice.get_by_role('button', name='Cancel').click()
    alice.get_by_role('button', name='Discard changes').click()
    card(alice, 'Design hero image').wait_for()
    step('Unsaved card edits require an explicit discard choice')

    card(alice, 'Design hero image').drag_to(card(alice, 'Set up hosting'))
    column(alice, 'Backlog').locator('.task-card').first.get_by_text('Design hero image').wait_for()
    card(alice, 'Set up hosting').drag_to(card(alice, 'Design hero image'))
    column(alice, 'Backlog').locator('.task-card').first.get_by_text('Set up hosting').wait_for()
    card(alice, 'Write copy').drag_to(column(alice, 'In Progress').locator('.column-cards'))
    column(alice, 'In Progress').get_by_text('Write copy').wait_for()
    alice.locator('.toast').get_by_role('button', name='Undo').click()
    column(alice, 'Backlog').get_by_text('Write copy').wait_for()
    card(alice, 'Write copy').drag_to(column(alice, 'In Progress').locator('.column-cards'))
    column(alice, 'In Progress').get_by_text('Write copy').wait_for()
    card(alice, 'Write copy').drag_to(column(alice, 'Backlog').locator('.column-cards'))
    column(alice, 'Backlog').get_by_text('Write copy').wait_for()
    step('Desktop drag and drop within/across columns, with Undo')

    open_settings(alice, 'Labels')
    alice.get_by_role('tab', name='Labels').focus()
    alice.keyboard.press('ArrowRight')
    assert alice.get_by_role('tab', name='People').get_attribute('aria-selected') == 'true'
    alice.keyboard.press('ArrowLeft')
    assert alice.get_by_role('tab', name='Labels').get_attribute('aria-selected') == 'true'
    for label_name, color in [('Content', 'blue'), ('Bug', 'red')]:
        alice.get_by_label('Label name').fill(label_name)
        alice.get_by_label('Color').select_option(color)
        alice.get_by_role('button', name='Add label').click()
        alice.get_by_text(label_name, exact=True).last.wait_for()
    close_dialog(alice)
    card(alice, 'Write copy').click()
    alice.locator('.toast').wait_for(state='hidden')
    alice.screenshot(path=str(SHOTS / 'editor.png'), full_page=True)
    alice.get_by_label('Due date').fill((date.today() - timedelta(days=1)).isoformat())
    alice.get_by_role('checkbox', name='Content').check()
    alice.locator('.card-form .form-row select').select_option(label='In Progress')
    alice.get_by_role('button', name='Save changes').click()
    column(alice, 'In Progress').get_by_text('Write copy').wait_for()
    assert card(alice, 'Write copy').get_by_text('Overdue', exact=False).is_visible()
    step('Board labels, overdue date and cross-column move')

    alice.get_by_role('button', name='Open card').click()
    alice.get_by_role('heading', name='Edit card').wait_for()
    assert alice.get_by_role('textbox', name='Title', exact=True).input_value() == 'Write copy'
    close_dialog(alice)
    alice.get_by_role('button', name='View overdue cards').click()
    assert alice.locator('.task-card').count() == 1
    alice.get_by_role('button', name='Clear filters').first.click()
    step('Attention cue opens overdue cards in one click')

    alice.get_by_placeholder('Search cards').fill('HOSTING')
    assert alice.locator('.task-card').count() == 1
    alice.get_by_placeholder('Search cards').fill('NAVIGATION')
    assert alice.locator('.task-card').count() == 1
    alice.get_by_placeholder('Search cards').fill('')
    alice.get_by_label('Filter by label').select_option(label='Content')
    alice.get_by_label('Overdue only').check()
    assert alice.locator('.task-card').count() == 1
    alice.get_by_label('Filter by label').select_option(label='Bug')
    assert alice.locator('.task-card').count() == 0
    alice.get_by_text('No cards match these filters.').wait_for()
    alice.get_by_role('button', name='Clear filters').first.click()
    assert alice.locator('.task-card').count() == 3
    step('Case-insensitive title/description search and combined filters')

    card(alice, 'Write copy').click()
    alice.get_by_label('Due date').fill((date.today() + timedelta(days=7)).isoformat())
    alice.get_by_role('button', name='Save changes').click()
    assert card(alice, 'Write copy').get_by_text('Overdue', exact=False).count() == 0
    alice.get_by_text('Coming up', exact=True).wait_for()
    card(alice, 'Write copy').click()
    alice.get_by_label('Due date').fill((date.today() - timedelta(days=1)).isoformat())
    alice.get_by_role('button', name='Save changes').click()
    card(alice, 'Write copy').get_by_text('Overdue', exact=False).wait_for()
    alice.reload(wait_until='networkidle')
    assert [item.inner_text() for item in alice.locator('.board-column h2').all()] == ['Backlog', 'In Progress', 'Review', 'Done']
    step('Due-date change and board/card persistence after reload')

    # A second board starts with its own label collection.
    alice.get_by_role('button', name='Create board').first.click()
    alice.get_by_label('Board name').fill('Separate board')
    alice.get_by_role('button', name='Create board', exact=True).last.click()
    assert alice.get_by_label('Filter by label').locator('option').count() == 1
    step('Labels are isolated per board')
    alice.get_by_role('link', name='Website Relaunch').click()
    alice.get_by_role('heading', name='Website Relaunch').wait_for()
    open_settings(alice)
    alice.get_by_label('Board name').fill('Website Relaunch Updated')
    alice.get_by_role('button', name='Save name').click()
    alice.get_by_role('heading', name='Website Relaunch Updated').wait_for()
    alice.get_by_label('Board name').fill('Website Relaunch')
    alice.get_by_role('button', name='Save name').click()
    alice.get_by_role('heading', name='Website Relaunch').wait_for()
    close_dialog(alice)
    step('Board rename persists in the workspace')

    # Signed-in contexts share the server, but never share cookies or local state.
    bob_context = browser.new_context(viewport={'width': 1280, 'height': 800})
    bob = bob_context.new_page()
    bob.on('pageerror', lambda error: page_errors.append(str(error)))
    bob.bring_to_front()
    create_account(bob, bob_email)
    carol_context = browser.new_context(viewport={'width': 1280, 'height': 800})
    carol = carol_context.new_page()
    carol.on('pageerror', lambda error: page_errors.append(str(error)))
    carol.bring_to_front()
    create_account(carol, carol_email)
    alice.bring_to_front()
    open_settings(alice, 'People')
    alice.get_by_label('Add an existing user by email').fill(bob_email)
    alice.get_by_role('button', name='Add member').click()
    alice.locator('.member-row').filter(has_text=bob_email).wait_for()
    close_dialog(alice)
    step('Three accounts and owner invitation')

    bob.bring_to_front()
    bob.reload(wait_until='networkidle')
    bob.get_by_role('link', name='Website Relaunch').click()
    bob.get_by_role('heading', name='Website Relaunch').wait_for()
    assert bob.get_by_role('button', name='Board settings').count() == 0
    assert bob.get_by_role('button', name='Add column').count() == 0
    column(bob, 'Backlog').get_by_role('button', name='Add card').click()
    column(bob, 'Backlog').get_by_label('Card title for Backlog').fill('Bob task')
    column(bob, 'Backlog').get_by_role('button', name='Add card').click()
    column(bob, 'Backlog').get_by_role('button', name='Cancel').click()
    card(bob, 'Bob task').click()
    bob.get_by_role('textbox', name='Title', exact=True).fill('Bob edited task')
    bob.locator('.card-form .form-row select').select_option(label='Done')
    bob.get_by_role('button', name='Save changes').click()
    column(bob, 'Done').get_by_text('Bob edited task').wait_for()
    step('Member can create, edit and move cards')

    for method, path, body in [
        ('PATCH', f'/api/boards/{board_id}', {'name': 'Unauthorized rename'}),
        ('POST', f'/api/boards/{board_id}/columns', {'name': 'Unauthorized column'}),
        ('POST', f'/api/boards/{board_id}/labels', {'name': 'Unauthorized label', 'color': 'red'}),
        ('POST', f'/api/boards/{board_id}/members', {'email': carol_email}),
    ]:
        response = bob.request.fetch(BASE + path, method=method, data=body, headers={'Content-Type': 'application/json', 'Origin': BASE})
        assert response.status == 403, (path, response.status, response.text())
    step('Data layer rejects member board, column, label and membership changes')

    carol.bring_to_front()
    assert carol.get_by_role('link', name='Website Relaunch').count() == 0
    carol.goto(f'{BASE}/boards/{board_id}', wait_until='networkidle')
    carol.get_by_role('heading', name='Board unavailable').wait_for()
    assert carol.request.get(f'{BASE}/api/boards/{board_id}').status == 404
    step('Nonmember cannot list or open a guessed board address')

    alice.bring_to_front()
    alice.reload(wait_until='networkidle')
    column(alice, 'Done').get_by_text('Bob edited task').wait_for()
    SHOTS.mkdir(exist_ok=True)
    alice.screenshot(path=str(SHOTS / 'desktop.png'), full_page=True)
    open_settings(alice, 'People')
    alice.screenshot(path=str(SHOTS / 'settings.png'), full_page=True)
    close_dialog(alice)
    step('Owner sees member changes after reload; desktop and settings captured')

    # Test the authenticated mobile layout in the same visible browser.
    alice.set_viewport_size({'width': 390, 'height': 844})
    alice.evaluate('window.scrollTo(0, 0)')
    alice.wait_for_timeout(300)
    assert alice.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'Mobile page overflows horizontally'
    assert column(alice, 'Backlog').is_visible()
    alice.screenshot(path=str(SHOTS / 'mobile.png'), full_page=True)
    alice.get_by_role('button', name='Open navigation').click()
    alice.locator('.mobile-close').click()
    step('Mobile board layout and navigation')

    alice.set_viewport_size({'width': 320, 'height': 700})
    alice.wait_for_timeout(250)
    assert alice.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'Narrow mobile page overflows horizontally'
    assert alice.get_by_role('button', name='New card').is_visible()
    step('Narrow mobile viewport retains primary action without page overflow')

    alice.set_viewport_size({'width': 1440, 'height': 900})
    column(alice, 'Review').get_by_role('button', name='Review options').click()
    alice.get_by_role('button', name='Delete column').click()
    alice.get_by_role('button', name='Delete column').last.click()
    assert column(alice, 'Review').count() == 0
    column(alice, 'Backlog').get_by_role('button', name='Backlog options').click()
    alice.get_by_role('button', name='Delete column').click()
    assert alice.get_by_text('Move the 2 cards out', exact=False).is_visible()
    alice.get_by_role('button', name='Delete column').last.click()
    alice.get_by_role('alert').filter(has_text='Move the cards').wait_for()
    close_dialog(alice)
    step('Empty column deleted; populated column blocked by the server')

    card(alice, 'Bob edited task').click()
    alice.get_by_role('button', name='Delete card').click()
    alice.get_by_role('button', name='Delete card').last.click()
    assert card(alice, 'Bob edited task').count() == 0
    open_settings(alice, 'Labels')
    alice.get_by_role('button', name='Delete Bug label').click()
    alice.get_by_role('button', name='Delete label').click()
    assert alice.get_by_role('button', name='Delete Bug label').count() == 0
    step('Card and label deletion')

    open_settings(alice)
    alice.get_by_role('button', name='Delete board').click()
    alice.get_by_role('button', name='Delete board').last.click()
    alice.get_by_role('link', name='Website Relaunch').wait_for(state='detached')
    assert bob.request.get(f'{BASE}/api/boards/{board_id}').status == 404
    step('Board deletion removes access for members')

    bob.bring_to_front()
    bob.get_by_role('button', name='Sign out').click()
    bob.get_by_role('heading', name='Welcome back.').wait_for()
    bob.set_viewport_size({'width': 390, 'height': 844})
    bob.screenshot(path=str(SHOTS / 'auth-mobile.png'), full_page=True)
    assert bob.request.get(f'{BASE}/api/boards').status == 401
    bob.get_by_label('Email address').fill(bob_email)
    bob.get_by_label('Password').fill('password123')
    bob.get_by_role('button', name='Sign in', exact=True).click()
    bob.get_by_text('Your boards will appear here.').wait_for()
    step('Sign-out rejects API access; sign-in restores the account')

    assert not page_errors, page_errors
    step('No uncaught browser errors')
    browser.close()
