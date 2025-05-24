import random
from typing import Dict, List, Tuple, Callable


def get_current_score(player_results: List[Tuple[int, float]]) -> float:
    return sum([res[1] for res in player_results])


def group_by_tie_breaker_score(tied_players: List[int],
                               all_players_results: Dict[int, List[Tuple[int, float]]],
                               tie_breaker: Callable[[int, Dict[int, List[Tuple[int, float]]]], float]) \
        -> List[Tuple[float, List[int]]]:
    grouped_players: List[Tuple[float, List[int]]] = []
    for player in tied_players:
        tie_break_score = tie_breaker(player, all_players_results)
        found_matched_tie_breaker_score = False
        for i in range(len(grouped_players)):
            if grouped_players[i][0] == tie_break_score:
                grouped_players[i][1].append(player)
                found_matched_tie_breaker_score = True
                break
        if not found_matched_tie_breaker_score:
            grouped_players.append((tie_break_score, [player]))
    grouped_players.sort(key=lambda x: x[0], reverse=True)
    return grouped_players


def group_by_current_scores(all_players_results: Dict[int, List[Tuple[int, float]]]) -> Dict[float, List[int]]:
    grouped_players = {}
    for player in all_players_results:
        final_score = get_current_score(all_players_results[player])
        if final_score in grouped_players:
            grouped_players[final_score].append(player)
        else:
            grouped_players[final_score] = [player]
    return grouped_players


def tie_break_group(tied_players: List[int],
                    all_players_results: Dict[int, List[Tuple[int, float]]],
                    tie_breakers: List[Callable[[int, Dict[int, List[Tuple[int, float]]]], float]]) -> List[int]:
    if len(tied_players) == 1 or len(tie_breakers) == 0:
        if len(tie_breakers) == 0 and len(tied_players) > 1:
            print(f'Players {tied_players} arbitrarily ranked due to running out of tie-breakers.')
        return tied_players
    ranked_players = []
    grouped_by_tie_breakers = group_by_tie_breaker_score(tied_players=tied_players,
                                                         all_players_results=all_players_results,
                                                         tie_breaker=tie_breakers[0])
    for tied_group in grouped_by_tie_breakers:
        player_group = tied_group[1]
        ranked_players.extend(tie_break_group(tied_players=player_group,
                                              all_players_results=all_players_results,
                                              tie_breakers=tie_breakers[1:]))
    return ranked_players


def generate_pairings(all_players_results: Dict[int, List[Tuple[int, float]]],
                      float_record: Dict[str, List[int]],
                      relax_float_protection: bool = False) -> List[Tuple[int, int]]:
    float_record_delta: Dict[str, List[int]] = {'downfloated': [], 'upfloated': []}
    if len(all_players_results.keys()) % 2 == 1:
        raise NotImplementedError('Pairings for odd number of players not supported yet.')
    grouped_by_current_scores = group_by_current_scores(all_players_results)
    pairings = []
    already_paired: List[int] = []
    current_scores_in_order = list(grouped_by_current_scores.keys())
    current_scores_in_order.sort(reverse=True)
    for i in range(len(current_scores_in_order)):
        if len(already_paired) == len((all_players_results.keys())):
            break
        current_score = current_scores_in_order[i]
        players_to_pair: List[int] = [player for player in grouped_by_current_scores[current_score]
                                      if player not in already_paired].copy()
        while len(players_to_pair) > 0:
            player_to_pair = choose_player_to_pair(players_to_pair, float_record, relax_float_protection)
            already_faced: List[int] = [res[0] for res in all_players_results[player_to_pair]]
            eligible_opponents = [player for player in players_to_pair
                                  if (player != player_to_pair) and (player not in already_faced)]
            j = i
            while len(eligible_opponents) == 0 and j < len(current_scores_in_order) - 1:
                next_current_score: float = current_scores_in_order[j+1]
                eligible_opponents.extend([player for player in grouped_by_current_scores[next_current_score]
                                           if (player not in already_faced) and (player not in already_paired)])
                j += 1
            if len(eligible_opponents) == 0:
                print('Failed to generate pairings. Restarting pairing procedure with relaxed float protection.')
                return generate_pairings(all_players_results, float_record, relax_float_protection=True)
            else:
                downfloat = j - i
                opponent = choose_opponent_to_pair(eligible_opponents, float_record, downfloat, relax_float_protection)
                if downfloat > 0:
                    print(f'Player {player_to_pair} downfloated by {downfloat} score group(s). Player {opponent} upfloated to play Player {player_to_pair}.')
                    float_record_delta['downfloated'].append(player_to_pair)
                    float_record_delta['upfloated'].append(opponent)
                already_paired.extend([player_to_pair, opponent])
                pairings.append((player_to_pair, opponent))
                for k in range(len(players_to_pair)):
                    if players_to_pair[k] == player_to_pair:
                        players_to_pair.pop(k)
                        break
                for k in range(len(players_to_pair)):
                    if players_to_pair[k] == opponent:
                        players_to_pair.pop(k)
                        break
    float_record['downfloated'].extend(float_record_delta['downfloated'])
    float_record['upfloated'].extend(float_record_delta['upfloated'])
    return pairings


