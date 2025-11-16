import random
from typing import Dict, List, Tuple, Set
from copy import deepcopy

from bot_training.swiss_tournament import get_current_score, sonneborn_berger, tie_break_group, \
    group_by_current_scores, n_wins


def generate_pairings(current_results: Dict[int, List[Tuple[int, float]]]) -> List[Tuple[int, int]]:
    pairings: List[Tuple[int, int]] = []
    all_players: List[int] = list(current_results.keys())
    if len(all_players) % 2 == 1:
        raise NotImplementedError('Pairing for odd number of players not supported.')
    available_to_pair = all_players.copy()
    for player_to_pair in all_players:
        if player_to_pair not in available_to_pair:
            continue
        already_faced: List[int] = [res[0] for res in current_results[player_to_pair]]
        try:
            opponent = random.choice([opp for opp in available_to_pair if (opp != player_to_pair)
                                        and (opp not in already_faced)])
        except IndexError:
            return generate_pairings(current_results)
        pairings.append((player_to_pair, opponent))
        available_to_pair.remove(opponent)
        available_to_pair.remove(player_to_pair)
        # to_pop = []
        # for i in range(len(available_to_pair)):
        #     if available_to_pair[i] == player_to_pair or available_to_pair[i] == opponent:
        #         to_pop.append(i)
        # to_pop.sort(reverse=True)
        # for j in to_pop:
        #     available_to_pair.pop(j)
    return pairings


def get_performance_in_score_group(player: int, final_results: Dict[int, List[Tuple[int, float]]]) -> int:
    player_score = get_current_score(final_results[player])
    num_wins = 0
    num_losses = 0
    grouped_by_score = group_by_current_scores(final_results)
    players_in_score_group = grouped_by_score[player_score]
    results_of_player = final_results[player]
    results_in_score_group = [res for res in results_of_player if res[0] in players_in_score_group]
    for res in results_in_score_group:
        if res[1] == 1:
            num_wins += 1
        elif res[1] == 0:
            num_losses += 1
    return num_wins - num_losses


def rank_all_players(final_results: Dict[int, List[Tuple[int, float]]]) -> List[int]:

    def first_tie_breaker(player: int, all_results: Dict[int, List[Tuple[int, float]]]) -> float:
        return get_current_score(all_results[player])

    tie_breakers_in_order = [first_tie_breaker, get_performance_in_score_group, sonneborn_berger, n_wins]

    return tie_break_group(list(final_results.keys()), final_results, tie_breakers_in_order)


def generate_pairings_all_rounds(players: List[int]) -> Dict[int, List[Tuple[int, int]]]:
    n_players = len(players)
    all_pairings = {}
    all_needed_pairings: List[Set[int]] = []
    for i in players:
        for j in players:
            if i == j:
                continue
            if {i, j} not in all_needed_pairings:
                all_needed_pairings.append({i, j})

    for i in range(1, n_players):
        all_pairings[i] = []
        possible_this_round = deepcopy(all_needed_pairings)
        while possible_this_round:
            chosen_pairing = random.choice(possible_this_round)
            possible_this_round = list(filter(lambda x: not x.intersection(chosen_pairing), possible_this_round))
            all_pairings[i].append(tuple(chosen_pairing))
            all_needed_pairings.remove(chosen_pairing)
    return all_pairings
