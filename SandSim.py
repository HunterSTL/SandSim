import pygame
import math
import random

grid_width = 50
grid_height = 50
scaling = 20

max_frames = 10000

BlockColor = {
    0: (0, 0, 0),       # Air
    1: (200, 200, 0),   # Sand
    2: (100, 100, 100), # Rock
    3: (100, 100, 255), # Water
    4: (100, 50, 0),    # Wood
    5: (50, 50, 127),   # Water Source
    6: (100, 100, 0),   # Sand Source
    7: (245, 84, 66)    # Fire
}

class GridObject:
    def initialize(self, width, height):
        self.Rows = height
        self.Columns = width
        grid = []
        for y in range(height, 0, -1):
            row = []
            for x in range(1, width + 1):
                row.append(0)
            grid.append(row)
        self.Grid = grid

    def Get(self, x, y):
        if 1 <= x <= self.Columns and 1 <= y <= self.Rows:
            return self.Grid[self.Rows - y][x - 1]
        else:
            return None

    def Set(self, x, y, id):
        self.Grid[self.Rows - y][x - 1] = id

class Block(pygame.sprite.Sprite):
    def __init__(self, x, y, id):
        super().__init__()
        self.image = pygame.Surface((scaling, scaling))
        self.image.fill(BlockColor[id])
        self.rect = self.image.get_rect()
        self.rect.topleft = (x * scaling, y * scaling)

class Hotbar:
    def __init__(self, block_types):
        self.block_types = block_types
        self.selected_block = 0
        self.block_size = 4

    def select_next_block(self):
        self.selected_block = (self.selected_block + 1) % len(self.block_types)

    def select_previous_block(self):
        self.selected_block = (self.selected_block - 1) % len(self.block_types)

    def draw(self, screen, x_offset, y_offset):
        hotbar_rect = pygame.Rect(0, y_offset, grid_width * self.block_size * self.block_size, self.block_size)
        pygame.draw.rect(screen, (50, 50, 50), hotbar_rect)

        for i, block_id in enumerate(self.block_types):
            for x in range(self.block_size):
                for y in range(self.block_size):
                    block_rect = pygame.Rect(i * self.block_size * self.block_size + x * self.block_size, y_offset + y * self.block_size + self.block_size, self.block_size, self.block_size)
                    pygame.draw.rect(screen, BlockColor[block_id], block_rect)

            if i == self.selected_block:
                selected_block_rect_outer = pygame.Rect(i * self.block_size * self.block_size, y_offset, self.block_size * self.block_size, self.block_size)
                pygame.draw.rect(screen, (255, 0, 0), selected_block_rect_outer, 2)

def PrintGrid(GridObject):
    grid = GridObject.Grid
    for row in grid:
        row_string = ''.join([str(id) for id in row])
        print(row_string)

def DrawBlock(Screen, x, y, id):    
    Square = pygame.Rect(x * scaling, y * scaling, scaling, scaling)
    pygame.draw.rect(Screen, BlockColor[id], Square)

def DrawGrid(Screen, sprite_groups):
    Screen.fill(BlockColor[0])
    for sprite_group in sprite_groups:
        sprite_group.draw(Screen)

def CursorLocation(mouse_x, mouse_y):
    mouse_x /= scaling
    mouse_y /= scaling
    mouse_x = math.ceil(mouse_x)
    mouse_y = math.ceil(mouse_y)
    mouse_y = grid_height + 1 - mouse_y

    if mouse_x <= 0 or mouse_x > grid_width:
        return 0, 0
    if mouse_y <= 0 or mouse_y > grid_height:
        return 0, 0
    return mouse_x, mouse_y

