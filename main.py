import random
import time
import asyncio
import curses

from curses_tools import draw_frame, read_controls, get_frame_size
from frames import get_rockets_frames, get_garbage_frames
from physics import update_speed
from explosion import explode
from game_over import show_gameover
from obstacles import Obstacle, show_obstacles
from game_scenario import PHRASES, get_garbage_delay_tics

TIC_TIMEOUT = 0.1
STARTS_SIMBOLS = '+*.:'
FRAME_BORDER_SIZE = 2
YEAR_TICS = int(1.5 / TIC_TIMEOUT)
INFO_WINDOW_WIDTH = 50
PLASMA_GUN_ERA = 2020
STARS_NUMBER = 200
DEV_MODE = False

coroutines = []
obstacles = []
obstacles_in_last_collisions = []
rocket_frames = get_rockets_frames()
spaceship_frame = rocket_frames[0]
year = 1957


async def sleep(tics=1):
    for _ in range(tics):
        await asyncio.sleep(0)


async def change_years():
    global year
    while True:
        for _ in range(YEAR_TICS):
            await asyncio.sleep(0)
        year += 1


async def show_messages(canvas):
    message_template = "Year: {} {}"
    while True:
        yr = message_template.format(year, PHRASES.get(year, ''))
        draw_frame(canvas, 0, 0, yr)
        await asyncio.sleep(0)
        draw_frame(canvas, 0, 0, yr, negative=True)


async def animate_spaceship():
    global spaceship_frame
    while True:
        for frame in rocket_frames:
            spaceship_frame = frame
            await asyncio.sleep(0)


async def run_spaceship(canvas, start_row, start_col):
    row, column = start_row, start_col
    row_speed, column_speed = 0, 0
    min_row, min_column = FRAME_BORDER_SIZE, FRAME_BORDER_SIZE
    max_row, max_column = get_max_row_column_of_canvas(canvas)

    while True:
        temp_spaceship_frame = spaceship_frame
        # frame_size = get_frame_size(temp_spaceship_frame)
        rows, columns = get_frame_size(temp_spaceship_frame)
        move_row, move_column, space_pressed = read_controls(canvas)
        row_speed, column_speed = update_speed(
            row_speed, column_speed, move_row, move_column)
        row, column = row + row_speed, column + column_speed

        column = min(max(min_column, column), max_column -
                     columns - FRAME_BORDER_SIZE)
        row = min(max(min_row, row), max_row -
                  rows - FRAME_BORDER_SIZE)

        collisions = [obstacle
                      for obstacle in obstacles if obstacle.has_collision(row, column, rows, columns)]
        if collisions:
            await show_gameover(canvas, start_row, start_col)

        if space_pressed and year >= PLASMA_GUN_ERA:
            coroutines.append(
                fire(canvas, row, column + columns // 2))

        draw_frame(canvas, row, column, temp_spaceship_frame)

        await sleep()
        draw_frame(canvas, row, column, temp_spaceship_frame, negative=True)


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await sleep()

    canvas.addstr(round(row), round(column), 'O')
    await sleep()
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    max_row, max_column = get_max_row_column_of_canvas(canvas)
    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await sleep()
        canvas.addstr(round(row), round(column), ' ')

        collisions = [obstacle
                      for obstacle in obstacles if obstacle.has_collision(round(row), round(column))]
        if collisions:
            obstacles_in_last_collisions.extend(collisions)
            return

        row += rows_speed
        column += columns_speed


async def blink(canvas, row, column, symbol='*'):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        for i in range(random.randint(1, 21)):
            await asyncio.sleep(0)
        canvas.addstr(row, column, symbol)
        for i in range(random.randint(1, 5)):
            await asyncio.sleep(0)
        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for i in range(random.randint(1, 6)):
            await asyncio.sleep(0)
        canvas.addstr(row, column, symbol)
        for i in range(random.randint(1, 5)):
            await asyncio.sleep(0)


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 0
    row_size, column_size = get_frame_size(garbage_frame)
    obstacle = Obstacle(row, column, row_size, column_size)
    obstacles.append(obstacle)

    while row < rows_number:
        draw_frame(canvas, row, column, garbage_frame)
        obstacle.row, obstacle.column = row, column
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)

        if obstacle in obstacles_in_last_collisions:
            obstacles_in_last_collisions.remove(obstacle)
            await explode(canvas, row + row_size // 2, column + column_size // 2)
            break

        row += speed

    obstacles.remove(obstacle)


async def fill_orbit_with_garbage(canvas, max_width):
    garbage_objects = get_garbage_frames()

    while True:
        delay_tics = get_garbage_delay_tics(year)
        if delay_tics:
            random_garbage_column = random.randint(FRAME_BORDER_SIZE,
                                                   max_width - FRAME_BORDER_SIZE)
            coroutines.append(
                fly_garbage(canvas,
                            random_garbage_column,
                            random.choice(garbage_objects)))

        await sleep(delay_tics or 1)


def get_max_row_column_of_canvas(canvas):
    max_row, max_column = canvas.getmaxyx()
    return max_row - 1, max_column - 1


def draw(canvas):
    curses.curs_set(False)
    canvas.border()
    canvas.refresh()
    canvas.nodelay(True)
    max_row, max_column = get_max_row_column_of_canvas(canvas)
    center_row, center_col = max_row // 2, max_column // 2

    info_window = canvas.derwin(
        1, INFO_WINDOW_WIDTH, max_row - FRAME_BORDER_SIZE, center_col)

    global coroutines
    coroutines = [blink(canvas,
                        random.randint(1, max_row),
                        random.randint(1, max_column),
                        random.choice(list(STARTS_SIMBOLS)))
                  for _ in range(STARS_NUMBER)]

    coroutines.append(animate_spaceship())
    coroutines.append(run_spaceship(canvas, center_row, center_col))
    coroutines.append(fill_orbit_with_garbage(canvas, max_column))
    coroutines.append(show_messages(info_window))
    coroutines.append(change_years())

    if DEV_MODE:
        coroutines.append(show_obstacles(canvas, obstacles))

    canvas.refresh()
    while True:
        exhausted_coroutines = []
        for coroutine in coroutines:
            try:
                coroutine.send(None)
            except StopIteration:
                exhausted_coroutines.append(coroutine)

        canvas.border()
        canvas.refresh()
        info_window.refresh()
        time.sleep(TIC_TIMEOUT)
        for coroutine_to_remove in exhausted_coroutines:
            coroutines.remove(coroutine_to_remove)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
