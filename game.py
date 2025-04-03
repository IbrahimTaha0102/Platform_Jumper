"""
Infinite Cat Jumper
Author: Ibrahim Taha
Version: 04.02.2025
"""
# flint was used to write comments, create ideation, and debugging.
# https://app.flintk12.com/activity/pygame-debug-le-1fe068/session/b55e9445-98d8-4071-912a-c247380bb987
# https://app.flintk12.com/activity/pygame-debug-le-1fe068/session/9c5da727-ded3-4009-88ae-44053733fb62


import pygame, random, math, sys

# ------------------------------------------------------------
# INITIAL SETUP: Pygame initialization, constants, and globals
# ------------------------------------------------------------
pygame.init()  # Initialize pygame's core modules
pygame.mixer.init()  # Initialize pygame mixer for sound effects

# Window / Screen dimensions
WIDTH, HEIGHT = 800, 600

# Create the main window surface
screen = pygame.display.set_mode((WIDTH, HEIGHT))

# Set the window title (appears in the title bar)
pygame.display.set_caption("Infinite Cat Jumper")

# --------------- Color constants (RGB format) ----------------
WHITE = (255, 255, 255)  # Used for text and fallback images
BLACK = (0, 0, 0)  # Used for background and text spacing
GREEN = (0, 255, 0)  # Used for safe platforms or fallback item color
RED = (255, 0, 0)  # Used for hazard platforms
RAINBOW = [
    (255, 0, 0),  # Red
    (255, 127, 0),  # Orange
    (255, 255, 0),  # Yellow
    (0, 255, 0),  # Green
    (0, 0, 255),  # Blue
    (75, 0, 130),  # Indigo
    (148, 0, 211)  # Violet
]

# -------------- Gameplay Constants ------------------
GRAV = 0.5  # Normal gravity every frame
EASYGRAV = 0.2  # Reduced gravity for the first jump
JUMP = 15  # Velocity for the 1st jump
DJUMP = 12  # Velocity for the 2nd jump (double jump)

# The updated level goals => 10 for Level 1, 15 for Level 2, 25 for Level 3
level_goals = [10, 15, 25]

# Will store the final score reached at each level (filled during play)
level_scores = [None, None, None]

# -------------- Load external assets ----------------
try:
    cat_img = pygame.image.load('cat.png')  # Attempt to load a cat graphic
    cat_img = pygame.transform.scale(cat_img, (50, 50))  # Resize it to 50x50
except:
    # If the file is missing, create a simple 50x50 white square
    cat_img = pygame.Surface((50, 50))
    cat_img.fill(WHITE)

try:
    item_img = pygame.image.load('obtainable.png')  # Attempt to load item graphic
    item_img = pygame.transform.scale(item_img, (30, 30))  # Resize to 30x30
except:
    # Fallback: create a 30x30 green square if the file doesn't exist
    item_img = pygame.Surface((30, 30))
    item_img.fill(GREEN)

try:
    collect_sound = pygame.mixer.Sound('sound_affect.mp3')  # Attempt to load a sound effect
except:
    collect_sound = None  # If not found, no sound will be played


