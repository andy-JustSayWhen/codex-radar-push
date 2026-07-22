import re
from html import unescape


def collapse_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def strip_tags(value: str) -> str:
    text = re.sub(r"<script\b[^>]*>.*?</script>", "", value, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style\b[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "\n", text)
    return unescape(text)


def html_section(html: str, class_name: str) -> str:
    section_pattern = re.compile(r"<section\b[^>]*>", flags=re.IGNORECASE)
    class_pattern = re.compile(r"""\bclass\s*=\s*(['"])(.*?)\1""", flags=re.IGNORECASE | re.DOTALL)

    section_match = None
    section_matches = list(section_pattern.finditer(html))
    for candidate in section_matches:
        class_match = class_pattern.search(candidate.group(0))
        if not class_match:
            continue
        classes = class_match.group(2).split()
        if class_name in classes:
            section_match = candidate
            break

    if section_match is None:
        return ""

    next_section = None
    for candidate in section_matches:
        if candidate.start() > section_match.start():
            next_section = candidate
            break

    if next_section is None:
        return html[section_match.start() :]
    return html[section_match.start() : next_section.start()]
