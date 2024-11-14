import tkinter as tk
from blackboard import Blackboard
import random

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
        self.blackboard.gamestate.ball_position = (field_length / 2, field_width / 2)
        
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

    def game_loop(self):
        # Update player positions based on AI decisions
        self.blackboard.team.execute_strategy()

        # Update ball position based on the velocity
        self.blackboard.kick.update_ball_position()
        
        # Check if the ball is in the goal
        self.blackboard.gamestate.is_ball_in_goal(self.blackboard.gamestate.ball_position, self.blackboard)
        self.update_players()
        self.update_ball()

        # Update ball position in the canvas and update AI decisions based on the new position
        ball_x, ball_y = self.blackboard.gamestate.ball_position
        canvas_x, canvas_y = ball_x * 7 + 50, ball_y * 7 + 50  # Scale and offset
        self.canvas.coords(self.ball, canvas_x-5, canvas_y-5, canvas_x+5, canvas_y+5)
        
        # Find the closest player from both teams
        closest_player, min_distance, kicking_team = None, float('inf'), None
        for team_id, team in [('a', self.blackboard.team.players), ('b', self.blackboard.team.enemies)]:
            for player, pos in team.items():
                distance = ((pos[0] - ball_x)**2 + (pos[1] - ball_y)**2)**0.5
                if distance < min_distance:
                    min_distance = distance
                    closest_player = player
                    kicking_team = team_id
        
        self.blackboard.kick.auto_kick()

        # Update score display
        score_a = self.blackboard.gamestate.get_score('a')
        score_b = self.blackboard.gamestate.get_score('b')
        self.master.title(f"Robotic Soccer Game - Score: A {score_a} - B {score_b}")
        print(self.canvas.coords(self.ball)[:2])

        self.update_score_display()

        self.master.after(100, self.game_loop)


if __name__ == "__main__":
    root = tk.Tk()
    blackboard = Blackboard()
    game_ui = SoccerGameUI(root, blackboard)
    root.mainloop()