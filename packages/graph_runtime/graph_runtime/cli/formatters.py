def format_error(message: str, next_steps: list[str] | None = None) -> str:
    lines = [message]
    if next_steps:
        lines.append("可以试试：")
        lines.extend(f"  {step}" for step in next_steps)
    return "\n".join(lines)
