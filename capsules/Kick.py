import math
import random
import numpy as np

class KickCapsule:
    def __init__(self, blackboard):
        self.blackboard = blackboard
        self.kick_power = 0
        self.kick_direction = 0
        self.range = 3
        self.ball_velocity = (0, 0)
        self.friction = 0.98
        self.max_velocity = 10

    def set_kick_power(self, power):
        self.kick_power = power

    def set_kick_direction(self, direction):
        self.kick_direction = direction

    def set_range(self, range):
        self.range = range

    def _calculate_smart_shooting_target(self, x_ball, y_ball, goal_pos):
        goal_width = 10  
        goal_height = 5

        # Get the current ball velocity
        vx, vy = self.ball_velocity
        # Calculate the position of the goalkeeper
        if goal_pos[0] == 100:  # Right goal
            keeper = self.blackboard.team.keeper_b
            keeper_pos = self.blackboard.team.enemies[keeper]
        else:  # Left goal
            keeper = self.blackboard.team.keeper_a
            keeper_pos = self.blackboard.team.players[keeper]

        # Calculate the distance between the ball and the goal
        distance_to_goal = math.sqrt((x_ball - goal_pos[0])**2 + (y_ball - goal_pos[1])**2)

        # Determine the shooting area based on the goalkeeper's position
        keeper_relative_y = (keeper_pos[1] - goal_pos[1]) / goal_height

        if keeper_relative_y < 0.4:  # Goalkeeper is low
            target_y = goal_pos[1] + random.uniform(goal_height * 0.6, goal_height * 0.9)
        elif keeper_relative_y > 0.6:  # Goalkeeper is high
            target_y = goal_pos[1] + random.uniform(goal_height * 0.1, goal_height * 0.4)
        else:  # Goalkeeper is centered
            if random.random() < 0.5:
                target_y = goal_pos[1] + random.uniform(goal_height * 0.7, goal_height * 0.9)
            else:
                target_y = goal_pos[1] + random.uniform(goal_height * 0.1, goal_height * 0.3)

        # Add some randomness to the x-coordinate
        if goal_pos[0] == 100:  # Right goal
            target_x = goal_pos[0] - random.uniform(0, 0.5)
        else:  # Left goal
            target_x = goal_pos[0] + random.uniform(0, 0.5)

        # Adjust target based on current ball velocity
        prediction_time = distance_to_goal / self.max_velocity  # Estimated time for ball to reach goal
        target_x += vx * prediction_time * 0.5  # Adjust less to maintain accuracy
        target_y += vy * prediction_time * 0.5  # Adjust less to maintain accuracy

        # Adjust the shooting power based on the distance and current velocity
        max_distance = 100  # Assuming the field length is 100 units
        min_power = 5
        max_power = self.max_velocity

        # Calculate base power: higher for longer distances, but never below min_power
        base_power = max(min_power, min(max_power, distance_to_goal / max_distance * max_power))

        # Add some randomness to the power
        power_variation = random.uniform(-1, 1)
        shooting_power = min(max_power, base_power + power_variation)

        # Adjust power based on current velocity
        current_speed = math.sqrt(vx**2 + vy**2)
        if current_speed > 0:
            dot_product = (vx * (target_x - x_ball) + vy * (target_y - y_ball)) / (current_speed * distance_to_goal)
            if dot_product > 0:  # Ball is already moving towards the target
                shooting_power *= 0.8  # Reduce power as ball is already moving in right direction
            else:  # Ball is moving away from the target
                shooting_power *= 1.2  # Increase power to overcome opposite momentum
        # For very close shots, ensure a minimum power to prevent weak shots
        if distance_to_goal < 10:
            shooting_power = max(shooting_power, min_power + 2)

        return (target_x, target_y), shooting_power

    def auto_kick(self):
        x_ball, y_ball = self.blackboard.gamestate.ball_position
        
        # Find the nearest player from both teams
        nearest_player, nearest_distance, team = None, float('inf'), None
        for team_id, team_dict in [('a', self.blackboard.team.players), ('b', self.blackboard.team.enemies)]:
            for player, pos in team_dict.items():
                distance = math.sqrt((x_ball - pos[0])**2 + (y_ball - pos[1])**2)
                if distance < nearest_distance:
                    nearest_player = player
                    nearest_distance = distance
                    team = team_id

        if nearest_distance > self.range:
            print(f"No player is close enough to kick the ball.")
            return

        # Determine whether to shoot or pass
        goal_pos = (100,25) if team == 'a' else (0, 25)
        distance_to_goal = math.sqrt((x_ball - goal_pos[0])**2 + (y_ball - goal_pos[1])**2)

        if distance_to_goal < 50:  # If close to goal, shoot
            target, shooting_power = self._calculate_smart_shooting_target(x_ball, y_ball, goal_pos)
            action = "shoot"
        else:  # Otherwise, pass to the nearest teammate (excluding the kicker)
            teammates = {p: pos for p, pos in (self.blackboard.team.players.items() if team == 'a' else self.blackboard.team.enemies.items()) if p != nearest_player}
            if not teammates:
                print(f"No other teammates to pass to.")
                return
            nearest_teammate = min(teammates.items(), key=lambda x: np.linalg.norm(np.array(x[1]) - np.array([x_ball, y_ball])))
            target = nearest_teammate[1]
            shooting_power = min(15, math.sqrt((target[0] - x_ball)**2 + (target[1] - y_ball)**2) * 0.3)
            action = "pass"

        # Calculate kick direction and power
        dx, dy = target[0] - x_ball, target[1] - y_ball
        self.kick_direction = math.degrees(math.atan2(dy, dx))
        self.kick_power = shooting_power
        velocity_scale = 0.2  # Adjust this value to control overall speed (lower = slower)
        max_velocity = 10  # Maximum velocity cap
        velocity_x = min((self.kick_power) * math.cos(math.radians(self.kick_direction)) * velocity_scale, max_velocity)
        velocity_y = min((self.kick_power) * math.sin(math.radians(self.kick_direction)) * velocity_scale, max_velocity)

        # Set ball velocity
        self.ball_velocity = (velocity_x, velocity_y)

        print(f"{'Player' if team == 'a' else 'Enemy'} {nearest_player} decided to {action} the ball.")
        print(f"Kick power: {self.kick_power}, kick direction: {self.kick_direction}")

    def update_ball_position(self):
        x, y = self.blackboard.gamestate.ball_position
        vx, vy = self.ball_velocity
        
        # Update position
        x += vx * 0.1  # Reduced from 1 to 0.1 to slow down movement
        y += vy * 0.1  # Reduced from 1 to 0.1 to slow down movement
        
        # Apply friction
        self.ball_velocity = (self.ball_velocity[0]*self.friction, self.ball_velocity[1]*self.friction)
        
        # Stop the ball if it's moving very slowly
        if abs(self.ball_velocity[0]) < 0.1 and abs(self.ball_velocity[1]) < 0.1:
            self.ball_velocity = [0, 0]
        
        # Update ball position in the blackboard
        self.blackboard.gamestate.ball_position = (x, y)

    def kickable(self):
        x_ball = self.blackboard.gamestate.ball_position[0]
        y_ball = self.blackboard.gamestate.ball_position[1]
        name = None
        distance_to_ball = float("inf")
        for player in self.blackboard.team.players:
            x_player, y_player = self.blackboard.team.players[player]
            distance = math.sqrt((x_ball - x_player)**2 + (y_ball - y_player)**2)
            if distance < distance_to_ball:
                name = player
                distance_to_ball = distance
                return True
        for enemy in self.blackboard.team.enemies:
            x_enemy, y_enemy = self.blackboard.team.enemies[enemy]
            distance = math.sqrt((x_ball - x_enemy)**2 + (y_ball - y_enemy)**2)
            if distance < distance_to_ball:
                name = enemy
                distance_to_ball = distance
                return True
        return False

    def execute_kick(self):
        x_ball, y_ball = self.blackboard.gamestate.ball_position
        nearest_player, nearest_distance, kicking_team = self._find_nearest_player(x_ball, y_ball)

        if nearest_distance > self.range:
            print(f"No player is close enough to kick the ball. Nearest player is {nearest_distance:.2f} units away.")
            return

        if kicking_team == 'enemy':
            self._handle_enemy_possession(nearest_player, x_ball, y_ball)
        else:
            self._perform_kick(nearest_player, x_ball, y_ball)

    def _find_nearest_player(self, x_ball, y_ball):
        nearest_player, nearest_distance, kicking_team = None, float('inf'), None
        
        for team_id, team_dict in [('player', self.blackboard.team.players), ('enemy', self.blackboard.team.enemies)]:
            for player, pos in team_dict.items():
                distance = math.sqrt((x_ball - pos[0])**2 + (y_ball - pos[1])**2)
                if distance < nearest_distance:
                    nearest_player, nearest_distance, kicking_team = player, distance, team_id
        
        return nearest_player, nearest_distance, kicking_team

    def _handle_enemy_possession(self, nearest_enemy, x_ball, y_ball):
        closest_player = min(self.blackboard.team.players.items(), 
                            key=lambda x: math.sqrt((x[1][0] - x_ball)**2 + (x[1][1] - y_ball)**2))
        player_name, player_pos = closest_player
        
        dx, dy = x_ball - player_pos[0], y_ball - player_pos[1]
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > 0:
            move_speed = min(1.0, distance)  # Cap speed at 1.0
            new_x = player_pos[0] + (dx / distance) * move_speed
            new_y = player_pos[1] + (dy / distance) * move_speed
            
            self.blackboard.team.players[player_name] = (new_x, new_y)
            print(f"Player {player_name} is moving towards the ball to challenge {nearest_enemy}.")

    def _perform_kick(self, kicking_player, x_ball, y_ball):
        # Determine if this is a long-range shot
        field_length, field_width = self.blackboard.field_info.get_field_dimensions()
        distance_to_goal = min(x_ball, field_length - x_ball)  # Distance to nearest goal
        is_long_range = distance_to_goal > field_length / 3

        # Increase power for long-range shots
        power_multiplier = 2 if is_long_range else 1.5
        adjusted_power = self.kick_power * power_multiplier

        # Calculate ball movement
        angle_rad = math.radians(self.kick_direction)
        delta_x = adjusted_power * math.cos(angle_rad)
        delta_y = adjusted_power * math.sin(angle_rad)

        # Update ball position
        new_ball_x = x_ball + delta_x
        new_ball_y = y_ball + delta_y

        # Ensure the ball stays within the field boundaries
        new_ball_x = max(0, min(new_ball_x, field_length))
        new_ball_y = max(0, min(new_ball_y, field_width))

        self.blackboard.gamestate.ball_position = (new_ball_x, new_ball_y)

        # Set ball velocity for smoother movement
        velocity_scale = 0.5  # Increase this value for faster ball movement
        self.ball_velocity = (delta_x * velocity_scale, delta_y * velocity_scale)

        # Apply maximum velocity cap
        max_velocity = 15  # Increase this for higher maximum speed
        velocity_magnitude = math.sqrt(self.ball_velocity[0]**2 + self.ball_velocity[1]**2)
        if velocity_magnitude > max_velocity:
            scale_factor = max_velocity / velocity_magnitude
            self.ball_velocity = (self.ball_velocity[0] * scale_factor, self.ball_velocity[1] * scale_factor)

        print(f"Player {kicking_player} kicked the ball!")
        print(f"Kick power: {adjusted_power}, kick direction: {self.kick_direction}, range: {self.range}")
        print(f"Ball position now: ({new_ball_x:.2f}, {new_ball_y:.2f})")
        print(f"Ball velocity: ({self.ball_velocity[0]:.2f}, {self.ball_velocity[1]:.2f})")