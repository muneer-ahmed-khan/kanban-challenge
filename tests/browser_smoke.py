"""Run with Playwright installed and a local server on port 8765."""
from playwright.sync_api import sync_playwright
from uuid import uuid4
from pathlib import Path
import os

BASE = 'http://127.0.0.1:8765/'

with sync_playwright() as p:
    chrome = os.environ.get('KANBAN_BROWSER') or '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    browser = p.chromium.launch(headless=True, **({'executable_path': chrome} if Path(chrome).exists() else {}))
    alice = browser.new_context(viewport={'width': 1440, 'height': 900})
    page = alice.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(BASE, wait_until='networkidle')
    assert page.locator('#auth').is_visible()
    assert not page.locator('#workspace').is_visible()
    print('signed-out layout OK', flush=True)

    page.locator('#auth-toggle').click()
    page.locator('#auth-form [name=email]').fill(f'alice-{uuid4().hex[:8]}@example.com')
    page.locator('#auth-form [name=password]').fill('password123')
    page.locator('#auth-form button').click()
    page.locator('#workspace').wait_for(state='visible', timeout=10000)
    print('signup OK', flush=True)

    page.locator('#new-board').click()
    page.locator('#settings [name=name]').fill('Website Relaunch')
    page.locator('#settings button[type=submit]').click()
    page.locator('#board-title').get_by_text('Website Relaunch').wait_for(timeout=10000)
    print('board creation OK', flush=True)

    page.locator('[data-add]').first.click()
    page.locator('#editor [name=title]').fill('Write copy')
    page.locator('#editor [name=description]').fill('Homepage words')
    page.locator('#editor button[type=submit]').click()
    page.wait_for_timeout(1500)
    page.locator('[data-card]').wait_for(timeout=10000)
    print('card creation OK', flush=True)

    page.locator('[data-add]').first.click()
    page.locator('#editor [name=title]').fill('Design hero')
    page.locator('#editor button[type=submit]').click()
    page.locator('[data-card]').filter(has_text='Design hero').click()
    page.locator('#position-card select').select_option('0')
    page.locator('#editor button[type=submit]').click()
    page.locator('.column').first.locator('[data-card]').first.get_by_text('Design hero').wait_for(timeout=10000)
    print('same-column reorder OK', flush=True)

    page.locator('#manage').click()
    page.locator('#add-label [name=name]').fill('Content')
    page.locator('#add-label button').click()
    page.locator('[data-remove-label]').wait_for(timeout=10000)
    page.locator('#close-settings').click()
    print('label creation OK', flush=True)

    page.locator('[data-card]').filter(has_text='Write copy').click()
    page.locator('#card-labels input').check()
    page.locator('#move-card select').select_option(label='In Progress')
    page.locator('#editor button[type=submit]').click()
    page.locator('.column').nth(1).get_by_text('Write copy').wait_for(timeout=10000)
    page.locator('#search').fill('HOMEPAGE')
    assert page.locator('[data-card]').count() == 1
    page.locator('#search').fill('')
    page.reload(wait_until='networkidle')
    page.locator('.column').nth(1).get_by_text('Write copy').wait_for(timeout=10000)
    page.screenshot(path='/tmp/kanban-board.png')
    print('card move, search, reload OK; page errors:', errors, flush=True)
    assert not errors

    bob_email = f'bob-{uuid4().hex[:8]}@example.com'
    bob = browser.new_context(viewport={'width': 390, 'height': 844})
    bob_page = bob.new_page()
    bob_page.goto(BASE, wait_until='networkidle')
    bob_page.locator('#auth-toggle').click()
    bob_page.locator('#auth-form [name=email]').fill(bob_email)
    bob_page.locator('#auth-form [name=password]').fill('password123')
    bob_page.locator('#auth-form button').click()
    bob_page.locator('#workspace').wait_for(state='visible')
    assert bob_page.locator('.board-link').count() == 0
    page.locator('#manage').click()
    page.locator('#invite-member [name=email]').fill(bob_email)
    page.locator('#invite-member button').click()
    page.locator('#close-settings').click()
    bob_page.reload(wait_until='networkidle')
    bob_page.locator('.board-link').first.click()
    bob_page.locator('[data-card]').filter(has_text='Write copy').click()
    bob_page.locator('#editor [name=title]').fill('Bob updated copy')
    bob_page.locator('#editor button[type=submit]').click()
    bob_page.get_by_text('Bob updated copy').wait_for()
    assert not bob_page.locator('#manage').is_visible()
    board_id = bob_page.evaluate("Number(localStorage.getItem('kanban-board'))")
    response = bob_page.request.patch(BASE + f'api/boards/{board_id}', data={'name':'Blocked'})
    assert response.status == 403
    bob_page.screenshot(path='/tmp/kanban-mobile.png', full_page=True)
    print('member edit, server permission, mobile view OK', flush=True)

    carol = browser.new_context()
    carol_page = carol.new_page()
    carol_page.goto(BASE, wait_until='networkidle')
    carol_page.locator('#auth-toggle').click()
    carol_page.locator('#auth-form [name=email]').fill(f'carol-{uuid4().hex[:8]}@example.com')
    carol_page.locator('#auth-form [name=password]').fill('password123')
    carol_page.locator('#auth-form button').click()
    carol_page.locator('#workspace').wait_for(state='visible')
    assert carol_page.locator('.board-link').count() == 0
    assert carol_page.request.get(BASE + f'api/boards/{board_id}').status == 404
    print('non-member isolation OK', flush=True)
    browser.close()
