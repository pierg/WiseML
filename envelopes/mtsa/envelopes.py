import random



try:
    from configurations import config_grabber as cg

    from extendedminigrid import *
    from mtsa.controller import *
    from envelopes.perception import Perception

    import gym

except Exception as e:
    print(e)
    pass



class SafetyEnvelope(gym.core.Wrapper):
    """
    Safety envelope for safe exploration.
    Uses controllers for avoiding unsafe actions and shaping rewards
    """

    def __init__(self, env):
        super(SafetyEnvelope, self).__init__(env)

        # Grab configuration
        self.config = cg.Configuration.grab()

        print("Controllers: " + str(self.config.controllers))
        print("Rewards: " + str(self.config.rewards))

        # Perceptions of the agent, it gets updated at each step with the current observations
        self.perception = Perception(env.gen_obs_decoded())

        # State Machine MTSA controllers
        self.controllers = []

        # Safety controllers
        for controller in self.config.controllers.safety:
            new_controller = Controller(controller, "safe", self.perception)
            self.controllers.append(new_controller)

        # Reachability controllers
        if hasattr(self.config.controllers, 'reachability'):
            for controller in self.config.controllers.reachability:
                new_controller = Controller(controller, "reach", self.perception)
                self.controllers.append(new_controller)

        # Set controller rewards
        # self.respected_reward = self.config.rewards.controller.respected
        # self.violated_reward = self.config.rewards.controller.violated

        # Set controller rewards
        self.respected_reward = 1
        self.violated_reward = -1

        self.proposed_action = None
        self.safe_actions = None



    def observe(self):
        list_actions = []
        for controller in self.controllers:
            controller.observe(self.env)
            if controller.is_active():
                safe_actions_strings = controller.get_available_actions_for_agent()
                if self.config.debug_mode: print("  ---> available_actions: " + str(safe_actions_strings))
                list_actions.append(safe_actions_strings)
            else:
                if self.config.debug_mode: print(controller.controller_name + " is inactive, all actions allowed")
        if len(list_actions)>0:
            safe_actions = set(list_actions[0])
            if len(list_actions) > 1:
                for s in list_actions[1:]:
                    safe_actions.intersection_update(s)

                    if self.config.debug_mode: print("safe_actions: " + str(safe_actions))
            self.safe_actions = self.env.strings_to_actions(list(safe_actions))



    def step(self, proposed_action):

        self.proposed_action = self.env.action_to_string(proposed_action)

        # Updating the perceptions from raw observations
        self.perception.update(self.env.gen_obs_decoded())

        if self.config.rendering:
            self.env.render('human')

        if proposed_action == -1:
            self.observe()
        else:
            if self.config.training_mode:
                self.observe()

            if self.config.debug_mode: print("proposed_action: " + self.proposed_action)
            if self.config.debug_mode: print("safe_actions: " + str(self.safe_actions))

            # The environment model is supported by the controllers
            if self.safe_actions is not None and len(self.safe_actions) > 0:
                if proposed_action in self.safe_actions:
                    controller_action = self.proposed_action
                    if self.config.debug_mode: print("action_to_execution_1: " + controller_action)
                    obs, reward, done, info = self.env.step(proposed_action)
                    reward += self.respected_reward
                else:
                    if self.config.debug_mode: print("the proposed action is not safe! Choosing a random safe action...")
                    safe_action = random.choice(self.safe_actions)
                    controller_action = self.env.action_to_string(safe_action)
                    if self.config.debug_mode: print("action_to_execution_2: " + controller_action)
                    obs, reward, done, info = self.env.step(safe_action)
                    reward += self.violated_reward
                    info["event"].append("violation")

                for controller in self.controllers:
                    controller.act(controller_action)

            # The environment model is not supported by the controller, the agent is free to explore
            else:
                if self.config.debug_mode: print("##### Environment not modeled by the controllers -> free exploration! ######")
                obs, reward, done, info = self.env.step(proposed_action)


            if self.config.debug_mode: print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n\n")
            return obs, reward, done, info