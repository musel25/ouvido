from ouvido.render import render_card


def test_substitutes_fields():
    html = render_card({"Item": "cê", "Gloss": "you"}, {"Front": "<b>{{Item}}</b>", "Back": ""})
    assert "<b>cê</b>" in html


def test_conditional_shown_when_field_nonempty():
    html = render_card({"Cuidado": "no es 'ce'"},
                       {"Front": "{{#Cuidado}}⚠️ {{Cuidado}}{{/Cuidado}}", "Back": ""})
    assert "⚠️ no es 'ce'" in html


def test_conditional_hidden_when_field_empty():
    html = render_card({"Cuidado": ""},
                       {"Front": "{{#Cuidado}}⚠️ {{Cuidado}}{{/Cuidado}}", "Back": ""})
    assert "⚠️" not in html


def test_conditional_hidden_when_field_absent():
    html = render_card({}, {"Front": "{{#Ear}}👂{{/Ear}}", "Back": ""})
    assert "👂" not in html


def test_sound_tag_becomes_audio_element():
    html = render_card({"A": "[sound:ouv_abc_s1.mp3]"}, {"Front": "{{A}}", "Back": ""})
    assert "<audio controls" in html and "ouv_abc_s1.mp3" in html


def test_frontside_is_substituted_into_back():
    html = render_card({"Item": "né"},
                       {"Front": "<i>{{Item}}</i>", "Back": "{{FrontSide}}<hr>answer"})
    assert html.count("<i>né</i>") == 2   # once on front, once echoed into back


def test_unknown_field_renders_empty_not_literal():
    html = render_card({"Item": "x"}, {"Front": "{{Item}}{{Nonexistent}}", "Back": ""})
    assert "{{Nonexistent}}" not in html
