import random
import math
import numpy as np

class TeamCapsule:
    def __init__(self, blackboard):
        self.blackboard = blackboard
        self.players = {}
        self.enemies = {}
        self.player_velocities = {}
        self.enemy_velocities = {}
        self.strategy = 'default'
        self.defensive = False
        self.offensive = False
        self.keeper_a = None
        self.keeper_b = None

        self.learning_rate = 0.1
        self.discount_factor = 0.9
        self.epsilon = 0.1
        self.q_table = {}

    def add_player(self, player, x=50, y=25, is_keeper=False):
        if is_keeper:
            self.keeper_a = player
            self.players[player] = (5,25)
        else:
            self.players[player] = (x,y)
            self.player_velocities[player] = (0, 0)

    def add_enemy(self, enemy, x=50, y=25, is_keeper=False):
        if is_keeper:
            self.keeper_b = enemy
            self.enemies[enemy] = (5,25)
        else:
            self.enemies[enemy] = (x,y)
            self.enemy_velocities[enemy] = (0, 0)

    def get_enemy(self, enemy):
        print(self.enemies[enemy])

    def get_player(self, player):
        print(self.players[player])

    def get_all_enemies(self):
        for enemy in self.enemies:
            print(self.enemies[enemy])

    def get_all_players(self):
        for player in self.players:
            print(self.players[player])

    def remove_player(self, player):
        del self.players[player]

    def random_team_positions(self):
        for player in self.players:
            self.players[player] = (random.randint(0, 100), random.randint(0, 50))

    def random_enemy_positions(self):
        for enemy in self.enemies:
            self.enemies[enemy] = (random.randint(0, 100), random.randint(0, 50))

    def random_all_positions(self):
        for player in self.players:
            self.players[player] = (random.randint(0, 100), random.randint(0, 50))
        for enemy in self.enemies:
            self.enemies[enemy] = (random.randint(0, 100), random.randint(0, 50))

    def set_strategy(self, strategy):
        if strategy in ['default', 'offensive', 'defensive']:
            self.strategy = strategy
            if strategy == 'offensive':
                self.offensive = True
                self.defensive = False
            elif strategy == 'defensive':
                self.offensive = False
                self.defensive = True
            elif strategy == 'default':
                self.offensive = False
                self.defensive = False

    def execute_strategy(self):
        ball_position = self.blackboard.gamestate.ball_position
        field_length, field_width = self.blackboard.field_info.get_field_dimensions()
        # Determine which team has possession of the ball
        team_a_possession = self._is_ball_possessed_by_team('a')
        team_b_possession = self._is_ball_possessed_by_team('b')

        # Execute strategy for Team A
        if team_a_possession:
            # self.team_positioning('a')
            self._offensive_play('a', ball_position)
        else:
            # self.team_positioning('a')
            self._defensive_play('a', ball_position)

        # Execute strategy for Team B
        if team_b_possession:
            # self.team_positioning('b')
            self._offensive_play('b', ball_position)
        else:
            # self.team_positioning('b')
            self._defensive_play('b',ball_position)

        # Always position keepers
        self._position_keeper('a', ball_position)
        self._position_keeper('b', ball_position)

    def _calculate_spread_positions(self, ball_position, team_id):
        field_length, field_width = self.blackboard.field_info.get_field_dimensions()
        players = self.players if team_id == 'a' else self.enemies
        num_players = len(players) - 1  # Exclude the keeper
        spread_positions = []

        # Define the radius of the circle around the ball
        radius = 15  # Adjust this value as needed

        # Calculate the center of the spread formation
        if team_id == 'a':
            center_x = min(ball_position[0] + 10, field_length - radius)
        else:
            center_x = max(ball_position[0] - 10, radius)
        center_y = ball_position[1]

        # Calculate positions in a circular formation around the center
        for i in range(num_players):
            angle = 2 * math.pi * i / num_players
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)

            # Ensure the positions are within the field boundaries
            x = max(0, min(x, field_length))
            y = max(0, min(y, field_width))

            spread_positions.append((x, y))

        return spread_positions

    def _avoid_enemies_while_dribbling(self, player_x, player_y, goal_x, goal_y, enemies):
        dribble_distance = 1.0
        avoidance_radius = 5.0  # Radius to consider for enemy avoidance

        # Calculate the direction towards the goal
        dx = goal_x - player_x
        dy = goal_y - player_y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > 0:
            dx /= distance
            dy /= distance

        # Check for nearby enemies
        for enemy, enemy_pos in enemies.items():
            enemy_distance = math.sqrt((enemy_pos[0] - player_x)**2 + (enemy_pos[1] - player_y)**2)
            if enemy_distance < avoidance_radius:
                # Calculate avoidance vector
                avoid_x = player_x - enemy_pos[0]
                avoid_y = player_y - enemy_pos[1]
                avoid_distance = math.sqrt(avoid_x**2 + avoid_y**2)
                if avoid_distance > 0:
                    avoid_x /= avoid_distance
                    avoid_y /= avoid_distance
                    
                    # Blend the goal direction with the avoidance direction
                    dx = (dx + avoid_x) / 2
                    dy = (dy + avoid_y) / 2

        # Normalize the final direction
        final_distance = math.sqrt(dx**2 + dy**2)
        if final_distance > 0:
            dx /= final_distance
            dy /= final_distance

        # Calculate the new ball position
        new_ball_x = player_x + dx * dribble_distance
        new_ball_y = player_y + dy * dribble_distance

        return new_ball_x, new_ball_y

    def _offensive_play(self, team_id, ball_position):
        field_length, field_width = self.blackboard.field_info.get_field_dimensions()
        players = self.players if team_id == 'a' else self.enemies
        enemies = self.enemies if team_id == 'a' else self.players
        goal_x = field_length if team_id == 'a' else 0
        max_speed = 1.0
        dribble_distance = 1.0

        closest_player = min(players.items(), key=lambda x: math.sqrt((x[1][0] - ball_position[0])**2 + (x[1][1] - ball_position[1])**2))

        # Calculate spread positions
        spread_positions = self._calculate_spread_positions(ball_position, team_id)
        spread_index = 0

        for player, pos in players.items():
            if player == (self.keeper_a if team_id == 'a' else self.keeper_b):
                continue

            current_x, current_y = pos

            if player == closest_player[0]:
                # The closest player should dribble the ball towards the goal
                target_x, target_y = self._calculate_safe_dribble_path(current_x, current_y, goal_x, field_width / 2, enemies)
            else:
                # Other players should spread out
                target_x, target_y = spread_positions[spread_index]
                spread_index = (spread_index + 1) % len(spread_positions)

            dx = target_x - current_x
            dy = target_y - current_y
            distance = math.sqrt(dx**2 + dy**2)

            if distance > 0:
                # Normalize direction
                dx /= distance
                dy /= distance

                # Move the player
                speed = min(max_speed, distance)
                new_x = current_x + dx * speed
                new_y = current_y + dy * speed

                # Boundary checks
                new_x = max(0, min(new_x, field_length))
                new_y = max(0, min(new_y, field_width))

                players[player] = (new_x, new_y)

                # Update ball position if this is the dribbling player
                if player == closest_player[0]:
                    new_ball_x, new_ball_y = self._avoid_enemies_while_dribbling(new_x, new_y, goal_x, field_width / 2, enemies)
                    self.blackboard.gamestate.ball_position = (new_ball_x, new_ball_y)

                    # If close to the goal, attempt a shot
                    if (team_id == 'a' and new_x > field_length * 0.75) or (team_id == 'b' and new_x < field_length * 0.25):
                        self._attempt_shot(player, team_id)
        # Encourage passing
        self._consider_passing(team_id, closest_player[0])

    def _calculate_safe_dribble_path(self, start_x, start_y, goal_x, goal_y, enemies):
        # Define the step size for path finding
        step_size = 2.0

        # Calculate the direct path to the goal
        dx = goal_x - start_x
        dy = goal_y - start_y
        distance = math.sqrt(dx**2 + dy**2)

        if distance == 0:
            return start_x, start_y

        # Normalize the direction
        dx /= distance
        dy /= distance

        # Initialize the best path
        best_x, best_y = start_x + dx * step_size, start_y + dy * step_size

        # Check for nearby enemies and adjust the path
        for _, enemy_pos in enemies.items():
            enemy_distance = math.sqrt((enemy_pos[0] - best_x)**2 + (enemy_pos[1] - best_y)**2)
            if enemy_distance < 5:  # If an enemy is too close
                # Try to move perpendicular to the enemy
                perp_dx, perp_dy = -dy, dx  # Perpendicular direction

                # Check both perpendicular directions
                for direction in [1, -1]:
                    new_x = best_x + direction * perp_dx * step_size
                    new_y = best_y + direction * perp_dy * step_size

                    # Check if this new position is better (farther from enemies)
                    if all(math.sqrt((e[0] - new_x)**2 + (e[1] - new_y)**2) > enemy_distance for e in enemies.values()):
                        best_x, best_y = new_x, new_y
                        break

        return best_x, best_y

    def _consider_passing(self, team_id, ball_carrier):
        players = self.players if team_id == 'a' else self.enemies
        ball_pos = self.blackboard.gamestate.ball_position
        
        best_pass_target = None
        best_pass_score = -float('inf')
        
        for player, pos in players.items():
            if player == ball_carrier or player == (self.keeper_a if team_id == 'a' else self.keeper_b):
                continue
            
            # Calculate a pass score based on distance to goal and to other players
            distance_to_ball = math.sqrt((pos[0] - ball_pos[0])**2 + (pos[1] - ball_pos[1])**2)
            distance_to_goal = math.sqrt((pos[0] - (self.blackboard.field_info.field_length if team_id == 'a' else 0))**2 + (pos[1] - self.blackboard.field_info.field_width/2)**2)
            
            pass_score = -distance_to_goal - 0.5 * distance_to_ball
            
            if pass_score > best_pass_score:
                best_pass_score = pass_score
                best_pass_target = player
        
        # If a good pass target is found, pass the ball
        if best_pass_target and best_pass_score > -50:  # You may need to adjust this threshold
            self.blackboard.kick.auto_kick()  # Adjust kick strength as needed

    def _find_best_path(self, start_x, start_y, goal_x, goal_y, defenders):
        # Basic avoidance technique
        best_x, best_y = goal_x, goal_y
        for _, def_pos in defenders.items():
            if abs(def_pos[0] - start_x) < 10 and abs(def_pos[1] - start_y) < 10:
                if start_y < def_pos[1]:
                    best_y = max(0, best_y - 5)
                else:
                    best_y = min(self.blackboard.field_info.get_field_dimensions()[1], best_y + 5)
        return best_x, best_y

    def _find_supporting_position(self, current_x, current_y, ball_position, defenders):
        # Implement logic to find a good supporting position
        # For now, we'll just try to stay open for a pass
        target_x = (ball_position[0] + current_x) / 2
        target_y = ball_position[1]
        for _, def_pos in defenders.items():
            if abs(def_pos[0] - target_x) < 5 and abs(def_pos[1] - target_y) < 5:
                target_y = def_pos[1] + 10 if current_y > def_pos[1] else def_pos[1] - 10
        return target_x, target_y

    def _has_clear_shot(self, x, y, goal_x, goal_y, defenders):
        # Check if there's a clear path to the goal
        for _, def_pos in defenders.items():
            if abs(def_pos[1] - y) < 5 and ((x < def_pos[0] < goal_x) or (goal_x < def_pos[0] < x)):
                return False
        return True

    def _defensive_play(self, team_id, ball_position):
        field_length, field_width = self.blackboard.field_info.get_field_dimensions()
        defenders = self.players if team_id == 'a' else self.enemies
        attackers = self.enemies if team_id == 'a' else self.players
        goal_x = 0 if team_id == 'a' else field_length
        max_speed = 1.0

        # Convert ball_position to float if it's stored as strings
        ball_x, ball_y = float(ball_position[0]), float(ball_position[1])

        # Find the closest defender to the ball
        closest_defender = min(defenders.items(), key=lambda x: math.sqrt((x[1][0] - ball_x)**2 + (x[1][1] - ball_y)**2))
        closest_defender_name, closest_defender_pos = closest_defender

        # Aggressive ball recovery for the closest defender
        if closest_defender_name != (self.keeper_a if team_id == 'a' else self.keeper_b):
            dx = ball_x - closest_defender_pos[0]
            dy = ball_y - closest_defender_pos[1]
            distance = math.sqrt(dx**2 + dy**2)

            if distance > 0:
                # Normalize direction
                dx /= distance
                dy /= distance

                # Move the defender aggressively towards the ball
                speed = min(max_speed * 1.2, distance)  # Slightly faster for aggressive recovery
                new_x = closest_defender_pos[0] + dx * speed
                new_y = closest_defender_pos[1] + dy * speed

                # Boundary checks
                new_x = max(0, min(new_x, field_length))
                new_y = max(0, min(new_y, field_width))

                defenders[closest_defender_name] = (new_x, new_y)

                # Attempt interception if close to the ball
                if distance < 1:
                    self._attempt_interception(closest_defender_name, team_id)

        # Sort attackers by their distance to our goal
        sorted_attackers = sorted(attackers.items(), key=lambda x: abs(x[1][0] - goal_x))

        # Assign remaining defenders to mark attackers or cover spaces
        for defender, def_pos in defenders.items():
            if defender == closest_defender_name or defender == (self.keeper_a if team_id == 'a' else self.keeper_b):
                continue

            if sorted_attackers:
                attacker, att_pos = sorted_attackers.pop(0)
                
                # Calculate position to mark the attacker
                mark_x = (att_pos[0] + goal_x) / 2  # Position between attacker and our goal
                mark_y = att_pos[1]

                # Move towards the marking position
                dx = mark_x - def_pos[0]
                dy = mark_y - def_pos[1]
            else:
                # If no attackers left to mark, cover spaces
                cover_x = (def_pos[0] + goal_x) / 2  # Move towards our goal
                cover_y = def_pos[1]  # Maintain lateral position
                dx = cover_x - def_pos[0]
                dy = cover_y - def_pos[1]

            distance = math.sqrt(dx**2 + dy**2)

            if distance > 0:
                # Normalize direction
                dx /= distance
                dy /= distance

                # Move the defender
                speed = min(max_speed, distance)
                new_x = def_pos[0] + dx * speed
                new_y = def_pos[1] + dy * speed

                # Boundary checks
                new_x = max(0, min(new_x, field_length))
                new_y = max(0, min(new_y, field_width))

                defenders[defender] = (new_x, new_y)

    def _deep_line_defense(self, defenders, goal_x, field_width, max_speed):
        defense_line_x = goal_x + 20 if goal_x == 0 else goal_x - 20
        for defender, pos in defenders.items():
            if defender == (self.keeper_a if goal_x == 0 else self.keeper_b):
                continue
            target_y = (field_width / (len(defenders) - 1)) * list(defenders.keys()).index(defender)
            dx = defense_line_x - pos[0]
            dy = target_y - pos[1]
            distance = math.sqrt(dx**2 + dy**2)
            if distance > 0:
                speed = min(max_speed, distance)
                new_x = pos[0] + (dx / distance) * speed
                new_y = pos[1] + (dy / distance) * speed
                defenders[defender] = (new_x, new_y)

    def _man_marking_defense(self, defenders, attackers, goal_x, field_length, field_width, max_speed):
        sorted_attackers = sorted(attackers.items(), key=lambda x: abs(x[1][0] - goal_x))
        for i, (defender, def_pos) in enumerate(defenders.items()):
            if defender == (self.keeper_a if goal_x == 0 else self.keeper_b):
                continue
            if i < len(sorted_attackers):
                attacker, att_pos = sorted_attackers[i]
                mark_x = (att_pos[0] + goal_x) / 2
                mark_y = att_pos[1]
                dx = mark_x - def_pos[0]
                dy = mark_y - def_pos[1]
                distance = math.sqrt(dx**2 + dy**2)
                if distance > 0:
                    speed = min(max_speed, distance)
                    new_x = def_pos[0] + (dx / distance) * speed
                    new_y = def_pos[1] + (dy / distance) * speed
                    new_x = max(0, min(new_x, field_length))
                    new_y = max(0, min(new_y, field_width))
                    defenders[defender] = (new_x, new_y)

    def _ball_avoidance_defense(self, defenders, ball_position, goal_x, field_length, field_width, max_speed):
        for defender, pos in defenders.items():
            if defender == (self.keeper_a if goal_x == 0 else self.keeper_b):
                continue
            dx = goal_x - pos[0]
            dy = (field_width / 2) - pos[1]
            ball_dx = ball_position[0] - pos[0]
            ball_dy = ball_position[1] - pos[1]
            ball_distance = math.sqrt(ball_dx**2 + ball_dy**2)
            
            if ball_distance < 10:  # If the ball is close, move away from it
                dx -= ball_dx
                dy -= ball_dy
            
            distance = math.sqrt(dx**2 + dy**2)
            if distance > 0:
                speed = min(max_speed, distance)
                new_x = pos[0] + (dx / distance) * speed
                new_y = pos[1] + (dy / distance) * speed
                new_x = max(0, min(new_x, field_length))
                new_y = max(0, min(new_y, field_width))
                defenders[defender] = (new_x, new_y)

    def _attempt_interception(self, player, team_id):
        self.blackboard.kick.auto_kick()

    def get_state(self):
        ball_post = self.blackboard.gamestate.ball_position
        return (round(ball_post[0]), round(ball_post[1]), self.strategy)

    def choose_action(self, state):
        if state not in self.q_table:
            self.q_table[state] = {'spread':0, 'cluster':0, 'man_mark':0}

        if random.random() < self.epsilon:
            return random.choice(['spread', 'cluster', 'man_mark'])
        else:
            return max(self.q_table[state], key=self.q_table[state].get)
        
    def update_q_table(self, state, action, reward, next_state):
        if next_state not in self.q_table:
            self.q_table[next_state] = {'spread':0, 'cluster':0, 'man_mark':0}

        current_q = self.q_table[state][action]
        max_next_q = max(self.q_table[next_state].values())
        new_q = current_q + self.learning_rate * (reward + self.discount_factor * max_next_q - current_q)
        self.q_table[state][action] = new_q

    def team_positioning(self, team_id):
        state = self.get_state()
        action = self.choose_action(state)
        ball_position = self.blackboard.gamestate.ball_position

        if action =='spread':
            print(f'Team {team_id}: Spreading formation')
            self._spread_formation(ball_position, team_id)
        elif action == 'cluster':
            print(f'Team {team_id}: Clustering formation')
            self._cluster_formation(ball_position, team_id)
        elif action =='man_mark':
            print(f'Team {team_id}:Man-mark formation')
            self._man_mark_formation(ball_position, team_id)

        reward = self._calculate_reward(action, team_id)
        next_state = self.get_state()
        self.update_q_table(state, action, reward, next_state)

    def _spread_formation(self, ball_position, team_id):
        field_length, field_width = self.blackboard.field_info.get_field_dimensions()
        max_speed = 1.0  # Maximum speed a player can move in one step

        if team_id == 'a':
            players = self.players
            keeper = self.keeper_a
            direction = 1
        else:
            players = self.enemies
            keeper = self.keeper_b
            direction = -1

        for i, (player, pos) in enumerate(players.items()):
            if player == keeper:
                continue
            angle = 2 * np.pi * i / len(players)
            radius = 5
            target_x = ball_position[0] + radius * np.cos(angle)
            target_y = ball_position[1] + radius * np.sin(angle)
            current_x, current_y = pos
            
            dx = target_x - current_x
            dy = target_y - current_y
            distance = np.sqrt(dx**2 + dy**2)
            
            if distance > 0:
                # Calculate direction
                direction_x = dx / distance
                direction_y = dy / distance
                
                # Move towards the target, but not more than max_speed
                move_distance = min(max_speed, distance)
                new_x = current_x + direction_x * move_distance
                new_y = current_y + direction_y * move_distance

                # Boundary checks
                new_x = max(0, min(new_x, field_length))
                new_y = max(0, min(new_y, field_width))
                
                # Update position
                players[player] = (new_x, new_y)

        self._position_keeper(team_id, ball_position)
    def _position_keeper(self, team_id, ball_position):
        field_length, field_width = self.blackboard.field_info.get_field_dimensions()
        max_speed = 1.0  # Maximum speed the keeper can move in one step

        if team_id == 'a':
            keeper = self.keeper_a
            players = self.players
            goal_x = 0
        else:
            keeper = self.keeper_b
            players = self.enemies
            goal_x = field_length

        keeper_x, keeper_y = players[keeper]
        
        # Calculate target position (always on the goal line)
        target_y = min(max(ball_position[1], field_width * 0.3), field_width * 0.7)
        
        # Move towards the target
        dy = target_y - keeper_y
        distance = abs(dy)
        
        if distance > 0:
            direction_y = dy / distance
            move_distance = min(max_speed, distance)
            new_y = keeper_y + direction_y * move_distance

            # Update position (x remains constant on the goal line)
            players[keeper] = (goal_x, new_y)

    def _dribble_ball(self, player, ball_position, team_id):
        field_length, field_width = self.blackboard.field_info.get_field_dimensions()
        max_speed = 1.0  # Maximum speed a player can move in one step

        if team_id == 'a':
            players = self.players
            goal_x = field_length
            opponents = self.enemies
        else:
            players = self.enemies
            goal_x = 0
            opponents = self.players

        current_x, current_y = players[player]

        # Calculate direction to the opponent's goal
        dx = goal_x - current_x
        dy = (field_width / 2) - current_y
        distance_to_goal = math.sqrt(dx**2 + dy**2)

        # Check for nearby opponents
        nearest_opponent_distance = float('inf')
        for opponent in opponents.values():
            dist = math.sqrt((opponent[0] - current_x)**2 + (opponent[1] - current_y)**2)
            if dist < nearest_opponent_distance:
                nearest_opponent_distance = dist

        # Check for passing opportunities
        best_passing_option = self._find_best_passing_option(player, team_id)

        # Decision making
        if distance_to_goal < 20:  # Close to goal
            self._attempt_shot(player, team_id)
        elif nearest_opponent_distance < 5 and best_passing_option:
            # If opponent is close and we have a good passing option, pass the ball
            self._pass_ball(player, best_passing_option, team_id)
        else:
            # Continue dribbling towards the goal
            self._continue_dribble(player, dx, dy, distance_to_goal, field_length, field_width)

        # Update ball position
        self.blackboard.gamestate.ball_position = players[player]

    def _find_best_passing_option(self, player, team_id):
        field_length = self.blackboard.field_info.get_field_dimensions()[0]
        players = self.players if team_id == 'a' else self.enemies
        current_x, current_y = players[player]
        goal_x = field_length if team_id == 'a' else 0

        best_passing_option = None
        best_passing_score = float('-inf')

        for teammate, pos in players.items():
            if teammate != player:
                pass_dx = pos[0] - current_x
                pass_dy = pos[1] - current_y
                pass_distance = math.sqrt(pass_dx**2 + pass_dy**2)

                # Calculate a score based on teammate's position and proximity to goal
                teammate_to_goal = abs(goal_x - pos[0])
                passing_score = (field_length - teammate_to_goal) - pass_distance

                if passing_score > best_passing_score:
                    best_passing_score = passing_score
                    best_passing_option = teammate

        return best_passing_option

    def _pass_ball(self, player, target_player, team_id):
        players = self.players if team_id == 'a' else self.enemies
        current_x, current_y = players[player]
        target_x, target_y = players[target_player]

        dx = target_x - current_x
        dy = target_y - current_y
        distance = math.sqrt(dx**2 + dy**2)

        # Set kick parameters
        self.blackboard.kick.set_kick_power(min(10, distance * 0.3))  # Adjust power based on distance
        self.blackboard.kick.set_kick_direction(math.degrees(math.atan2(dy, dx)))

        # Execute the kick
        self.blackboard.kick.execute_kick()

    def _continue_dribble(self, player, dx, dy, distance, field_length, field_width):
        players = self.players if player in self.players else self.enemies
        current_x, current_y = players[player]

        if distance > 0:
            direction_x = dx / distance
            direction_y = dy / distance

            move_distance = min(1.0, distance)  # Max speed of 1.0
            new_x = current_x + direction_x * move_distance
            new_y = current_y + direction_y * move_distance

            # Boundary checks
            new_x = max(0, min(new_x, field_length))
            new_y = max(0, min(new_y, field_width))

            # Update player position
            players[player] = (new_x, new_y)

    def _attempt_shot(self, player, team_id):
        field_length, field_width = self.blackboard.field_info.get_field_dimensions()
        players = self.players if team_id == 'a' else self.enemies
        goal_x = field_length if team_id == 'a' else 0
        current_x, current_y = players[player]

        # Calculate direction to the goal
        dx = goal_x - current_x
        dy = (field_width / 2) - current_y
        distance_to_goal = math.sqrt(dx**2 + dy**2)

        # Get goalkeeper position
        keeper = self.keeper_b if team_id == 'a' else self.keeper_a
        keeper_x, keeper_y = self.enemies[keeper] if team_id == 'a' else self.players[keeper]

        # Determine the best spot to aim (away from the goalkeeper)
        if keeper_y < field_width / 2:
            target_y = field_width * 0.5  # Aim high
        else:
            target_y = field_width * 0.3  # Aim low

        # Calculate shot direction
        shot_dx = goal_x - current_x
        shot_dy = target_y - current_y
        shot_distance = math.sqrt(shot_dx**2 + shot_dy**2)

        # Set kick parameters
        shot_power = min(20, distance_to_goal * 0.5+2)  # Adjust power based on distance
        shot_direction = math.degrees(math.atan2(shot_dy, shot_dx))

        # Calculate velocity components
        velocity_x = shot_power * math.cos(math.radians(shot_direction))
        velocity_y = shot_power * math.sin(math.radians(shot_direction))

        # Set the ball's initial position and velocity
        self.blackboard.gamestate.ball_position = (current_x+2, current_y+2)
        self.blackboard.gamestate.ball_velocity = (min(velocity_x,25), min(velocity_y,25))

        # Execute the kick
        self.blackboard.kick.set_kick_power(shot_power)
        self.blackboard.kick.set_kick_direction(shot_direction)
        self.blackboard.kick.execute_kick()

        print(f"Player {player} from team {team_id} attempts a shot!")
        print(f"Ball initial position: {self.blackboard.gamestate.ball_position}")
        print(f"Ball velocity: {self.blackboard.gamestate.ball_velocity}")
    
    def _cluster_formation(self, ball_position, team_id):
        field_length, field_width = self.blackboard.field_info.get_field_dimensions()
        max_speed = 1.0  # Maximum speed a player can move in one step

        if team_id == 'a':
            players = self.players
            keeper = self.keeper_a
        else:
            players = self.enemies
            keeper = self.keeper_b

        for player, pos in players.items():
            if player == keeper:
                continue
            current_x, current_y = pos
            dx = ball_position[0] - current_x
            dy = ball_position[1] - current_y
            distance = np.sqrt(dx**2 + dy**2)
            
            if distance > 10:
                # Calculate direction
                direction_x = dx / distance
                direction_y = dy / distance
                
                # Move towards the ball, but not more than max_speed
                move_distance = min(max_speed, distance - 10)
                new_x = current_x + direction_x * move_distance
                new_y = current_y + direction_y * move_distance

                # Boundary checks
                new_x = max(0, min(new_x, field_length))
                new_y = max(0, min(new_y, field_width))
                
                # Update position
                players[player] = (new_x, new_y)

        self._position_keeper(team_id, ball_position)

    def _man_mark_formation(self, ball_position, team_id):
        field_length, field_width = self.blackboard.field_info.get_field_dimensions()
        max_speed = 1.0  # Maximum speed a player can move in one step
        buffer_distance = 3  # Buffer distance to reduce stuttering

        if team_id == 'a':
            players = self.players
            keeper = self.keeper_a
            opponents = self.enemies
        else:
            players = self.enemies
            keeper = self.keeper_b
            opponents = self.players

        # Find the opponent closest to the ball (assumed to be in possession)
        ball_carrier = min(opponents.items(), key=lambda x: ((x[1][0] - ball_position[0])**2 + (x[1][1] - ball_position[1])**2))
        
        # Sort opponents by their distance to the ball, with the ball carrier first
        sorted_opponents = sorted(
            opponents.items(),
            key=lambda x: (x[0] != ball_carrier[0], (x[1][0] - ball_position[0])**2 + (x[1][1] - ball_position[1])**2)
        )

        # Sort our players by their x-coordinate (reversed for team B)
        sorted_players = sorted(players.items(), key=lambda x: x[1][0], reverse=(team_id == 'b'))

        # Remove the keeper from the list of players to assign
        sorted_players = [player for player in sorted_players if player[0] != keeper]

        # Assign players to mark opponents
        for (player, player_pos), (opponent, opponent_pos) in zip(sorted_players, sorted_opponents):
            current_x, current_y = player_pos
            target_x, target_y = opponent_pos

            # Calculate distance to the assigned opponent
            dx = target_x - current_x
            dy = target_y - current_y
            distance = math.sqrt(dx**2 + dy**2)

            if distance > buffer_distance:  # Only move if the player is more than buffer_distance away from the target
                # Calculate direction
                direction_x = dx / distance
                direction_y = dy / distance

                # Move towards the opponent, but not more than max_speed
                move_distance = min(max_speed, (distance - buffer_distance) * 0.5)  # Smooth out movement
                new_x = current_x + direction_x * move_distance
                new_y = current_y + direction_y * move_distance

                # Boundary checks
                new_x = max(0, min(new_x, field_length))
                new_y = max(0, min(new_y, field_width))

                # Update position
                players[player] = (new_x, new_y)

        # Position the keeper
        self._position_keeper(team_id, ball_position)

        # If we have extra players, make them cluster around the ball
        if len(sorted_players) > len(sorted_opponents):
            extra_players = sorted_players[len(sorted_opponents):]
            for player, player_pos in extra_players:
                current_x, current_y = player_pos
                dx = ball_position[0] - current_x
                dy = ball_position[1] - current_y
                distance = math.sqrt(dx**2 + dy**2)

                if distance > 5:  # Only move if the player is more than 5 units away from the ball
                    direction_x = dx / distance
                    direction_y = dy / distance

                    move_distance = min(max_speed, (distance - 5) * 0.5)  # Smooth out movement
                    new_x = current_x + direction_x * move_distance
                    new_y = current_y + direction_y * move_distance

                    # Boundary checks
                    new_x = max(0, min(new_x, field_length))
                    new_y = max(0, min(new_y, field_width))

                    # Update position
                    players[player] = (new_x, new_y)

        # If we have extra players, make them cluster around the ball
        if len(sorted_players) > len(sorted_opponents):
            extra_players = sorted_players[len(sorted_opponents):]
            for player, player_pos in extra_players:
                current_x, current_y = player_pos
                dx = ball_position[0] - current_x
                dy = ball_position[1] - current_y
                distance = math.sqrt(dx**2 + dy**2)

                if distance > 5:  # Only move if the player is more than 5 units away from the ball
                    direction_x = dx / distance
                    direction_y = dy / distance

                    move_distance = min(max_speed, distance - 5)
                    new_x = current_x + direction_x * move_distance
                    new_y = current_y + direction_y * move_distance

                    # Boundary checks
                    new_x = max(0, min(new_x, field_length))
                    new_y = max(0, min(new_y, field_width))

                    # Update position
                    players[player] = (new_x, new_y)

    def _calculate_reward(self, action, team_id):
        reward = 0
        ball_position = self.blackboard.gamestate.ball_position
        if self._is_ball_possessed_by_team(team_id):
            reward += 10
        else:
            reward -= 5

        if team_id == 'a':
            if ball_position[0] > 75:
                reward += 5
            elif ball_position[0] < 25:
                reward -= 5
        elif team_id == 'b':
            if ball_position[0] < 25:
                reward += 5
            elif ball_position[0] > 75:
                reward -= 5

        if self.strategy == 'offensive':
            if action == 'spread':
                reward += 3
            elif action == 'cluster':
                reward += 1
        elif self.strategy == 'defensive':
            if action == 'man_mark':
                reward += 3
            elif action == 'cluster':
                reward += 1

        avg_distance_to_ball = self._average_distance_to_ball(team_id)
        if avg_distance_to_ball < 20:
            reward += 5
        elif avg_distance_to_ball > 40:
            reward -= 5

        if self._players_too_close(team_id):
            reward -= 3

        if action == 'man_mark':
            reward += self._calculate_marking_effectiveness(team_id)

        score_difference = self._get_score_difference(team_id)
        reward += score_difference*2

        keeper_reward = self._calculate_keeper_reward(team_id)
        reward += keeper_reward 

        return reward
    
    def _calculate_keeper_reward(self, team_id):
        reward = 0
        ball_position = self.blackboard.gamestate.ball_position

        if team_id == 'a':
            keeper_pos = self.players[self.keeper_a]
            if ball_position[0]<10: # Ball is close to the keeper
                distance_to_ball = np.linalg.norm(np.array(keeper_pos) - np.array(ball_position))
                if distance_to_ball < 5:
                    reward += 10 # Reward keeper for keeping the ball close to the keeper
                else:
                    reward -= 5 # Penalize keeper for not keeping the ball close to the keeper
        elif team_id == 'b':
            keeper_pos = self.enemies[self.keeper_b]
            if ball_position[0]>90: # Ball is close to the keeper
                distance_to_ball = np.linalg.norm(np.array(keeper_pos) - np.array(ball_position))
                if distance_to_ball < 5:
                    reward += 10 # Reward keeper for keeping the ball close to the keeper
                else:
                    reward -= 5 # Penalize keeper for not keeping the ball close to the keeper
        return reward

    def _is_ball_possessed_by_team(self, team_id):
        ball_position = self.blackboard.gamestate.ball_position
        if team_id == 'a': 
            for player_pos in self.players.values():
                if np.linalg.norm(np.array(player_pos) - np.array(ball_position)) < self.blackboard.kick.range:
                    return True
        elif team_id == 'b':
            for enemy_pos in self.enemies.values():
                if np.linalg.norm(np.array(enemy_pos) - np.array(ball_position)) < self.blackboard.kick.range:
                    return True
        return False
    
    def _average_distance_to_ball(self, team_id):
        ball_position = self.blackboard.gamestate.ball_position
        if team_id == 'a':
            distances = [np.linalg.norm(np.array(player_pos) - np.array(ball_position)) for player_pos in self.players.values()]
        elif team_id == 'b':
            distances = [np.linalg.norm(np.array(enemy_pos) - np.array(ball_position)) for enemy_pos in self.enemies.values()]
        return np.mean(distances)
    
    def _players_too_close(self, team_id):
        if team_id == 'a':
            positions = list(self.players.values())
        elif team_id == 'b':
            positions = list(self.enemies.values())
        for i in range(len(positions)):
            for j in range(i+1, len(positions)):
                if np.linalg.norm(np.array(positions[i]) - np.array(positions[j])) < 5:
                    return True
        return False
    
    def _calculate_marking_effectiveness(self, team_id):
        effectiveness = 0
        if team_id == 'a':
            for player_pos in self.players.values():
                if np.linalg.norm(np.array(player_pos) - np.array(self.blackboard.gamestate.ball_position)) < 5:
                    effectiveness += 1
        elif team_id == 'b':
            for enemy_pos in self.enemies.values():
                if np.linalg.norm(np.array(enemy_pos) - np.array(self.blackboard.gamestate.ball_position)) < 5:
                    effectiveness += 1     
        return effectiveness
    
    def _get_score_difference(self, team_id):
        if team_id == 'a':
            own_score = self.blackboard.gamestate.get_score('a')
            opp_score = self.blackboard.gamestate.get_score('b')
        elif team_id == 'b':
            own_score = self.blackboard.gamestate.get_score('b')
            opp_score = self.blackboard.gamestate.get_score('a')
        return own_score - opp_score
        

    
