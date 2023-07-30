import pygame
import math
import random
import time

grid_width = 20
grid_height = 30
scaling = 10

fire_lifetime = 500
smoke_lifetime = 200
explosion_size = 5

unique_number = 0
max_frames = 10000

class Cell:
    def __init__(self, x, y, name, id, color, lifetime, unique_number):
        self.x = x
        self.y = y
        self.name = name
        self.id = id
        self.color = color
        self.lifetime = lifetime
        self.unique_number = unique_number

    @classmethod
    def create(cls, x, y, name):
        global unique_number

        unique_number += 1
        cls.unique_number = unique_number

        id = Block[name].id
        initial_color = Block[name].color
        initial_lifetime = Block[name].lifetime

        if initial_lifetime != -1:
            #between 80% and 100% 
            lifetime_modifyer = random.random() * 0.2 + 0.8
            initial_lifetime = int(initial_lifetime * lifetime_modifyer)
            r = int(initial_color[0] * lifetime_modifyer)
            g = int(initial_color[1] * lifetime_modifyer)
            b = int(initial_color[2] * lifetime_modifyer)
            initial_color = (r, g, b)
        return cls(x, y, name, id, initial_color, initial_lifetime, unique_number)

class Grid:
    def __init__(self, width, height):
        self.rows = height
        self.columns = width
        grid = []
        for y in range(height, 0, -1):
            row = []
            for x in range(1, width + 1):
                cell = Cell.create(x, y, "Air")
                row.append(cell)
            grid.append(row)
        self.grid = grid

    def get(self, x, y):
        if 1 <= x <= self.columns and 1 <= y <= self.rows:
            return self.grid[self.rows - y][x - 1]
        else:
            return Block["Out Of Bounds"]
        
    def get_by_unique_number(self, unique_number):
        for row in self.grid:
            for cell in row:
                if cell.unique_number == unique_number:
                    return cell
        return None
        
    def set(self, x, y, name, unique_number):
        if unique_number is None:
            cell = Cell.create(x, y, name)
        else:
            cell = self.get_by_unique_number(unique_number)
            cell.x = x
            cell.y = y
        self.grid[self.rows - y][x - 1] = cell

class Hotbar:
    def __init__(self, block_types):
        self.block_types = block_types
        self.selected_block = 0
        self.block_size = 4
        self.selected_block_name = Block[NameByID(self.selected_block)].name

    def select_next_block(self):
        self.selected_block = (self.selected_block + 1) % (len(self.block_types) - 1)
        self.selected_block_name = Block[NameByID(self.selected_block)].name

    def select_previous_block(self):
        self.selected_block = (self.selected_block - 1) % (len(self.block_types) - 1)
        self.selected_block_name = Block[NameByID(self.selected_block)].name

    def draw(self, screen, y_offset):
        hotbar_rect = pygame.Rect(0, y_offset, grid_width * self.block_size * self.block_size, self.block_size)
        pygame.draw.rect(screen, (50, 50, 50), hotbar_rect)

        for i, id in enumerate(self.block_types):
            for x in range(self.block_size):
                for y in range(self.block_size):
                    block_rect = pygame.Rect(i * self.block_size * self.block_size + x * self.block_size, y_offset + y * self.block_size + self.block_size, self.block_size, self.block_size)
                    pygame.draw.rect(screen, ColorByID(id), block_rect)

            if i == self.selected_block:
                selected_block_rect_outer = pygame.Rect(i * self.block_size * self.block_size, y_offset, self.block_size * self.block_size, self.block_size)
                pygame.draw.rect(screen, (255, 0, 0), selected_block_rect_outer, 2)

class Sprite(pygame.sprite.Sprite):
    def __init__(self, x, y, cell):
        super().__init__()
        self.image = pygame.Surface((scaling, scaling))
        self.image.fill(cell.color)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x * scaling, y * scaling)

def ColorByID(id):
    for cell in Block.values():
        if cell.id == id:
            return cell.color
    return (0, 0, 0)

def NameByID(id):
    for cell in Block.values():
        if cell.id == id:
            return cell.name
    return ""

def ReduceLifetime(cell, amount):
    if cell.lifetime != -1:
        cell.lifetime = max(cell.lifetime - amount, 0)

        if cell.lifetime == 0:
            grid.set(cell.x, cell.y, "Air", None)
        else:
            remaining_lifetime_ratio = cell.lifetime / Block[cell.name].lifetime
            r = int(Block[cell.name].color[0] * remaining_lifetime_ratio)
            g = int(Block[cell.name].color[1] * remaining_lifetime_ratio)
            b = int(Block[cell.name].color[2] * remaining_lifetime_ratio)
            cell.color = (r, g, b)

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

