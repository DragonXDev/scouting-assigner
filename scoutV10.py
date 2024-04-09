import random
import itertools
import requests

def distribute_teams(matches, users):
    # Extract team data and create team pool
    all_teams = set(itertools.chain.from_iterable(match['alliances']['blue']['team_keys'] + match['alliances']['red']['team_keys'] for match in matches if match['comp_level'] == 'qm'))
    team_pool = list(all_teams)

    # Determine distribution of teams among users
    num_teams = len(team_pool)
    num_users = len(users)
    teams_per_user = [num_teams // num_users] * num_users
    for i in range(num_teams % num_users):
        teams_per_user[i] += 1

    # Create conflict graph (teams that play against each other)
    conflict_graph = {team: set() for team in team_pool}
    for match in matches:
        if match['comp_level'] == 'qm':
            blue_teams = match['alliances']['blue']['team_keys']
            red_teams = match['alliances']['red']['team_keys']
            for blue_team in blue_teams:
                conflict_graph[blue_team].update(red_teams)
            for red_team in red_teams:
                conflict_graph[red_team].update(blue_teams)

    # Assign teams to users
    assignments = {user: [] for user in users}
    while team_pool:
        for user, team_count in zip(users, teams_per_user):
            if team_count == 0:
                continue

            # Find valid teams (no conflicts)
            valid_teams = [team for team in team_pool if not conflict_graph[team].intersection(assignments[user])]

            if valid_teams:
                # Prioritize "chunked" schedules if possible
                team_match_numbers = {team: [match['match_number'] for match in matches if team in match['alliances']['blue']['team_keys'] + match['alliances']['red']['team_keys']] for team in valid_teams}
                team_scores = {team: sum(abs(m1 - m2) for m1, m2 in zip(numbers, numbers[1:])) for team, numbers in team_match_numbers.items()}
                best_team = min(team_scores, key=team_scores.get) 
            else:
                # If no perfectly "chunked" team, pick any valid team
                print("TEAM POOL: ", team_pool)
                if not team_pool:
                    break
                best_team = random.choice(team_pool)  
                

            assignments[user].append(best_team)
            team_pool.remove(best_team)
            team_count -= 1

    return assignments

# Generate random user names
users = ['User_' + str(i) for i in range(30)] 

event_key = '2024casj'  # Replace with actual event key
api_key = 'U3magfm5xr9Sc7mzWuxKfDJYYD1jMtUqWiVuNbMmxdDURf7M2vHbSpxkuMjYnn4H'  # Replace with actual API key

url = f'https://www.thebluealliance.com/api/v3/event/{event_key}/matches/simple'
headers = {'X-TBA-Auth-Key': api_key}
response = requests.get(url, headers=headers)
matches = response.json()

assignments = distribute_teams(matches, users)

if assignments:
    # Create a dictionary to store matches and counts for each user
    user_matches = {user: [] for user in users}
    user_match_counts = {user: 0 for user in users}

    for match in matches:
        if match['comp_level'] == 'qm':
            teams_involved = set(itertools.chain.from_iterable(match['alliances'].values()))
            for user, assigned_teams in assignments.items():
                for alliance in ['blue', 'red']:
                    assigned_teams_in_alliance = set(assigned_teams).intersection(match['alliances'][alliance]['team_keys'])
                    if len(assigned_teams_in_alliance) == 1:
                        user_matches[user].append(match['match_number'])
                        user_match_counts[user] += 1
                    elif len(assigned_teams_in_alliance) > 1:
                        # Conflict resolution with duplicate check
                        potential_users = [(user2, count) for user2, count in user_match_counts.items() 
                                           if user2 != user and not set(assignments[user2]).intersection(teams_involved) 
                                           and match['match_number'] not in user_matches[user2]]
                        if potential_users:
                            least_busy_user = min(potential_users, key=lambda item: item[1])[0]
                            user_matches[least_busy_user].append(match['match_number'])
                            user_match_counts[least_busy_user] += 1
                        else:
                            print(f"Unresolved conflict in match {match['match_number']}")

    # Identify matches with duplicates and put them in a separate list
    duplicate_matches = []
    for user, matches in user_matches.items():
        seen_matches = set()
        unique_matches = [] 
        for match in matches:
            if match in seen_matches:
                # duplicate_matches.append(f"{match} + {assignments[user][0]}") 
                duplicate_matches.append(f"{match} + {assignments[user][0]}") 
            else:
                seen_matches.add(match)
                unique_matches.append(match)
        user_matches[user] = unique_matches 

    # Assign duplicate matches to users without conflicts
    while duplicate_matches:
        match_str = duplicate_matches.pop() 
        match_number = match_str.split(" + ")[0] 

        for user, user_match_list in user_matches.items():
            if match_number not in user_match_list: 
                # user_matches[user].append(int(match_str.split(" + ")[1][3:]))
                user_matches[user].append((match_str))
                break
        else:
            print(f"Could not assign duplicate match: {match_str}")

    # Print user assignments and their observing schedule
    for user, teams in assignments.items():
        print(f"{user}: {teams}")
        print(f"  Observing Matches: {(user_matches[user])}, DUPLICATES: {len(user_matches[user]) != len(set(user_matches[user]))}") 

else:
    print("No valid team distribution found.")