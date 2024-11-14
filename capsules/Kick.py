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
        goal_width = 10  # Assuming the goal is 10 units wide
        goal_height = 5  # Assuming the goal is 5 units high

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
        if keeper_pos[1] < goal_pos[1]:  # Goalkeeper is below the center
            target_y = goal_pos[1] + random.uniform(0, goal_height/2)
        else:  # Goalkeeper is above the center
            target_y = goal_pos[1] - random.uniform(0, goal_height/2)

        # Add some randomness to the x-coordinate
        if goal_pos[0] == 100:  # Right goal
            target_x = goal_pos[0] - random.uniform(0, 1)
        else:  # Left goal
            target_x = goal_pos[0] + random.uniform(0, 1)

        # Adjust the shooting power based on the distance
        shooting_power = min(self.max_velocity, distance_to_goal * 0.2)

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

        # Set ball velocity
        self.ball_velocity = (
            self.kick_power * math.cos(math.radians(self.kick_direction)),
            self.kick_power * math.sin(math.radians(self.kick_direction))
        )

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
        x_ball = self.blackboard.gamestate.ball_position[0]
        y_ball = self.blackboard.gamestate.ball_position[1]
        distance_to_ball = float("inf")
        name = None
        for player in self.blackboard.team.players:
            x_player, y_player = self.blackboard.team.players[player]
            distance = math.sqrt((x_ball - x_player)**2 + (y_ball - y_player)**2)
            if distance < distance_to_ball:
                distance_to_ball = distance
                name = player
        for enemy in self.blackboard.team.enemies:
            x_enemy, y_enemy = self.blackboard.team.enemies[enemy]
            distance = math.sqrt((x_ball - x_enemy)**2 + (y_ball - y_enemy)**2)
            if distance < distance_to_ball:
                distance_to_ball = distance
                name = enemy
        if name in self.blackboard.team.enemies:
             # Move towards the ball instead of just printing a message
            closest_player = min(self.blackboard.team.players.items(), key=lambda x: math.sqrt((x[1][0] - x_ball)**2 + (x[1][1] - y_ball)**2))
            player_name, player_pos = closest_player
            
            # Calculate direction towards the ball
            dx = x_ball - player_pos[0]
            dy = y_ball - player_pos[1]
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance > 0:
                # Normalize direction and move towards the ball
                move_speed = min(1.0, distance)  # Cap speed at 1.0
                new_x = player_pos[0] + (dx / distance) * move_speed
                new_y = player_pos[1] + (dy / distance) * move_speed
                
                # Update player position
                self.blackboard.team.players[player_name] = (new_x, new_y)
        elif distance_to_ball <= self.range:
            delta_x = self.kick_power * math.cos(math.radians(self.kick_direction))
            delta_y = self.kick_power * math.sin(math.radians(self.kick_direction))
            self.blackboard.gamestate.ball_position = (delta_x+self.blackboard.gamestate.ball_position[0], delta_y+self.blackboard.gamestate.ball_position[1])
            print(f"Robot {name} kicked the ball!")
            print(f"Kick power: {self.kick_power}, kick direction: {self.kick_direction}, range: {self.range}")
            print(f"Ball position now: ({self.blackboard.gamestate.ball_position[0]}, {self.blackboard.gamestate.ball_position[1]})")
        else:
            print("Robot cannot kick the ball due to distance.")
