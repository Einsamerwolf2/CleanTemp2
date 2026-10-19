"""Browser regression checks. Never requests scanning or cleaning."""
from pathlib import Path
import os
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[2]
URL = os.environ.get('CLEANTEMP_TEST_URL', 'http://127.0.0.1:5000')
OUT = ROOT / 'tmp/ui'
OUT.mkdir(parents=True, exist_ok=True)
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel='msedge', headless=True)
    context = browser.new_context(viewport={'width':1280,'height':900})
    context.route('**/api/updates', lambda route: route.fulfill(json={'state':'offline'}))
    page = context.new_page()
    errors = []
    dangerous_requests = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('request', lambda request: dangerous_requests.append(request.url) if '/api/scan' in request.url or '/api/clean' in request.url else None)
    page.goto(URL, wait_until='networkidle')
    assert page.locator('.app-icon').evaluate('(img) => img.complete && img.naturalWidth > 0')
    tour = page.locator('#quick-tour')
    expect(tour).to_be_visible()
    expect(page.locator('#tour-prev')).to_be_disabled()
    expect(page.locator('#tour-progress')).to_have_text('Passo 1 de 7')
    page.screenshot(path=str(OUT / 'tour-desktop.png'))
    page.locator('#tour-next').click()
    expect(page.locator('#tour-progress')).to_have_text('Passo 2 de 7')
    page.locator('#tour-prev').click()
    expect(page.locator('#tour-progress')).to_have_text('Passo 1 de 7')
    page.locator('#tour-skip').click()
    expect(tour).not_to_be_visible()
    page.reload(wait_until='networkidle')
    expect(tour).not_to_be_visible()
    page.locator('#start-tour').click()
    expect(tour).to_be_visible()
    page.keyboard.press('Escape')
    expect(tour).not_to_be_visible()
    page.locator('#start-tour').click()
    for _ in range(6):
        page.locator('#tour-next').click()
    expect(page.locator('#tour-next')).to_have_text('Concluir')
    page.locator('#tour-next').click()
    expect(tour).not_to_be_visible()
    expect(page.locator('#start-tour')).to_be_focused()
    page.locator('#support-discord').click()
    expect(page.locator('#support-status')).to_contain_text('Em desenvolvimento')
    guide = context.request.get(URL + '/help/primeiros-passos.pdf')
    assert guide.status == 200 and guide.body().startswith(b'%PDF')
    terms = context.request.get(URL + '/help/terms')
    assert terms.status == 200 and 'Aceitação' in terms.text()
    page.screenshot(path=str(OUT / 'panel-desktop.png'), full_page=True)
    page.set_viewport_size({'width':375,'height':812})
    page.locator('#start-tour').click()
    page.locator('#tour-next').click()
    page.screenshot(path=str(OUT / 'tour-mobile.png'))
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    for _ in range(5):
        page.locator('#tour-next').click()
    expect(page.locator('#tour-next')).to_have_text('Concluir')
    page.locator('#tour-next').click()
    page.screenshot(path=str(OUT / 'panel-mobile.png'), full_page=True)
    assert not errors, errors
    assert not dangerous_requests, dangerous_requests
    browser.close()
print('Tour: próximo, anterior, saltar, Escape, concluir e reabrir OK')
print('Persistência, guia offline, termos, desktop e tela pequena OK')
print('Nenhuma análise ou limpeza solicitada pelo tour')


