"""The privacy page: it is served, every page reaches it, the consent box points to it, and the promises it makes stay
tied to the code that keeps them. If one of these fails, either the page or the code changed without the other."""
import re

from fastapi.testclient import TestClient

from api import config
from api.log_store import CONTACT_RETENTION_DAYS
from api.main import PAGES, app

client = TestClient(app)
STATIC = config.STATIC_DIRECTORY


def privacy_text() -> str:
    return re.sub(r"\s+", " ", client.get("/privacy").text)


def test_privacy_page_is_served_and_not_cached():
    response = client.get("/privacy")
    assert response.status_code == 200 and "<html" in response.text
    assert "Privacy policy" in response.text
    assert response.headers["cache-control"] == "no-cache"


def test_every_page_links_to_the_privacy_page():
    # The footer is drawn by app.js on every page that calls renderBottomNav, so the link is checked in both places.
    app_source = (STATIC / "app.js").read_text(encoding="utf-8")
    footer = app_source[app_source.index("function siteFooter"):app_source.index("// Cases this phone has sent")]
    assert 'href="/privacy"' in footer
    assert "siteFooter(items, active)" in app_source[app_source.index("function renderBottomNav"):app_source.index("function siteFooter")]
    for path in PAGES:
        page = client.get(path).text
        assert "/static/app.js" in page and "renderBottomNav(" in page, path


def test_consent_box_links_to_how_the_number_is_used():
    source = (STATIC / "result.html").read_text(encoding="utf-8")
    form = source[source.index("function referralForm"):source.index("function referralConfirmation")]
    consent = form.index('id="contact-consent"')
    link = form.index('href="/privacy#phone"')
    assert consent < link < form.index('id="phone-block"'), "the link sits right under the consent box"
    assert 'id="phone"' in client.get("/privacy").text


def test_privacy_page_states_its_limits():
    text = privacy_text()
    assert "runs when an officer opens the list, not on a timer" in text
    assert "share one access code" in text
    assert "not a confirmed diagnosis" in text
    assert "never recommends a pesticide or a dose" in text


def test_retention_period_on_the_page_matches_the_code():
    assert f"after {CONTACT_RETENTION_DAYS} days" in privacy_text()


def test_privacy_page_does_not_link_to_the_officer_view():
    assert 'href="/officer"' not in client.get("/privacy").text


def test_no_page_puts_the_check_code_in_a_web_address():
    for page in ("my_case.html", "result.html"):
        source = (STATIC / page).read_text(encoding="utf-8")
        assert not re.search(r"[?&](check_)?code=", source), page   # a query parameter, not the data-code attribute
    my_case = (STATIC / "my_case.html").read_text(encoding="utf-8")
    assert 'fetch("/case", { method: "POST"' in my_case


def test_contact_and_deletion_request_are_on_the_page():
    text = privacy_text()
    assert "mailto:justineumuhoza74@gmail.com" in text
    assert "deleted when your case is marked answered" in text
    assert "cannot delete it from the officer's own phone" in text
