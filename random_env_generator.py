import argparse
import json
from random import randint
from configurations.config_grabber import Configuration
import os

parser = argparse.ArgumentParser(description='Arguments for creating the environments and its configuration')
parser.add_argument('--environment_file', type=str, required=False, help="A json file containing the keys: "
                                                                         "step, goal, near, immediate, violated. "
                                                                         "The values should be the wanted rewards "
                                                                         "of the actions")
parser.add_argument('--rewards_file', type=str, required=False, help="A json file containing the keys: "
                                                                     "step, goal, near, immediate, violated. "
                                                                     "The values should be the wanted rewards "
                                                                     "of the actions")

environment_path = "..//gym_minigrid/envs/"
configuration_path = "../gym-minigrid/configurations/"
random_token = randint(0, 9999)

""" This script creates a random environment in the gym_minigrid/envs folder. It uses a token_hex(4) 
        as the ID and the random seed for placing tiles in the grid.
    This to ensure that certain environments can be reproduced 
        in case the agent behaves strange in certain environments, in order to investigate why.        
"""


def generate_environment(environment="default", rewards="default"):
    elements = Configuration.grab("environments/" + environment)
    grid_size = elements.grid_size
    n_water = elements.n_water
    n_dirt = elements.n_dirt
    n_boxes = elements.n_boxes
    locked = elements.locked
    n_deadend = 0
    light_switch = elements.light_switch
    random_each_episode = False
    rewards = Configuration.grab("rewards/" + rewards)

    env_filename = environment_path + "randoms/" + "randomenv{0}.py".format(random_token)
    os.makedirs(os.path.dirname(env_filename), exist_ok=True)
    with open(env_filename, 'w') as env:
        env.write("""
from gym_minigrid.extendedminigrid import *
from gym_minigrid.register import register

import random

class RandomEnv(ExMiniGridEnv):

    def __init__(self, size=8):
        super().__init__(
            grid_size=size,
            max_steps=4*size*size,
            # Set this to True for maximum speed
            see_through_walls= not {3}
        )

    def getRooms(self):
        return self.roomList

    # Goal is to turn on the light before reaching the goal
    def goal_enabled(self):
        return self.light_on_room() and self.clean_room()

    def light_on_room(self):
        for element in self.grid.grid:
            if element is not None and element.type == "lightsw" \
                    and hasattr(element, 'is_on'):
                return element.is_on
        return False

    # Enables the goal only when the room has been completely cleaned
    def clean_room(self):
        nodirt = True
        for element in self.grid.grid:
            if element is not None and element.type == "dirt":
                nodirt = False
        return nodirt

    def saveElements(self,room):
        tab=[]
        (x , y) = room.position
        (width , height) = room.size
        for i in range(x , x + width):
            for j in range(y , y + height):
                objType = self.grid.get(i,j)
                if objType is not None:
                    tab.append((i,j,0))
                else:
                    tab.append((i, j, 1))
        return tab

    def _random_or_not_position(self, xmin, xmax, ymin, ymax ):
        if {5}:
            width_pos, height_pos = self._rand_pos( xmin, xmax + 1, ymin, ymax + 1)
        else:
            width_pos = random.randint( xmin, xmax)
            height_pos = random.randint( ymin, ymax)
        return width_pos, height_pos

    def _random_number(self, min, max):
        if {5}:
            return self._rand_int(min,max+1)
        else:
            return random.randint(min,max)

    def _random_or_not_bool(self):
        if {5}:
            return self._rand_bool()
        else:
            return random.choice([True, False])

    def _reachable_elements(self, x_agent, y_agent):
        queue = [(x_agent, y_agent)]
        elements = set()
        visited = set()
        dirt_count = 0
        boxes_count = 0

        while len(queue) > 0:
            (x,y) = queue.pop()
            visited.add((x,y))
            directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
            for (dx,dy) in directions:
                other_pos = (x+dx,y+dy)
                (ox,oy) = other_pos
                if 0 < ox < self.grid.width and 0 < oy < self.grid.height and other_pos not in visited and other_pos not in queue:
                    if isinstance(self.grid.get(ox,oy), type(None)) or isinstance(self.grid.get(ox,oy), Door)  or isinstance(self.grid.get(ox,oy), Box) or isinstance(self.grid.get(ox,oy), Key) or isinstance(self.grid.get(ox,oy), LockedDoor)  or isinstance(self.grid.get(ox,oy), Dirt):
                        queue.append(other_pos)
                    if isinstance(self.grid.get(ox,oy), LightSwitch) or isinstance(self.grid.get(ox,oy), Door) or isinstance(self.grid.get(ox,oy), Key)  or isinstance(self.grid.get(ox,oy), LockedDoor) or isinstance(self.grid.get(ox,oy), Goal):
                        elements.add(type(self.grid.get(ox,oy)))
                    if isinstance(self.grid.get(ox,oy), Dirt):
                        dirt_count+=1
                    if isinstance(self.grid.get(ox,oy), Box):
                        boxes_count+=1
        return (elements,dirt_count, boxes_count)                

    def _valid_free_position(self, x_agent, y_agent, x_bound, y_bound):
        x = random.randint(1, x_bound - 1)
        y = random.randint(1, y_bound - 1)
        while type(self.grid.get(x, y)) != type(None) or (x_agent == x and y_agent ==y):
            x = random.randint(1, x_bound - 1)
            y = random.randint(1, y_bound -1)
        return (x,y)


    def _place_randomly(self, x_agent, y_agent, n ,Element, color=None):
        water = []
        while n > len(water):        
            (x_water, y_water) = self._valid_free_position(x_agent, y_agent,  self.grid.width - 1, self.grid.height - 1)
            if color != None:
                self.grid.set(x_water, y_water, Element(color))
            else: 
                self.grid.set(x_water, y_water, Element())
            water += [(x_water, y_water)]
        return water 

    def _reset_positions(self, water):
        for (x,y) in water:
            self.grid.set(x,y,None)

    #Places the agent in a random position within the first room.         
    def _place_agent(self, width_pos, height_pos):
        max_height = self.grid.height
        x_agent = random.randint(1, width_pos)
        y_agent = random.randint(1, max_height)
        while x_agent == width_pos and y_agent == height_pos:
            x_agent = random.randint(1, width_pos)
            y_agent = random.randint(1, max_height)
        self.start_pos = (x_agent, y_agent)

    def _gen_grid(self, width, height):
        # Create an empty grid
        self.grid = Grid(width, height)

        # Generate the surrounding walls
        self.grid.wall_rect(0, 0, width, height)

        # Set the random seed to the random token, so we can reproduce the environment
        random.seed("{4}")

        #Place lightswitch
        width_pos = random.randint(2,{0}-5) # x position of the light switch (2 tiles space for each room)
        height_pos = random.randint(2,{0}-2) # y position of light switch (needs space for the wall and door)
        xdoor = width_pos + 1 # x position of the door 
        ydoor = height_pos -1 # y position of the door
        switchRoom = LightSwitch()

        # Place the agent
        self.start_dir = random.randint(0,3)
        x_agent = 1
        y_agent = 1
        self.start_pos = (x_agent, y_agent)

        # Place a goal square 
        x_goal = width - 2 #random.randint(xdoor + 1, width - 2)
        y_goal = height -2 #random.randint(1,height -2)

        #Avoid placing it in front of the door. 
        while x_goal ==  xdoor + 1 and ydoor == y_goal:
            x_goal = random.randint(xdoor + 1, width - 2)
            y_goal = random.randint(1,width -2)            

        self.grid.set(x_goal, y_goal , Goal())

        #Place the wall
        self.grid.vert_wall(xdoor, 1, height-2)


        #The number of elements that need to be reachable in the room (Door, Goal, LightSwitch)
        n_elements = 3

        if {8}:        
            self.grid.set(xdoor, ydoor , LockedDoor('yellow'))
            (x_key, y_key) = self._valid_free_position(x_agent, y_agent, xdoor, self.grid.height - 1)
            self.grid.set(x_key, y_key, Key())
            n_elements += 1
        else:
            self.grid.set(xdoor, ydoor ,Door('yellow'))


        #Add the room
        self.roomList = []
        self.roomList.append(Room(0,(width_pos + 2, height),(0, 0),True))
        self.roomList.append(Room(1,(width - width_pos - 2, height),(width_pos + 2, 0),False))
        self.roomList[1].setEntryDoor((xdoor,ydoor))
        self.roomList[0].setExitDoor((xdoor,ydoor))        


        #Place the lightswitch
        switchRoom.affectRoom(self.roomList[1])
        switchRoom.setSwitchPos((width_pos,height_pos))
        switchRoom.cur_pos = (width_pos, height_pos)

        self.grid.set(width_pos, height_pos, switchRoom)
        self.switchPosition = []
        self.switchPosition.append((width_pos, height_pos))


        n_water = {1}
        n_dirt = {7}
        n_boxes = {9}

        dirt = self._place_randomly(x_agent,y_agent,n_dirt,Dirt)

        boxes = self._place_randomly(x_agent,y_agent,n_boxes,Box,'red')

        # Place water
        water = self._place_randomly(x_agent,y_agent,n_water,Water)

        (elements, dirt_count, boxes_count) = self._reachable_elements(x_agent,y_agent)

        stop = 0

        while (len(elements) != n_elements or boxes_count != n_boxes or dirt_count != n_dirt) and stop < 100000:
            self._reset_positions(water)
            self._reset_positions(dirt)
            self._reset_positions(boxes)
            water = self._place_randomly(x_agent,y_agent,n_water,Water)
            dirt = self._place_randomly(x_agent,y_agent,n_dirt,Dirt)
            boxes = self._place_randomly(x_agent,y_agent,n_boxes,Box,'red')
            (elements, dirt_count, boxes_count) = self._reachable_elements(x_agent,y_agent)
            stop += 1

        tab = self.saveElements(self.roomList[1])
        switchRoom.elements_in_room(tab)
        switchRoom.elements_in_room(tab)

        self.mission = ""

class RandomEnv{0}x{0}_{4}(RandomEnv):
    def __init__(self):
        super().__init__(size={0})

register(
    id='MiniGrid-RandomEnv-{0}x{0}-{4}-v0',
    entry_point='gym_minigrid.envs:RandomEnv{0}x{0}_{4}'
)
""".format(grid_size, n_water, n_deadend, light_switch, random_token, random_each_episode, rewards.standard.death,
           n_dirt, locked, n_boxes))
        env.close()
    # Adds the import statement to __init__.py in the envs folder in gym_minigrid,
    # otherwise the environment is unavailable to use.
    init_filename = environment_path + "__init__.py"
    os.makedirs(os.path.dirname(init_filename), exist_ok=True)
    with open(init_filename, 'a') as init_file:
        init_file.write("\n")
        init_file.write("from gym_minigrid.envs.randoms.randomenv{0} import *".format(random_token))
        init_file.close()

    # Creates a json config file for the random environment
    config_filename = configuration_path + "randoms/" + "randomEnv-{0}x{0}-{1}-v0.json".format(grid_size, random_token)
    os.makedirs(os.path.dirname(config_filename), exist_ok=True)
    with open(config_filename, 'w') as config:
        list_of_json_patterns = {}
        patterns_map = {}
        if hasattr(elements, "monitors"):
            if hasattr(elements.monitors, "patterns"):
                for type in elements.monitors.patterns:
                    for monitor in type:
                        type_of_monitor = monitor.type
                        respected = 1
                        violated = -1
                        for current_monitor in rewards:
                            if hasattr(current_monitor, "name"):
                                if current_monitor.name == type_of_monitor:
                                    respected = current_monitor.respected
                                    violated = current_monitor.violated
                        list_of_json_patterns[monitor.name] = {
                            "{0}".format(monitor.name): {
                                "type": "{0}".format(monitor.type),
                                "mode": "{0}".format(monitor.mode),
                                "active": True if monitor.active else False,
                                "context": "{0}".format(monitor.context),
                                "name": "{0}".format(monitor.name),
                                "action_planner": "{0}".format(monitor.action_planner) if hasattr(monitor,
                                                                                                  "action_planner") else "wait",
                                "conditions": "{0}".format(monitor.conditions) if not hasattr(monitor.conditions,
                                                                                              "pre") else {
                                    "pre": "{0}".format(monitor.conditions.pre),
                                    "post": "{0}".format(monitor.conditions.post)
                                },
                                "rewards": {
                                    "respected": float(
                                        "{0:.2f}".format(respected)),
                                    "violated": float(
                                        "{0:.2f}".format(violated))
                                }
                            }
                        }
                        if monitor.type in patterns_map:
                            patterns_map[monitor.type].append(monitor.name)
                        else:
                            patterns_map[monitor.type] = [monitor.name]

        json_object = json.dumps({
            "config_name": "randomEnv-s{0}-w{1}-r{2}".format(grid_size, n_water, random_token),
            "algorithm": "a2c",
            "env_name": "MiniGrid-RandomEnv-{0}x{0}-{1}-v0".format(grid_size, random_token),
            "envelope": bool(elements.envelope),
            "rendering": bool(elements.rendering),
            "recording": bool(elements.recording),
            "log_interval": int("{0}".format(elements.log_interval)),
            "max_num_frames": int("{0}".format(elements.max_num_frames)),
            "max_num_steps_episode": int("{0}".format(elements.max_num_steps_episode)),
            "debug_mode": bool(elements.debug_mode),
            "evaluation_directory_name": str(elements.evaluation_directory_name),
            "training_mode": bool(elements.training_mode),
            "agent_view_size": int("{0}".format(elements.agent_view_size)),
            "visdom": bool(elements.visdom),
            "a2c": {
                "algorithm": "a2c",
                "save_model_interval": int("{0}".format(elements.a2c.save_model_interval)),
                "num_processes": int("{0}".format(elements.a2c.num_processes)),
                "stop_learning": int("{0}".format(elements.a2c.stop_learning)),
                "optimal_num_step": int("{0}".format(elements.a2c.optimal_num_step)),
                "stop_after_update_number": int("{0}".format(elements.a2c.stop_after_update_number)),
                "num_steps": int("{0}".format(elements.a2c.num_steps)),
                "save_evaluation_interval": int("{0}".format(elements.a2c.save_evaluation_interval))
            },
            "dqn": {
                "exploration_rate": float("{0:.2f}".format(elements.dqn.exploration_rate)),
                "results_log_interval": int("{0}".format(elements.dqn.results_log_interval)),
                "epsilon_decay_episodes": int("{0}".format(elements.dqn.epsilon_decay_episodes)),
                "epsilon_final": float("{0:.2f}".format(elements.dqn.epsilon_final)),
                "epsilon_decay_frame": int("{0}".format(elements.dqn.epsilon_decay_frame)),
                "epsilon_start": float("{0:.2f}".format(elements.dqn.epsilon_start)),
                "discount_factor": float("{0:.2f}".format(elements.dqn.discount_factor))
            },
            "monitors": {
                "patterns": {

                }
            },
            "rewards": {
                "actions": {
                    "forward": float(
                        "{0:.5f}".format(rewards.actions.forward if hasattr(rewards.actions, 'forward') else 0))
                },
                "standard": {
                    "goal": float("{0:.5f}".format(rewards.standard.goal if hasattr(rewards.standard, 'goal') else 1)),
                    "step": float("{0:.5f}".format(rewards.standard.step if hasattr(rewards.standard, 'step') else 0)),
                    'death': float(
                        "{0:.5f}".format(rewards.standard.death if hasattr(rewards.standard, 'death') else -1))
                },
                "cleaningenv": {
                    "clean": float(
                        "{0:.5f}".format(rewards.cleaningenv.clean if hasattr(rewards.cleaningenv, 'clean') else 0.5))
                }
            }
        }, indent=2)

        d = {}
        dPatterns = {}

        for p in patterns_map:
            if isinstance(patterns_map[p], str):
                if p in dPatterns:
                    dPatterns[p].update(list_of_json_patterns[patterns_map[p]])
                else:
                    dPatterns[p] = list_of_json_patterns[patterns_map[p]]
            else:
                for value in patterns_map[p]:
                    if p in dPatterns:
                        dPatterns[p].update(list_of_json_patterns[value])
                    else:
                        dPatterns[p] = list_of_json_patterns[value]

        d = json.loads(json_object)
        d['monitors']['patterns'].update(dPatterns)
        config.write(json.dumps(d, sort_keys=True, indent=2))
        config.close()

    return "randomEnv-{0}x{0}-{1}-v0.json".format(grid_size, random_token)


def main():
    args = parser.parse_args()
    environment = "default"
    rewards = "default"
    if args.rewards_file is not None:
        rewards = args.rewards_file
    if args.environment_file is not None:
        environment = args.environment_file
    file_name = generate_environment(environment, rewards)
    print(file_name)


if __name__ == '__main__':
    main()