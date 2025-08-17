# /sitecontent/templatetags/inr.py
from django import template

register = template.Library()

def _format_indian_number(n: int) -> str:
    s = str(n)
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return ",".join(parts + [tail])

@register.filter(name="inr")
def inr(value, show_symbol=True):
    try:
        amt = float(value)
    except (TypeError, ValueError):
        return value
    sign = "-" if amt < 0 else ""
    amt = abs(amt)
    rupees = int(amt)
    paise = int(round((amt - rupees) * 100))
    rupee_str = _format_indian_number(rupees)
    formatted = f"{rupee_str}.{paise:02d}" if paise else rupee_str
    symbol = "₹" if (str(show_symbol).lower() not in ["false", "0", "no"]) else ""
    return f"{sign}{symbol}{formatted}"
