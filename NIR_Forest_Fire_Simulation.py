import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# параметры модели
N = 200
p_growth = 0.00000000001  # скорость роста деревьев новых 
base_p_ignition = 0.99  # базовая вероятность воспламенения
p_lightning = 0.00001  # вероятность удара молнии летом
steps = 500
WIND_BOOST = 2.8  # ускорение распространения огня по ветру

# 8 направлений ветра (dr, dc). dr изменение строки, dc изменение столбца
wind_directions = {
    "N": (-1, 0), "NE": (-1, 1), "E": (0, 1), "SE": (1, 1),
    "S": (1, 0), "SW": (1, -1), "W": (0, -1), "NW": (-1, -1)
}
wind_name = np.random.choice(list(wind_directions.keys()))
wind_dir = wind_directions[wind_name]
print(f"Выбранное направление ветра: {wind_name}")

# сезоны
seasons = ["spring", "summer", "autumn"]
season_start = np.random.choice(seasons)  # один раз при старте

def get_seasonal_multiplier(season):
    multipliers = {
        "spring": 1.0,
        "summer": 1.2,
        "autumn": 1.1
    }
    return multipliers[season]

def initialize_grid_with_big_river(n):
    grid = np.zeros((n, n), dtype=int)

    # заполняем поле: 0 - пусто, 1 - дерево
    for i in range(n):
        for j in range(n):
            if np.random.random() < 0.8:  # 80% деревья
                grid[i, j] = 1

    # генерация длинной извилистой реки
    river_path = [(0, np.random.randint(0, n))]
    while river_path[-1][0] < n - 1:
        x, y = river_path[-1]
        next_options = []
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < n and 0 <= ny < n:
                next_options.append((nx, ny))
        next_pos = next_options[np.random.randint(len(next_options))]
        river_path.append(next_pos)

    for x, y in river_path:
        grid[x, y] = 3  # вода

    # найти деревья и случайно выбрать одно для поджога
    tree_positions = np.argwhere(grid == 1)
    if len(tree_positions) == 0:
        print("Ошибка: деревьев нет, невозможно начать огонь.")
        return grid

    random_tree = tree_positions[np.random.randint(len(tree_positions))]
    x, y = random_tree
    grid[x, y] = 2  # огонь

    print(f"Огонь появился на позиции ({x}, {y})")
    return grid

def next_state(grid, season, wind_dir):
    new_grid = grid.copy()
    seasonal_multiplier = get_seasonal_multiplier(season)
    p_ignition = min(base_p_ignition * seasonal_multiplier, 1.0)
    n = grid.shape[0]

    for i in range(n):
        for j in range(n):
            cell = grid[i, j]
            if cell == 2:  # огонь
                new_grid[i, j] = 0  # сгорает - пусто
            elif cell == 1:  # дерево
                p_ignite_total = 0.0
                # проверяем 4 соседей
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = i + dx, j + dy
                    if 0 <= nx < n and 0 <= ny < n and grid[nx, ny] == 2:
                        # направление ОТ горящего соседа К текущей клетке
                        dir_to_cell = (-dx, -dy)
                        
                        # определяем влияние ветра
                        if dir_to_cell == wind_dir:
                            # полное совпадение с направлением ветра
                            p_neighbor = p_ignition * WIND_BOOST
                        elif (wind_dir[0] != 0 and dir_to_cell[0] == wind_dir[0] and dir_to_cell[1] == 0) or \
                             (wind_dir[1] != 0 and dir_to_cell[0] == 0 and dir_to_cell[1] == wind_dir[1]):
                            # диагональный ветер- частичное ускорение для совпадающих осей
                            p_neighbor = p_ignition * (1 + (WIND_BOOST - 1) * 0.5)
                        else:
                            p_neighbor = p_ignition
                        
                        # ограничиваем вероятность 1.0 и объединяем независимые вероятности от соседей
                        p_neighbor = min(p_neighbor, 1.0)
                        p_ignite_total = 1 - (1 - p_ignite_total) * (1 - p_neighbor)

                if np.random.random() < p_ignite_total:
                    new_grid[i, j] = 2  # загорается
                    
            elif cell == 0:  # пусто
                if np.random.random() < p_growth:
                    new_grid[i, j] = 1  # вырастает дерево

    # молния- только летом
    if season == "summer":
        if np.random.random() < p_lightning:
            tree_positions = np.argwhere(new_grid == 1)
            if len(tree_positions) > 0:
                random_tree = tree_positions[np.random.randint(len(tree_positions))]
                x, y = random_tree
                new_grid[x, y] = 2

    return new_grid

def animate(frame_num, img, grid, season, wind_dir, ax, stats):
    new_grid = next_state(grid, season, wind_dir)
    img.set_array(new_grid)
    grid[:] = new_grid[:]
    ax.set_title(f"Season: {season} | Wind: {wind_name}", fontsize=14)

    fire_count = np.sum(grid == 2)
    stats['fire_duration'] += 1 if fire_count > 0 else 0
    stats['burned_area'] += np.sum(grid == 0) - stats['initial_empty']
    return img,

# запуск
grid = initialize_grid_with_big_river(N)

stats = {
    'fire_duration': 0,
    'burned_area': 0,
    'initial_empty': np.sum(grid == 0),
    'crossed_river': 0
}

fig, ax = plt.subplots()
# цвета: 0=серый (пусто), 1=зелёный (дерево), 2=красный (огонь), 3=синий (вода)
cmap_custom = plt.cm.colors.ListedColormap(['gray', 'green', 'red', 'blue'])
bounds = [0, 1, 2, 3, 4]
norm = plt.cm.colors.BoundaryNorm(bounds, cmap_custom.N)

img = ax.imshow(grid, cmap=cmap_custom, norm=norm)
ani = animation.FuncAnimation(
    fig, animate, 
    fargs=(img, grid, season_start, wind_dir, ax, stats),
    frames=steps,
    interval=200,
    repeat=False
)

plt.show()

# вывод статистики
final_burned_area = stats['burned_area']
fire_duration = stats['fire_duration']

water_positions = np.argwhere(grid == 3)
crossed_river = 0
for x, y in water_positions:
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nx, ny = x + dx, y + dy
        if 0 <= nx < N and 0 <= ny < N and grid[nx, ny] == 0:
            crossed_river = 1
            break
    if crossed_river:
        break

print("\n--- Статистика ---")
print(f"Площадь пожара: {final_burned_area}")
print(f"Длительность пожара (в тактах): {fire_duration}")
print(f"Время года начала: {season_start}")
print(f"Огонь перешёл через реку: {'Да' if crossed_river else 'Нет'}")