def InitializeScreen():
    global Screen
    global frame

    pygame.init()
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
    global smoke_group
    global tnt_group

    air_group = pygame.sprite.Group()
    sand_group = pygame.sprite.Group()
    rock_group = pygame.sprite.Group()
    water_group = pygame.sprite.Group()
    wood_group = pygame.sprite.Group()
    water_source_group = pygame.sprite.Group()
    sand_source_group = pygame.sprite.Group()
    fire_group = pygame.sprite.Group()
    smoke_group = pygame.sprite.Group()
    tnt_group = pygame.sprite.Group()

    for y, row in enumerate(grid.grid):
        for x, cell in enumerate(row):
            if cell.name == "Sand":
                sand_group.add(Sprite(x, y, cell))
            elif cell.name == "Rock":
                rock_group.add(Sprite(x, y, cell))
            elif cell.name == "Water":
                water_group.add(Sprite(x, y, cell))
            elif cell.name == "Wood":
                wood_group.add(Sprite(x, y, cell))
            elif cell.name == "Water Source":
                water_source_group.add(Sprite(x, y, cell))
            elif cell.name == "Sand Source":
                sand_source_group.add(Sprite(x, y, cell))
            elif cell.name == "Fire":
                fire_group.add(Sprite(x, y, cell))
            elif cell.name == "Smoke":
                smoke_group.add(Sprite(x, y, cell))
            elif cell.name == "TNT":
                tnt_group.add(Sprite(x, y, cell))

    sprite_groups = [air_group, sand_group, rock_group, water_group, wood_group, water_source_group, sand_source_group, fire_group, smoke_group, tnt_group]

def UpdateSpritePositions():
    global sprite_groups
    sand_group.empty()
    rock_group.empty()
    water_group.empty()
    wood_group.empty()
    water_source_group.empty()
    sand_source_group.empty()
    fire_group.empty()
    smoke_group.empty()
    tnt_group.empty()

    for y, row in enumerate(grid.grid):
        for x, cell in enumerate(row):
            if cell.name == "Sand":
                sand_group.add(Sprite(x, y, cell))
            elif cell.name == "Rock":
                rock_group.add(Sprite(x, y, cell))
            elif cell.name == "Water":
                water_group.add(Sprite(x, y, cell))
            elif cell.name == "Wood":
                wood_group.add(Sprite(x, y, cell))
            elif cell.name == "Water Source":
                water_source_group.add(Sprite(x, y, cell))
            elif cell.name == "Sand Source":
                sand_source_group.add(Sprite(x, y, cell))
            elif cell.name == "Fire":
                fire_group.add(Sprite(x, y, cell))
            elif cell.name == "Smoke":
                smoke_group.add(Sprite(x, y, cell))
            elif cell.name == "TNT":
                tnt_group.add(Sprite(x, y, cell))

