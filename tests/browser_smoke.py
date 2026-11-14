"""Run with Playwright installed and a local server on port 8765."""
from playwright.sync_api import sync_playwright
from uuid import uuid4
from pathlib import Path
import os
from datetime import date, timedelta

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

    page.locator('#add-column').click()
    page.locator('#settings [name=name]').fill('Review')
    page.locator('#settings button[type=submit]').click()
    page.locator('.column h2').filter(has_text='Review').wait_for()
    review = page.locator('.column').filter(has=page.locator('h2').filter(has_text='Review'))
    review.locator('[data-col-act=left]').click()
    page.locator('.column').nth(2).locator('h2').filter(has_text='Review').wait_for()
    page.locator('.column').first.locator('[data-col-act=edit]').click()
    page.locator('#settings [name=name]').fill('Backlog')
    page.locator('#settings button[type=submit]').click()
    page.locator('.column').first.locator('h2').filter(has_text='Backlog').wait_for()
    print('column add, reorder, rename OK', flush=True)

    page.locator('[data-add]').first.click()
    page.locator('#editor [name=title]').fill(' ')
    page.locator('#editor button[type=submit]').click()
    assert page.locator('#editor').is_visible()
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
    page.locator('#add-label [name=name]').fill('Bug')
    page.locator('#add-label [name=color]').select_option('red')
    page.locator('#add-label button').click()
    page.locator('[data-remove-label]').nth(1).wait_for(timeout=10000)
    page.locator('#close-settings').click()
    print('label creation OK', flush=True)

    page.locator('[data-card]').filter(has_text='Write copy').click()
    page.locator('#card-labels input').first.check()
    page.locator('#editor [name=due_date]').fill((date.today()-timedelta(days=1)).isoformat())
    page.locator('#move-card select').select_option(label='In Progress')
    page.locator('#editor button[type=submit]').click()
    page.locator('.column').nth(1).get_by_text('Write copy').wait_for(timeout=10000)
    assert page.locator('.card small.overdue').count()==1
    page.locator('#search').fill('HOMEPAGE')
    assert page.locator('[data-card]').count() == 1
    page.locator('#search').fill('')
    page.locator('#label-filter').select_option(label='Content')
    page.locator('#overdue-filter').check()
    assert page.locator('[data-card]').count()==1
    page.locator('#label-filter').select_option(label='Bug')
    assert page.locator('[data-card]').count()==0
    assert page.locator('#filter-empty').is_visible()
    page.locator('#label-filter').select_option('')
    page.locator('#overdue-filter').uncheck()
    page.locator('[data-card]').filter(has_text='Write copy').click()
    page.locator('#editor [name=due_date]').fill((date.today()+timedelta(days=7)).isoformat())
    page.locator('#editor button[type=submit]').click()
    page.locator('.card small.overdue').wait_for(state='detached')
    page.locator('[data-card]').filter(has_text='Write copy').click()
    page.locator('#editor [name=due_date]').fill((date.today()-timedelta(days=1)).isoformat())
    page.locator('#editor button[type=submit]').click()
    page.locator('.card small.overdue').wait_for()
    print('due-date and combined-filter checks OK', flush=True)
    page.reload(wait_until='networkidle')
    page.locator('.column').nth(1).get_by_text('Write copy').wait_for(timeout=10000)
    assert page.locator('#columns').evaluate('(node)=>node.scrollLeft')==0
    assert page.locator('.column').first.bounding_box()['x'] >= page.locator('#columns').bounding_box()['x']-1
    page.set_viewport_size({'width':1920,'height':1080})
    Path('screenshots').mkdir(exist_ok=True)
    page.locator('#account span').evaluate('(node)=>node.textContent="demo@example.com"')
    page.screenshot(path='screenshots/desktop.png', full_page=True)
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
    for path, payload in [
        ('columns', {'name':'Blocked'}),
        ('labels', {'name':'Blocked','color':'red'}),
        ('members', {'email':'nobody@example.com'}),
    ]:
        assert bob_page.request.post(BASE + f'api/boards/{board_id}/{path}', data=payload).status == 403
    bob_page.locator('.column').filter(has=bob_page.locator('h2').filter(has_text='Done')).locator('[data-add]').click()
    bob_page.locator('#editor [name=title]').fill('Bob created card')
    bob_page.locator('#editor button[type=submit]').click()
    bob_page.locator('[data-card]').filter(has_text='Bob created card').wait_for()
    bob_page.locator('[data-card]').filter(has_text='Bob created card').click()
    bob_page.locator('#move-card select').select_option(label='Backlog')
    bob_page.locator('#editor button[type=submit]').click()
    bob_page.locator('.column').first.get_by_text('Bob created card').wait_for()
    bob_page.wait_for_function("document.querySelector('#columns').scrollLeft < 4")
    bob_page.set_viewport_size({'width':320,'height':720})
    assert bob_page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    bob_page.set_viewport_size({'width':390,'height':844})
    bob_page.locator('#account span').evaluate('(node)=>node.textContent="member@example.com"')
    bob_page.screenshot(path='screenshots/mobile.png', full_page=True)
    print('member create/edit/move, owner-only API refusal, mobile view OK', flush=True)

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

    bob_page.locator('#signout').click()
    bob_page.locator('#auth').wait_for(state='visible')
    assert bob_page.request.get(BASE+'api/boards').status == 401
    bob_page.locator('#auth-form [name=email]').fill(bob_email)
    bob_page.locator('#auth-form [name=password]').fill('password123')
    bob_page.locator('#auth-form button').click()
    bob_page.locator('#workspace').wait_for(state='visible')
    bob_page.locator('.board-link').first.wait_for()
    page.reload(wait_until='networkidle')
    page.locator('[data-card]').filter(has_text='Bob created card').wait_for()
    page.locator('[data-card]').filter(has_text='Bob created card').click()
    page.on('dialog', lambda dialog: dialog.accept())
    page.locator('#delete-card').click()
    page.locator('[data-card]').filter(has_text='Design hero').wait_for()
    assert page.locator('[data-card]').filter(has_text='Bob created card').count() == 0
    review = page.locator('.column').filter(has=page.locator('h2').filter(has_text='Review'))
    review.locator('[data-col-act=edit]').click()
    page.locator('#remove-name').click()
    page.locator('.column h2').filter(has_text='Review').wait_for(state='detached')
    assert page.request.delete(BASE + f'api/boards/{board_id}/columns/' + str(page.locator('.column').first.get_attribute('data-column'))).status == 409
    page.locator('#manage').click()
    page.locator('#delete-board').click()
    page.locator('#empty').wait_for(state='visible')
    assert page.request.get(BASE + f'api/boards/{board_id}').status == 404
    print('sign-out/sign-in, card/column/board deletion and protected-column rule OK', flush=True)
    browser.close()
