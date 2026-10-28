import ast
import operator
import re
from datetime import datetime

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
}


def _eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))
    raise ValueError('Unsupported expression')


def calculator(expression):
    try:
        expression = expression.strip()
        if len(expression) > 100:
            return 'That expression is too long.'
        value = _eval(ast.parse(expression, mode='eval').body)
        if isinstance(value, float):
            value = round(value, 6)
        return f'{expression} = {value}'
    except ZeroDivisionError:
        return "I can't divide by zero."
    except Exception:
        return "I couldn't work that out."


def get_time():
    now = datetime.now()
    return f"It's {now:%H:%M} on {now:%A, %d %B %Y} (server time)."


def run_tools(query, state):
    """Return a tool result string, or None if no tool applies."""
    q = query.strip()
    low = q.lower()

    if low.startswith('note:'):
        state['notes'].append(q[5:].strip())
        return f"Saved note. You have {len(state['notes'])} note(s)."

    if low.startswith('task:'):
        state['tasks'].append(q[5:].strip())
        return 'Your tasks: ' + ', '.join(state['tasks'])

    if low in ('show notes', 'notes'):
        return 'Your notes: ' + (', '.join(state['notes']) or 'none yet')

    if low in ('show tasks', 'tasks'):
        return 'Your tasks: ' + (', '.join(state['tasks']) or 'none yet')

    if re.search(r"what\s+(time|day|date)|current\s+(time|date)|today'?s\s+date", low):
        return get_time()

    m = re.search(r'\d[\d\s+\-*/().%]*', q)
    if m:
        expr = m.group(0).strip()
        if re.search(r'\d\s*[+\-*/%]\s*[\d(]', expr):
            return calculator(expr)

    return None
