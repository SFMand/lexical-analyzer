from collections import defaultdict
import string
epsilon = 'ε'

class State:
  def __init__(self,token_name = None, token_priority = None, accept_status = False):
    self.token_name = token_name
    self.token_priority = token_priority
    self.transitions: dict[str, set['State']] = defaultdict(set) # dict -> key: symbol | value: set of states
    self.is_accept: bool = accept_status

class NFA:
  def __init__(self, start_state, accept_state):
    self.start_state: State = start_state
    self.accept_state: State = accept_state

def single_char_nfa(char: str) -> NFA:
  start = State()
  accept = State(accept_status=True)
  start.transitions[char].add(accept)
  return NFA(start, accept)

def union_nfa(nfa1: NFA, nfa2: NFA) -> NFA:
  new_start = State()
  new_accept = State(accept_status=True)
  
  new_start.transitions[epsilon].add(nfa1.start_state)
  new_start.transitions[epsilon].add(nfa2.start_state)
  
  nfa1.accept_state.transitions[epsilon].add(new_accept)
  nfa2.accept_state.transitions[epsilon].add(new_accept)
  
  nfa1.accept_state.is_accept = False
  nfa2.accept_state.is_accept = False
  
  return NFA(new_start, new_accept)

def concat_nfa(nfa1: NFA, nfa2: NFA) -> NFA:
  nfa1.accept_state.transitions[epsilon].add(nfa2.start_state)
  
  nfa1.accept_state.is_accept = False
  
  return NFA(nfa1.start_state, nfa2.accept_state)

def kleene_star_nfa(nfa: NFA) -> NFA:
  new_start = State()
  new_accept = State(accept_status=True)
  
  new_start.transitions[epsilon].add(nfa.start_state)
  new_start.transitions[epsilon].add(new_accept)
  
  nfa.accept_state.transitions[epsilon].add(nfa.start_state)
  nfa.accept_state.transitions[epsilon].add(new_accept)
  nfa.accept_state.is_accept = False
  
  return NFA(new_start, new_accept)

def epsilon_nfa() -> NFA:
  return single_char_nfa(epsilon)

def plus_nfa(nfa: NFA) -> NFA:
  new_start = State()
  new_accept = State(accept_status=True)

  new_start.transitions[epsilon].add(nfa.start_state)
  
  nfa.accept_state.transitions[epsilon].add(nfa.start_state)
  nfa.accept_state.transitions[epsilon].add(new_accept)
  nfa.accept_state.is_accept = False
  
  return NFA(new_start, new_accept)


def optional_nfa(nfa: NFA) -> NFA:
  return union_nfa(nfa, epsilon_nfa())

  
SPACE_RE = "[ \t\n]"
LETTER_RE = "[A-Za-z]"
DIGIT_RE = "[0-9]"

TOKEN_REGEX = [
  ("SPACE", f"{SPACE_RE}+"), 

  ("KW_IF", "if"),
  ("KW_THEN", "then"),
  ("KW_ELSE", "else"),
  ("KW_WHILE", "while"),
  ("KW_RETURN", "return"),
  ("KW_FOR", "for"),
  ("KW_BREAK", "break"),
  ("KW_CONTINUE", "continue"),
  ("KW_INT", "int"),
  ("KW_FLOAT", "float"),
  
  ("ID", f"{LETTER_RE}({LETTER_RE}|{DIGIT_RE}|_)*"),
  ("NUM",  f"{DIGIT_RE}+(\\.{DIGIT_RE}+)?"),
  
  ("EQ", "=="),
  ("NEQ", "!="),
  ("LTE", "<="),
  ("GTE", ">="),
  
  ("ASSIGN", "="),
  ("OP_PLUS", "\\+"),
  ("OP_MINUS", "-"),
  ("OP_MULT", "\\*"),
  ("OP_DIV", "/"),
  ("LT", "<"),
  ("GT", ">"),
  ("LPAREN", "\\("),
  ("RPAREN", "\\)"),
  ("LBRACE", "\\{"),
  ("RBRACE", "\\}"),
  ("SEMI", ";"),
  ("COMMA", ",")
]

