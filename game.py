"""
Infinite Cat Jumper
Author: Ibrahim Taha
Version: 04.02.2025
"""

# Importing required modules:
# pygame: for creating the game window, handling graphics, sound, and events.
# random: for generating random numbers (used in platform/item generation).
# math: for mathematical operations (used in platform rotation in level 3).
# sys: for system-specific functions (exiting the program).
import pygame, random, math, sys

# Initialize all imported pygame modules (graphics, events, etc.)
pygame.init()
# Initialize the mixer module for handling sound effects
pygame.mixer.init()

# Define constants for the game window dimensions.
WIDTH, HEIGHT = 800, 600
# Set up the display with the specified width and height.
screen = pygame.display.set_mode((WIDTH, HEIGHT))
# Set the window title.
pygame.display.set_caption("Infinite Cat Jumper")

# Define commonly used colors as RGB tuples.
WHITE   = (255, 255, 255)
BLACK   = (0, 0, 0)
GREEN   = (0, 255, 0)
RED     = (255, 0, 0)
# A list of colors for a rainbow effect (used for special items).
RAINBOW = [
    (255, 0, 0),
    (255, 127, 0),
    (255, 255, 0),
    (0, 255, 0),
    (0, 0, 255),
    (75, 0, 130),
    (148, 0, 211)
]

# Define physics-related constants:
GRAV     = 0.5   # Gravity force applied to the player normally.
EASYGRAV = 0.2   # Reduced gravity for the very first jump (to ease initial movement).
JUMP     = 15    # Initial jump velocity.
DJUMP    = 12    # Double jump velocity.

# Level goals and placeholders for level scores:
level_goals  = [10, 15, 25]         # Score goals needed to complete levels 1, 2, and 3.
level_scores = [None, None, None]    # To store scores achieved in each level.

# Load images and sounds with error handling:
try:
    # Attempt to load the cat image from file and scale it to 50x50 pixels.
    cat_img = pygame.image.load('cat.png')
    cat_img = pygame.transform.scale(cat_img, (50, 50))
except:
    # Fallback: create a plain white surface if the image fails to load.
    cat_img = pygame.Surface((50, 50))
    cat_img.fill(WHITE)

try:
    # Attempt to load the item image from file and scale it to 30x30 pixels.
    item_img = pygame.image.load('obtainable.png')
    item_img = pygame.transform.scale(item_img, (30, 30))
except:
    # Fallback: create a plain green surface if the image fails to load.
    item_img = pygame.Surface((30, 30))
    item_img.fill(GREEN)

try:
    # Attempt to load a sound effect for item collection.
    collect_sound = pygame.mixer.Sound('sound_affect.mp3')
except:
    # Fallback: if the sound fails to load, use None.
    collect_sound = None

# =====================
# Class Definitions
# =====================

