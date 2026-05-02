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

def epsilon_nfa() -> NFA:
  return single_char_nfa(epsilon)

def plus_nfa(nfa: NFA) -> NFA:
  new_start = State()
  new_accept = State(accept_status=True)

  new_start.transistions[epsilon].add(nfa.start_state)
  
  nfa.accept_state.transistions[epsilon].add(nfa.start_state)
  nfa.accept_state.transistions[epsilon].add(new_accept)
  nfa.accept_state.is_accept = False
  
  return NFA(new_start, new_accept)


def optional_nfa(nfa: NFA) -> NFA:
  return union_nfa(nfa, epsilon_nfa())


SPACE_CHAR = " "
LETTER_RE = "[A-Za-z]"
DIGIT_RE = "[0-9]"

TOKEN_REGEX = [
  ("SPACE", f"{SPACE_CHAR}+"),
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
    chars.extend(chr(unicode) for unicode in range(start, end))
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


def infix_to_postfix(regex: str) -> str:
  precedence = {'*': 3, '.': 2, '|': 1}
  output = []
  stack = []
  
  i = 0
  while i < len(regex):
    char = regex[i]
    if char == '\\' and i + 1 < len(regex):
      output.append(regex[i + 1])
      i += 2
      continue
    if char.isalnum() or char == epsilon or char in {'_', ' '}:
      output.append(char)
    elif char in precedence:
      while (stack and stack[-1] != '(' and precedence[stack[-1]] >= precedence[char]):
        output.append(stack.pop())
      stack.append(char)
    elif char == '(':
      stack.append(char)
    elif char == ')':
      while stack and stack[-1] != '(':
        output.append(stack.pop())
      if stack and stack[-1] == '(':
        stack.pop()
    else:
      output.append(char)
    i += 1
  
  while stack:
    output.append(stack.pop())
  
  return ''.join(output)

def regex_to_nfa(regex: str) -> NFA:
  stack = []
  postfix_regex = infix_to_postfix(regex)
  
  for char in postfix_regex:
    if char.isalnum() or char == epsilon:
      stack.append(single_char_nfa(char))
    elif char == '|':
      nfa2 = stack.pop()
      nfa1 = stack.pop()
      stack.append(union_nfa(nfa1, nfa2))
    elif char == '*':
      stack.append(kleene_star_nfa(stack.pop())) 
    elif char == '.':
      nfa2 = stack.pop()
      nfa1 = stack.pop()
      stack.append(concat_nfa(nfa1, nfa2))
      
  return stack.pop()

def build_final_nfa(token_regex_list: list[tuple[str, str]]):
  final_nfa = None
  for _, regex in token_regex_list:
    nfa = regex_to_nfa(regex)
    if final_nfa == None:
      final_nfa = nfa
    else:
      final_nfa = union_nfa(final_nfa, nfa)  
      
  return final_nfa     