def SimulateGrid(grid):
    global frame

    def SimulateSand(unique_number, updated_blocks):
        if grid.get(x, y - 1).name == "Air":
            grid.set(x, y - 1, "Sand", unique_number)
            grid.set(x, y, "Air", None)
            updated_blocks.add((x, y - 1))
        elif grid.get(x, y - 1).name == "Water":
            grid.set(x, y - 1, "Sand", unique_number)
            grid.set(x, y, "Water", None)
            updated_blocks.add((x, y - 1))
        elif grid.get(x - 1, y - 1).name == "Air" and grid.get(x - 1, y).name == "Air":
            grid.set(x - 1, y - 1, "Sand", unique_number)
            grid.set(x, y, "Air", None)
            updated_blocks.add((x - 1, y - 1))
        elif grid.get(x + 1, y - 1).name == "Air" and grid.get(x + 1, y).name == "Air":
            grid.set(x + 1, y - 1, "Sand", unique_number)
            grid.set(x, y, "Air", None)
            updated_blocks.add((x + 1, y - 1))

    def SimulateWater(unique_number, updated_blocks):
        if grid.get(x, y - 1).name == "Air":
            grid.set(x, y - 1, "Water", unique_number)
            grid.set(x, y, "Air", None)
            updated_blocks.add((x, y - 1))
        elif grid.get(x - 1, y).name == "Air" and grid.get(x + 1, y).name == "Air":
            if random.randint(1, 2) == 1:
                grid.set(x - 1, y, "Water", unique_number)
                updated_blocks.add((x - 1, y))
            else:
                grid.set(x + 1, y, "Water", unique_number)
                updated_blocks.add((x + 1, y))
            grid.set(x, y, "Air", None)
        elif grid.get(x - 1, y).name == "Air":
            grid.set(x - 1, y, "Water", unique_number)
            grid.set(x, y, "Air", None)
            updated_blocks.add((x - 1, y))
        elif grid.get(x + 1, y).name == "Air":
            grid.set(x + 1, y, "Water", unique_number)
            grid.set(x, y, "Air", None)
            updated_blocks.add((x + 1, y))

    def SimulateWaterSource():
        if grid.get(x, y - 1).name == "Air":
            grid.set(x, y - 1, "Water", None)
        elif grid.get(x - 1, y).name == "Air":
            grid.set(x - 1, y, "Water", None)
        elif grid.get(x + 1, y).name == "Air":
            grid.set(x + 1, y, "Water", None)

    def SimulateSandSource():
        if grid.get(x, y - 1).name == "Air":
            grid.set(x, y - 1, "Sand", None)
    
    def SimulateFire(unique_number, updated_blocks):
        for dy in range(y - 1, y + 2): 
            for dx in range(x - 1, x + 2):
                if grid.get(dx, dy).name == "Water":
                    grid.set(x, y, "Wood", None)
                    updated_blocks.add((x, y))
                    return

        cell = grid.get_by_unique_number(unique_number)
        if cell.lifetime > 0:
            if grid.get(x, y + 1).name == "Air":
                if random.randint(1, 10) == 1:
                    grid.set(x, y + 1, "Smoke", None)
                    updated_blocks.add((x, y + 1))
        ReduceLifetime(cell, 1)

    def SimulateSmoke(unique_number, updated_blocks):
        cell = grid.get_by_unique_number(unique_number)

        if grid.get(x, y + 1).name == "Air":
            grid.set(x, y + 1, "Smoke", unique_number)
            grid.set(x, y, "Air", None)
            updated_blocks.add((x, y + 1))
        elif grid.get(x - 1, y + 1).name == "Air":
            grid.set(x - 1, y + 1, "Smoke", unique_number)
            grid.set(x, y, "Air", None)
            updated_blocks.add((x - 1, y + 1))
        elif grid.get(x + 1, y + 1).name == "Air":
            grid.set(x + 1, y + 1, "Smoke", unique_number)
            grid.set(x, y, "Air", None)
            updated_blocks.add((x + 1, y + 1))
        elif grid.get(x - 1, y).name == "Air":
            grid.set(x - 1, y, "Smoke", unique_number)
            grid.set(x, y, "Air", None)
            updated_blocks.add((x - 1, y))
        elif grid.get(x + 1, y).name == "Air":
            grid.set(x + 1, y, "Smoke", unique_number)
            grid.set(x, y, "Air", None)
            updated_blocks.add((x + 1, y))
        ReduceLifetime(cell, 1)
    
    def SimulateWood(updated_blocks):
        for dy in range(y - 1, y + 2): 
            for dx in range(x - 1, x + 2):
                if grid.get(dx, dy).name == "Water":
                    return
        
        fire_count = 0
        for dy in range(y - 1, y + 2): 
            for dx in range(x - 1, x + 2):
                if grid.get(dx, dy).name == "Fire":
                    fire_count += 1
        
        fire_chance = 9 - fire_count
        if fire_count > 0 and random.randint(1, fire_chance * 5) == 1:
            grid.set(x, y, "Fire", None)
            updated_blocks.add((x, y))
    
    def SimulateTNT():
        def ExplodeTNT(x, y):
            grid.set(x, y, "Air", None)
            for dy in range(y - 1 - explosion_size, y + 2 + explosion_size): 
                for dx in range(x - 1 - explosion_size, x + 2 + explosion_size):
                    if grid.get(dx, dy).name == "TNT":
                        ExplodeTNT(dx, dy)
                    if dx > 0 and dx < grid_width and dy > 0 and dy < grid_height:
                        grid.set(dx, dy, "Smoke", None)

        for dy in range(y - 1, y + 2): 
            for dx in range(x - 1, x + 2):
                if grid.get(dx, dy).name == "Fire":
                    ExplodeTNT(x, y)
                    return

    if simulation_running and not drawing:
        if frame < max_frames:
            frame += 1
            updated_blocks = set()

            for x in range(1, grid_width + 1):
                for y in range(1, grid_height + 1):
                    cell = grid.get(x, y)

                    if cell.name == "Sand" and (x, y) not in updated_blocks:
                        SimulateSand(cell.unique_number, updated_blocks)
                    elif cell.name == "Water" and (x, y) not in updated_blocks:
                        SimulateWater(cell.unique_number, updated_blocks)
                    elif cell.name == "Wood" and (x, y) not in updated_blocks:
                        SimulateWood(updated_blocks)
                    elif cell.name == "Water Source" and (x, y) not in updated_blocks:
                        SimulateWaterSource()
                    elif cell.name == "Sand Source" and (x, y) not in updated_blocks:
                        SimulateSandSource()
                    elif cell.name == "Fire" and (x, y) not in updated_blocks:
                        SimulateFire(cell.unique_number, updated_blocks)
                    elif cell.name == "Smoke" and (x, y) not in updated_blocks:
                        SimulateSmoke(cell.unique_number, updated_blocks)
                    elif cell.name == "TNT" and (x, y) not in updated_blocks:
                        SimulateTNT()

