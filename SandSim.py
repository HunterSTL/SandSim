import pygame
import math
import random
import cProfile

grid_width = 100
grid_height = 80
scaling = 10

fire_lifetime = 200
smoke_lifetime = 100
explosion_particle_lifetime = 10
lit_fuse_lifetime = 50
explosion_size = 5

unique_number = 0
max_frames = 10000

class Cell:
    def __init__(self, x, y, name, id, color, lifetime, unique_number, burning):
        self.x = x
        self.y = y
        self.name = name
        self.id = id
        self.color = color
        self.lifetime = lifetime
        self.unique_number = unique_number
        self.burning = burning

    @classmethod
    def create(cls, x, y, name):
        global unique_number

        unique_number += 1
        cls.unique_number = unique_number

        id = Block[name].id
        initial_color = Block[name].color
        initial_lifetime = Block[name].lifetime
        burning = Block[name].burning

        if initial_lifetime != -1:
            #between 80% and 100% 
            lifetime_modifyer = random.random() * 0.2 + 0.8
            initial_lifetime = int(initial_lifetime * lifetime_modifyer)
            r = int(initial_color[0] * lifetime_modifyer)
            g = int(initial_color[1] * lifetime_modifyer)
            b = int(initial_color[2] * lifetime_modifyer)
            initial_color = (r, g, b)
        return cls(x, y, name, id, initial_color, initial_lifetime, unique_number, burning)

class Grid:
    def __init__(self, width, height):
        self.rows = height
        self.columns = width
        self.grid = []
        self.unique_number_to_cell = {}

        for y in range(height, 0, -1):
            row = []
            for x in range(1, width + 1):
                cell = Cell.create(x, y, "Air")
                row.append(cell)
                if cell.unique_number is not None:
                    self.unique_number_to_cell[cell.unique_number] = cell
            self.grid.append(row)

    def get(self, x, y):
        if 1 <= x <= self.columns and 1 <= y <= self.rows:
            return self.grid[self.rows - y][x - 1]
        else:
            return Block["Out Of Bounds"]
        
    def get_by_unique_number(self, unique_number):
        return self.unique_number_to_cell.get(unique_number)
        
    def set(self, x, y, name, unique_number):
        if unique_number is None:
            cell = Cell.create(x, y, name)
        else:
            cell = self.get_by_unique_number(unique_number)
            if cell is not None:
                cell.x = x
                cell.y = y
        self.grid[self.rows - y][x - 1] = cell
        if cell.unique_number is not None:
            self.unique_number_to_cell[cell.unique_number] = cell

class Hotbar:
    def __init__(self, block_types):
        self.block_types = block_types
        self.selected_block = 0
        self.block_size = 4
        self.selected_block_name = Block[NameByID(self.selected_block)].name
        self.brush_size = 1

    def change_brush_size(self, size):
        if 0 < self.brush_size + size < 10:
            self.brush_size += size

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

    sprite_groups = [pygame.sprite.Group() for _ in range(len(Block))]

    for y, row in enumerate(grid.grid):
        for x, cell in enumerate(row):
            if cell.name != "Air":
                sprite_groups[cell.id].add(Sprite(x, y, cell))