# Player class: Manages the cat character controlled by the user.
class Player:
    def __init__(self, x, y):
        # Initialize player's position, size, and movement properties.
        self.x = x                 # Horizontal position.
        self.y = y                 # Vertical position.
        self.w = 50                # Width of the player's hitbox.
        self.h = 50                # Height of the player's hitbox.
        self.vy = 0                # Vertical velocity.
        self.jumps = 0             # Number of jumps performed (to limit double jumps).
        self.score = 0             # Player's score (items collected).
        self.lives = 3             # Number of lives the player has.
        self.initial = True        # Flag to indicate if it's the first jump.
        self.alive = True          # Player state: alive or dead.
        self.double_end = 0        # Timer for double score effect expiration.
        
        # Timer (in frames) for temporary invulnerability after being hit.
        self.invul = 0
        # Flag to prevent multiple damage registrations while in contact with a hazard.
        self.hit_recently = False
        # Store starting coordinates for respawn purposes.
        self.start_x = x
        self.start_y = y

    def hit(self):
        """Handle the player being hit by a hazard:
           Decrease lives, reset position if lives remain, and set temporary invulnerability."""
        self.lives -= 1  # Deduct one life.
        if self.lives <= 0:
            # If no lives remain, mark the player as dead.
            self.alive = False
        else:
            # If lives remain, provide a short invulnerability period.
            self.invul = 30  # About half a second at 60 FPS.
            # Reset the player's position to the starting point.
            self.x = self.start_x
            self.y = self.start_y
            self.vy = 0      # Reset vertical velocity.
            self.jumps = 0   # Reset jump counter.
            self.hit_recently = True  # Mark that the player was hit to prevent duplicate hits.

    def update(self, plats):
        # Apply gravity based on whether it’s the very first jump.
        # Use EASYGRAV (less gravity) if the player hasn't jumped yet.
        g = EASYGRAV if (self.initial and self.jumps == 0) else GRAV
        
        # Apply a slightly reduced gravity if the player is moving upward.
        if self.vy < 0:
            self.vy += g * 0.6
        else:
            self.vy += g  # Normal gravity when falling.
        
        self.y += self.vy  # Update vertical position by current velocity.
        
        # Decrement the invulnerability timer if active.
        if self.invul > 0:
            self.invul -= 1
        
        # Check for collisions with hazardous platforms (only if not invulnerable).
        collision = False
        if self.invul == 0:
            for p in plats:
                # Check rectangular overlap between player and platform.
                if (self.x + self.w > p.x and self.x < p.x + p.w and
                    self.y + self.h > p.y and self.y < p.y + p.h and p.hazard):
                    collision = True
                    break  # Stop checking if collision is detected.
        
        # If collision occurs and the player wasn't recently hit, apply hit logic.
        if collision:
            if not self.hit_recently:
                self.hit()
        else:
            # Reset the recently hit flag if no collision is found.
            self.hit_recently = False

        # Check for safe landing on non-hazard platforms (only when falling).
        if self.alive and self.vy >= 0:
            for p in plats:
                # Check if player's bottom edge is within platform bounds.
                if (not p.hazard and
                    self.y + self.h >= p.y and self.y + self.h <= p.y + p.h and
                    self.x + self.w > p.x and self.x < p.x + p.w):
                    # Snap player to the platform top.
                    self.y = p.y - self.h
                    self.vy = 0     # Reset vertical velocity on landing.
                    self.jumps = 0  # Reset jump counter.
                    self.initial = False  # Mark that the initial jump is over.
                    break

        # Ensure the player stays within horizontal screen bounds.
        if self.x < 0:
            self.x = 0
        if self.x + self.w > WIDTH:
            self.x = WIDTH - self.w

    def jump(self):
        # Allow jump or double jump based on the current jump count.
        if self.jumps == 0:
            self.vy = -JUMP  # Set upward velocity for the first jump.
            self.jumps = 1   # Increment jump count.
            self.initial = False  # No longer in the initial state.
        elif self.jumps == 1:
            self.vy = -DJUMP  # Set upward velocity for the double jump.
            self.jumps = 2    # Increment jump count to indicate double jump used.

    def move_left(self):
        # Move player left by subtracting a fixed speed.
        self.x -= 5

    def move_right(self):
        # Move player right by adding a fixed speed.
        self.x += 5

    def draw(self, surf):
        # Draw the player's image on the provided surface at the player's coordinates.
        surf.blit(cat_img, (self.x, self.y))

    def collect(self, items):
        # Get the current time in milliseconds.
        now = pygame.time.get_ticks()
        # Loop over a copy of the items list (to allow removal while iterating).
        for it in items[:]:
            # Check for collision between player and item using rectangular boundaries.
            if (self.x < it.get_x() + it.w and self.x + self.w > it.get_x() and
                self.y < it.get_y() + it.h and self.y + self.h > it.get_y()):
                # If the item is marked as special, set the double score timer.
                if it.special:
                    self.double_end = now + 5000  # 5 seconds of double score.
                # Increase score by 2 if within the double score period; otherwise by 1.
                if now < self.double_end:
                    self.score += 2
                else:
                    self.score += 1
                # Remove the collected item from the list.
                items.remove(it)
                # Play a sound effect if one is loaded.
                if collect_sound:
                    collect_sound.play()

