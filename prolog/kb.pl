:- use_module(library(lists)).

grid_size(5).

% Check if a cell is within the 5x5 grid
valid_cell(cell(R, C)) :-
    grid_size(S), 
    Max is S - 1,
    between(0, Max, R),
    between(0, Max, C).

% Standard move logic
adjacent(cell(R1, C1), cell(R2, C2)) :-
    (   nonvar(R1), nonvar(C1)
    ->  (   (R2 is R1 + 1, C2 = C1) ; (R2 is R1 - 1, C2 = C1) 
        ;   (R2 = R1, C2 is C1 + 1) ; (R2 = R1, C2 is C1 - 1) 
        )
    ;   nonvar(R2), nonvar(C2)
    ->  (   (R1 is R2 + 1, C1 = C2) ; (R1 is R2 - 1, C1 = C2) 
        ;   (R1 = R2, C1 is C2 + 1) ; (R1 = R2, C1 is C2 - 1) 
        )
    ),
    valid_cell(cell(R1, C1)),
    valid_cell(cell(R2, C2)).

:- dynamic visited/1, percept/2, confirmed_captain/1, confirmed_safe/1, defeated_captain/1.
:- dynamic has_bankai/0, bankai_used/0, captain_target_count/1.

% Inference rules
frontier(Cell) :-
    valid_cell(Cell), \+ visited(Cell),
    visited(V), adjacent(V, Cell).

% Basic danger flagging
possible_captain(C) :-
    valid_cell(C), \+ visited(C), \+ defeated_captain(C), \+ confirmed_safe(C),
    percept(N, spiritual_pressure), adjacent(N, C).

possible_rift(C) :-
    valid_cell(C), \+ visited(C), \+ confirmed_safe(C),
    percept(N, spatial_distortion), adjacent(N, C).

% Rukia location scoring logic
possible_rukia(C) :-
    valid_cell(C), \+ visited(C),
    percept(N, golden_glistening), adjacent(N, C).

rukia_score(C, Score) :-
    possible_rukia(C),
    findall(G, (adjacent(C, G), visited(G), percept(G, golden_glistening)), Gs),
    findall(R, (adjacent(C, R), visited(R), percept(R, spatial_distortion)), Rs),
    length(Gs, GC), length(Rs, RC),
    Score is GC - (RC * 0.5).

% Captain deduction
inferred_captain(C) :- confirmed_captain(C).
inferred_captain(C) :-
    percept(S, spiritual_pressure),
    findall(Cand, (adjacent(S, Cand), \+ visited(Cand), \+ defeated_captain(Cand)), [C]).
inferred_captain(C) :-
    \+ visited(C), \+ defeated_captain(C),
    percept(P1, spiritual_pressure), percept(P2, spiritual_pressure), P1 \= P2,
    adjacent(P1, C), adjacent(P2, C),
    findall(C1, (adjacent(P1, C1), \+ visited(C1), \+ defeated_captain(C1)), Cs1),
    findall(C2, (adjacent(P2, C2), \+ visited(C2), \+ defeated_captain(C2)), Cs2),
    intersection(Cs1, Cs2, [C]).

% Safety rules
danger_percept(P) :- percept(P, spiritual_pressure).
danger_percept(P) :- percept(P, spatial_distortion).

inferred_safe(C) :- confirmed_safe(C).
inferred_safe(C) :- visited(C).
inferred_safe(C) :-
    frontier(C), visited(V), adjacent(V, C), \+ danger_percept(V).
inferred_safe(C) :-
    frontier(C), \+ possible_captain(C), \+ possible_rift(C).
inferred_safe(C) :-
    frontier(C), all_accounted, \+ possible_rift(C).

accounted(C) :- inferred_captain(C).
accounted(C) :- defeated_captain(C).

all_accounted :-
    findall(C, accounted(C), Raw), sort(Raw, Uniq),
    captain_target_count(T), length(Uniq, T).

% High-level safety check for python
safe_move(C) :- frontier(C), inferred_safe(C).

% Risk assessment for fallback moves
h_weight(spatial_distortion, 1.5).
h_weight(spiritual_pressure, 1.0).

risk_score(C, Total) :-
    frontier(C),
    findall(W, (adjacent(C, N), visited(N), percept(N, T), h_weight(T, W)), Ws),
    sum_list(Ws, Total).

% Shortcuts for python

assert_vis(cell(R, C)) :-
    assertz(visited(cell(R, C))),
    assertz(confirmed_safe(cell(R, C))).

assert_p(cell(R, C), T) :- 
    (percept(cell(R, C), T) -> true ; assertz(percept(cell(R, C), T))).

assert_cap(cell(R, C)) :-
    (confirmed_captain(cell(R, C)) -> true ; assertz(confirmed_captain(cell(R, C)))).

assert_kill(cell(R, C)) :-
    assertz(defeated_captain(cell(R, C))),
    retractall(confirmed_captain(cell(R, C))),
    assertz(confirmed_safe(cell(R, C))).

assert_ready :- (has_bankai -> true ; assertz(has_bankai)), retractall(bankai_used).
assert_used :- retractall(has_bankai), (bankai_used -> true ; assertz(bankai_used)).

reset_kb :-
    retractall(visited(_)), retractall(percept(_, _)),
    retractall(confirmed_captain(_)), retractall(confirmed_safe(_)),
    retractall(defeated_captain(_)), retractall(has_bankai),
    retractall(bankai_used), retractall(captain_target_count(_)).