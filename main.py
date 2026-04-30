from collections import defaultdict
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
