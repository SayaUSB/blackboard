import random
import time

class GameStatusCapsule:
    def __init__(self, blackboard):
        self.blackboard = blackboard
        self.score = {'a': 0, 'b': 0}
        self.time_remaining = 45
        self.current_phase = 'first_half'
        self.ball_position = (50, 25)

    def is_ball_out_of_bounds(self, ball_position, blackboard):
        field_width = self.blackboard.field_info.field_width
        field_length = self.blackboard.field_info.field_length
        if (ball_position[0] < 0 or ball_position[0] > field_length or
            ball_position[1] < 0 or ball_position[1] > field_width):
            print("Ball is out of bounds!")
            time.sleep(1)
            self.blackboard.kick.ball_velocity = (0, 0)
            self.reset_ball_and_players(blackboard)
            return True
        return False

    def reset_ball_and_players(self, blackboard):
        field_width = self.blackboard.field_info.field_width
        field_length = self.blackboard.field_info.field_length
        self.ball_position = (field_length / 2, field_width / 2)
        print("Ball and player positions have been reset.")

    def scored(self, team):
        if team in self.score:
            self.score[team] += 1

    def set_time_remaining(self, time):
        self.time_remaining = time

    def set_current_phase(self, phase):
        self.current_phase = phase

    def get_score(self, team):
        return self.score[team]

    def get_time_remaining(self):
        return self.time_remaining

    def get_current_phase(self):
        return self.current_phase
    
    def reset_position(self, blackboard):
        for player in blackboard.team.players:
                self.blackboard.team.players[player] = (random.randint(10,40),random.randint(5,20))
        for enemy in blackboard.team.enemies:
                self.blackboard.team.enemies[enemy] = (random.randint(60,90),random.randint(5,20))
        self.ball_position = (50, 25)

    def reset(self, blackboard):
        self.score = {'a': 0, 'b': 0}
        self.time_remaining = 45
        self.current_phase = 'first_half'
        self.reset_position(blackboard)

    def is_ball_in_goal(self, ball_position, blackboard):
        field_length = blackboard.field_info.field_length
        
        # Check if ball is in Team A's goal (left side)
        if ball_position[0] <= 0 and blackboard.field_info.goal_lines['a'][0] <= ball_position[1] <= blackboard.field_info.goal_lines['a'][1]:
            self.scored('b')
            print('Team B scored!')
            self.reset_position(blackboard)
            time.sleep(1)
        
        # Check if ball is in Team B's goal (right side)
        elif ball_position[0] >= field_length and blackboard.field_info.goal_lines['b'][0] <= ball_position[1] <= blackboard.field_info.goal_lines['b'][1]:
            self.scored('a')
            print('Team A scored!')
            self.reset_position(blackboard)
            time.sleep(1)
            
        # Check if ball is out of bounds
        elif self.is_ball_out_of_bounds(ball_position, blackboard):
            return
        
    def reset(self, blackboard):
        self.score = {'a': 0, 'b': 0}
        self.time_remaining = 45  # or whatever your default game time is
        self.current_phase = 'first_half'
        self.reset_ball_and_players(blackboard)

    def reset_ball_and_players(self, blackboard):
        field_length = self.blackboard.field_info.field_length
        field_width = self.blackboard.field_info.field_width
        self.ball_position = (field_length / 2, field_width / 2)
        
        for player in blackboard.team.players:
            blackboard.team.players[player] = (random.randint(10, field_length // 2 - 10),
                                               random.randint(5, field_width - 5))
        for enemy in blackboard.team.enemies:
            blackboard.team.enemies[enemy] = (random.randint(field_length // 2 + 10, field_length - 10),
                                              random.randint(5, field_width - 5))