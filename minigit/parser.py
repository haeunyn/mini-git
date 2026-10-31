"""명령줄 한 줄을 토큰으로 쪼갠다 (따옴표 안의 공백은 유지)."""


def tokenize(line: str):
    tokens = []
    buf = []
    in_quotes = False
    for ch in line:
        if ch == '"':
            in_quotes = not in_quotes
        elif ch.isspace() and not in_quotes:
            if buf:
                tokens.append("".join(buf))
                buf = []
        else:
            buf.append(ch)
    if buf:
        tokens.append("".join(buf))
    return tokens


def parse_option(token: str, name: str):
    """--name=value 형태에서 value 를 꺼낸다. 형식이 아니면 None.

    예: parse_option("--author=Alice", "author") -> "Alice"
    """
    prefix = f"--{name}="
    if token.startswith(prefix):
        return token[len(prefix):]
    return None
