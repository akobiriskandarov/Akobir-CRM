from bovari_bot.agents import AGENTS, PLAN_SCHEMA
from bovari_bot.formatting import md_to_tg_html, split_markdown
from bovari_bot.storage import Storage


def test_seven_agents():
    assert set(AGENTS) == {
        "marketolog", "smm", "pm", "dizayner", "kopirayter", "analitik", "montajyor"
    }
    for a in AGENTS.values():
        assert "Bovari Agency" in a.system_prompt
        assert a.title in a.system_prompt
    assert PLAN_SCHEMA["properties"]["steps"]["items"]["properties"]["agent"]["enum"] == list(AGENTS)


def test_md_to_html():
    out = md_to_tg_html("## Sarlavha\n**qalin** va *kursiv* <tag> & `x<y`\n- band\n[link](https://a.uz/b)")
    assert "<b>Sarlavha</b>" in out
    assert "<b>qalin</b>" in out
    assert "<i>kursiv</i>" in out
    assert "&lt;tag&gt; &amp;" in out
    assert "<code>x&lt;y</code>" in out
    assert "• band" in out
    assert '<a href="https://a.uz/b">link</a>' in out


def test_code_block_not_formatted():
    out = md_to_tg_html("```\n**not bold** <x>\n```")
    assert out == "<pre>**not bold** &lt;x&gt;</pre>"


def test_split_preserves_fences_and_limit():
    text = "Kirish\n```\n" + "\n".join(f"line {i}" for i in range(2000)) + "\n```\nOxiri"
    chunks = split_markdown(text, limit=1000)
    assert len(chunks) > 1
    assert all(len(c) <= 1010 for c in chunks)
    for c in chunks:
        assert c.count("```") % 2 == 0
    assert split_markdown("qisqa") == ["qisqa"]


def test_storage(tmp_path):
    s = Storage(str(tmp_path / "t.db"))
    assert s.get_agent(1) is None
    s.set_agent(1, "smm")
    s.set_agent(1, "pm")
    assert s.get_agent(1) == "pm"
    for i in range(5):
        s.add_turn(1, "pm", f"q{i}", f"a{i}")
    s.add_turn(1, "smm", "x", "y")
    h = s.history(1, "pm", 2)
    assert [m["content"] for m in h] == ["q3", "a3", "q4", "a4"]
    assert [m["role"] for m in h] == ["user", "assistant"] * 2
    assert s.reset(1, "pm") == 5
    assert s.history(1, "smm", 10)[0]["content"] == "x"
    s.log_usage(1, "smm", 100, 50, 10)
    assert s.usage_since(0)[0][:2] == ("smm", 1)