def UpdateScreen():
    global frame
    global simulation_running
    global Screen
    global sprite_groups
    global grid

    def InitializeScreen():
        global frame
        global simulation_running
        global Screen

        pygame.init()
        simulation_running = False
        hotbar_height = 50
        screen_width = grid_width * scaling
        screen_height = grid_height * scaling + hotbar_height
        Screen = pygame.display.set_mode((screen_width, screen_height))
        frame = 0
        pygame.display.set_caption("Sand Simulation")

    def CreateSpriteGroups():
        global grid
        global sprite_groups
        global air_group
        global sand_group
        global rock_group
        global water_group
        global wood_group
        global water_source_group
        global sand_source_group
        global fire_group

        air_group = pygame.sprite.Group()
        sand_group = pygame.sprite.Group()
        rock_group = pygame.sprite.Group()
        water_group = pygame.sprite.Group()
        wood_group = pygame.sprite.Group()
        water_source_group = pygame.sprite.Group()
        sand_source_group = pygame.sprite.Group()
        fire_group = pygame.sprite.Group()

        for y, row in enumerate(grid.Grid):
            for x, id in enumerate(row):
                if id == 1:
                    sand_group.add(Block(x, y, 1))
                elif id == 2:
                    rock_group.add(Block(x, y, 2))
                elif id == 3:
                    water_group.add(Block(x, y, 3))
                elif id == 4:
                    wood_group.add(Block(x, y, 4))
                elif id == 5:
                    water_source_group.add(Block(x, y, 5))
                elif id == 6:
                    sand_source_group.add(Block(x, y, 6))
                elif id == 7:
                    fire_group.add(Block(x, y, 7))

        sprite_groups = [air_group, sand_group, rock_group, water_group, wood_group, water_source_group, sand_source_group, fire_group]

    def UpdateSpritePositions():
        global sprite_groups
        sand_group.empty()
        rock_group.empty()
        water_group.empty()
        wood_group.empty()
        water_source_group.empty()
        sand_source_group.empty()
        fire_group.empty()

        for y, row in enumerate(grid.Grid):
            for x, id in enumerate(row):
                if id == 1:
                    sand_group.add(Block(x, y, 1))
                elif id == 2:
                    rock_group.add(Block(x, y, 2))
                elif id == 3:
                    water_group.add(Block(x, y, 3))
                elif id == 4:
                    wood_group.add(Block(x, y, 4))
                elif id == 5:
                    water_source_group.add(Block(x, y, 5))
                elif id == 6:
                    sand_source_group.add(Block(x, y, 6))
                elif id == 7:
                    fire_group.add(Block(x, y, 7))

    def SimulateGrid(GridObject):
        global frame

        def SimulateSand(x, y, updated_blocks):
            if GridObject.Get(x, y - 1) == 0:
                GridObject.Set(x, y, 0)
                GridObject.Set(x, y - 1, 1)
                updated_blocks.add((x, y - 1))
            elif GridObject.Get(x, y - 1) == 3:
                GridObject.Set(x, y, 3)
                GridObject.Set(x, y - 1, 1)
                updated_blocks.add((x, y - 1))
            elif GridObject.Get(x - 1, y - 1) == 0 and GridObject.Get(x - 1, y) == 0:
                GridObject.Set(x, y, 0)
                GridObject.Set(x - 1, y - 1, 1)
                updated_blocks.add((x - 1, y - 1))
            elif GridObject.Get(x + 1, y - 1) == 0 and GridObject.Get(x + 1, y) == 0:
                GridObject.Set(x, y, 0)
                GridObject.Set(x + 1, y - 1, 1)
                updated_blocks.add((x + 1, y - 1))

        def SimulateWater(x, y, updated_blocks):
            if GridObject.Get(x, y - 1) == 0:
                GridObject.Set(x, y, 0)
                GridObject.Set(x, y - 1, 3)
                updated_blocks.add((x, y - 1))
            elif GridObject.Get(x - 1, y) == 0 and GridObject.Get(x + 1, y) == 0:
                GridObject.Set(x, y, 0)
                if random.randint(1, 2) == 1:
                    GridObject.Set(x - 1, y, 3)
                    updated_blocks.add((x - 1, y))
                else:
                    GridObject.Set(x + 1, y, 3)
                    updated_blocks.add((x + 1, y))
            elif GridObject.Get(x - 1, y) == 0:
                GridObject.Set(x, y, 0)
                GridObject.Set(x - 1, y, 3)
                updated_blocks.add((x - 1, y))
            elif GridObject.Get(x + 1, y) == 0:
                GridObject.Set(x, y, 0)
                GridObject.Set(x + 1, y, 3)
                updated_blocks.add((x + 1, y))

        def SimulateWaterSource(x, y, updated_blocks):
            if GridObject.Get(x, y - 1) == 0:
                GridObject.Set(x, y - 1, 3)
            elif GridObject.Get(x - 1, y) == 0:
                GridObject.Set(x - 1, y, 3)
            elif GridObject.Get(x + 1, y) == 0:
                GridObject.Set(x + 1, y, 3)

        def SimulateSandSource(x, y, updated_blocks):
            if GridObject.Get(x, y - 1) == 0:
                GridObject.Set(x, y - 1, 1)
        
        def SimulateFire(x, y, z, updated_blocks):
            for dy in range(y - 1, y + 2): 
                for dx in range(x - 1, x + 2):
                    if GridObject.Get(dx, dy) == 4 and random.randint(1, 1000) == 1:
                        GridObject.Set(dx, dy, 7)

        if simulation_running and not drawing:
            if frame < max_frames:
                frame += 1
                updated_blocks = set()

                for x in range(1, grid_width + 1):
                    for y in range(1, grid_height + 1):
                        current_block = GridObject.Get(x, y)

                        if current_block == 1 and (x, y) not in updated_blocks:
                            SimulateSand(x, y, updated_blocks)
                        elif current_block == 3 and (x, y) not in updated_blocks:
                            SimulateWater(x, y, updated_blocks)
                        elif current_block == 5 and (x, y) not in updated_blocks:
                            SimulateWaterSource(x, y, updated_blocks)
                        elif current_block == 6 and (x, y) not in updated_blocks:
                            SimulateSandSource(x, y, updated_blocks)
                        elif current_block == 7 and (x, y) not in updated_blocks:
                            SimulateFire(x, y, 5, updated_blocks)
        pass

    grid = GridObject()
    grid.initialize(grid_width, grid_height)

    InitializeScreen()
    CreateSpriteGroups()

    drawing = False
    erasing = False
    hotbar = Hotbar([0, 1, 2, 3, 4, 5, 6, 7])

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    simulation_running = not simulation_running
                elif event.key == pygame.K_RIGHT:
                    hotbar.select_next_block()
                elif event.key == pygame.K_LEFT:
                    hotbar.select_previous_block()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    actual_mouse_x, actual_mouse_y = pygame.mouse.get_pos()
                    mouse_x, mouse_y = CursorLocation(actual_mouse_x, actual_mouse_y)
                    if mouse_x + mouse_y > 0:
                        grid.Set(mouse_x, mouse_y, hotbar.selected_block)
                elif event.button == 3:
                    actual_mouse_x, actual_mouse_y = pygame.mouse.get_pos()
                    mouse_x, mouse_y = CursorLocation(actual_mouse_x, actual_mouse_y)
                    if mouse_x + mouse_y > 0:
                        grid.Set(mouse_x, mouse_y, 0)
            elif event.type == pygame.MOUSEMOTION:
                if drawing:
                    actual_mouse_x, actual_mouse_y = pygame.mouse.get_pos()
                    mouse_x, mouse_y = CursorLocation(actual_mouse_x, actual_mouse_y)
                    if mouse_x + mouse_y > 0:
                        grid.Set(mouse_x, mouse_y, hotbar.selected_block)
                elif erasing:
                    actual_mouse_x, actual_mouse_y = pygame.mouse.get_pos()
                    mouse_x, mouse_y = CursorLocation(actual_mouse_x, actual_mouse_y)
                    if mouse_x + mouse_y > 0:
                        grid.Set(mouse_x, mouse_y, 0)

        if pygame.mouse.get_pressed()[0]:
            drawing = True
            erasing = False
        elif pygame.mouse.get_pressed()[2]:
            drawing = False
            erasing = True
        else:
            drawing = False
            erasing = False

        SimulateGrid(grid)
        UpdateSpritePositions()
        DrawGrid(Screen, sprite_groups)
        hotbar.draw(Screen, 0, grid_height * scaling)
        pygame.display.flip()

if __name__ == "__main__":
    UpdateScreen()