# ----------------------------------------------------
# PARENT CLASS: PLAYER
# Manages the cat's position, jumps, lives, and scoring.
# ----------------------------------------------------
class Player:
    def __init__(self, x, y):
        """
        Initialize the player's state:
        - (x, y): starting position
        - w, h: dimensions of the player sprite
        - vy: vertical velocity
        - jumps: how many jumps used (0, 1, or 2)
        - score: how many items collected so far
        - lives: how many lives remain (default 3)
        - initial: True before the first jump, for lighter gravity
        - alive: False if lives reach 0
        - double_end: timestamp until which the cat scores double points
        """
        self.x = x
        self.y = y
        self.w = 50
        self.h = 50
        self.vy = 0
        self.jumps = 0
        self.score = 0
        self.lives = 3
        self.initial = True
        self.alive = True
        self.double_end = 0

    def hit(self):
        """
        Called if the cat touches a hazard (red) platform.
        Decrements lives; respawns if any remain, or sets alive=False if none left.
        """
        self.lives -= 1
        if self.lives <= 0:
            self.alive = False
        else:
            # Respawn near middle, above screen
            self.x = WIDTH // 2 - self.w // 2
            self.y = -100
            self.vy = 0
            self.jumps = 0

    def update(self, plats):
        """
        Apply gravity, then check for collisions with hazard or safe platforms.
        The first jump uses reduced gravity if the cat hasn't jumped yet.
        """
        g = EASYGRAV if (self.initial and self.jumps == 0) else GRAV

        # If cat is moving up (negative vy), reduce gravity by 40%
        if self.vy < 0:
            self.vy += g * 0.6
        else:
            self.vy += g

        # Move vertically by vy
        self.y += self.vy

        # Check hazard platforms
        for p in plats:
            # If colliding with a hazard platform => lose a life
            if (self.x + self.w > p.x and self.x < p.x + p.w and
                    self.y + self.h > p.y and self.y < p.y + p.h and p.hazard):
                self.hit()
                break

        # Check safe landing (only if still alive and moving downward)
        if self.alive and self.vy >= 0:
            for p in plats:
                if (not p.hazard and
                        self.y + self.h >= p.y and self.y + self.h <= p.y + p.h and
                        self.x + self.w > p.x and self.x < p.x + p.w):
                    # Land on top of safe platform
                    self.y = p.y - self.h
                    self.vy = 0
                    self.jumps = 0
                    self.initial = False
                    break

        # Keep the cat within the horizontal bounds of the screen
        if self.x < 0:
            self.x = 0
        if self.x + self.w > WIDTH:
            self.x = WIDTH - self.w

    def jump(self):
        """
        Allow up to 2 consecutive jumps:
        - If jumps==0 => normal jump
        - If jumps==1 => second jump
        """
        if self.jumps == 0:
            self.vy = -JUMP
            self.jumps = 1
            self.initial = False
        elif self.jumps == 1:
            self.vy = -DJUMP
            self.jumps = 2

    def move_left(self):
        """Move the cat left by a fixed speed (5 px/frame)."""
        self.x -= 5

    def move_right(self):
        """Move the cat right by a fixed speed (5 px/frame)."""
        self.x += 5

    def draw(self, surf):
        """Render the player's cat image on the given surface."""
        surf.blit(cat_img, (self.x, self.y))

    def collect(self, items):
        """
        Check for collisions with collectible items.
        If the item is special => enable double points for 5 seconds.
        """
        now = pygame.time.get_ticks()
        for it in items[:]:
            # Check bounding boxes for overlap
            if (self.x < it.get_x() + it.w and self.x + self.w > it.get_x() and
                    self.y < it.get_y() + it.h and self.y + self.h > it.get_y()):

                # If it's special => set double_end 5s from now
                if it.special:
                    self.double_end = now + 5000

                # If currently under double points, +2. Otherwise, +1
                if now < self.double_end:
                    self.score += 2
                else:
                    self.score += 1

                items.remove(it)  # Remove from the list so it won't be collected again
                if collect_sound:
                    collect_sound.play()


# ----------------------------------------------------
# PARENT CLASS: PLATFORM
# Represents a platform that can be safe or hazardous.
# Moves differently depending on the level.
# ----------------------------------------------------
class Platform:
    def __init__(self, x, y, w, h=20):
        """
        Basic rectangular platform:
        - (x, y): top-left corner
        - w, h: width and height
        - hazard: True => kills cat on contact (drawn in red)
        - For movement:
          slide => used in level 1
          vx, vy => used in level 2
          radius, angle, rot_speed, cx, cy => used in level 3 (circular motion)
        """
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.hazard = False
        self.slide = None  # Movement logic for level 1
        self.vx = 0  # Movement logic for level 2
        self.vy = 0
        self.radius = 0  # Movement logic for level 3
        self.angle = 0
        self.rot_speed = 0
        self.cx = 0
        self.cy = 0

    def draw(self, surf):
        """
        Draw the platform on the screen:
        Red if hazard, otherwise green.
        """
        color = RED if self.hazard else GREEN
        pygame.draw.rect(surf, color, (self.x, self.y, self.w, self.h))


