class FieldInfoCapsule:
    def __init__(self, blackboard):
        self.blackboard = blackboard
        self.field_length = 100
        self.field_width = 50
        self.goal_width = 5
        self.center_circle_radius = 10
        self.goal_lines = {
            'a': (0, (self.field_width - self.goal_width) / 2, 0, (self.field_width + self.goal_width) / 2),
            'b': (self.field_length, -(self.field_width - self.goal_width) / 2, self.field_length, -(self.field_width + self.goal_width) / 2)
        }

    def get_field_dimensions(self):
        return self.field_length, self.field_width

    def get_goal_width(self):
        return self.goal_width

    def get_center_circle_radius(self):
        return self.center_circle_radius
    
    def get_goal_lines(self):
        return self.goal_lines
    
    def set_field_dimensions(self, length, width):
        self.field_length = length
        self.field_width = width

    def set_field_length(self, length):
        self.field_length = length

    def set_field_width(self, width):
        self.field_width = width
    
    def switch_goal_lines(self):
        self.goal_lines['team_a'], self.goal_lines['team_b'] = self.goal_lines['team_b'], self.goal_lines['team_a']