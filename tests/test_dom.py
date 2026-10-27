from sdom.dom import Document, diff_ids, est_tokens


def test_parse_hierarchy_and_ids(cv):
    assert cv.root.text == "Jane Doe — CV"
    assert cv.nodes["s1"].text == "Summary"
    assert cv.nodes["s1.i1"].style == "para"
    assert cv.nodes["s2.s1"].text.startswith("Lead Engineer — Initech")
    assert cv.nodes["s2.s1.i2"].text == "Cut costs by 25% at Initech."
    assert cv.nodes["s2.s1.i2"].style == "bullet"
    assert cv.nodes["s2.s1.i2"].section().id == "s2.s1"
    assert cv.nodes["s2.s1.i1"].path_titles() == ["Experience", cv.nodes["s2.s1"].text]


def test_render_round_trip_is_stable(cv, corpus):
    assert Document.parse(cv.render(), "cv").render() == cv.render()
    for doc, _ in corpus.values():
        again = Document.parse(doc.render(), doc.doc_type)
        assert again.render() == doc.render()
        assert list(again.nodes) == list(doc.nodes)


def test_set_text_logs_and_revert(cv):
    assert cv.set_text("s2.s1.i1", "New text") is True
    assert cv.set_text("s2.s1.i1", "New text") is False  # no-op
    assert cv.log[-1]["old"].startswith("Built a Kafka")
    assert cv.revert("s2.s1.i1") is True
    assert cv.nodes["s2.s1.i1"].text.startswith("Built a Kafka")
    assert cv.revert("s2.s1.i1") is False
    assert [e["origin"] for e in cv.log] == ["llm", "revert"]


def test_insert_after_and_delete(cv):
    new_id = cv.insert_after("s2.s1.i1", "Ran the on-call rota.")
    assert cv.nodes[new_id].style == "bullet" and cv.nodes[new_id].parent is cv.nodes["s2.s1"]
    again = Document.parse(cv.render(), "cv")
    assert [c.text for c in again.nodes["s2.s1"].children][1] == "Ran the on-call rota."
    assert cv.delete("s2.s1.i2") is True
    assert "Cut costs" not in cv.render()
    assert cv.log[-1]["new"] is None and cv.log[-2]["old"] is None
    sec_id = cv.insert_after("s3", "Tools: Terraform")  # on a section: becomes its first item
    assert cv.nodes["s3"].children[0].id == sec_id
    assert cv.delete("s2.s2") and "Globex" not in cv.render()  # subtree removed
    assert cv.delete("missing") is False


def test_render_node_and_skeleton(cv):
    block = cv.render_node(cv.nodes["s2.s1"])
    assert block.splitlines()[0] == "[s2.s1] ### Lead Engineer — Initech (2020–Present)"
    assert "[s2.s1.i1] - Built a Kafka" in block
    assert "[" not in cv.render_node(cv.nodes["s2.s1"], with_ids=False)
    sk = cv.skeleton()
    assert "[s2] Experience (2 subsections, 3 items)" in sk
    assert "s2.s1" not in sk  # depth-limited


def test_locate_offset_and_diff(cv):
    assert cv.locate("cut costs") == ["s2.s1.i2"]
    assert cv.offset_fraction("s1") < cv.offset_fraction("s3.i1") == 1.0
    before = cv.snapshot()
    cv.set_text("s3.i1", "Platforms: AWS")
    assert diff_ids(before, cv.snapshot()) == {"s3.i1"}
    assert diff_ids({"a": "x"}, {"b": "y"}) == {"a", "b"}


def test_paragraph_after_bullets_renders_with_blank_line():
    doc = Document.parse("# T\n\n## A\n\n- one\n- two\n\nPara here.\n", "generic")
    assert doc.render() == "# T\n\n## A\n\n- one\n- two\n\nPara here.\n"


def test_est_tokens():
    assert est_tokens("") == 1
    assert est_tokens("x" * 400) == 100
