def beautiful_numeral(n):
    numerals = ["чат", "чата", "чатов"]
    if n % 10 == 1:
        return f"{n} {numerals[0]}"
    elif 2 <= n % 10 <= 4:
        return f"{n} {numerals[1]}"
    else:
        return f"{n} {numerals[2]}"