import time
import curses
import asyncio
import random
import curses_tools

TIC_TIMEOUT = 0.1
STARTS_SIMBOLS = '+*.:'
STARS_NUMBER = 100
BORDER_SIZE = 2


async def blink(canvas, row, column, symbol='*', TIC_TIMEOT=0.1):
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


def load_rocket_frames():
    rocket_frames = []
    for file_name in ['rocket_frame_1.txt', 'rocket_frame_2.txt']:
        with open(file_name, "r", encoding="UTF-8") as rocket_frame_file:
            rocket_frames.append(rocket_frame_file.read())
    return rocket_frames


async def animate_rocket(canvas, row, column, rocket_frames):
    while True:
        for rocket_frame in rocket_frames:
            row, column = get_rocket_position(
                canvas, row, column, controls, rocket_frame)
            curses_tools.draw_frame(
                canvas, row, column, rocket_frame)
            await asyncio.sleep(0)
            curses_tools.draw_frame(
                canvas, row, column, rocket_frame, negative=True)


def get_rocket_position(canvas, current_row, current_column, controls, frame):
    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - BORDER_SIZE, columns - BORDER_SIZE
    frame_rows, frame_columns = get_frame_size(frame)
    controls_row, controls_column, _ = controls
    row, column = current_row + controls_row, current_column + controls_column
    row = max(BORDER_SIZE, min(row, max_row - frame_rows))
    column = max(BORDER_SIZE, min(column, max_column - frame_columns))
    return row, column


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot. Direction and speed can be specified."""
    row, column = start_row, start_column
    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')
    row += rows_speed
    column += columns_speed
    symbol = '-' if columns_speed else '|'
    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1
    curses.beep()
    while BORDER_SIZE < row < max_row and 2 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


def get_frame_size(frame):
    lines = frame.splitlines()
    rows = len(lines)
    columns = max([len(line) for line in lines])
    return rows, columns


def draw(canvas):
    canvas.border()
    canvas.nodelay(True)
    curses.curs_set(False)
    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - BORDER_SIZE, columns - BORDER_SIZE
    coroutines = [blink(canvas,
                        random.randint(1, max_row),
                        random.randint(1, max_column),
                        random.choice(list(STARTS_SIMBOLS)))
                  for _ in range(STARS_NUMBER)]
    rocket_frames = load_rocket_frames()
    rocket_rows, rocket_columns = get_frame_size(rocket_frames[0])
    coroutines.append(animate_rocket(
        canvas,  max_row-10, max_column/2-2, rocket_frames))
    coroutines.append(fire(canvas, max_row-rocket_rows,
                           max_column/2, rows_speed=-0.5))
    global controls
    while True:
        controls = curses_tools.read_controls(canvas)
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        time.sleep(TIC_TIMEOUT)
        canvas.refresh()


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
