from rag import chunking as ch

DOC = {
    "doc_id": "gi-test-00000000", "title": "Test Talent", "page_type": "talent",
    "source_url": "https://example.org/wiki/Test_Talent", "crawled_at": "2026-10-10T00:00:00+00:00",
    "effective_date": "2026-01-14",
    "blocks": [
        {"heading_path": ["Test Talent"], "kind": "text", "text": "Test Talent is an Elemental Skill."},
        {"heading_path": ["Test Talent", "Attribute Scaling"], "kind": "table", "text": "",
         "table": {"headers": ["", "1", "2", "3"],
                   "rows": [[f"Hit {i} DMG (%)", "10.5", "11.25", "12.0"] for i in range(200)]}},
        {"heading_path": ["Test Talent", "Other Languages"], "kind": "text", "text": "Skipped section."},
    ],
}


def test_ids_deterministic_and_unique():
    for strat in ("A", "B"):
        a, b = ch.build(strat, [DOC]), ch.build(strat, [DOC])
        assert [c.chunk_id for c in a] == [c.chunk_id for c in b]
        assert len({c.chunk_id for c in a}) == len(a)
        assert a[0].chunk_id == f"gi-test-00000000#{strat}#0000"
        assert all(c.doc_id == DOC["doc_id"] and c.strategy == strat for c in a)


def test_skipped_sections_dropped_for_both():
    for strat in ("A", "B"):
        assert not any("Skipped section" in c.text for c in ch.build(strat, [DOC]))


def test_structured_splits_tables_with_header_and_path():
    chunks = ch.chunk_structured(DOC, max_tokens=128)
    table_chunks = [c for c in chunks if "Lv1" in c.text]
    assert len(table_chunks) > 1
    for c in table_chunks:
        lines = c.text.splitlines()
        assert lines[0] == "Test Talent > Attribute Scaling"     # heading path carried
        assert lines[1] == " | Lv1 | Lv2 | Lv3"                    # header repeated in every row group
        assert c.url.endswith("#Attribute_Scaling")
    assert all(ch.n_tokens(c.text) <= 128 for c in chunks)


def test_fixed_windows_overlap():
    chunks = ch.chunk_fixed(DOC, size=64, overlap=16)
    assert len(chunks) > 2
    assert all(c.heading_path == [] for c in chunks)
    assert all(ch.n_tokens(c.text) <= 65 for c in chunks)


def test_overlong_table_row_is_split_not_truncated():
    long_row = ["Long note", " ".join(f"word{i}" for i in range(300)), "x", "y"]
    doc = {**DOC, "blocks": [{"heading_path": ["Test Talent", "Notes"], "kind": "table", "text": "",
                              "table": {"headers": ["", "1", "2", "3"], "rows": [long_row]}}]}
    text = "\n".join(c.text for c in ch.chunk_structured(doc, max_tokens=128))
    assert "word0" in text and "word299" in text