TOKEN_OP_MAP = {
    '(': 'LPAREN_OP', ')': 'RPAREN_OP',
    '|': 'OP', '*': 'OP', '+': 'OP', '?': 'OP', '.': 'OP'
}

def expand_char_class(regex: str):
  chars = []
  i = 0
  while i < len(regex):
   if regex[i] == '\\' and i + 1 < len(regex):
    chars.append(regex[i + 1])
    i += 2
   elif i + 2 < len(regex) and regex[i + 1] == '-' and regex[i + 2] != ']':
    start, end = ord(regex[i]), ord(regex[i + 2])
    chars.extend(chr(unicode) for unicode in range(start, end + 1))
    i += 3
   else:
     chars.append(regex[i])
     i += 1
      
  return chars

def tokenize_regex(regex: str):
  tokens = []
  i = 0
  
  while i < len(regex):
    char = regex[i]
    
    if char == '\\' and i + 1 < len(regex):
      tokens.append(("LITERAL", regex[i + 1]))
      i += 2
      continue
    
    if char == '[':
      end_idx = regex.find(']', i + 1)
      expanded_class = expand_char_class(regex[i + 1:end_idx])
      
      tokens.append(("LPAREN_OP", "("))
      for index, ch in enumerate(expanded_class):
        if index > 0:
          tokens.append(("OP", "|"))
        tokens.append(("LITERAL", ch))
      tokens.append(("RPAREN_OP", ")"))
      i = end_idx + 1
      continue
    
    token_type = TOKEN_OP_MAP.get(char,"LITERAL")
    tokens.append((token_type, char))
    i += 1
    
  return tokens   

def explicit_concat(tokens: list[tuple[str, str]]):
  result = [tokens[0]]
  
  for token in tokens[1:]:
    prev_type, prev_char = result[-1]
    curr_type, _ = token
        
    # implicit concat happens after: a Literal, ')', or a */+/?
    prev_valid = prev_type in {"LITERAL", "RPAREN_OP"} or (prev_type == "OP" and prev_char in {"*", "+", "?"})
        
    # implicit concat happens before a Literal or '('
    curr_valid = curr_type in {"LITERAL", "LPAREN_OP"}
        
    if prev_valid and curr_valid:
      result.append(("OP", "."))
            
    result.append(token)
        
  return result


def infix_to_postfix(regex: str):
  precedence = {'*': 3, '+': 3, '?': 3,
                '.': 2,
                '|': 1,
                '(': 0}
  
  output = []
  stack = []
  tokens = explicit_concat(tokenize_regex(regex))
  
  for token in tokens:
    token_type, token_char = token
    
    if token_type == 'LITERAL':
      output.append(token)
    elif token_type == 'LPAREN_OP':
      stack.append(token)
    elif token_type == 'RPAREN_OP':
      while stack and stack[-1][0] != 'LPAREN_OP':
        output.append(stack.pop())  
      stack.pop() # remove left parantheses
      
    elif token_type == 'OP':
      while stack and precedence.get(stack[-1][1], -1) >= precedence[token_char]:
        output.append(stack.pop())
      stack.append(token)
      continue
     
  while stack:
    output.append(stack.pop())  
  return output
  
  
def regex_to_nfa(regex: str) -> NFA:
  stack = []
  
  
  for token_type, token_char in infix_to_postfix(regex):
    
    if token_type == 'LITERAL':
      stack.append(single_char_nfa(token_char))
    elif token_char == '|':
      nfa2 = stack.pop()
      nfa1 = stack.pop()
      stack.append(union_nfa(nfa1, nfa2))
    elif token_char == '*':
      stack.append(kleene_star_nfa(stack.pop()))
    elif token_char == '+':
      stack.append(plus_nfa(stack.pop()))
    elif token_char == '?':
      stack.append(optional_nfa(stack.pop()))
    elif token_char == '.':
      nfa2 = stack.pop()
      nfa1 = stack.pop()
      stack.append(concat_nfa(nfa1, nfa2))
      
  return stack.pop()


def build_final_nfa(token_regex_list: list[tuple[str, str]]):
  start_state = State()
  for priority, (id, regex) in enumerate(token_regex_list):
    nfa = regex_to_nfa(regex)
    nfa.accept_state.token_name = id
    nfa.accept_state.token_priority = priority
    start_state.transitions[epsilon].add(nfa.start_state)
    
  return NFA(start_state, State(accept_status=False))     