# Platform class: Represents a platform that the player can jump on.
class Platform:
    def __init__(self, x, y, w, h=20):
        self.x = x     # Horizontal position.
        self.y = y     # Vertical position.
        self.w = w     # Width of the platform.
        self.h = h     # Height of the platform (default is 20 pixels).
        self.hazard = False  # Flag indicating if the platform is hazardous.
        self.slide = None    # For horizontal sliding movement.
        self.vx = 0          # Horizontal velocity (used in level 2).
        self.vy = 0          # Vertical velocity (used in level 2).
        self.radius = 0      # Radius for circular motion (used in level 3).
        self.angle = 0       # Angle for circular motion (used in level 3).
        self.rot_speed = 0   # Rotation speed for circular motion (used in level 3).
        self.cx = 0          # Center x-coordinate for circular motion.
        self.cy = 0          # Center y-coordinate for circular motion.

    def draw(self, surf):
        # Choose the platform color based on whether it is hazardous.
        color = RED if self.hazard else GREEN
        # Draw the platform as a rectangle.
        pygame.draw.rect(surf, color, (self.x, self.y, self.w, self.h))

# Item class: Represents a collectible item that may appear on a platform.
class Item:
    def __init__(self, x, y, plat=None):
        self.plat = plat  # Reference to the platform the item is attached to (if any).
        if plat:
            # If attached to a platform, store the offset relative to the platform.
            self.ox = x - plat.x
            self.oy = y - plat.y
        else:
            # Otherwise, set the absolute position.
            self.x = x
            self.y = y
        self.w = 30      # Width of the item.
        self.h = 30      # Height of the item.
        self.special = False  # Flag to indicate if the item gives a bonus (double score).

    def update(self):
        # If the item is attached to a platform, update its absolute position based on the platform's movement.
        if self.plat:
            self.x = self.plat.x + self.ox
            self.y = self.plat.y + self.oy

    def get_x(self):
        # Ensure the item’s position is updated if attached to a platform.
        if self.plat:
            self.update()
        return self.x

    def get_y(self):
        # Ensure the item’s position is updated if attached to a platform.
        if self.plat:
            self.update()
        return self.y

    def draw(self, surf):
        # Update position and draw the item image on the surface.
        self.update()
        surf.blit(item_img, (self.get_x(), self.get_y()))
        # If the item is special, draw a rainbow-colored border around it.
        if self.special:
            # Determine which rainbow color to use based on the current time.
            idx = (pygame.time.get_ticks() // 100) % len(RAINBOW)
            col = RAINBOW[idx]
            # Draw the border with a 2-pixel thickness.
            pygame.draw.rect(surf, col,
                             (self.get_x()-2, self.get_y()-2,
                              self.w+4, self.h+4), 2)

# =====================
# Helper Functions
# =====================

def gen_platform(y, dummy):
    """
    Generates a platform at a given vertical position.
    Randomly determines the platform width and horizontal position.
    Randomly flags some platforms as hazardous.
    """
    w = random.randint(50, 120)                 # Random width between 50 and 120 pixels.
    x = random.randint(0, WIDTH - w)              # Random x position ensuring the platform fits on screen.
    p = Platform(x, y, w)                         # Create a new platform.
    p.hazard = (random.random() < 0.2)            # 20% chance to mark the platform as hazardous.
    return p

def spawn_item(p):
    """
    Spawns an item on the provided platform with a probability of 60%.
    Also randomly designates the item as special.
    """
    if random.random() < 0.6:
        x = random.randint(p.x, p.x + p.w - 30)   # Random x position on the platform (accounting for item width).
        y = p.y - 30                              # Place the item just above the platform.
        it = Item(x, y, p)                        # Create a new item attached to the platform.
        it.special = (random.random() < 0.125)      # 12.5% chance for the item to be special.
        return it
    return None

def start_screen():
    """
    Displays the starting screen with game instructions.
    Waits for the user to press ENTER to begin.
    """
    f1 = pygame.font.SysFont(None, 72)  # Large font for the game title.
    f2 = pygame.font.SysFont(None, 36)  # Smaller font for instructions.
    texts = [
        f1.render("Infinite Cat Jumper", True, WHITE),
        f2.render("Use LEFT/RIGHT arrows to move; UP to jump.", True, WHITE),
        f2.render("Double Jump allowed!", True, WHITE),
        f2.render("Level 1: Collect 10 items, Level 2: 15, Level 3: 25", True, WHITE),
        f2.render("Press ENTER to start.", True, WHITE),
        f2.render("Avoid RED platforms!", True, WHITE)
    ]
    screen.fill(BLACK)  # Fill the screen with black.
    positions = [
        HEIGHT // 4,
        HEIGHT // 2 - 100,
        HEIGHT // 2 - 60,
        HEIGHT // 2 - 20,
        HEIGHT // 2 + 20,
        HEIGHT // 2 + 60
    ]
    # Blit each text surface onto the screen at the calculated positions.
    for t, p in zip(texts, positions):
        screen.blit(t, (WIDTH // 2 - t.get_width() // 2, p))
    pygame.display.flip()  # Update the display.
    
    # Wait in a loop for the user to press ENTER or quit.
    while True:
        ev = pygame.event.wait()
        if ev.type == pygame.QUIT:
            return False
        if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            return True

def init_game(lvl):
    """
    Initializes the game state for the given level.
    Creates platforms, items, and positions the player on the starting platform.
    """
    plats = []  # List to store platforms.
    its = []    # List to store items.
    
    # Create a starting platform at the bottom of the screen.
    sw = random.randint(100, 200)                      # Random width for the starting platform.
    sx = random.randint(0, WIDTH - sw)                 # Random x position for the starting platform.
    sy = HEIGHT - 100                                  # y position near the bottom.
    start_plat = Platform(sx, sy, sw)                  # Instantiate the starting platform.
    start_plat.hazard = False                          # Ensure the starting platform is not hazardous.
    plats.append(start_plat)
    
    # Set the vertical position for the next platform.
    y = sy - random.randint(80, 150)
    # Determine spacing between platforms based on level.
    if lvl in (1, 2):
        spacing = random.randint(80, 150)
    else:
        spacing = int(random.randint(160, 300) / 1.6)
    
    # Generate platforms and items while the y coordinate is within screen bounds.
    while y > -HEIGHT:
        p = gen_platform(y, 0)   # Generate a new platform.
        plats.append(p)
        it = spawn_item(p)       # Possibly spawn an item on the platform.
        if it:
            its.append(it)
        y -= spacing             # Move up by the spacing amount.
    
    # For level 2, assign random horizontal and vertical velocities to platforms.
    if lvl == 2:
        for p in plats[1:]:
            p.vx = random.choice([-3, -2, -1, 1, 2, 3])
            p.vy = random.choice([-3, -2, -1, 1, 2, 3])
    # For level 3, set parameters for circular platform motion.
    if lvl == 3:
        for p in plats[1:]:
            p.radius    = random.randint(50, 150)
            p.angle     = random.uniform(0, 2 * math.pi)
            p.cx        = WIDTH // 2 + random.randint(-100, 100)
            p.cy        = p.y
            p.rot_speed = random.uniform(0.01, 0.05)
    
    # Position the player on the starting platform.
    player_x = start_plat.x + (start_plat.w - 50) // 2  # Center the player horizontally.
    player_y = start_plat.y - 50                        # Place the player above the platform.
    player = Player(player_x, player_y)
    # Store the player's respawn position.
    player.start_x = player_x
    player.start_y = player_y
    
    return player, plats, its

def level_trans(font, lvl, ttime):
    """
    Displays a level transition screen with instructions to continue.
    Waits for the user to press ENTER to proceed to the next level.
    """
    text = font.render("Press ENTER to continue to next level.", True, WHITE)
    screen.fill(BLACK)
    screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2))
    pygame.display.flip()
    
    # Wait for user input to continue or quit.
    while True:
        ev = pygame.event.wait()
        if ev.type == pygame.QUIT:
            return False
        if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            return True

def save_score(initials, sc, ttime):
    """
    Saves the player's score, initials, and time to the scoreboard.
    Reads existing scores, adds the new score, sorts them, and writes the top 10.
    """
    scores = []
    try:
        with open("scoreboard.txt", "r") as f:
            for line in f:
                parts = line.strip().split()
                if parts and parts[0].endswith('.'):
                    parts = parts[1:]
                if len(parts) == 3:
                    scores.append((parts[0], int(parts[1]), float(parts[2])))
    except:
        pass
    # Append the new score and sort based on time.
    scores.append((initials, sc, ttime))
    scores.sort(key=lambda x: x[2])
    scores = scores[:10]  # Keep only the top 10 scores.
    
    with open("scoreboard.txt", "w") as f:
        for i, e in enumerate(scores, start=1):
            f.write(f"{i}. {e[0]} {e[1]} {e[2]:.2f}\n")

def check_top10(ttime):
    """
    Checks if the current time qualifies for the top 10 scoreboard.
    Returns True if the scoreboard has fewer than 10 entries or the current time is better.
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
        return True
    if len(scores) < 10:
        return True
    scores.sort()
    # Return True if current time is better (i.e. lower) than the worst time in the top 10.
    return ttime < scores[-1] if scores else True

def show_scoreboard(font):
    """
    Displays the scoreboard on the screen for 5 seconds.
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
    # Display each line of the scoreboard.
    for line in lines:
        txt = font.render(line.strip(), True, WHITE)
        screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, y_off))
        y_off += 40
    pygame.display.flip()
    pygame.time.wait(5000)  # Pause for 5 seconds.

