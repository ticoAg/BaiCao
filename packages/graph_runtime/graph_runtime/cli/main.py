from .formatters import format_error
from .help import ASK_HELP, ROOT_HELP


def run_cli(argv: list[str]) -> int:
    command = argv[0] if argv else "help"

    if command in {"help", "--help", "-h"}:
        print(ROOT_HELP)
        return 0

    if command == "ask":
        if len(argv) >= 2 and argv[1] in {"help", "--help", "-h"}:
            print(ASK_HELP)
            return 0
        if len(argv) < 2:
            print(
                format_error(
                    "缺少问题内容。",
                    ['graph ask "黄芩的功效是什么？"', "graph ask --help"],
                )
            )
            return 2
        return 0

    print(format_error(f"未知命令: {command}", ["graph help"]))
    return 2