# ----------------------------------------------------
# PARENT CLASS: ITEM
# Collectible item. May be special, giving double points.
# Can be attached to a platform to move with it.
# ----------------------------------------------------
class Item:
    def __init__(self, x, y, plat=None):
        """
        (x, y): spawn coordinates
        plat: if provided, item 'sticks' to that platform
        special: True => triggers double points in the cat
        """
        self.plat = plat
        if plat:
            # If attached to a platform => track offset from platform.x, platform.y
            self.ox = x - plat.x
            self.oy = y - plat.y
        else:
            self.x = x
            self.y = y
        self.w = 30
        self.h = 30
        self.special = False  # If True => cat gets double points temporarily

    def update(self):
        """
        If the item is attached to a platform, update its position
        based on the platform's current location.
        """
        if self.plat:
            self.x = self.plat.x + self.ox
            self.y = self.plat.y + self.oy

    def get_x(self):
        """Returns current x, calling update if needed."""
        if self.plat:
            self.update()
        return getattr(self, 'x', 0)

    def get_y(self):
        """Returns current y, calling update if needed."""
        if self.plat:
            self.update()
        return getattr(self, 'y', 0)

    def draw(self, surf):
        """
        Draw the item image (item_img). If it's special,
        also draw a rainbow-colored border that animates over time.
        """
        self.update()  # Sync item position if attached to a moving platform
        surf.blit(item_img, (self.get_x(), self.get_y()))
        if self.special:
            # Use time to pick a color from the RAINBOW list
            idx = (pygame.time.get_ticks() // 100) % len(RAINBOW)
            col = RAINBOW[idx]
            pygame.draw.rect(surf, col,
                             (self.get_x() - 2, self.get_y() - 2,
                              self.w + 4, self.h + 4), 2)


# -------------------------------------------------
# Helper function to create a random platform
# -------------------------------------------------
def gen_platform(y, dummy):
    """
    Creates a new platform at vertical position y,
    with random width between 50 and 120,
    a random horizontal position, and 20% hazard chance.

    'dummy' is just a placeholder parameter so we can
    pass extra arguments if needed without error.
    """
    w = random.randint(50, 120)
    x = random.randint(0, WIDTH - w)
    p = Platform(x, y, w)
    p.hazard = (random.random() < 0.2)  # 20% chance to be red/hazard
    return p


def spawn_item(p):
    """
    60% chance to spawn an item on top of this platform p.
    The item is "special" 12.5% of the time, awarding double points.
    """
    if random.random() < 0.6:
        x = random.randint(p.x, p.x + p.w - 30)
        y = p.y - 30
        it = Item(x, y, p)
        it.special = (random.random() < 0.125)
        return it
    return None


# ------------------------------------------------
# Start screen that appears at the beginning
# ------------------------------------------------
def start_screen():
    """
    Draw the title, instructions, and updated item requirements on screen,
    then wait until the user presses ENTER or closes the window.
    Return True if the user starts the game, False if they quit.
    """
    f1 = pygame.font.SysFont(None, 72)  # Larger font for the main title
    f2 = pygame.font.SysFont(None, 36)  # Smaller font for instructions

    # The text lines to show
    texts = [
        f1.render("Infinite Cat Jumper", True, WHITE),
        f2.render("Use LEFT and RIGHT arrows to move.", True, WHITE),
        f2.render("Press UP to jump (double jump).", True, WHITE),
        # Updated line indicating the new item requirements
        f2.render("Level 1: Collect 10 items, Level 2: 15, Level 3: 25", True, WHITE),
        f2.render("Press ENTER to start.", True, WHITE),
        f2.render("Avoid RED platforms!", True, WHITE)
    ]

    # Clear the screen to black
    screen.fill(BLACK)

    # List of vertical positions to place each text line
    positions = [
        HEIGHT // 4,  # near top
        HEIGHT // 2 - 100,
        HEIGHT // 2 - 60,
        HEIGHT // 2 - 20,
        HEIGHT // 2 + 20,
        HEIGHT // 2 + 60
    ]

    # Render each text line at the corresponding y-position
    for t, p in zip(texts, positions):
        screen.blit(t, (WIDTH // 2 - t.get_width() // 2, p))

    pygame.display.flip()

    # Wait for user input
    while True:
        ev = pygame.event.wait()
        if ev.type == pygame.QUIT:
            return False  # If the user closed the window, no game start
        if ev.type == pygame.KEYDOWN:
            if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return True  # Start the game


# -------------------------------------------------
# Function to initialize the platforms and items for
# a specified level, plus create the Player object
# -------------------------------------------------
def init_game(lvl):
    """
    lvl: the current level (1, 2, or 3)
    Returns: (player, platforms, items)
    """
    plats = []
    its = []

    # Large "starting" platform near the bottom
    sw = random.randint(100, 200)  # random width
    sx = random.randint(0, WIDTH - sw)  # random horizontal position
    sy = HEIGHT - 100  # vertical position near bottom
    start_plat = Platform(sx, sy, sw)
    start_plat.hazard = False
    plats.append(start_plat)

    # We'll fill platforms upwards from this start_plat
    y = sy - random.randint(80, 150)

    # Decide vertical spacing between platforms differently per level
    if lvl == 1:
        spacing = random.randint(80, 150)
    elif lvl == 2:
        spacing = random.randint(80, 150)
    else:  # lvl == 3
        spacing = int(random.randint(160, 300) / 1.6)

    # Keep generating platforms until we go above the top of the screen
    while y > -HEIGHT:
        p = gen_platform(y, 0)
        plats.append(p)
        it = spawn_item(p)
        if it:
            its.append(it)
        y -= spacing

    # Extra movement for Level 2
    if lvl == 2:
        for p in plats[1:]:
            p.vx = random.choice([-3, -2, -1, 1, 2, 3])
            p.vy = random.choice([-3, -2, -1, 1, 2, 3])

    # Circular movement for Level 3
    if lvl == 3:
        for p in plats[1:]:
            p.radius = random.randint(50, 150)
            p.angle = random.uniform(0, 2 * math.pi)
            p.cx = WIDTH // 2 + random.randint(-100, 100)
            p.cy = p.y
            p.rot_speed = random.uniform(0.01, 0.05)

    # Create a new player object, spawning above the screen center
    player = Player(WIDTH // 2 - 25, -100)

    return player, plats, its


# -------------------------------------------------
# Show the "transition" message between levels
# -------------------------------------------------
def level_trans(font, lvl, ttime):
    """
    Display a simple message telling the user to press ENTER to continue.
    Returns False if the user quits, True if they press ENTER.
    """
    text = font.render("Press ENTER to continue to next level.", True, WHITE)
    screen.fill(BLACK)
    screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2))
    pygame.display.flip()

    while True:
        ev = pygame.event.wait()
        if ev.type == pygame.QUIT:
            return False
        if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            return True


# -------------------------------------------------
# Saving and loading the scoreboard logic
# -------------------------------------------------
def save_score(initials, sc, ttime):
    """
    Save a new entry to scoreboard.txt, containing:
    - player's initials
    - their final score
    - their total time
    Sort by time ascending (lower is better),
    keeping only top 10 results.
    """
    scores = []
    try:
        with open("scoreboard.txt", "r") as f:
            for line in f:
                parts = line.strip().split()
                # If the line starts with "1." or "2." etc, skip that token
                if parts and parts[0].endswith('.'):
                    parts = parts[1:]
                # Now we expect something like [ABC, 25, 12.34]
                if len(parts) == 3:
                    scores.append((parts[0], int(parts[1]), float(parts[2])))
    except:
        pass

    # Add the new entry
    scores.append((initials, sc, ttime))
    # Sort by total time ascending
    scores.sort(key=lambda x: x[2])
    # Keep only top 10
    scores = scores[:10]

    # Overwrite scoreboard.txt
    with open("scoreboard.txt", "w") as f:
        for i, e in enumerate(scores, start=1):
            f.write(f"{i}. {e[0]} {e[1]} {e[2]:.2f}\n")


def check_top10(ttime):
    """
    Returns True if the player can fit in the top 10 (if there are <10 entries
    or their time is better than the worst time).
    """
    scores = []
    try:
        with open("scoreboard.txt", "r") as f:
            for line in f:
                parts = line.strip().split()
                if parts and parts[0].endswith('.'):
                    parts = parts[1:]
                if len(parts) == 3:
                    scores.append(float(parts[2]))
    except:
        # If file doesn't exist or can't read => let them in
        return True

    if len(scores) < 10:
        return True

    scores.sort()
    return ttime < scores[-1] if scores else True


def show_scoreboard(font):
    """
    Read scoreboard.txt and display each line for 5 seconds.
    If scoreboard is empty or missing => show an empty list.
    """
    try:
        with open("scoreboard.txt", "r") as ff:
            lines = ff.readlines()
    except:
        lines = []

    screen.fill(BLACK)
    title = font.render("Scoreboard", True, WHITE)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))
    y_off = 100
    for line in lines:
        txt = font.render(line.strip(), True, WHITE)
        screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, y_off))
        y_off += 40

    pygame.display.flip()
    pygame.time.wait(5000)


