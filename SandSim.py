from Classes import Grid, Sprite, Hotbar, Block
from Simulation import SimulateGrid
import pygame
import math
import cProfile
import time

grid_width = 100
grid_height = 50
scaling = 5

unique_number = 0

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
    pygame.init()
    hotbar_height = 50
    screen_width = grid_width * scaling
    screen_height = grid_height * scaling + hotbar_height
    Screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Sand Simulation")
    return Screen

def CreateSpriteGroups():
    global grid
    global sprite_groups

    sprite_groups = [pygame.sprite.Group() for _ in range(len(Block))]

    for y, row in enumerate(grid.grid):
        for x, cell in enumerate(row):
            if cell.name != "Air":
                sprite_groups[cell.id].add(Sprite(x, y, cell, scaling))

def UpdateSpritePositions():
    global sprite_groups

    for group in sprite_groups:
        group.empty()

    for y, row in enumerate(grid.grid):
        for x, cell in enumerate(row):
            if cell.name != "Air":
                sprite_groups[cell.id].add(Sprite(x, y, cell, scaling))

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
    frame = 0

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

        if SimulateGrid(grid, simulation_running):
            frame += 1
        UpdateSpritePositions()
        DrawGrid(Screen, sprite_groups)
        DrawBrushOutline(Screen)

        hotbar.draw(Screen, grid_height * scaling, grid_width * scaling)
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
    Screen = InitializeScreen()
    CreateSpriteGroups()
    cProfile.run('UpdateScreen()', filename='SandSimResults')
    #UpdateScreen()