import tkinter as tk
from blackboard import Blackboard
import random
import math

class SoccerGameUI:
    def __init__(self, master, blackboard):
        self.master = master
        self.blackboard = blackboard
        self.master.title("Robotic Soccer Game")

        field_length, field_width = self.blackboard.field_info.get_field_dimensions()
        self.scale_factor = 7
        self.x_offset = 50
        self.y_offset = 50
        
        self.create_reset_button()
        self.create_pause_button()
        self.canvas = tk.Canvas(self.master, width=800, height=400, bg="green")
        self.canvas.pack()

        self.draw_field()
        self.ball = self.canvas.create_oval(395, 195, 405, 205, fill="white")
        
        self.add_player_button = tk.Button(self.master, text="Add Player", command=self.add_new_player)
        self.add_player_button.pack()

        self.add_enemy_button = tk.Button(self.master, text="Add Enemy", command=self.add_new_enemy)
        self.add_enemy_button.pack()

        self.team_a_players = {}
        self.team_b_players = {}
        self.keeper_a = None
        self.keeper_b = None
        self.initialize_keepers()
        self.update_players()

        self.canvas.bind("<Button-1>", self.on_click)
        
        self.master.after(100, self.game_loop)

    def initialize_keepers(self):
        field_length, field_width = self.blackboard.field_info.get_field_dimensions()
        
        # Initialize keeper for team A if not present
        if not self.blackboard.team.keeper_a:
            keeper_a_name = "KeeperA"
            keeper_a_x = 5  # Near the left goal
            keeper_a_y = field_width / 2
            self.blackboard.team.add_player(keeper_a_name, keeper_a_x, keeper_a_y)
            self.blackboard.team.keeper_a = keeper_a_name

        # Initialize keeper for team B if not present
        if not self.blackboard.team.keeper_b:
            keeper_b_name = "KeeperB"
            keeper_b_x = field_length - 5  # Near the right goal
            keeper_b_y = field_width / 2
            self.blackboard.team.add_enemy(keeper_b_name, keeper_b_x, keeper_b_y)
            self.blackboard.team.keeper_b = keeper_b_name


    def create_reset_button(self):
        self.reset_button = tk.Button(self.master, text="Reset Game", command=self.reset_game)
        self.reset_button.pack(pady=10)

    def reset_game(self):
        # Reset the game state
        self.blackboard.gamestate.reset(self.blackboard)
        
        # Reset ball position
        field_length, field_width = self.blackboard.field_info.get_field_dimensions()
        self.blackboard.gamestate.ball_position = (field_length / 2, random.randint(20, 30))
        
        # Update the UI
        self.update_players()
        self.update_ball()
        
        # Reset the score
        self.blackboard.gamestate.score = {'a': 0, 'b': 0}
        
        # Update the score display
        self.update_score_display()

    def update_ball(self):
        ball_x, ball_y = self.blackboard.gamestate.ball_position
        canvas_x = ball_x * self.scale_factor + self.x_offset
        canvas_y = ball_y * self.scale_factor + self.y_offset
        self.canvas.coords(self.ball, canvas_x-5, canvas_y-5, canvas_x+5, canvas_y+5)

    def update_score_display(self):
        score_a = self.blackboard.gamestate.get_score('a')
        score_b = self.blackboard.gamestate.get_score('b')
        self.master.title(f"Robotic Soccer Game - Score: A {score_a} - B {score_b}")

    def add_new_player(self):
        new_player_name = f"Player{len(self.blackboard.team.players) + 1}"
        self.blackboard.team.add_player(new_player_name, random.randint(10, 40), random.randint(10, 40))
        self.update_players()

    def add_new_enemy(self):
        new_enemy_name = f"Enemy{len(self.blackboard.team.enemies) + 1}"
        self.blackboard.team.add_enemy(new_enemy_name, random.randint(60, 90), random.randint(10, 40))
        self.update_players()

    def draw_field(self):
        # Draw the field lines
        self.canvas.create_rectangle(50, 50, 750, 350, outline="white")
        self.canvas.create_line(400, 50, 400, 350, fill="white")
        self.canvas.create_oval(350, 150, 450, 250, outline="white")

        # Draw the goals
        self.canvas.create_rectangle(30, 150, 50, 250, outline="white", fill="")
        self.canvas.create_rectangle(750, 150, 770, 250, outline="white", fill="")

    def update_keeper_positions(self):
        field_length, field_width = self.blackboard.field_info.get_field_dimensions()
        ball_x, ball_y = self.blackboard.gamestate.ball_position
        
        # Update keeper A (left side)
        keeper_a_pos = self.blackboard.team.players[self.blackboard.team.keeper_a]
        target_y_a = min(max(ball_y, field_width * 0.2), field_width * 0.8)
        new_x_a = min(max(keeper_a_pos[0], 2), field_length * 0.2)
        new_y_a = keeper_a_pos[1] + (target_y_a - keeper_a_pos[1]) * 0.1
        self.blackboard.team.players[self.blackboard.team.keeper_a] = (new_x_a, new_y_a)
        
        # Update keeper B (right side)
        keeper_b_pos = self.blackboard.team.enemies[self.blackboard.team.keeper_b]
        target_y_b = min(max(ball_y, field_width * 0.2), field_width * 0.8)
        new_x_b = max(min(keeper_b_pos[0], field_length - 2), field_length * 0.8)
        new_y_b = keeper_b_pos[1] + (target_y_b - keeper_b_pos[1]) * 0.1
        self.blackboard.team.enemies[self.blackboard.team.keeper_b] = (new_x_b, new_y_b)

    def update_players(self):
        for player, pos in self.blackboard.team.players.items():
            x, y = pos
            x, y = x * 7 + 50, y * 7 + 50  # Scale and offset
            if player == self.blackboard.team.keeper_a:
                if self.keeper_a:
                    self.canvas.coords(self.keeper_a, x-7, y-7, x+7, y+7)
                else:
                    self.keeper_a = self.canvas.create_oval(x-7, y-7, x+7, y+7, fill="lightblue", outline="blue", width=2)
            else:
                if player in self.team_a_players:
                    self.canvas.coords(self.team_a_players[player], x-5, y-5, x+5, y+5)
                else:
                    self.team_a_players[player] = self.canvas.create_oval(x-5, y-5, x+5, y+5, fill="blue")

        for enemy, pos in self.blackboard.team.enemies.items():
            x, y = pos
            x, y = x * 7 + 50, y * 7 + 50  # Scale and offset
            if enemy == self.blackboard.team.keeper_b:
                if self.keeper_b:
                    self.canvas.coords(self.keeper_b, x-7, y-7, x+7, y+7)
                else:
                    self.keeper_b = self.canvas.create_oval(x-7, y-7, x+7, y+7, fill="orange", outline="red", width=2)
            else:
                if enemy in self.team_b_players:
                    self.canvas.coords(self.team_b_players[enemy], x-5, y-5, x+5, y+5)
                else:
                    self.team_b_players[enemy] = self.canvas.create_oval(x-5, y-5, x+5, y+5, fill="red")

    def on_click(self, event):
        # Move the ball when clicked
        x, y = event.x, event.y
        self.canvas.coords(self.ball, x-5, y-5, x+5, y+5)
        
        # Update ball position in the blackboard
        self.blackboard.gamestate.ball_position = ((x-50)/7, (y-50)/7)

    def create_pause_button(self):
        self.paused = False
        self.pause_button = tk.Button(self.master, text="Pause", command=self.toggle_pause)
        self.pause_button.pack(pady=5)

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.pause_button.config(text="Resume")
        else:
            self.pause_button.config(text="Pause")
            self.game_loop()  

    def game_loop(self):
        if not self.paused:
            # Update player positions based on AI decisions
            self.blackboard.team.execute_strategy()
            self.update_keeper_positions()

            # Update ball position based on the velocity
            self.blackboard.kick.update_ball_position()

            # Check if the ball is in the goal
            self.blackboard.gamestate.is_ball_in_goal(self.blackboard.gamestate.ball_position, self.blackboard)
            self.update_players()
            self.update_ball()

            # Update ball position in the canvas and update AI decisions based on the new position
            ball_x, ball_y = self.blackboard.gamestate.ball_position
            canvas_x, canvas_y = ball_x * self.scale_factor + self.x_offset, ball_y * self.scale_factor + self.y_offset
            self.canvas.coords(self.ball, canvas_x-5, canvas_y-5, canvas_x+5, canvas_y+5)

            # Find the closest player from both teams
            closest_player, min_distance, kicking_team = self.find_closest_player(ball_x, ball_y)

            if closest_player and kicking_team == 'a':  # If the closest player is from team A
                better_positioned_player = self.find_better_positioned_teammate(closest_player, ball_x, ball_y)
                if better_positioned_player:
                    self.pass_ball(closest_player, better_positioned_player)
                else:
                    self.blackboard.kick.auto_kick()
            else:
                self.blackboard.kick.auto_kick()

            # Update score display
            self.update_score_display()

            self.master.after(100, self.game_loop)

    def find_closest_player(self, ball_x, ball_y):
        closest_player, min_distance, kicking_team = None, float('inf'), None
        for team_id, team in [('a', self.blackboard.team.players), ('b', self.blackboard.team.enemies)]:
            for player, pos in team.items():
                distance = ((pos[0] - ball_x)**2 + (pos[1] - ball_y)**2)**0.5
                if distance < min_distance:
                    min_distance = distance
                    closest_player = player
                    kicking_team = team_id
        return closest_player, min_distance, kicking_team

    def find_better_positioned_teammate(self, current_player, ball_x, ball_y):
        field_length = self.blackboard.field_info.field_length
        current_pos = self.blackboard.team.players[current_player]
        best_player = None
        best_score = 0

        for player, pos in self.blackboard.team.players.items():
            if player != current_player:
                # Calculate a score based on proximity to the ball and the enemy goal
                distance_to_ball = ((pos[0] - ball_x)**2 + (pos[1] - ball_y)**2)**0.5
                distance_to_goal = field_length - pos[0]
                score = (field_length - distance_to_goal) * 2 - distance_to_ball

                if score > best_score and pos[0] > current_pos[0]:  # Check if the player is closer to the enemy goal
                    best_player = player
                    best_score = score

        return best_player

    def pass_ball(self, from_player, to_player):
        from_pos = self.blackboard.team.players[from_player]
        to_pos = self.blackboard.team.players[to_player]

        # Calculate direction and power for the pass
        dx = to_pos[0] - from_pos[0]
        dy = to_pos[1] - from_pos[1]
        distance = (dx**2 + dy**2)**0.5

        # Set kick parameters
        self.blackboard.kick.set_kick_power(min(10, distance * 0.3))  # Adjust power based on distance
        self.blackboard.kick.set_kick_direction(math.degrees(math.atan2(dy, dx)))

        # Execute the kick
        self.blackboard.kick.execute_kick()
        print(f"{from_player} passed the ball to {to_player}")


if __name__ == "__main__":
    root = tk.Tk()
    blackboard = Blackboard()
    game_ui = SoccerGameUI(root, blackboard)
    root.mainloop()