# ------------------------------------------------
# Victory screen (when user completes all 3 levels)
# ------------------------------------------------
def victory(font, ttime, sc):
    """
    If the user is in the top 10 => prompt for initials and save to scoreboard.
    Otherwise => just show scoreboard for 5 seconds.
    """
    if not check_top10(ttime):
        # They didn't place in top 10 => just show scoreboard
        show_scoreboard(font)
        return

    initials = ""
    while True:
        screen.fill(BLACK)
        lines = [
            font.render("Congratulations! You Won!", True, WHITE),
            font.render(f"Total Time: {ttime:.2f} sec", True, WHITE),
            font.render(f"Final Score: {sc}", True, WHITE),
            font.render("Enter your initials (3 letters): " + initials, True, WHITE)
        ]
        # Position them roughly in the middle
        screen.blit(lines[0], (WIDTH // 2 - lines[0].get_width() // 2, HEIGHT // 2 - 150))
        screen.blit(lines[1], (WIDTH // 2 - lines[1].get_width() // 2, HEIGHT // 2 - 100))
        screen.blit(lines[2], (WIDTH // 2 - lines[2].get_width() // 2, HEIGHT // 2 - 50))
        screen.blit(lines[3], (WIDTH // 2 - lines[3].get_width() // 2, HEIGHT // 2))

        pygame.display.flip()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_BACKSPACE:
                    # Remove last char
                    initials = initials[:-1]
                elif ev.key == pygame.K_RETURN and len(initials) == 3:
                    # Save results
                    save_score(initials, sc, ttime)
                    show_scoreboard(font)
                    return
                else:
                    # Only accept letters, and limit to 3
                    if len(initials) < 3 and ev.unicode.isalpha():
                        initials += ev.unicode.upper()


# ------------------------------------------------
# Game Over screen
# ------------------------------------------------
def game_over(font, sc, needed, lvl):
    """
    Display a "Game Over" message. If the player's final score
    is higher than the recorded high score => update highscore.txt.
    Then wait 5 seconds so the user can read it.
    """
    # Read current high score from file
    try:
        with open('highscore.txt', 'r') as ff:
            hi = int(ff.read())
    except:
        hi = 0

    # If new high score => store it
    if sc > hi:
        hi = sc
        with open('highscore.txt', 'w') as ff:
            ff.write(str(hi))

    # Fill unattempted levels with 0 to show in summary
    for i in range(3):
        if level_scores[i] is None:
            level_scores[i] = 0

    # Build a list of how many items were still needed for each level
    extra_msgs = []
    for i in range(3):
        short = level_goals[i] - level_scores[i]
        if short > 0:
            msg = f"Level {i + 1}: {short} more item(s) needed."
            extra_msgs.append(msg)

    # Clear screen and display "Game Over" stats
    screen.fill(BLACK)
    y = HEIGHT // 2 - 200
    lines = [
        font.render("Game Over!", True, WHITE),
        font.render(f"Final Score: {sc}", True, WHITE),
        font.render(f"Final Level: {lvl}", True, WHITE),
        font.render(f"High Score: {hi}", True, WHITE)
    ]
    # Display these lines, spaced 40 px apart vertically
    for line in lines:
        screen.blit(line, (WIDTH // 2 - line.get_width() // 2, y))
        y += 40

    # Display the "needed items" messages below that
    for msg in extra_msgs:
        surf = font.render(msg, True, WHITE)
        screen.blit(surf, (WIDTH // 2 - surf.get_width() // 2, y))
        y += 40

    pygame.display.flip()
    pygame.time.wait(5000)  # Wait 5s so user can see
    return False  # Then exit main()


# ------------------------------------------------
# MAIN GAME LOOP
# - Manages transitions across levels
# - Checks for victory or game over
# - Renders all elements each frame
# ------------------------------------------------
def main():
    global level_scores

    clock = pygame.time.Clock()  # Helps limit game FPS to ~60
    font = pygame.font.SysFont(None, 36)  # Common font for HUD/text
    total_time = 0.0  # Track total time across all levels

    # 1) Show the start menu
    if not start_screen():
        # If user closed window on start screen => end
        pygame.quit()
        return

    # 2) Start at level 1
    lvl = 1
    level_scores = [None, None, None]  # Reset each time a new game starts
    player, plats, items = init_game(lvl)  # Platforms, items, plus a new player
    start_time = pygame.time.get_ticks()  # For measuring time

    # 3) Run the game until user quits or game finishes
    running = True
    while running:
        # Process events
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
                break
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_UP:
                    # Up arrow => attempt jump
                    player.jump()
                elif ev.key == pygame.K_l:
                    # Debug: skip collecting items => jump to next level
                    player.score = level_goals[lvl - 1]
                    player.y = HEIGHT + 1  # triggers level transition

        # If user closed window, stop
        if not running:
            break

        # Handle movement keys
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            player.move_left()
        if keys[pygame.K_RIGHT]:
            player.move_right()

        # Update player physics and item collection
        player.update(plats)
        player.collect(items)

        # Check if player died (no lives left)
        if not player.alive:
            level_scores[lvl - 1] = player.score
            left = level_goals[lvl - 1] - player.score
            if left < 0:
                left = 0
            game_over(font, player.score, left, lvl)
            break  # End the game loop

        # Check if level goal is met
        if player.score >= level_goals[lvl - 1]:
            level_scores[lvl - 1] = player.score
            elapsed = (pygame.time.get_ticks() - start_time) / 1000
            total_time += elapsed
            if lvl < 3:
                # If there's another level => show transition
                cont = level_trans(font, lvl, total_time)
                if not cont:
                    break
                lvl += 1  # increment level
                # Re-init the new level
                player, plats, items = init_game(lvl)
                start_time = pygame.time.get_ticks()  # reset level timer
            else:
                # If finished level 3 => victory
                victory(font, total_time, player.score)
                break

        # -----------------------
        # Auto-scroll if cat is high on the screen
        # If cat's y < 1/3 screen height => shift everything down
        if player.y < HEIGHT / 3:
            off = (HEIGHT / 3) - player.y
            player.y += off
            for p in plats:
                p.y += off
                # Adjust platform center if level 3 so it maintains circular motion
                if lvl == 3 and hasattr(p, 'cy'):
                    p.cy += off
            for it in items:
                # If item isn't attached to a platform => shift it as well
                if not it.plat:
                    it.y += off

        # Remove platforms that moved off the bottom of the screen
        plats = [p for p in plats if p.y < HEIGHT]

        # Remove items if their platform is gone or they're off-screen
        new_items = []
        for it in items:
            if it.plat:
                # Keep item if platform is still in the game
                if it.plat in plats:
                    new_items.append(it)
            else:
                # If item is not platform-bound => remove if off-screen
                if it.get_y() < HEIGHT:
                    new_items.append(it)
        items = new_items

        # Potentially spawn new platform above the top if needed
        if plats:
            top_y = min(p.y for p in plats)
            if lvl == 1:
                spc = random.randint(80, 150)
            elif lvl == 2:
                spc = random.randint(80, 150)
            else:  # lvl == 3
                spc = int(random.randint(160, 300) / 1.6)

            # If there's space above the topmost platform
            if top_y > 0:
                new_y = top_y - spc
                new_plat = gen_platform(new_y, player.vy)
                plats.append(new_plat)
                new_it = spawn_item(new_plat)
                if new_it:
                    items.append(new_it)

                # If level 3 => give it circular motion
                if lvl == 3:
                    new_plat.radius = random.randint(50, 150)
                    new_plat.angle = random.uniform(0, 2 * math.pi)
                    new_plat.cx = WIDTH // 2 + random.randint(-100, 100)
                    new_plat.cy = new_plat.y
                    new_plat.rot_speed = random.uniform(0.01, 0.05)

        # If the cat falls off the bottom of the screen => game over unless goal is met
        if player.y > HEIGHT:
            if player.score < level_goals[lvl - 1]:
                level_scores[lvl - 1] = player.score
                left = level_goals[lvl - 1] - player.score
                game_over(font, player.score, left, lvl)
            break

        # Level-specific platform movement
        if lvl == 1:
            # Horizontal sliding
            for p in plats:
                if p.slide is None:
                    p.slide = random.choice([-3, -2, -1, 1, 2, 3])
                p.x += p.slide
                # Occasionally choose a new direction
                if random.random() < 0.01:
                    p.slide = random.choice([-3, -2, -1, 1, 2, 3])
                # Bounce at screen edges
                if p.x < 0:
                    p.x = 0
                    p.slide = abs(p.slide)
                if p.x + p.w > WIDTH:
                    p.x = WIDTH - p.w
                    p.slide = -abs(p.slide)
        elif lvl == 2:
            # 2D random bouncing
            for p in plats:
                p.x += p.vx
                p.y += p.vy
                if random.random() < 0.01:
                    p.vx = random.choice([-3, -2, -1, 1, 2, 3])
                if random.random() < 0.01:
                    p.vy = random.choice([-3, -2, -1, 1, 2, 3])
                # Bounce off screen edges
                if p.x < 0 or p.x + p.w > WIDTH:
                    p.vx *= -1
                if p.y < 0 or p.y + p.h > HEIGHT:
                    p.vy *= -1
        else:
            # lvl == 3 => circular motion
            for p in plats:
                p.x = p.cx + p.radius * math.cos(p.angle) - p.w / 2
                p.y = p.cy + p.radius * math.sin(p.angle) - p.h / 2
                p.angle += p.rot_speed

        # ---------------------------
        # DRAW PHASE: Render objects
        # ---------------------------
        screen.fill(BLACK)  # Clear background

        # Draw all platforms
        for p in plats:
            p.draw(screen)

        # Draw all items
        for it in items:
            it.draw(screen)

        # Draw the player
        player.draw(screen)

        # Draw HUD (Heads-Up Display) text: level, score, goal, lives
        s_txt = f"Level: {lvl}  Score: {player.score}  Goal: {level_goals[lvl - 1]}  Lives: {player.lives}"
        info = font.render(s_txt, True, WHITE)
        screen.blit(info, (10, 10))

        # Calculate how long we've been in this level
        cur_time = (pygame.time.get_ticks() - start_time) / 1000
        t_txt = f"Time: {total_time + cur_time:.2f} sec"
        time_surf = font.render(t_txt, True, WHITE)
        screen.blit(time_surf, (10, 40))

        # If double points are active => show a timer
        now = pygame.time.get_ticks()
        if now < player.double_end:
            left = (player.double_end - now) / 1000
            dbl_surf = font.render(f"Double: {left:.1f}s", True, WHITE)
            screen.blit(dbl_surf, (WIDTH - dbl_surf.get_width() - 10, 10))

        # Update entire display
        pygame.display.flip()

        # Cap at ~60 frames per second
        clock.tick(60)

    # After the loop ends => close pygame
    pygame.quit()


# ------------------------------------------------
# Program Entry Point
# ------------------------------------------------
if __name__ == "__main__":
    main()