def UpdateSpritePositions():
    global sprite_groups

    for group in sprite_groups:
        group.empty()

    for y, row in enumerate(grid.grid):
        for x, cell in enumerate(row):
            if cell.name != "Air":
                sprite_groups[cell.id].add(Sprite(x, y, cell))

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

    def SimulateSmoke(cell, updated_blocks):
        unique_number = cell.unique_number

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

        for reach in range(1, 3):
            if grid.get(x, y - reach).burning == True:
                if random.randint(1, 10 * reach) == 1:
                    grid.set(x, y, "Fire", None)
            elif grid.get(x - reach, y - reach).burning == True:
                if random.randint(1, 20 * reach) == 1:
                    grid.set(x, y, "Fire", None)
            elif grid.get(x + reach, y - reach).burning == True:
                if random.randint(1, 20 * reach) == 1:
                    grid.set(x, y, "Fire", None)
            elif grid.get(x - reach, y).burning == True:
                if random.randint(1, 25 * reach) == 1:
                    grid.set(x, y, "Fire", None)
            elif grid.get(x + reach, y).burning == True:
                if random.randint(1, 25 * reach) == 1:
                    grid.set(x, y, "Fire", None)
            elif grid.get(x, y + reach).burning == True:
                if random.randint(1, 100 * reach) == 1:
                    grid.set(x, y, "Fire", None)
            elif grid.get(x - reach, y + reach).burning == True:
                if random.randint(1, 200 * reach) == 1:
                    grid.set(x, y, "Fire", None)
            elif grid.get(x + reach, y + reach).burning == True:
                if random.randint(1, 200 * reach) == 1:
                    grid.set(x, y, "Fire", None)
    
    def SimulateTNT():
        def ExplodeTNT(x, y):
            grid.set(x, y, "Air", None)
            for dy in range(y - 1 - explosion_size, y + 2 + explosion_size): 
                for dx in range(x - 1 - explosion_size, x + 2 + explosion_size):
                    if grid.get(dx, dy).name == "TNT":
                        ExplodeTNT(dx, dy)
                    if dx > 0 and dx < grid_width and dy > 0 and dy < grid_height:
                        if random.randint(1, 3) == 1:
                            grid.set(dx, dy, "Smoke", None)
                        elif random.randint(1, 5) == 1:
                            grid.set(dx, dy, "Explosion Particle", None)
                        else:
                            grid.set(dx, dy, "Air", None)

        for dy in range(y - 1, y + 2): 
            for dx in range(x - 1, x + 2):
                if grid.get(dx, dy).burning == True:
                    ExplodeTNT(x, y)
                    return
                
    def SimulateExplosionParticle(cell):
        ReduceLifetime(cell, 1)

    def SimulateFuse():
        for dy in range(y - 1, y + 2): 
            for dx in range(x - 1, x + 2):
                if grid.get(dx, dy).burning == True:
                    grid.set(x, y, "Lit Fuse", None)
                    return
                
    def SimulateLitFuse(cell):
        ReduceLifetime(cell, 1)

    if simulation_running and not drawing:
        if frame < max_frames:
            frame += 1
            updated_blocks = set()
            cell_positions = [(x, y) for x in range(1, grid_width + 1) for y in range(1, grid_height + 1)]
            random.shuffle(cell_positions)

            for x, y in cell_positions:
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
                    SimulateSmoke(cell, updated_blocks)
                elif cell.name == "TNT" and (x, y) not in updated_blocks:
                    SimulateTNT()
                elif cell.name == "Explosion Particle" and (x, y) not in updated_blocks:
                    SimulateExplosionParticle(cell)
                elif cell.name == "Fuse" and (x, y) not in updated_blocks:
                    SimulateFuse()
                elif cell.name == "Lit Fuse" and (x, y) not in updated_blocks:
                    SimulateLitFuse(cell)

def DrawGrid(Screen, sprite_groups):
    Screen.fill(Block["Air"].color)
    for sprite_group in sprite_groups:
        sprite_group.draw(Screen)

def BrushStroke(x, y, name):
    size = hotbar.brush_size
    for dy in range(y + 1 - size, y + size): 
        for dx in range(x + 1 - size, x + size):
            if 0 < dx < grid_width + 1 and 0 < dy < grid_height + 1:
                grid.set(dx, dy, name, None)

def DrawBrushOutline(screen):
    global prev_brush_pos

    actual_mouse_x, actual_mouse_y = pygame.mouse.get_pos()
    mouse_x, mouse_y = CursorLocation(actual_mouse_x, actual_mouse_y)
    brush_size = hotbar.brush_size
    brush_rect = pygame.Rect((mouse_x - brush_size) * scaling, (grid_height - mouse_y - brush_size + 1) * scaling, (2 * brush_size - 1) * scaling, (2 * brush_size - 1) * scaling)

    #DrawGrid(screen, sprite_groups)
    pygame.draw.rect(screen, (255, 255, 255), brush_rect, 1)
    prev_brush_pos = (mouse_x, mouse_y)

