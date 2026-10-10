"""Site (#64/#66): built only from data/genshin/normalized/md, every page renders, no chatbot text, no third parties."""
import html
import re

from web import wiki


def test_every_markdown_page_is_loaded_with_its_header():
    pages = wiki.pages()
    files = sorted(wiki.MD_DIR.glob("*.md"))
    assert len(pages) == len(files) > 0
    assert all(p.url.startswith("https://") and p.type != "other" for p in pages.values())
    known = {t for t, _ in wiki.SECTIONS}
    assert {p.type for p in pages.values()} <= known  # every page type has a home-page section


def test_home_links_every_page_and_features_both_regions():
    page = wiki.render("t", wiki.home_body())
    for slug in wiki.pages():
        assert f'href="/wiki/{slug}"' in page, slug
    for region in wiki.FEATURED:
        assert f">{region}</a></h2>" in page


def test_page_view_renders_infobox_and_tables_and_escapes_html():
    lauma = next(p for p in wiki.pages().values() if p.title == "Lauma")
    assert lauma.info.get("Element") == "Dendro"
    body = wiki.page_body(lauma)
    assert '<dl class="infobox">' in body and "<table>" in body and lauma.url in body
    assert wiki.render_block("", "<script>alert(1)</script>") == "<p>&lt;script&gt;alert(1)&lt;/script&gt;</p>"


def test_every_page_renders():
    for p in wiki.pages().values():
        body = wiki.page_body(p)
        assert f"<h1>{html.escape(p.title.removeprefix('Version/'))}</h1>" in body, p.slug
        assert "<details" in body or "<div class=\"lead\">" in body, p.slug


def test_site_text_does_not_describe_the_chatbot():
    # team decision for #64: a general page about the game; the chat is only the corner pop-up and "Ask about" buttons
    page = wiki.render("t", wiki.home_body())
    visible = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", page, flags=re.S)
    for word in ("FanBot", "chatbot", "AI model", "retrieval", "assistant"):
        assert word.lower() not in visible.lower(), word


def test_no_third_party_scripts_or_styles():
    page = wiki.render("t", wiki.home_body())
    assert re.findall(r'<(?:script|link)[^>]+(?:src|href)="(https?://[^"]+)"', page) == []


def test_accessibility_basics():
    page = wiki.render("t", wiki.home_body())
    assert '<a class="skip" href="#main">' in page and '<main id="main"' in page
    assert 'role="status" aria-live="polite"' in page  # search results are announced
    assert 'aria-label="5 stars"' not in page and '<span class="sr">5-star</span>' in page


def test_images_come_only_from_the_wiki_image_server_and_are_decorative():
    import re
    from web.images import IMAGE_HOST, images

    assert len(images()) >= 300                                      # nearly every page has a picture
    lauma = next(p for p in wiki.pages().values() if p.title == "Lauma")
    assert images()[lauma.slug]["thumb"].endswith("Lauma_Icon.png/revision/latest/scale-to-width-down/160")
    for doc in [wiki.home_body(), wiki.page_body(lauma)]:
        tags = re.findall(r"<img [^>]*>", doc)
        assert tags
        for t in tags:
            assert f'src="{IMAGE_HOST}' in t and 'alt=""' in t and 'referrerpolicy="no-referrer"' in t



def test_home_background_video_is_muted_never_autoplays_from_html_and_can_be_paused():
    import json
    from web.images import IMAGE_HOST, clips

    assert len(clips()) >= 60
    home = wiki.home_body()
    v = re.search(r'<video class="bannervideo"[^>]*>', home).group(0)
    assert "muted" in v and "autoplay" not in v and 'aria-hidden="true"' in v
    reel = json.loads(html.unescape(re.search(r'data-reel="([^"]+)"', v).group(1)))
    assert reel and all(c["src"].startswith(IMAGE_HOST) and c["src"].endswith(".mp4/revision/latest") for c in reel)
    assert 'class="bgtoggle"' in home
    assert "<video" not in wiki.page_body(next(p for p in wiki.pages().values() if p.title == "Lauma"))



def test_version_ask_buttons_name_the_version():
    home = wiki.home_body()
    assert 'data-q="Tell me about Version 7.0."' in home and 'data-q="Tell me about 7.0."' not in home
    v = next(p for p in wiki.pages().values() if p.title == "Version/7.0")
    assert 'data-q="Tell me about Version 7.0."' in wiki.page_body(v)
