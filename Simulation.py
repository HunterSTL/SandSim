from Classes import Grid, Sprite, Hotbar, Block
import random
import queue

explosion_size = 5

def SimulateGrid(grid, simulation_running):
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

    grid_width = grid.columns
    grid_height = grid.rows

    if simulation_running:
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
        return True
    return False