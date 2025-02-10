import os
import sys

import numpy as np
from PIL import Image, ImageDraw


class Orientation:
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

class Actions:
    FORWARD = 0
    LEFT = 1
    RIGHT = 2
    GRAB = 3
    SHOOT = 4
    CLIMB = 5

class Percepts:
    # [stench,breeze,glitter,bump,scream]
    STENCH = 0
    BREEZE = 1
    GLITTER = 2
    BUMP = 3
    SCREAM = 4

def get_concat_h(im1, im2):
    """
    Concatenate two images
    """
    dst = Image.new('RGB', (im1.width + im2.width, im1.height))
    dst.paste(im1, (0, 0))
    dst.paste(im2, (im1.width, 0))
    return dst

class Wumpus:
    def __init__(
        self, seed=2024, size=(4,4), p_pit=0.2, Tmax=50,
        with_wumpus=True,
        start_pos=(0,0),
        start_orientation=Orientation.NORTH,
    ):
        """
        seed ... seed for random number generator
        size ... size of the grid of the Wumpus world
        p_pit ... probability of a pit
        """
        self.rng = np.random.default_rng(seed=seed)
        self.size = size

        self.with_wumpus = with_wumpus
        self.start_pos = start_pos
        self.start_orientation = start_orientation

        ## for drawing
        self.wall_width = 3 # wall width in pixels
        self.cell_size = 100 # cell size in pixels for drawing

        self.terminated = True
        self.__p_pit = p_pit
        self.__Tmax = Tmax
        self._reset_p_pit()
        self._reset_Tmax()

        self.__load_icons()
    
    def _reset_p_pit(self):
        if isinstance(self.__p_pit, float):
            self.p_pit = self.__p_pit
        else:
            low, high = self.__p_pit
            self.p_pit = np.random.uniform(low, high)

    def _reset_Tmax(self):
        if isinstance(self.__Tmax, int):
            self.Tmax = self.__Tmax
        else:
            low, high = self.__Tmax
            self.Tmax = np.random.randint(low, high)

    def __load_icons(self):
        """
        load icons
        """
        self.icons = {}

        # [stench,breeze,glitter,bump,scream]

        for name, filename in [("wumpus", "monster.png"), ("gold", "gold.png"), ("pit", "pit.png"), ("agent", "robot.png"), ("north", "robot-north.png"), ("east", "robot-east.png"), ("south", "robot-south.png"), ("west", "robot-west.png"), ("stench", "stench.png"), ("breeze", "breeze.png"), ("glitter", "glitter.png"), ("bump", "bump.png"), ("scream", "scream.png")]:
            icon = Image.open(os.path.join("icons", filename))
            icon = icon.resize((30,30), Image.Resampling.LANCZOS)
            self.icons[name] = icon

    def __index_to_pos(self, index):
        """
        Convert index to (x,y)-coordinates
        """
        y = index // self.size[0]
        x = index - y * self.size[0]

        return (x,y)

    def reset(self):
        """
        Generate a new Wumpus world
        """
        self._reset_p_pit()
        self._reset_Tmax()

        self.pos_agent = self.start_pos
        if self.pos_agent is None:
            # self.pos_agent = (np.random.randint(0, self.size[0] - 1), np.random.randint(0, self.size[1] - 1))
            self.pos_agent = (
                np.random.choice([0, self.size[0] - 1]),
                np.random.choice([0, self.size[1] - 1])
            )
        self.pos_exit = self.pos_agent
        self.orientation_agent = self.start_orientation
        if self.start_orientation is None:
            self.orientation_agent = np.random.randint(0, 4)
        
        self.has_arrow = True
        self.has_gold = False
        self.terminated = False
        self.wumpus_alive = True
        self.reward = 0

        # generate pits
        pits = self.rng.random(self.size) <= self.p_pit
        pits[self.pos_exit] = False
        self.pits = np.hstack([x.reshape((-1,1))for x in np.where(pits)])

        # select position for wumpus
        while True:
            idx_wumpus = self.rng.integers(low=0, high=np.prod(self.size))
            self.pos_wumpus = self.__index_to_pos(idx_wumpus)
            if self.pos_wumpus != self.pos_exit:
                break
        if not self.with_wumpus:
            # self.pos_wumpus = None
            self.wumpus_alive = False
            if np.random.rand() < 0.5:
                self.has_arrow = False

        # select position for gold
        idx_gold = self.rng.integers(low=0, high=np.prod(self.size))
        self.pos_gold = self.__index_to_pos(idx_gold)

        # generate initial percept
        obs = obs = np.zeros((5,), dtype=int)

        stench = self.__is_stench()
        breeze = self.__is_breeze()
        glitter = self.__is_glitter()
        bump = False
        scream = False
        
        if stench:
            obs[Percepts.STENCH] = True
        if breeze:
            obs[Percepts.BREEZE] = True
        if glitter:
            obs[Percepts.GLITTER] = True
        if bump:
            obs[Percepts.BUMP] = True
        if scream:
            obs[Percepts.SCREAM] = True

        self.obs = obs
        self.t = 0
        
        self.visited = set()
        self.visited.add(self.pos_agent)

        return self.obs

    def __offset_for_pos(self, pos):
        """
        Get the offset for drawing for a position (top left of a cell)
        """
        x_offset = self.wall_width + pos[0] * (self.cell_size + self.wall_width)
        y_offset = self.wall_width + self.size[1] * (self.wall_width + self.cell_size) - ((1 + pos[1]) * (self.cell_size + self.wall_width))

        return (x_offset, y_offset)

    def render(self):
        """
        Render the current state of the wumpus world
        """
        height = self.size[1] * (self.cell_size + self.wall_width) + self.wall_width
        width = self.size[0] * (self.cell_size + self.wall_width) + self.wall_width
        # img = 255*np.ones((width, height, 3), dtype=int)
        img = Image.new(mode='RGB', size=(width, height), color = (255,255,255))
        draw = ImageDraw.Draw(img)

        # grid
        sidx = 0
        for i in range(self.size[0] + 1):
            draw.rectangle((sidx, 0) + (sidx+self.wall_width,img.size[1]), fill=(0,0,0))
            #img[sidx:sidx+self.wall_width,:,:] = 0
            sidx += self.wall_width + self.cell_size
        sidx = 0
        for i in range(self.size[1] + 1):
            draw.rectangle((0, sidx) + (img.size[0],sidx+self.wall_width), fill=(0,0,0))
            #img[:,sidx:sidx+self.wall_width,:] = 0
            sidx += self.wall_width + self.cell_size

        # labels
        #fnt = ImageFont.truetype("Pillow/Tests/fonts/FreeMono.ttf", 40)
        for x in range(self.size[0]):
            for y in range(self.size[1]):
                x_pos = self.wall_width + 3 + x * (self.cell_size + self.wall_width)
                y_pos = img.size[1] - self.wall_width - 3 - 10 - y * (self.cell_size + self.wall_width)
                draw.text((x_pos, y_pos), f"({x+1},{y+1})", fill=(100, 100, 100)) # font=fnt, 

        # show wumpus
        if self.wumpus_alive:
            offset = self.__offset_for_pos(self.pos_wumpus)
            img.paste(self.icons["wumpus"], (offset[0] + 10, offset[1] + 10), self.icons["wumpus"])

        # show gold
        if self.pos_gold is not None:
            offset = self.__offset_for_pos(self.pos_gold)
            img.paste(self.icons["gold"], (offset[0] + 10 + self.cell_size // 2, offset[1] + 10), self.icons["gold"])

        # show pits
        for pit in self.pits:
            pos_pit = pit
            # print("  pos pit: ", pos_pit)
            offset = self.__offset_for_pos(pos_pit)
            img.paste(self.icons["pit"], (offset[0] + 10, offset[1] + 5 + self.cell_size // 2), self.icons["pit"])

        # show robot
        offset = self.__offset_for_pos(self.pos_agent)
        if self.orientation_agent == Orientation.NORTH:
            agent_icon = self.icons["north"]
        elif self.orientation_agent == Orientation.EAST:
            agent_icon = self.icons["east"]
        elif self.orientation_agent == Orientation.SOUTH:
            agent_icon = self.icons["south"]
        elif self.orientation_agent == Orientation.WEST:
            agent_icon = self.icons["west"]
        img.paste(agent_icon, (offset[0] + 10 + self.cell_size // 2, offset[1] + 5 + self.cell_size // 2), agent_icon)

        ## render percepts
        obs = self.obs
        percepts = Image.new(mode='RGB', size=(self.cell_size, height), color = (255,255,255))
        draw = ImageDraw.Draw(percepts)
        draw.text((10,10), "percepts", fill=(0,0,0))
        for i, k in [(Percepts.STENCH, "stench"), (Percepts.BREEZE, "breeze"), (Percepts.GLITTER, "glitter"), (Percepts.BUMP, "bump"), (Percepts.SCREAM, "scream")]:
            if obs[i]:
                percepts.paste(self.icons[k], (10, 30 + i*40), self.icons[k])
        
        ## render status
        status = Image.new(mode='RGB', size=(20+self.cell_size, height), color = (255,255,255))
        draw = ImageDraw.Draw(status)
        draw.text((10,10), f"reward={self.reward}", fill=(0,0,0))
        draw.text((10,30), f"terminated={self.terminated}", fill=(0,0,0))
        draw.text((10,50), f"arrow={self.has_arrow}", fill=(0,0,0))
        draw.text((10,70), f"gold={self.has_gold}", fill=(0,0,0))

        return get_concat_h(get_concat_h(img, percepts), status)
    
    def __is_glitter(self):
        # are we on a field with gold
        if self.pos_agent == self.pos_gold:
            return True
        else:
            return False
        
    def __is_stench(self):
        # are we next to a wumpus?
        if self.pos_wumpus is None:
            return False
        dx = self.pos_agent[0] - self.pos_wumpus[0]
        dy = self.pos_agent[1] - self.pos_wumpus[1]
        if np.abs(dx) + np.abs(dy) <= 1:
            return True
        else:
            return False
        
    def __is_breeze(self):
        # are we next to a pit?
        for pos_pit in self.pits:
            dx = self.pos_agent[0] - pos_pit[0]
            dy = self.pos_agent[1] - pos_pit[1]
            if np.abs(dx) + np.abs(dy) == 1:
                return True
        return False
    
    def step(self, action):
        if self.terminated:
            raise AssertionError("Environment already terminted. Reset before taking any further actions.")

        # percept variables
        # [stench,breeze,glitter,bump,scream]
        stench = False
        breeze = False
        glitter = False
        bump = False
        scream = False

        r_gold_grab = 15
        r_arrow_shoot = -4
        r_escape_with_gold = 100
        r_death = -80
        r_new_cell_explored = 2

        reward = -0.2 # any actions costs
        if self.has_gold and self.pos_agent == self.pos_exit:
            reward += 0.5
        terminated = False
        info = {}
        if action == Actions.LEFT:
            self.orientation_agent = (self.orientation_agent - 1) % 4
        elif action == Actions.RIGHT:
            self.orientation_agent = (self.orientation_agent + 1) % 4
        elif action == Actions.FORWARD:
            old_pos = self.pos_agent
            dx = 0
            dy = 0
            if self.orientation_agent == Orientation.EAST:
                dx = 1
            elif self.orientation_agent == Orientation.WEST:
                dx = -1
            elif self.orientation_agent == Orientation.NORTH:
                dy = 1
            elif self.orientation_agent == Orientation.SOUTH:
                dy = -1

            new_x = max(0, min(self.size[0] - 1, self.pos_agent[0] + dx))
            new_y = max(0, min(self.size[1] - 1, self.pos_agent[1] + dy))
    
            new_pos = (new_x, new_y)
            if old_pos == new_pos:
                bump = True
            self.pos_agent = new_pos
        elif action == Actions.SHOOT:
            if self.has_arrow:
                reward += r_arrow_shoot
                self.has_arrow = False

                # do we hit the wumpus?
                if self.orientation_agent == Orientation.NORTH:
                    dx = 0
                    dy = 1
                elif self.orientation_agent == Orientation.EAST:
                    dx = 1
                    dy = 0
                elif self.orientation_agent == Orientation.SOUTH:
                    dx = 0
                    dy = -1
                elif self.orientation_agent == Orientation.WEST:
                    dx = -1
                    dy = 0
                for i in range(max(self.size)):
                    pos_arrow = (self.pos_agent[0] + i*dx, self.pos_agent[1] + i*dy)
                    if self.pos_wumpus == pos_arrow:
                        self.wumpus_alive = False
                        scream = True
        elif action == Actions.GRAB:
            if self.pos_agent == self.pos_gold:
                self.has_gold = True
                self.pos_gold = None
                reward += r_gold_grab
        elif action == Actions.CLIMB:
            if self.pos_agent == self.pos_exit: 
                terminated = True
                if self.has_gold:
                    reward += r_escape_with_gold

        # compile percepts, check for death
        if self.wumpus_alive and (self.pos_agent == self.pos_wumpus):
            reward += r_death
            terminated = True
        for pos_pit in self.pits:
            pos_pit = (pos_pit[0], pos_pit[1])
            if self.pos_agent == pos_pit:
                reward += r_death
                terminated = True

        if self.pos_gold == self.pos_agent:
            glitter = True

        # compile observation vector
        #   [stench,breeze,glitter,bump,scream]
        obs = np.zeros((5,), dtype=int)
        stench = self.__is_stench()
        breeze = self.__is_breeze()
        glitter = self.__is_glitter()
        if stench:
            obs[Percepts.STENCH] = True
        if breeze:
            obs[Percepts.BREEZE] = True
        if glitter:
            obs[Percepts.GLITTER] = True
        if bump:
            obs[Percepts.BUMP] = True
        if scream:
            obs[Percepts.SCREAM] = True

        self.obs = obs

        num_visited = len(self.visited)
        self.visited.add(self.pos_agent)
        if len(self.visited) > num_visited and not self.has_gold: 
            reward += r_new_cell_explored

        self.t += 1
        if not terminated:
            if self.t >= (self.Tmax - 1):
                reward += r_death
                # if self.has_gold:
                #     reward -= r_gold_grab
                terminated = True
                info = "Max steps reached."

        self.terminated = terminated
        self.reward = reward
        return obs, reward, terminated, info




if __name__ == "__main__":
    import pygame

    wumpus = Wumpus(1234, size=(4,4), p_pit=0.2, start_pos=None, start_orientation=None)
    wumpus.reset()

    # initialising pygame
    pygame.init()
    img = wumpus.render()

    # creating display
    display = pygame.display.set_mode((img.width, img.height))

    img = np.array(wumpus.render()).transpose([1,0,2])
    surf = pygame.surfarray.make_surface(img)
    display.blit(surf, (0, 0))
    pygame.display.update()

    # creating a running loop
    pygame.event.clear()
    while True:
        # creating a loop to check events that
        # are occurring
        event = pygame.event.wait()
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        
        # checking if keydown event happened or not
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                wumpus.step(Actions.FORWARD)
            elif event.key == pygame.K_LEFT:
                wumpus.step(Actions.LEFT)
            elif event.key == pygame.K_RIGHT:
                wumpus.step(Actions.RIGHT)
            elif event.key == pygame.K_g:
                wumpus.step(Actions.GRAB)
            elif event.key == pygame.K_c:
                wumpus.step(Actions.CLIMB)
            elif event.key == pygame.K_t:
                wumpus.step(Actions.SHOOT)
            elif event.key == pygame.K_r:
                wumpus.reset()
            elif event.key == pygame.K_q:
                pygame.quit()
                sys.exit()

            img = np.array(wumpus.render()).transpose([1,0,2])
            surf = pygame.surfarray.make_surface(img)
            display.blit(surf, (0, 0))
            pygame.display.update()
