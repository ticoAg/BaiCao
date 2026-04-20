from graph_runtime.cli.main import run_cli


def test_root_help_lists_progressive_commands(capsys):
    exit_code = run_cli(["help"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "ask" in captured.out
    assert "search" in captured.out
    assert "explore" in captured.out


def test_ask_without_question_suggests_next_step(capsys):
    exit_code = run_cli(["ask"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "graph ask --help" in captured.out
    assert 'graph ask "黄芩的功效是什么？"' in captured.out
