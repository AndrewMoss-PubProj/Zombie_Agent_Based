from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import ChartModule
from mesa.datacollection import DataCollector
import numpy as np
import matplotlib.pyplot as plt




def Human_Proportion(model):
    agent_states = [agent.state for agent in model.schedule.agents]
    humans = list(filter(lambda x: x == 'Human', agent_states))
    return len(humans)/len(agent_states)
def Zombies_Killed(model):
    return model.num_agents - len(model.schedule.agents)

def agent_portrayal(agent):
    portrayal = {"Shape": "circle",
                 "Filled": "true",
                 "r": .5}
    if (type(agent).__name__) == 'Person':
        if agent.state == 'Human':
            portrayal["Color"] = "red"
            portrayal["Layer"] = 0
        elif agent.state == 'Zombie':
            portrayal["Color"] = "green"
            portrayal["Layer"] = 0
    elif (type(agent).__name__) == 'Obstacle':
        portrayal["Color"] = "black"
        portrayal["Layer"] = 0

    return portrayal

class Person(Agent):
    """An agent that is either a zombie or a human"""

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.state = np.random.choice(['Human', 'Zombie'], p=[.8, .2])

    def move(self):
        if self.state == 'Zombie':
            possible_steps = self.model.grid.get_neighborhood(
                self.pos, moore=True, include_center=False
            )

            impossible_moves = []
            for index, step in enumerate(possible_steps):
                obstacle_list = self.model.grid.get_cell_list_contents([step])
                temp = list(filter(lambda x: type(x).__name__ == "Obstacle", obstacle_list))
                if len(temp) > 0:
                    impossible_moves.append(step)
            possible_steps = list(filter(lambda x: x not in impossible_moves, possible_steps))

            new_position = self.random.choice(possible_steps)
            self.model.grid.move_agent(self, new_position)
        elif self.state == 'Human':
            possible_steps = self.model.grid.get_neighborhood(
                self.pos, moore=True, include_center=False, radius=2
            )

            impossible_moves = []
            for index, step in enumerate(possible_steps):
                obstacle_list = self.model.grid.get_cell_list_contents([step])
                temp = list(filter(lambda x: type(x).__name__ == "Obstacle", obstacle_list))
                if len(temp) > 0:
                    impossible_moves.append(step)
            possible_steps = list(filter(lambda x: x not in impossible_moves, possible_steps))
            new_position = self.random.choice(possible_steps)
            self.model.grid.move_agent(self, new_position)

    def attack(self):
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        cellmates = [x for x in cellmates if self.state != x.state]
        if len(cellmates) > 1:
            other_agent = self.random.choice(cellmates)
            if other_agent.state == 'Zombie':
                winner = np.random.choice([self,other_agent],p=[.2,.8])
                if winner == self:
                    self.model.grid._remove_agent(other_agent.pos, other_agent)
                    self.model.schedule.remove(other_agent)
                else:
                    self.state = 'Zombie'
            elif other_agent.state == 'Human':
                winner = np.random.choice([self, other_agent], p=[.8, .2])
                if winner == self:
                    other_agent.state = 'Zombie'
                else:
                    self.model.grid._remove_agent(self.pos, self)
                    self.model.schedule.remove(self)

    def step(self):
        self.move()
        self.attack()

class Obstacle(Agent):
    """An agent that is either a zombie or a human"""

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)


class ZombieModel(Model):
    """A model with some number of agents."""

    def __init__(self, Agents, Obstacles, width, height):
        self.num_agents = Agents
        self.num_obstacles = Obstacles
        self.grid = MultiGrid(width, height, True)
        self.schedule = RandomActivation(self)
        self.running = True
        # Create agents
        for i in range(self.num_agents):
            a = Person(i, self)
            self.schedule.add(a)
            # Add the agent to a random grid cell
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(a, (x, y))
        for j in range(self.num_obstacles):
            b = Obstacle(j, self)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(b, (x, y))

        self.datacollector = DataCollector(
            model_reporters={"Human_Proportion": Human_Proportion,
                             "Zombies_Killed": Zombies_Killed},
            agent_reporters={"state": "state"}
        )


    def step(self):
        self.datacollector.collect(self)
        self.schedule.step()


Agents = np.random.randint(30, 65)
Obstacles = np.random.randint(5, 15)
grid = CanvasGrid(agent_portrayal, 10, 10, 500, 500)
server = ModularServer(ZombieModel,
                       [grid],
                       "Zombie Model",
                       {"Agents": Agents,
                        "Obstacles": Obstacles,
                       "width": 10, "height": 10})
server.port = 8521 # The default

chart = ChartModule([{"Label": "Human_Proportion",
                      "Color": "Black"},
                     {"Label": "Zombies_Killed",
                      "Color": "Red"}],
                    data_collector_name='datacollector')

server = ModularServer(ZombieModel,
                       [grid, chart],
                       "Zombie Model",
                       {"Agents": Agents, "Obstacles": Obstacles,
                        "width": 10, "height": 10})

server.launch()