def victory(font, ttime, sc):
    """
    Handles the victory scenario.
    If the score qualifies for the top 10, prompts the user to enter initials.
    Otherwise, displays the scoreboard.
    """
    if not check_top10(ttime):
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
        # Position the messages on the screen.
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
                    initials = initials[:-1]  # Remove the last character.
                elif ev.key == pygame.K_RETURN and len(initials) == 3:
                    save_score(initials, sc, ttime)
                    show_scoreboard(font)
                    return
                else:
                    # Add character if it's alphabetical and the initials are less than 3 letters.
                    if len(initials) < 3 and ev.unicode.isalpha():
                        initials += ev.unicode.upper()

def game_over(font, sc, needed, lvl):
    """
    Handles the game over scenario.
    Updates the high score if necessary, displays final stats, and extra messages
    regarding unachieved level goals.
    """
    try:
        with open('highscore.txt', "r") as ff:
            hi = int(ff.read())
    except:
        hi = 0
    # Update the high score if the current score is higher.
    if sc > hi:
        hi = sc
        with open('highscore.txt', "w") as ff:
            ff.write(str(hi))
    # Ensure level_scores list has a score for each level.
    for i in range(3):
        if level_scores[i] is None:
            level_scores[i] = 0
    extra_msgs = []
    # Generate messages for levels where the score goal was not met.
    for i in range(3):
        short = level_goals[i] - level_scores[i]
        if short > 0:
            msg = f"Level {i+1}: {short} more item(s) needed."
            extra_msgs.append(msg)
    screen.fill(BLACK)
    y = HEIGHT // 2 - 200
    lines = [
        font.render("Game Over!", True, WHITE),
        font.render(f"Final Score: {sc}", True, WHITE),
        font.render(f"Final Level: {lvl}", True, WHITE),
        font.render(f"High Score: {hi}", True, WHITE)
    ]
    # Blit the game over messages.
    for line in lines:
        screen.blit(line, (WIDTH // 2 - line.get_width() // 2, y))
        y += 40
    # Blit extra messages regarding levels.
    for msg in extra_msgs:
        surf = font.render(msg, True, WHITE)
        screen.blit(surf, (WIDTH // 2 - surf.get_width() // 2, y))
        y += 40
    pygame.display.flip()
    pygame.time.wait(5000)  # Wait 5 seconds before closing game over screen.
    return False

def main():
    """
    Main game loop:
    Handles initialization, event processing, game state updates, level transitions,
    and rendering.
    """
    global level_scores
    clock = pygame.time.Clock()  # Create a clock object to control the frame rate.
    font = pygame.font.SysFont(None, 36)  # Default font for game text.
    total_time = 0.0  # Variable to accumulate total game time.
    
    # Display the start screen and exit if the user closes the window.
    if not start_screen():
        pygame.quit()
        return
    
    lvl = 1  # Start at level 1.
    level_scores = [None, None, None]  # Reset level scores.
    # Initialize game objects for the first level.
    player, plats, items = init_game(lvl)
    start_time = pygame.time.get_ticks()  # Mark the start time of the level.
    running = True  # Flag to control the main game loop.
    
    while running:
        # Process all pending events.
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
                break
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_UP:
                    player.jump()  # Handle jump on UP key.
                elif ev.key == pygame.K_l:
                    # Debug cheat: skip to next level.
                    player.score = level_goals[lvl-1]
                    player.y = HEIGHT + 1  # Force a level transition.
        if not running:
            break
        
        # Handle continuous key presses for left/right movement.
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            player.move_left()
        if keys[pygame.K_RIGHT]:
            player.move_right()
        
        # Update the player state with collision checks against platforms.
        player.update(plats)
        # Check for item collection.
        player.collect(items)
        
        # If the player falls below the screen, treat it as a hit.
        if player.y > HEIGHT:
            if player.lives > 0:
                player.hit()
            else:
                level_scores[lvl-1] = player.score
                left = level_goals[lvl-1] - player.score
                if left < 0:
                    left = 0
                game_over(font, player.score, left, lvl)
                break
        if not player.alive:
            level_scores[lvl-1] = player.score
            left = level_goals[lvl-1] - player.score
            if left < 0:
                left = 0
            game_over(font, player.score, left, lvl)
            break
        
        # If the player meets the level's score goal, proceed to next level or victory.
        if player.score >= level_goals[lvl-1]:
            level_scores[lvl-1] = player.score
            elapsed = (pygame.time.get_ticks() - start_time) / 1000
            total_time += elapsed
            if lvl < 3:
                cont = level_trans(font, lvl, total_time)
                if not cont:
                    break
                lvl += 1
                player, plats, items = init_game(lvl)
                start_time = pygame.time.get_ticks()
            else:
                victory(font, total_time, player.score)
                break
        
        # If the player moves high up the screen, scroll the platforms and items downward.
        if player.y < HEIGHT / 3:
            off = (HEIGHT / 3) - player.y
            player.y += off
            for p in plats:
                p.y += off
                # For level 3, adjust the center of circular motion.
                if lvl == 3 and hasattr(p, 'cy'):
                    p.cy += off
            for it in items:
                if not it.plat:
                    it.y += off
        
        # Remove platforms that have scrolled off the bottom of the screen.
        plats = [p for p in plats if p.y < HEIGHT]
        # Filter out items that are no longer visible.
        new_items = []
        for it in items:
            if it.plat:
                if it.plat in plats:
                    new_items.append(it)
            else:
                if it.get_y() < HEIGHT:
                    new_items.append(it)
        items = new_items
        
        # Generate new platforms if the topmost platform is still visible.
        if plats:
            top_y = min(p.y for p in plats)
            if lvl in (1, 2):
                spc = random.randint(80, 150)
            else:
                spc = int(random.randint(160, 300) / 1.6)
            if top_y > 0:
                new_y = top_y - spc
                new_plat = gen_platform(new_y, player.vy)
                plats.append(new_plat)
                new_it = spawn_item(new_plat)
                if new_it:
                    items.append(new_it)
                if lvl == 3:
                    new_plat.radius    = random.randint(50, 150)
                    new_plat.angle     = random.uniform(0, 2 * math.pi)
                    new_plat.cx        = WIDTH // 2 + random.randint(-100, 100)
                    new_plat.cy        = new_plat.y
                    new_plat.rot_speed = random.uniform(0.01, 0.05)
        
        # Level-specific platform movements:
        if lvl == 1:
            # For level 1, platforms slide horizontally.
            for p in plats:
                if p.slide is None:
                    p.slide = random.choice([-3, -2, -1, 1, 2, 3])
                p.x += p.slide
                if random.random() < 0.01:
                    p.slide = random.choice([-3, -2, -1, 1, 2, 3])
                if p.x < 0:
                    p.x = 0
                    p.slide = abs(p.slide)
                if p.x + p.w > WIDTH:
                    p.x = WIDTH - p.w
                    p.slide = -abs(p.slide)
        elif lvl == 2:
            # For level 2, platforms move in both horizontal and vertical directions.
            for p in plats:
                p.x += p.vx
                p.y += p.vy
                if random.random() < 0.01:
                    p.vx = random.choice([-3, -2, -1, 1, 2, 3])
                if random.random() < 0.01:
                    p.vy = random.choice([-3, -2, -1, 1, 2, 3])
                if p.x < 0 or p.x + p.w > WIDTH:
                    p.vx *= -1
                if p.y < 0 or p.y + p.h > HEIGHT:
                    p.vy *= -1
        else:
            # For level 3, platforms follow a circular path.
            for p in plats:
                p.x = p.cx + p.radius * math.cos(p.angle) - p.w / 2
                p.y = p.cy + p.radius * math.sin(p.angle) - p.h / 2
                p.angle += p.rot_speed
        
        # Clear the screen for the next frame.
        screen.fill(BLACK)
        # Draw platforms.
        for p in plats:
            p.draw(screen)
        # Draw items.
        for it in items:
            it.draw(screen)
        # Draw the player.
        player.draw(screen)
        
        # Render and display game info such as level, score, goal, and lives.
        s_txt = f"Level: {lvl}  Score: {player.score}  Goal: {level_goals[lvl-1]}  Lives: {player.lives}"
        info = font.render(s_txt, True, WHITE)
        screen.blit(info, (10, 10))
        # Render and display elapsed time.
        cur_time = (pygame.time.get_ticks() - start_time) / 1000
        t_txt = f"Time: {total_time + cur_time:.2f} sec"
        time_surf = font.render(t_txt, True, WHITE)
        screen.blit(time_surf, (10, 40))
        # Display remaining time for double score effect if active.
        now = pygame.time.get_ticks()
        if now < player.double_end:
            left = (player.double_end - now) / 1000
            dbl_surf = font.render(f"Double: {left:.1f}s", True, WHITE)
            screen.blit(dbl_surf, (WIDTH - dbl_surf.get_width() - 10, 10))
        
        # Update the display with the new frame.
        pygame.display.flip()
        # Cap the frame rate at 60 frames per second.
        clock.tick(60)
    
    # Quit pygame once the game loop is exited.
    pygame.quit()

# Entry point for the game.
if __name__ == "__main__":
    main()