def epsilon_closure(states):
    closure = set(states)
    stack   = list(states)
    while stack:
        s = stack.pop()
        for target in s.transitions.get(epsilon, []):
            if target not in closure:
                closure.add(target)
                stack.append(target)
    return frozenset(closure)
  
  
def move(states, symbol):
    result = set()
    for s in states:
        for target in s.transitions.get(symbol, []):
            result.add(target)
    return result


def collect_alphabet(start):
    visited  = set()
    stack    = [start]
    alphabet = set()
    while stack:
        s = stack.pop()
        if id(s) in visited:
            continue
        visited.add(id(s))
        for sym, targets in s.transitions.items():
            if sym != epsilon:
                alphabet.add(sym)
            for t in targets:
                if id(t) not in visited:
                    stack.append(t)
    return alphabet


def winning_token(dfa_state):
    best = None
    for nfa_state in dfa_state:
        if nfa_state.is_accept and nfa_state.token_name is not None:
            if best is None or nfa_state.token_priority < best.token_priority:
                best = nfa_state
    if best:
        return (best.token_name, best.token_priority)
    return None


def build_dfa(nfa_start):
    alphabet  = collect_alphabet(nfa_start)
    dfa_start = epsilon_closure([nfa_start])

    dfa_transitions = {}   
    dfa_accept      = {}   
    worklist = [dfa_start]  
    visited  = set()

    while worklist:
        current = worklist.pop()
        if current in visited:
            continue
        visited.add(current)

        dfa_transitions[current] = {}

        token_info = winning_token(current)
        if token_info:
            dfa_accept[current] = token_info

        for sym in alphabet:
            next_nfa_states = move(current, sym)
            next_dfa_state  = epsilon_closure(next_nfa_states)
            if next_dfa_state:  # empty set means sink state — skip
                dfa_transitions[current][sym] = next_dfa_state
                if next_dfa_state not in visited:
                    worklist.append(next_dfa_state)

    return dfa_start, dfa_transitions, dfa_accept



def scan(text, dfa_start, dfa_transitions, dfa_accept):
    tokens = []
    pos    = 0
    line   = 1
    col    = 1

    print(f"{'Lexeme':<15} {'Token':<15} {'Position'}")
    print("-" * 50)

    while pos < len(text):
        current_state = dfa_start
        start_line    = line
        start_col     = col

        last_accept_pos   = None   # position after the last accepted character
        last_accept_token = None

        i = pos
        # keep reading characters as long as the DFA has a valid transition
        while i < len(text):
            symbol     = text[i]
            next_state = dfa_transitions.get(current_state, {}).get(symbol)
            if next_state is None:
                break                    # no transition — stop
            current_state = next_state
            i += 1
            if current_state in dfa_accept:  # remember this accepting position
                last_accept_pos   = i
                last_accept_token = dfa_accept[current_state][0]

        if last_accept_pos is None:
            # no token matched at all — lexing error
            print(f"\nLexing Error: unexpected character {repr(text[pos])} "
                  f"at Line {line}, col {col}")
            return tokens

        lexeme = text[pos:last_accept_pos]

        if last_accept_token != "SPACE":
            tokens.append((lexeme, last_accept_token, start_line, start_col))
            print(f"{repr(lexeme):<15} {last_accept_token:<15} "
                  f"Line {start_line}, col {start_col}")

        for ch in lexeme:
            if ch == '\n':
                line += 1
                col   = 1
            else:
                col += 1
        pos = last_accept_pos

    print("\nLexing Completed")
    return tokens



def main():
    # Step 1 — build one combined NFA from all token regexes
    nfa = build_final_nfa(TOKEN_REGEX)

    # Step 2 — convert the NFA to a DFA (subset construction)
    dfa_start, dfa_transitions, dfa_accept = build_dfa(nfa.start_state)

    # Step 3 — read the input file and scan it
    with open("input.txt", "r") as f:
        text = f.read()

    scan(text, dfa_start, dfa_transitions, dfa_accept)


if __name__ == "__main__":
    main()