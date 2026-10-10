"""Query rewrite helpers (#77)."""
import json


def test_zh_glossary_from_other_languages_tables(tmp_path, monkeypatch):
    # #77: official Chinese names come from the snapshot, per table, and the longest name wins over a name inside it
    from rag import config, generation
    def doc(title, blocks):
        return {"doc_id": title.lower(), "title": title, "blocks": blocks}
    def table(path, english, zh):
        return {"kind": "table", "heading_path": path, "text": "", "table": {"headers": ["Language", "Official Name"],
                "rows": [["English", english], ["Chinese (Simplified)", f"{zh} Pinyin"]]}}
    docs = [doc("Lunar-Charged", [table(["Lunar-Charged", "Other Languages"], "Lunar-Charged", "月感电")]),
            doc("Electro-Charged", [table(["Electro-Charged", "Other Languages"], "Electro-Charged", "感电")]),
            doc("Lunar-Bloom", [table(["Lunar-Bloom", "Other Languages", "Verdant Dew"], "Verdant Dew", "草露")])]
    path = tmp_path / "docs.jsonl"
    path.write_text("\n".join(json.dumps(d, ensure_ascii=False) for d in docs), encoding="utf-8")
    monkeypatch.setattr(config, "DOCS_PATH", path)
    generation.zh_glossary.cache_clear()
    try:
        assert generation.zh_glossary() == {"月感电": "Lunar-Charged", "感电": "Electro-Charged", "草露": "Verdant Dew"}
        assert generation.glossary_hints("说说月感电队可以配谁") == [("月感电", "Lunar-Charged")]
        assert generation.glossary_hints("感电和草露") == [("感电", "Electro-Charged"), ("草露", "Verdant Dew")]
        assert generation.glossary_hints("what is this") == []
    finally:
        generation.zh_glossary.cache_clear()