def UpdateScreen():
    global simulation_running
    global drawing
    global erasing
    global prev_brush_pos
    global prev_brush_size

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
                elif event.key == pygame.K_UP:
                    hotbar.change_brush_size(1)
                elif event.key == pygame.K_DOWN:
                    hotbar.change_brush_size(-1)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    actual_mouse_x, actual_mouse_y = pygame.mouse.get_pos()
                    mouse_x, mouse_y = CursorLocation(actual_mouse_x, actual_mouse_y)
                    BrushStroke(mouse_x, mouse_y, hotbar.selected_block_name)
                elif event.button == 3:
                    actual_mouse_x, actual_mouse_y = pygame.mouse.get_pos()
                    mouse_x, mouse_y = CursorLocation(actual_mouse_x, actual_mouse_y)
                    BrushStroke(mouse_x, mouse_y, "Air")
            elif event.type == pygame.MOUSEWHEEL:
                if event.y == 1:
                    hotbar.select_next_block()
                elif event.y == -1:
                    hotbar.select_previous_block()
            elif event.type == pygame.MOUSEMOTION:
                if drawing:
                    actual_mouse_x, actual_mouse_y = pygame.mouse.get_pos()
                    mouse_x, mouse_y = CursorLocation(actual_mouse_x, actual_mouse_y)
                    BrushStroke(mouse_x, mouse_y, hotbar.selected_block_name)
                elif erasing:
                    actual_mouse_x, actual_mouse_y = pygame.mouse.get_pos()
                    mouse_x, mouse_y = CursorLocation(actual_mouse_x, actual_mouse_y)
                    BrushStroke(mouse_x, mouse_y, "Air")

        if pygame.mouse.get_pressed()[0]:
            drawing = True
            erasing = False
        elif pygame.mouse.get_pressed()[2]:
            drawing = False
            erasing = True
        else:
            drawing = False
            erasing = False

        if simulation_running or drawing or erasing:
            SimulateGrid(grid)
            UpdateSpritePositions()
        DrawGrid(Screen, sprite_groups)

        DrawBrushOutline(Screen)

        hotbar.draw(Screen, grid_height * scaling)
        pygame.display.flip()
        clock.tick(60)

Block = {
    "Air":                  Cell(None, None, "Air", 0, (0, 0, 0), -1, None, False),
    "Sand":                 Cell(None, None, "Sand", 1, (200, 200, 0), -1, None, False),
    "Rock":                 Cell(None, None, "Rock", 2, (100, 100, 100), -1, None, False),
    "Water":                Cell(None, None, "Water", 3, (100, 100, 255), -1, None, False),
    "Wood":                 Cell(None, None, "Wood", 4, (100, 50, 0), -1, None, False),
    "Water Source":         Cell(None, None, "Water Source", 5, (28, 21, 189), -1, None, False),
    "Sand Source":          Cell(None, None, "Sand Source", 6, (212, 136, 15), -1, None, False),
    "Fire":                 Cell(None, None, "Fire", 7, (232, 55, 23), fire_lifetime, None, True),
    "Smoke":                Cell(None, None, "Smoke", 8, (150, 150, 150), smoke_lifetime, None, False),
    "TNT":                  Cell(None, None, "TNT", 9, (255, 0, 0), -1, None, False),
    "Explosion Particle":   Cell(None, None, "Explosion Particle", 10, (255, 150, 20), explosion_particle_lifetime, None, False),
    "Fuse":                 Cell(None, None, "Fuse", 11, (0, 54, 11), -1, None, False),
    "Lit Fuse":             Cell(None, None, "Lit Fuse", 12, (232, 55, 23), lit_fuse_lifetime, None, True),
    "Out Of Bounds":        Cell(None, None, "Out Of Bounds", 999, (0, 255, 0), -1, None, False)
}

if __name__ == "__main__":
    drawing = False
    erasing = False
    simulation_running = False

    block_types = []
    for i in range(len(Block)):
        block_types.append(i)
    hotbar = Hotbar(block_types)
    prev_brush_pos = (-1, -1)
    prev_brush_size = hotbar.brush_size

    grid = Grid(grid_width, grid_height)
    InitializeScreen()
    CreateSpriteGroups()
    #cProfile.run('UpdateScreen()', filename='SandSimResults')
    UpdateScreen()