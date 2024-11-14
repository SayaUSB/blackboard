from capsules.GameState import GameStatusCapsule
from capsules.Kick import KickCapsule
from capsules.FieldInfo import FieldInfoCapsule
from capsules.Team import TeamCapsule

class Blackboard:
    def __init__(self):
        self.gamestate = GameStatusCapsule(self)
        self.kick = KickCapsule(self)
        self.field_info = FieldInfoCapsule(self)
        self.team = TeamCapsule(self)
        