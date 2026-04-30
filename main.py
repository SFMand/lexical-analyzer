from collections import defaultdict
import string
epsilon = 'ε'

class State:
  def __init__(self, accept_status = False):
    self.transistions: dict[str, set['State']] = defaultdict(set) # dict -> key: symbol | value: set of states
    self.is_accept: bool = accept_status

class NFA:
  def __init__(self, start_state, accept_state):
    self.start_state: State = start_state
    self.accept_state: State = accept_state

def single_char_nfa(char: str) -> NFA:
  start = State()
  accept = State(accept_status=True)
  start.transistions[char].add(accept)
  return NFA(start, accept)

def union_nfa(nfa1: NFA, nfa2: NFA) -> NFA:
  new_start = State()
  new_accept = State(accept_status=True)
  
  new_start.transistions[epsilon].add(nfa1.start_state)
  new_start.transistions[epsilon].add(nfa2.start_state)
  
  nfa1.accept_state.transistions[epsilon].add(new_accept)
  nfa2.accept_state.transistions[epsilon].add(new_accept)
  
  nfa1.accept_state.is_accept = False
  nfa2.accept_state.is_accept = False
  
  return NFA(new_start, new_accept)

def concat_nfa(nfa1: NFA, nfa2: NFA) -> NFA:
  nfa1.accept_state.transistions[epsilon].add(nfa2.start_state)
  
  nfa1.accept_state.is_accept = False
  
  return NFA(nfa1.start_state, nfa2.accept_state)

def kleene_star_nfa(nfa: NFA) -> NFA:
  new_start = State()
  new_accept = State(accept_status=True)
  
  new_start.transistions[epsilon].add(nfa.start_state)
  new_start.transistions[epsilon].add(new_accept)
  
  nfa.accept_state.transistions[epsilon].add(nfa.start_state)
  nfa.accept_state.transistions[epsilon].add(new_accept)
  nfa.accept_state.is_accept = False
  
  return NFA(new_start, new_accept)


def build_char_union(chars: str) -> str:
  return '|'.join(chars)

SPACE_CHAR = " "
LETTER_RE = build_char_union(string.ascii_letters)
DIGIT_RE = build_char_union(string.digits)
ID_RE = f"{LETTER_RE}.({LETTER_RE}|{DIGIT_RE}|_)*"
INT_RE = f"{DIGIT_RE}.{DIGIT_RE}*"
FRAC_RE = f"\\.{DIGIT_RE}.{DIGIT_RE}*"
NUM_RE = f"({INT_RE})|(({INT_RE}).({FRAC_RE}))"
SPACE_RE = f"{SPACE_CHAR}.{SPACE_CHAR}*"

TOKEN_REGEX = [
  ("SPACE", SPACE_RE),
  ("KW_IF", "i.f"),
  ("KW_THEN", "t.h.e.n"),
  ("KW_ELSE", "e.l.s.e"),
  ("KW_WHILE", "w.h.i.l.e"),
  ("KW_RETURN", "r.e.t.u.r.n"),
  ("KW_FOR", "f.o.r"),
  ("KW_BREAK", "b.r.e.a.k"),
  ("KW_CONTINUE", "c.o.n.t.i.n.u.e"),
  ("KW_INT", "i.n.t"),
  ("KW_FLOAT", "f.l.o.a.t"),
  ("ID", ID_RE),
  ("NUM", NUM_RE),
  ("EQ", "=.="),
  ("NEQ", "!.="),
  ("LTE", "<.="),
  ("GTE", ">.="),
  ("ASSIGN", "="),
  ("OP_PLUS", "+"),
  ("OP_MINUS", "-"),
  ("OP_MULT", "\\*"),
  ("OP_DIV", "/"),
  ("LT", "<"),
  ("GT", ">"),
  ("LPAREN", "\\("),
  ("RPAREN", "\\)"),
  ("LBRACE", "{"),
  ("RBRACE", "}"),
  ("SEMI", ";"),
  ("COMMA", ",")
]