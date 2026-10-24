import re

_URL = re.compile(r"https?://\S+")
_MENTION = re.compile(r"@\w+")
_HASHTAG = re.compile(r"#(\w+)")
_HTML = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")
_TOKEN = re.compile(r"[A-Za-z][A-Za-z'-]+")
def clean(t):
    t = _HTML.sub(" ", t); t = _URL.sub(" ", t); t = _MENTION.sub(" ", t)
    t = _HASHTAG.sub(r"\1", t); t = _WS.sub(" ", t)
    return t.strip()
def tokens(t): return _TOKEN.findall(t)