def solkoff(player: int, all_players_results: Dict[int, List[Tuple[int, float]]]) -> float:
    solkoff_score = 0
    opponents_faced: List[int] = [res[0] for res in all_players_results[player]]
    for opponent in opponents_faced:
        solkoff_score += get_current_score(all_players_results[opponent])
    return solkoff_score


def solkoff_minus_1(player: int, all_players_results: Dict[int, List[Tuple[int, float]]]) -> float:
    opponents_faced = [res[0] for res in all_players_results[player]]
    opponent_scores = [get_current_score(all_players_results[opponent]) for opponent in opponents_faced]
    min_opponent_score = min(opponent_scores)
    return solkoff(player, all_players_results) - min_opponent_score


def sonneborn_berger(player: int, all_players_results: Dict[int, List[Tuple[int, float]]]) -> float:
    sb_score = 0
    results = all_players_results[player]
    for result in results:
        match_result = result[1]
        if match_result > 0:
            sb_score += match_result * get_current_score(all_players_results[result[0]])
    return sb_score


def progressive_score(player: int, all_players_results: Dict[int, List[Tuple[int, float]]]) -> float:
    player_results = all_players_results[player]
    scores_after_each_round: List[float] = []
    for i in range(len(player_results)):
        score_after_round = 0
        for j in range(i + 1):
            score_after_round += player_results[j][1]
        scores_after_each_round.append(score_after_round)
    return sum(scores_after_each_round)


def n_wins(player: int, all_players_results: Dict[int, List[Tuple[int, float]]]) -> int:
    player_results = all_players_results[player]
    return sum([res[1] for res in player_results if res[1] == 1])


def update_round_results(all_players_results: Dict[int, List[Tuple[int, float]]],
                         round_results: List[Tuple[int, int, str]]) -> None:
    for result in round_results:
        if result[2] == '0.5-0.5':
            all_players_results[result[0]].append((result[1], 0.5))
            all_players_results[result[1]].append((result[0], 0.5))
        elif result[2] == '1-0':
            all_players_results[result[0]].append((result[1], 1))
            all_players_results[result[1]].append((result[0], 0))
        elif result[2] == '0-1':
            all_players_results[result[0]].append((result[1], 0))
            all_players_results[result[1]].append((result[0], 1))


def rank_all_players(all_players_results: Dict[int, List[Tuple[int, float]]]) -> List[int]:

    def first_tie_breaker(player: int, all_results: Dict[int, List[Tuple[int, float]]]) -> float:
        return get_current_score(all_results[player])

    tie_breakers_in_order = [first_tie_breaker, solkoff, solkoff_minus_1, sonneborn_berger, progressive_score, n_wins]

    return tie_break_group(list(all_players_results.keys()), all_players_results, tie_breakers_in_order)


def generate_random_results(pairings: List[Tuple[int, int]], draw_rate: float = 0.2) -> List[Tuple[int, int, str]]:
    results = []
    for pairing in pairings:
        if random.random() < draw_rate:
            results.append((pairing[0], pairing[1], '0.5-0.5'))
        else:
            result = random.choice(['0-1', '1-0'])
            results.append((pairing[0], pairing[1], result))
    return results


def generate_starting_results(n_players: int) -> Dict[int, List]:
    starting_results = {}
    for i in range(n_players):
        starting_results[i] = []
    return starting_results


def find_previously_downfloated_players(players: List[int], float_record: Dict[str, List[int]]) -> List[int]:
    return [player for player in players if player in float_record['downfloated']]


def choose_player_to_pair(players: List[int], float_record: Dict[str, List[int]],
                          relax_float_protection: bool = False) -> int:
    if relax_float_protection:
        return random.choice(players)
    previously_downfloated = find_previously_downfloated_players(players, float_record)
    if len(previously_downfloated) == 0:
        return random.choice(players)
    else:
        return random.choice(previously_downfloated)


def find_not_previously_upfloated_players(players: List[int], float_record: Dict[str, List[int]]) -> List[int]:
    return [player for player in players if player not in float_record['upfloated']]


def choose_opponent_to_pair(opponents: List[int], float_record: Dict[str, List[int]], downfloat: int,
                            relax_float_protection: bool = False) -> int:
    if downfloat == 0 or relax_float_protection:
        return random.choice(opponents)
    not_previously_upfloated = find_not_previously_upfloated_players(opponents, float_record)
    if len(not_previously_upfloated) == 0:
        return random.choice(opponents)
    else:
        return random.choice(not_previously_upfloated)
