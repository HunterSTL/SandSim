import pygame
import random

grid_width = 50
scaling = 10

fire_lifetime = 200
smoke_lifetime = 100
explosion_particle_lifetime = 10
lit_fuse_lifetime = 50

unique_number = 0

class Cell:
    def __init__(self, x, y, name, id, color, lifetime, unique_number, burning, state):
        self.x = x
        self.y = y
        self.name = name
        self.id = id
        self.color = color
        self.lifetime = lifetime
        self.unique_number = unique_number
        self.burning = burning
        self.state = state

    @classmethod
    def create(cls, x, y, name):
        global unique_number

        unique_number += 1
        cls.unique_number = unique_number

        id = Block[name].id
        initial_color = Block[name].color
        initial_lifetime = Block[name].lifetime
        burning = Block[name].burning
        state = Block[name].state

        if initial_lifetime != -1:
            #between 80% and 100% 
            lifetime_modifyer = random.random() * 0.2 + 0.8
            initial_lifetime = int(initial_lifetime * lifetime_modifyer)
            r = int(initial_color[0] * lifetime_modifyer)
            g = int(initial_color[1] * lifetime_modifyer)
            b = int(initial_color[2] * lifetime_modifyer)
            initial_color = (r, g, b)
        return cls(x, y, name, id, initial_color, initial_lifetime, unique_number, burning, state)

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

Block = {
    "Air":                  Cell(None, None, "Air", 0, (0, 0, 0), -1, None, False, "Gas"),
    "Sand":                 Cell(None, None, "Sand", 1, (200, 200, 0), -1, None, False, "Solid"),
    "Rock":                 Cell(None, None, "Rock", 2, (100, 100, 100), -1, None, False, "Solid"),
    "Water":                Cell(None, None, "Water", 3, (100, 100, 255), -1, None, False, "Liquid"),
    "Wood":                 Cell(None, None, "Wood", 4, (100, 50, 0), -1, None, False, "Solid"),
    "Water Source":         Cell(None, None, "Water Source", 5, (28, 21, 189), -1, None, False, "Solid"),
    "Sand Source":          Cell(None, None, "Sand Source", 6, (212, 136, 15), -1, None, False, "Solid"),
    "Fire":                 Cell(None, None, "Fire", 7, (232, 55, 23), fire_lifetime, None, True, "Solid"),
    "Smoke":                Cell(None, None, "Smoke", 8, (150, 150, 150), smoke_lifetime, None, False, "Gas"),
    "TNT":                  Cell(None, None, "TNT", 9, (255, 0, 0), -1, None, False, "Solid"),
    "Explosion Particle":   Cell(None, None, "Explosion Particle", 10, (255, 150, 20), explosion_particle_lifetime, None, False, "Gas"),
    "Fuse":                 Cell(None, None, "Fuse", 11, (0, 54, 11), -1, None, False, "Solid"),
    "Lit Fuse":             Cell(None, None, "Lit Fuse", 12, (232, 55, 23), lit_fuse_lifetime, None, True, "Solid"),
    "Out Of Bounds":        Cell(None, None, "Out Of Bounds", 999, (0, 255, 0), -1, None, False, "Solid")
}