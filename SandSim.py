from Classes import Grid, Sprite, Hotbar, Block
import pygame
import math
import random
import cProfile
import time
import queue

grid_width = 50
grid_height = 100
scaling = 10

explosion_size = 5

unique_number = 0

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

    if 0 < mouse_x < grid_width and 0 < mouse_y < grid_height:
        return mouse_x, mouse_y
    return 0, 0

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
        cell_below = grid.get(x, y - 1)
        cell_left = grid.get(x - 1, y)
        cell_right = grid.get(x + 1, y)
        cell_below_left = grid.get(x - 1, y - 1)
        cell_below_right = grid.get(x + 1, y - 1)

        if cell_below.state == "Gas" or cell_below.state == "Liquid":
            grid.set(x, y - 1, "Sand", unique_number)
            grid.set(x, y, cell_below.name, cell_below.unique_number)
            updated_blocks.add((x, y - 1))
        elif (cell_below_left.state == "Gas" or cell_below_left.state == "Liquid") and (cell_left.state == "Gas" or cell_left.state == "Liquid"):
            grid.set(x - 1, y - 1, "Sand", unique_number)
            grid.set(x, y, cell_below_left.name, cell_below_left.unique_number)
            updated_blocks.add((x - 1, y - 1))
        elif (cell_below_right.state == "Gas" or cell_below_right.state == "Liquid") and (cell_right.state == "Gas" or cell_right.state == "Liquid"):
            grid.set(x + 1, y - 1, "Sand", unique_number)
            grid.set(x, y, cell_below_right.name, cell_below_right.unique_number)
            updated_blocks.add((x + 1, y - 1))

    def SimulateWater(unique_number, updated_blocks):
        cell_below = grid.get(x, y - 1)
        cell_left = grid.get(x - 1, y)
        cell_right = grid.get(x + 1, y)

        if cell_below.state == "Gas":
            grid.set(x, y - 1, "Water", unique_number)
            grid.set(x, y, cell_below.name, cell_below.unique_number)
            updated_blocks.add((x, y - 1))
        elif cell_left.state == "Gas" and cell_right.state == "Gas":
            if random.randint(1, 2) == 1:
                grid.set(x - 1, y, "Water", unique_number)
                grid.set(x, y, cell_left.name, cell_left.unique_number)
                updated_blocks.add((x - 1, y))
            else:
                grid.set(x + 1, y, "Water", unique_number)
                grid.set(x, y, cell_right.name, cell_right.unique_number)
                updated_blocks.add((x + 1, y))
        elif cell_left.state == "Gas":
            grid.set(x - 1, y, "Water", unique_number)
            grid.set(x, y, cell_left.name, cell_left.unique_number)
            updated_blocks.add((x - 1, y))
        elif cell_right.state == "Gas":
            grid.set(x + 1, y, "Water", unique_number)
            grid.set(x, y, cell_right.name, cell_right.unique_number)
            updated_blocks.add((x + 1, y))

    def SimulateWaterSource():
        cell_below = grid.get(x, y - 1)
        cell_left = grid.get(x - 1, y)
        cell_right = grid.get(x + 1, y)

        if cell_below.state == "Gas":
            grid.set(x, y - 1, "Water", None)
        elif cell_left.state == "Gas":
            grid.set(x - 1, y, "Water", None)
        elif cell_right.state == "Gas":
            grid.set(x + 1, y, "Water", None)

    def SimulateSandSource():
        cell_below = grid.get(x, y - 1)
        if cell_below.state == "Gas":
            grid.set(x, y - 1, "Sand", None)
    
    def SimulateFire(cell, updated_blocks):
        for dy in range(y - 1, y + 2): 
            for dx in range(x - 1, x + 2):
                if grid.get(dx, dy).name == "Water":
                    grid.set(x, y, "Wood", None)
                    updated_blocks.add((x, y))
                    return

        if cell.lifetime > 0:
            if grid.get(x, y + 1).state == "Gas":
                if random.randint(1, 10) == 1:
                    grid.set(x, y + 1, "Smoke", None)
                    updated_blocks.add((x, y + 1))
        ReduceLifetime(cell, 1)

    def SimulateSmoke(cell, updated_blocks):
        unique_number = cell.unique_number
        cell_above = grid.get(x, y + 1)
        cell_above_left = grid.get(x - 1, y + 1)
        cell_above_right = grid.get(x + 1, y + 1)
        cell_left = grid.get(x - 1, y)
        cell_right = grid.get(x + 1, y)

        if cell_above.name == "Air" and cell_above_left.name == "Air" and cell_above_right.name == "Air":
            random_choice = random.randint(1, 3)

            if random_choice == 1:
                grid.set(x, y + 1, "Smoke", unique_number)
                updated_blocks.add((x, y + 1))
            elif random_choice == 2:
                grid.set(x - 1, y + 1, "Smoke", unique_number)
                updated_blocks.add((x - 1, y + 1))
            else:
                grid.set(x + 1, y + 1, "Smoke", unique_number)
            grid.set(x, y, "Air", None)
        elif cell_above.name == "Air":
            grid.set(x, y + 1, "Smoke", unique_number)
            grid.set(x, y, "Air", None)
        elif cell_above_left.name == "Air":
            grid.set(x - 1, y + 1, "Smoke", unique_number)
            grid.set(x, y, "Air", None)
            updated_blocks.add((x - 1, y + 1))
        elif cell_above_right.name == "Air":
            grid.set(x + 1, y + 1, "Smoke", unique_number)
            grid.set(x, y, "Air", None)
            updated_blocks.add((x + 1, y + 1))
        elif cell_left.name == "Air":
            grid.set(x - 1, y, "Smoke", unique_number)
            grid.set(x, y, "Air", None)
            updated_blocks.add((x - 1, y))
        elif cell_right.name == "Air":
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
        tnt_cells = queue.Queue()

        def ExplodeTNT(x, y):
            grid.set(x, y, "Air", None)
            tnt_cells.put((x, y))

        def ExplodeAdjacentTNT():
            new_tnt_cells = queue.Queue()
            while not tnt_cells.empty():
                x, y = tnt_cells.get()
                for dy in range(y - 1 - explosion_size, y + 2 + explosion_size): 
                    for dx in range(x - 1 - explosion_size, x + 2 + explosion_size):
                        if grid.get(dx, dy).name == "TNT":
                            new_tnt_cells.put((dx, dy))
                        if dx > 0 and dx < grid_width and dy > 0 and dy < grid_height:
                            if random.randint(1, 3) == 1:
                                grid.set(dx, dy, "Smoke", None)
                            elif random.randint(1, 5) == 1:
                                grid.set(dx, dy, "Explosion Particle", None)
                            else:
                                grid.set(dx, dy, "Air", None)
            return new_tnt_cells

        for dy in range(y - 1, y + 2): 
            for dx in range(x - 1, x + 2):
                if grid.get(dx, dy).burning == True:
                    ExplodeTNT(x, y)
                    break

        while not tnt_cells.empty():
            tnt_cells = ExplodeAdjacentTNT()
                
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
                SimulateFire(cell, updated_blocks)
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
    if x == 0 or y == 0:
        return
    size = hotbar.brush_size
    for dy in range(y + 1 - size, y + size): 
        for dx in range(x + 1 - size, x + size):
            if 0 < dx < grid_width + 1 and 0 < dy < grid_height + 1:
                grid.set(dx, dy, name, None)

def DrawBrushOutline(screen):
    global prev_brush_pos

    actual_mouse_x, actual_mouse_y = pygame.mouse.get_pos()
    mouse_x, mouse_y = CursorLocation(actual_mouse_x, actual_mouse_y)

    if mouse_x > 0 and mouse_y > 0:
        brush_size = hotbar.brush_size
        brush_rect = pygame.Rect((mouse_x - brush_size) * scaling, (grid_height - mouse_y - brush_size + 1) * scaling, (2 * brush_size - 1) * scaling, (2 * brush_size - 1) * scaling)
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
        start_time = time.time_ns()
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
        simulation_time = (time.time_ns() - start_time) // 1_000_000
        #print("frame:\t" + str(simulation_time) + "ms")
        clock.tick(60)

if __name__ == "__main__":
    drawing = False
    erasing = False
    simulation_running = False

    block_types = []
    for i in range(len(Block)):
        block_types.append(i)
    hotbar = Hotbar(block_types)
    prev_brush_pos = (None, None)
    prev_brush_size = hotbar.brush_size

    grid = Grid(grid_width, grid_height)
    InitializeScreen()
    CreateSpriteGroups()
    cProfile.run('UpdateScreen()', filename='SandSimResults')
    UpdateScreen()