def DrawGrid(Screen, sprite_groups):
    Screen.fill(Block["Air"].color)
    for sprite_group in sprite_groups:
        sprite_group.draw(Screen)

def UpdateScreen():
    global simulation_running
    global drawing
    global erasing

    clock = pygame.time.Clock()

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
                        grid.set(mouse_x, mouse_y, hotbar.selected_block_name, None)
                elif event.button == 3:
                    actual_mouse_x, actual_mouse_y = pygame.mouse.get_pos()
                    mouse_x, mouse_y = CursorLocation(actual_mouse_x, actual_mouse_y)
                    if mouse_x + mouse_y > 0:
                        grid.set(mouse_x, mouse_y, "Air", None)
            elif event.type == pygame.MOUSEMOTION:
                if drawing:
                    actual_mouse_x, actual_mouse_y = pygame.mouse.get_pos()
                    mouse_x, mouse_y = CursorLocation(actual_mouse_x, actual_mouse_y)
                    if mouse_x + mouse_y > 0:
                        grid.set(mouse_x, mouse_y, hotbar.selected_block_name, None)
                elif erasing:
                    actual_mouse_x, actual_mouse_y = pygame.mouse.get_pos()
                    mouse_x, mouse_y = CursorLocation(actual_mouse_x, actual_mouse_y)
                    if mouse_x + mouse_y > 0:
                        grid.set(mouse_x, mouse_y, "Air", None)

        if pygame.mouse.get_pressed()[0]:
            drawing = True
            erasing = False
        elif pygame.mouse.get_pressed()[2]:
            drawing = False
            erasing = True
        else:
            drawing = False
            erasing = False

        clock.tick(60)

        SimulateGrid(grid)
        UpdateSpritePositions()
        DrawGrid(Screen, sprite_groups)
        hotbar.draw(Screen, grid_height * scaling)
        pygame.display.flip()

Block = {
    "Air":              Cell(None, None, "Air", 0, (0, 0, 0), -1, None),
    "Sand":             Cell(None, None, "Sand", 1, (200, 200, 0), -1, None),
    "Rock":             Cell(None, None, "Rock", 2, (100, 100, 100), -1, None),
    "Water":            Cell(None, None, "Water", 3, (100, 100, 255), -1, None),
    "Wood":             Cell(None, None, "Wood", 4, (100, 50, 0), -1, None),
    "Water Source":     Cell(None, None, "Water Source", 5, (50, 50, 127), -1, None),
    "Sand Source":      Cell(None, None, "Sand Source", 6, (100, 100, 0), -1, None),
    "Fire":             Cell(None, None, "Fire", 7, (245, 84, 66), fire_lifetime, None),
    "Smoke":            Cell(None, None, "Smoke", 8, (150, 150, 150), smoke_lifetime, None),
    "TNT":              Cell(None, None, "TNT", 9, (255, 0, 0), -1, None),
    "Out Of Bounds":    Cell(None, None, "Out Of Bounds", 999, (0, 255, 0), -1, None)
}

if __name__ == "__main__":
    drawing = False
    erasing = False
    simulation_running = False

    block_types = []
    for i in range(len(Block)):
        block_types.append(i)
    hotbar = Hotbar(block_types)

    grid = Grid(grid_width, grid_height)
    InitializeScreen()
    CreateSpriteGroups()
    UpdateScreen()