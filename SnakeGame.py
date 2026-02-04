from tkinter import *
from random import randint
import json
import os
from pygame import mixer

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller temp folder
        base_path = sys._MEIPASS
    except Exception:
        # Normal Python (not bundled)
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class Snake:
    def __init__(self):
        self.body_size = Snake_Body_Size
        self.coordinates = []
        self.squares = []

        start_x = (Game_Width // Space_Size // 2) * Space_Size
        start_y = (Game_Hight // Space_Size // 2) * Space_Size

        for i in range(Snake_Body_Size):
            self.coordinates.append([start_x, start_y])

        for x, y in self.coordinates:
            square = canvas.create_rectangle(x, y, x + Space_Size, y + Space_Size,
                                             fill=Snake_Color, tag='snake')
            self.squares.append(square)


class Food:
    def __init__(self):
        wall_coords = set(tuple(pos) for pos in walls)

        while True:
            x = randint(1, (Game_Width // Space_Size) - 2) * Space_Size
            y = randint(1, (Game_Hight // Space_Size) - 2) * Space_Size
            if (x, y) not in wall_coords:
                break

        self.coordinates = [x, y]
        canvas.create_oval(x, y, x + Space_Size, y + Space_Size,
                           fill=Food_Color, tag='food')


Game_Width = 0
Game_Hight = 0
Space_Size = 50
Slowness = 300
Speed_Increment = 15
Min_Slowness = 80
Snake_Body_Size = 3

WALL_COLOR = "#D16900"
walls = []
wall_squares = []

score = 0
direction = "down"
paused = False
turn_id = None
pause_menu_frame = None
high_score = 0
current_user = ''
error_label = None
snake = None
food = None
pause_text_id = None

mode = 'dark'
colors = {
    'dark':  {'bg': 'black',  'snake': 'yellow', 'food': 'red',   'text': 'white'},
    'light': {'bg': 'white',  'snake': 'yellow', 'food': 'red',   'text': 'black'}
}

SNAKE_COLOR_OPTIONS = [
    "#FFFF00", 
    "#00FF00",    
    "#FF4500",    
    "#FF69B4",    
    "#00BFFF",    
    "#9932CC",    
    "#FFFFFF",    
    "#472500",    
    "#494949",    
    "#007575"     
]

selected_snake_color = SNAKE_COLOR_OPTIONS[0]
music_playing = True
login_bg_color = '#000142'

DATA_FILE = resource_path('user_data.json')

settings_frame = None
inner_frame = None
mode_button = None
music_button = None
back_button = None
leaderboard_button = None


def create_walls():
    global walls, wall_squares
    walls.clear()
    for sq in wall_squares:
        canvas.delete(sq)
    wall_squares.clear()

    for x in range(0, Game_Width, Space_Size):
        walls.append([x, 0])
        sq = canvas.create_rectangle(x, 0, x + Space_Size, Space_Size, fill=WALL_COLOR, tag='wall')
        wall_squares.append(sq)

    for x in range(0, Game_Width, Space_Size):
        y = Game_Hight - Space_Size
        walls.append([x, y])
        sq = canvas.create_rectangle(x, y, x + Space_Size, y + Space_Size, fill=WALL_COLOR, tag='wall')
        wall_squares.append(sq)

    for y in range(Space_Size, Game_Hight - Space_Size, Space_Size):
        walls.append([0, y])
        sq = canvas.create_rectangle(0, y, Space_Size, y + Space_Size, fill=WALL_COLOR, tag='wall')
        wall_squares.append(sq)

    for y in range(Space_Size, Game_Hight - Space_Size, Space_Size):
        x = Game_Width - Space_Size
        walls.append([x, y])
        sq = canvas.create_rectangle(x, y, x + Space_Size, y + Space_Size, fill=WALL_COLOR, tag='wall')
        wall_squares.append(sq)


def next_turn():
    global score, Slowness, direction, paused, turn_id, food, snake

    if paused:
        turn_id = window.after(Slowness, next_turn)
        return

    x, y = snake.coordinates[0]

    if direction == 'up':
        y -= Space_Size
    elif direction == 'down':
        y += Space_Size
    elif direction == 'left':
        x -= Space_Size
    elif direction == 'right':
        x += Space_Size

    snake.coordinates.insert(0, [x, y])
    square = canvas.create_rectangle(x, y, x + Space_Size, y + Space_Size, fill=Snake_Color)
    snake.squares.insert(0, square)

    if x == food.coordinates[0] and y == food.coordinates[1]:
        score += 1
        label.config(text=f"Score:{score}")
        canvas.delete("food")
        food = Food()
        if Slowness > Min_Slowness:
            Slowness = max(Min_Slowness, Slowness - Speed_Increment)
    else:
        del snake.coordinates[-1]
        canvas.delete(snake.squares[-1])
        del snake.squares[-1]

    if check_game_over(snake):
        game_over()
    else:
        turn_id = window.after(Slowness, next_turn)


def change_direction(new_dir):
    global direction
    if new_dir == 'left' and direction != 'right':
        direction = new_dir
    elif new_dir == 'right' and direction != 'left':
        direction = new_dir
    elif new_dir == 'up' and direction != 'down':
        direction = new_dir
    elif new_dir == 'down' and direction != 'up':
        direction = new_dir


def check_game_over(snake):
    head_x, head_y = snake.coordinates[0]

    head_left = head_x
    head_right = head_x + Space_Size
    head_top = head_y
    head_bottom = head_y + Space_Size

    for wall_x, wall_y in walls:
        wall_left = wall_x
        wall_right = wall_x + Space_Size
        wall_top = wall_y
        wall_bottom = wall_y + Space_Size

        if not (head_right <= wall_left or head_left >= wall_right or
                head_bottom <= wall_top or head_top >= wall_bottom):
            return True

    if head_x < 0 or head_x + Space_Size > Game_Width or \
       head_y < 0 or head_y + Space_Size > Game_Hight:
        return True

    for sq in snake.coordinates[1:]:
        if head_x == sq[0] and head_y == sq[1]:
            return True

    return False


def game_over():
    global high_score, turn_id, snake, food
    if score > high_score:
        high_score = score
        data = load_data()
        data[current_user]['highscore'] = high_score
        save_data(data)

    if turn_id is not None:
        try:
            window.after_cancel(turn_id)
        except:
            pass
        turn_id = None

    canvas.delete(ALL)
    canvas.create_text(canvas.winfo_width()/2, canvas.winfo_height()/2,
                       font=("Terminal", 180), text="GAME OVER!", fill='red', tag='gameover')
    snake = None
    food = None


def restart_game():
    global score, direction, Slowness, snake, food, paused, turn_id
    try:
        pause_menu_frame.place_forget()
    except:
        pass

    if turn_id is not None:
        try:
            window.after_cancel(turn_id)
        except:
            pass
        turn_id = None

    paused = False
    canvas.delete(ALL)
    score = 0
    label.config(text=f"Score:{score}")
    Slowness = 300
    direction = "down"

    create_walls()
    snake = Snake()
    food = Food()
    turn_id = window.after(Slowness, next_turn)


def close_pause_menu():
    global paused, turn_id
    try:
        pause_menu_frame.place_forget()
    except:
        pass
    paused = False
    turn_id = window.after(Slowness, next_turn)


def exit_to_main_menu():
    global paused, turn_id, snake, food, pause_menu_frame
    if turn_id is not None:
        try:
            window.after_cancel(turn_id)
        except:
            pass
        turn_id = None
    paused = False

    try:
        canvas.destroy()
        label.destroy()
    except:
        pass

    try:
        pause_menu_frame.place_forget()
        pause_menu_frame = None
    except:
        pass

    snake = None
    food = None
    show_menu()


def open_pause_menu():
    global paused, pause_menu_frame, turn_id
    if not paused:
        paused = True
    if turn_id is not None:
        try:
            window.after_cancel(turn_id)
        except:
            pass
        turn_id = None

    if pause_menu_frame is None or not pause_menu_frame.winfo_exists():
        pause_menu_frame = Frame(window, bg=colors[mode]['bg'], bd=5, relief='ridge')
        Label(pause_menu_frame, text="Game Paused", font=("Arial", 40),
              bg=colors[mode]['bg'], fg=colors[mode]['text']).pack(pady=20)
        Button(pause_menu_frame, text="Restart", font=("Arial", 25),
               bg=colors[mode]['bg'], fg=colors[mode]['text'], command=restart_game, relief='raised').pack(pady=20, padx=50, fill='x')
        Button(pause_menu_frame, text="Resume", font=("Arial", 25),
               bg=colors[mode]['bg'], fg=colors[mode]['text'], command=close_pause_menu, relief='raised').pack(pady=20, padx=50, fill='x')
        Button(pause_menu_frame, text="Exit", font=("Arial", 25),
               bg=colors[mode]['bg'], fg=colors[mode]['text'], command=exit_to_main_menu, relief='raised').pack(pady=20, padx=50, fill='x')

    pause_menu_frame.place(relx=0.5, rely=0.5, anchor="center")


def handle_escape(event=None):
    try:
        if canvas.winfo_ismapped():
            open_pause_menu()
        else:
            window.attributes('-fullscreen', False)
    except:
        window.attributes('-fullscreen', False)


def toggle_fullscreen(event=None):
    current = window.attributes('-fullscreen')
    window.attributes('-fullscreen', not current)


def toggle_pause(event=None):
    global paused, pause_text_id, turn_id
    paused = not paused
    if paused:
        pause_text_id = canvas.create_text(Game_Width / 2, Game_Hight / 2,
                                           font=("Terminal", 60), text="PAUSED", fill='gray', tag='pause')
        if turn_id is not None:
            try:
                window.after_cancel(turn_id)
            except:
                pass
            turn_id = None
    else:
        canvas.delete('pause')
        turn_id = window.after(Slowness, next_turn)


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)


def submit():
    global current_user, high_score, error_label
    username = entry_user.get().strip()
    password = entry_pass.get().strip()
    if not username or not password:
        if error_label:
            error_label.destroy()
        error_label = Label(login_frame,
                           text="please enter username and password",
                           fg='red', bg=login_bg_color, font=("Arial", 18))
        error_label.place(relx=0.5, rely=0.78, anchor="center")
        return
    
    
    data = load_data()

    if username in data and data[username]['password'] == password:
        high_score = data[username].get('highscore', 0)
        current_user = username
        if error_label:
            error_label.destroy()
        login_frame.pack_forget()
        show_menu()
    elif username not in data:
        data[username] = {'password': password, 'highscore': 0}
        save_data(data)
        high_score = 0
        current_user = username
        if error_label:
            error_label.destroy()
        login_frame.pack_forget()
        show_menu()
    else:
        if error_label:
            error_label.destroy()
        error_label = Label(login_frame, text="Invalid password", fg='red', bg=login_bg_color, font=("Arial", 20))
        error_label.place(relx=0.5, rely=0.85, anchor="center")


def show_leaderboard():
    menu_frame.pack_forget()
    
    leaderboard_frame = Frame(window, bg=colors[mode]['bg'])
    leaderboard_frame.pack(expand=True, fill=BOTH)
    
    Label(leaderboard_frame, 
          text="Leaderboard - Top Scores", 
          font=("Arial", 60), 
          bg=colors[mode]['bg'], 
          fg=colors[mode]['text']).pack(pady=40)
    
    data = load_data()
    
    # مرتب‌سازی نزولی بر اساس highscore
    sorted_users = sorted(data.items(), key=lambda x: x[1].get('highscore', 0), reverse=True)
    
    # نمایش حداکثر ۱۰ نفر برتر
    for i, (username, info) in enumerate(sorted_users[:10], 1):
        score_val = info.get('highscore', 0)
        text = f"{i}. {username:<12} → {score_val:>5}"
        fg_color = 'gold' if i == 1 else 'silver' if i == 2 else '#cd7f32' if i == 3 else colors[mode]['text']
        
        Label(leaderboard_frame, 
              text=text, 
              font=("Consolas", 38 if i <= 3 else 32), 
              bg=colors[mode]['bg'], 
              fg=fg_color).pack(pady=6)
    
    Button(leaderboard_frame, 
           text="Back to Menu", 
           font=("Arial", 35),
           bg=colors[mode]['bg'], 
           fg=colors[mode]['text'],
           command=lambda: [leaderboard_frame.destroy(), show_menu()],
           relief='raised').pack(pady=80)


def show_menu():
    global menu_frame, welcome_label, high_label, start_button, settings_button, leaderboard_button
    menu_frame = Frame(window, bg=colors[mode]['bg'])
    menu_frame.pack(expand=True, fill=BOTH)

    welcome_label = Label(menu_frame, text=f"Welcome {current_user}", font=("Arial", 100),
                          bg=colors[mode]['bg'], fg=colors[mode]['text'])
    welcome_label.pack(pady=50)

    high_label = Label(menu_frame, text=f"High Score: {high_score}", font=("Arial", 55),
                       bg=colors[mode]['bg'], fg=colors[mode]['text'])
    high_label.pack(pady=20)

    start_button = Button(menu_frame, text="Start", font=("Arial", 40),
                          bg=colors[mode]['bg'], fg=colors[mode]['text'], 
                          command=show_color_selector, relief='raised')
    start_button.pack(pady=30)

    settings_button = Button(menu_frame, text="Settings", font=("Arial", 25),
                             bg=colors[mode]['bg'], fg=colors[mode]['text'], command=show_settings, relief='raised')
    settings_button.pack(pady=30)
    
    leaderboard_button = Button(menu_frame, text="Leaderboard", font=("Arial", 25),
                                bg=colors[mode]['bg'], fg=colors[mode]['text'], 
                                command=show_leaderboard, relief='raised')
    leaderboard_button.pack(pady=30)


def show_settings():
    global settings_frame, inner_frame, mode_button, music_button, back_button
    menu_frame.pack_forget()
    
    settings_frame = Frame(window, bg=colors[mode]['bg'])
    settings_frame.pack(expand=True, fill=BOTH)
    
    inner_frame = Frame(settings_frame, bg=colors[mode]['bg'])
    inner_frame.place(relx=0.5, rely=0.5, anchor="center")
    
    mode_button = Button(inner_frame, text="Toggle Mode", font=("Arial", 60),
                         bg=colors[mode]['bg'], fg=colors[mode]['text'],
                         command=toggle_mode, relief='raised')
    mode_button.pack(pady=40)
    
    music_button = Button(inner_frame, text="Toggle Music", font=("Arial", 50),
                          bg=colors[mode]['bg'], fg=colors[mode]['text'],
                          command=toggle_music, relief='raised')
    music_button.pack(pady=40)
    
    back_button = Button(inner_frame, text="Back", font=("Arial", 40),
                         bg=colors[mode]['bg'], fg=colors[mode]['text'],
                         command=back_to_menu, relief='raised')
    back_button.pack(pady=40)


def back_to_menu():
    settings_frame.pack_forget()
    show_menu()


def toggle_mode():
    global mode
    mode = 'light' if mode == 'dark' else 'dark'
    
    bg = colors[mode]['bg']
    fg = colors[mode]['text']
    
    if settings_frame and settings_frame.winfo_exists():
        settings_frame.config(bg=bg)
    if inner_frame and inner_frame.winfo_exists():
        inner_frame.config(bg=bg)
    if mode_button and mode_button.winfo_exists():
        mode_button.config(bg=bg, fg=fg)
    if music_button and music_button.winfo_exists():
        music_button.config(bg=bg, fg=fg)
    if back_button and back_button.winfo_exists():
        back_button.config(bg=bg, fg=fg)
    
    update_colors()


def toggle_music():
    global music_playing
    music_playing = not music_playing
    if music_playing:
        mixer.music.play(-1)
    else:
        mixer.music.stop()


def update_colors():
    bg = colors[mode]['bg']
    text = colors[mode]['text']
    snake_col = colors[mode]['snake']
    food_col = colors[mode]['food']

    try:
        if 'menu_frame' in globals() and menu_frame.winfo_exists():
            menu_frame.config(bg=bg)
            welcome_label.config(bg=bg, fg=text)
            high_label.config(bg=bg, fg=text)
            start_button.config(bg=bg, fg=text)
            settings_button.config(bg=bg, fg=text)
            if leaderboard_button and leaderboard_button.winfo_exists():
                leaderboard_button.config(bg=bg, fg=text)
    except:
        pass

    try:
        if 'settings_frame' in globals() and settings_frame.winfo_exists():
            settings_frame.config(bg=bg)
            if inner_frame and inner_frame.winfo_exists():
                inner_frame.config(bg=bg)
            if mode_button and mode_button.winfo_exists():
                mode_button.config(bg=bg, fg=text)
            if music_button and music_button.winfo_exists():
                music_button.config(bg=bg, fg=text)
            if back_button and back_button.winfo_exists():
                back_button.config(bg=bg, fg=text)
    except:
        pass

    try:
        if 'canvas' in globals() and canvas.winfo_exists():
            canvas.config(bg=bg)
            label.config(bg=bg, fg=text)
            for sq in snake.squares:
                canvas.itemconfig(sq, fill=snake_col)
            food_items = canvas.find_withtag('food')
            for item in food_items:
                canvas.itemconfig(item, fill=food_col)
            pause_items = canvas.find_withtag('pause')
            for item in pause_items:
                canvas.itemconfig(item, fill='gray')
            go_items = canvas.find_withtag('gameover')
            for item in go_items:
                canvas.itemconfig(item, fill='red')
    except:
        pass

    try:
        if pause_menu_frame and pause_menu_frame.winfo_exists():
            pause_menu_frame.config(bg=bg)
            for child in pause_menu_frame.winfo_children():
                child.config(bg=bg, fg=text)
    except:
        pass


def show_color_selector():
    global selected_snake_color
    
    menu_frame.pack_forget()
    
    selector_frame = Frame(window, bg=colors[mode]['bg'])
    selector_frame.pack(expand=True, fill=BOTH)
    
    Label(selector_frame, 
          text="Choose Your Snake Color", 
          font=("Arial", 50), 
          bg=colors[mode]['bg'], 
          fg=colors[mode]['text']).pack(pady=40)
    
    preview_canvas = Canvas(selector_frame, 
                           width=300, height=300, 
                           bg=colors[mode]['bg'], 
                           highlightthickness=0)
    preview_canvas.pack(pady=20)

    preview_squares = []
    start_x = 100
    start_y = 120
    
    def draw_preview(color):
        for sq in preview_squares:
            preview_canvas.delete(sq)
        preview_squares.clear()

        coords = [
            (start_x, start_y),                   
            (start_x, start_y + Space_Size), 
            (start_x, start_y + Space_Size*2),
            (start_x - Space_Size, start_y + Space_Size*2),
            (start_x - Space_Size, start_y + Space_Size*3),
        ]
        for x, y in coords:
            sq = preview_canvas.create_rectangle(
                x, y, x + Space_Size, y + Space_Size,
                fill=color, outline="#333333", width=1
            )
            preview_squares.append(sq)
    
    draw_preview(selected_snake_color)
    
    color_frame = Frame(selector_frame, bg=colors[mode]['bg'])
    color_frame.pack(pady=30)
    
    def select_color(color):
        global selected_snake_color
        selected_snake_color = color
        draw_preview(color)
    
    for col in SNAKE_COLOR_OPTIONS:
        btn = Button(color_frame, 
                     bg=col, 
                     width=6, height=3,
                     relief='raised',
                     command=lambda c=col: select_color(c))
        btn.pack(side=LEFT, padx=15)

    def proceed_to_game():
        selector_frame.destroy()
        start_game_with_selected_color()
    
    Button(selector_frame, 
           text="Start Game with Selected Color", 
           font=("Arial", 30),
           bg=colors[mode]['bg'], 
           fg=colors[mode]['text'],
           command=proceed_to_game,
           relief='raised').pack(pady=40)


def start_game_with_selected_color():
    global label, canvas, snake, food, score, direction, Slowness, Snake_Color, Food_Color, Background_Color, turn_id

    Snake_Color = selected_snake_color         
    Food_Color = colors[mode]['food']
    Background_Color = colors[mode]['bg']

    score = 0
    direction = "down"
    Slowness = 300
    turn_id = None

    canvas = Canvas(window, bg=Background_Color, height=Game_Hight, width=Game_Width, highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    label = Label(window, text=f"Score:{score}", font=("Arial", 30), bg=Background_Color, fg=colors[mode]['text'])
    label.place(x=20, y=10)

    window.bind('<p>', toggle_pause)

    create_walls()
    snake = Snake()
    food = Food()
    turn_id = window.after(Slowness, next_turn)


window = Tk()
window.attributes('-fullscreen', True)
window.bind('<F11>', toggle_fullscreen)
window.bind('<Escape>', handle_escape)

Game_Width = window.winfo_screenwidth()
Game_Hight = window.winfo_screenheight()

window.title("Snake Game")
window.resizable(False, False)
window.update()

window.bind('<Left>', lambda event: change_direction("left"))
window.bind('<Right>', lambda event: change_direction("right"))
window.bind('<Up>', lambda event: change_direction('up'))
window.bind('<Down>', lambda event: change_direction('down'))

mixer.init()
mixer.music.load(resource_path('The best Rock in world.mp3'))
mixer.music.play(-1)
  

login_frame = Frame(window, bg=login_bg_color)
login_frame.pack(expand=True, fill=BOTH)

user_label = Label(login_frame, text="Username:", font=("Arial", 35), bg=login_bg_color, fg=colors[mode]['text'])
user_label.place(relx=0.5, rely=0.3, anchor="center")

entry_user = Entry(login_frame, font=("Arial", 25), width=20)
entry_user.place(relx=0.5, rely=0.37, anchor="center")

pass_label = Label(login_frame, text="Password:", font=("Arial", 35), bg=login_bg_color, fg=colors[mode]['text'])
pass_label.place(relx=0.5, rely=0.45, anchor="center")

entry_pass = Entry(login_frame, show="*", font=("Arial", 25), width=20)
entry_pass.place(relx=0.5, rely=0.52, anchor="center")

submit_button = Button(login_frame, text="Submit", font=("Arial", 30),
                       bg=login_bg_color, fg=colors[mode]['text'], command=submit, relief='raised')
submit_button.place(relx=0.5, rely=0.65, anchor="center")

window.mainloop()