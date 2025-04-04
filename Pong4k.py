import random
import pygame
import sys
import numpy as np
from pygame.locals import *

# --- Initialization ---
# Initialize Pygame Mixer first for better sound performance
pygame.mixer.pre_init(44100, -16, 2, 512) # freq, size, channels, buffer
pygame.init()
fps = pygame.time.Clock()

# --- Constants ---
# Colors
WHITE = (255, 255, 255)
RED   = (255,   0,   0)
GREEN = (  0, 255,   0)
BLACK = (  0,   0,   0)
YELLOW= (255, 255,   0)

# Screen Dimensions
WIDTH  = 600
HEIGHT = 400

# Game Object Dimensions
BALL_RADIUS   = 15 # Slightly smaller ball for faster feel
PAD_WIDTH     = 8
PAD_HEIGHT    = 80
HALF_PAD_WIDTH  = PAD_WIDTH // 2
HALF_PAD_HEIGHT = PAD_HEIGHT // 2

# Paddle Speed
PADDLE_SPEED = 8

# Score Limit
WINNING_SCORE = 5

# Game States
START_SCREEN = 0
PLAYING = 1
GAME_OVER = 2

# --- Global Game Variables ---
ball_pos = [0, 0]
ball_vel = [0, 0]
paddle1_pos = [0, 0]
paddle2_pos = [0, 0]
paddle1_vel = 0
paddle2_vel = 0
l_score = 0
r_score = 0
game_state = START_SCREEN # Start with the title screen
winner = "" # Stores "Player 1" or "Player 2"

# --- Setup Window ---
window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Arcade Pong')

# --- Font Setup ---
# Try to find a monospace font for that retro feel
arcade_font_name = pygame.font.match_font('monospace', bold=True)
if not arcade_font_name:
    arcade_font_name = pygame.font.get_default_font() # Fallback
    print("Monospace font not found, using default.")

score_font = pygame.font.Font(arcade_font_name, 30)
message_font = pygame.font.Font(arcade_font_name, 24)
title_font = pygame.font.Font(arcade_font_name, 50)


# --- Sound Generation ---
def make_beep(frequency, duration=0.05, volume=0.3, sample_rate=44100):
    """
    Generate a simple beep sound (sine wave) in stereo using NumPy,
    convert it to a Pygame Sound object, and return it.
    Reduced default duration and volume for snappier sounds.
    """
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    wave = np.sin(2 * np.pi * frequency * t)
    # Scale to 16-bit signed integers (volume applied)
    wave = (wave * (2**15 - 1) * volume).astype(np.int16)
    # Convert to stereo by duplicating the mono signal into 2 channels
    stereo_wave = np.column_stack((wave, wave))
    return pygame.sndarray.make_sound(stereo_wave)

# Sound Effects - Adjusted frequencies for more distinct arcade sounds
bounce_sound = make_beep(660)  # Higher pitch for bounce
score_sound  = make_beep(220, duration=0.2) # Lower, longer pitch for score

# --- Game Functions ---
def ball_init(go_right):
    """
    Spawn the ball in the middle of the screen with a random velocity.
    If 'go_right' is True, ball goes to the right; otherwise, to the left.
    """
    global ball_pos, ball_vel
    ball_pos = [WIDTH // 2, HEIGHT // 2]
    # Increased base speed slightly
    horz = random.randrange(3, 5) # horizontal velocity component
    vert = random.randrange(1, 3) # vertical velocity component

    if not go_right:
        horz = -horz
    ball_vel = [horz, -vert] # Initial vertical direction is randomized by sign

def reset_game():
    """
    Reset paddle positions and ball for a new round (not full game reset).
    """
    global paddle1_pos, paddle2_pos, paddle1_vel, paddle2_vel
    paddle1_pos = [HALF_PAD_WIDTH, HEIGHT // 2] # Positioned correctly at edge
    paddle2_pos = [WIDTH - 1 - HALF_PAD_WIDTH, HEIGHT // 2] # Positioned correctly at edge
    paddle1_vel = 0
    paddle2_vel = 0
    # Randomize initial ball direction for the round
    ball_init(random.choice([True, False]))

def full_init():
    """
    Reset the entire game: scores, positions, ball, winner.
    """
    global l_score, r_score, winner
    l_score = 0
    r_score = 0
    winner = ""
    reset_game() # Reset positions and ball

def draw_start_screen(canvas):
    """Draws the initial start screen."""
    canvas.fill(BLACK)
    title_text = title_font.render("PONG", True, WHITE)
    title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 3))
    canvas.blit(title_text, title_rect)

    start_text = message_font.render("Press Any Key to Start", True, GREEN)
    start_rect = start_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    canvas.blit(start_text, start_rect)

    controls_text1 = message_font.render("P1: W/S", True, YELLOW)
    controls_rect1 = controls_text1.get_rect(center=(WIDTH // 4, HEIGHT * 3 // 4))
    canvas.blit(controls_text1, controls_rect1)

    controls_text2 = message_font.render("P2: UP/DOWN", True, YELLOW)
    controls_rect2 = controls_text2.get_rect(center=(WIDTH * 3 // 4, HEIGHT * 3 // 4))
    canvas.blit(controls_text2, controls_rect2)

    pygame.display.update()


def draw_game_over_screen(canvas):
    """Draws the game over screen."""
    canvas.fill(BLACK)
    game_over_text = title_font.render("GAME OVER", True, RED)
    game_over_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 3))
    canvas.blit(game_over_text, game_over_rect)

    winner_text = message_font.render(f"{winner} Wins!", True, GREEN)
    winner_rect = winner_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    canvas.blit(winner_text, winner_rect)

    restart_text = message_font.render("Press Any Key to Restart", True, WHITE)
    restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT * 2 // 3))
    canvas.blit(restart_text, restart_rect)

    pygame.display.update()


def draw_playing_field(canvas):
    """
    Draw the main game elements: paddles, ball, scores, field lines.
    """
    global paddle1_pos, paddle2_pos, ball_pos, ball_vel, l_score, r_score, game_state, winner

    # Fill background
    canvas.fill(BLACK)

    # Draw center line & gutters (thicker lines)
    pygame.draw.line(canvas, WHITE, (WIDTH // 2, 0), (WIDTH // 2, HEIGHT), 2)
    # Gutters are visual only, collision logic handles the scoring zone
    # pygame.draw.line(canvas, WHITE, (PAD_WIDTH, 0), (PAD_WIDTH, HEIGHT), 1)
    # pygame.draw.line(canvas, WHITE, (WIDTH - PAD_WIDTH, 0), (WIDTH - PAD_WIDTH, HEIGHT), 1)

    # Draw center circle (optional aesthetic)
    # pygame.draw.circle(canvas, WHITE, (WIDTH // 2, HEIGHT // 2), 70, 1)

    # --- Update Positions ---
    # Update paddle1 (left paddle) position; keep on screen
    paddle1_pos[1] += paddle1_vel
    paddle1_pos[1] = max(HALF_PAD_HEIGHT, min(HEIGHT - HALF_PAD_HEIGHT, paddle1_pos[1]))

    # Update paddle2 (right paddle) position; keep on screen
    paddle2_pos[1] += paddle2_vel
    paddle2_pos[1] = max(HALF_PAD_HEIGHT, min(HEIGHT - HALF_PAD_HEIGHT, paddle2_pos[1]))

    # Update ball position
    ball_pos[0] += int(ball_vel[0])
    ball_pos[1] += int(ball_vel[1])

    # --- Draw Game Objects ---
    # Draw paddles (simple rectangles)
    paddle1_rect = pygame.Rect(paddle1_pos[0] - HALF_PAD_WIDTH, paddle1_pos[1] - HALF_PAD_HEIGHT, PAD_WIDTH, PAD_HEIGHT)
    pygame.draw.rect(canvas, GREEN, paddle1_rect)

    paddle2_rect = pygame.Rect(paddle2_pos[0] - HALF_PAD_WIDTH, paddle2_pos[1] - HALF_PAD_HEIGHT, PAD_WIDTH, PAD_HEIGHT)
    pygame.draw.rect(canvas, GREEN, paddle2_rect)

    # Draw ball
    pygame.draw.circle(canvas, RED, (int(ball_pos[0]), int(ball_pos[1])), BALL_RADIUS)

    # --- Collision Detection & Scoring ---
    # Ball collision with top/bottom walls
    if ball_pos[1] <= BALL_RADIUS:
        ball_pos[1] = BALL_RADIUS # Prevent sticking
        ball_vel[1] = -ball_vel[1]
        bounce_sound.play()
    elif ball_pos[1] >= HEIGHT - 1 - BALL_RADIUS:
        ball_pos[1] = HEIGHT - 1 - BALL_RADIUS # Prevent sticking
        ball_vel[1] = -ball_vel[1]
        bounce_sound.play()

    # Ball collision with paddles or gutters
    scored = False
    # Left side collision check
    if ball_pos[0] <= BALL_RADIUS + PAD_WIDTH:
        # Check if ball is vertically aligned with paddle 1
        if paddle1_rect.collidepoint(ball_pos[0], ball_pos[1]):
             ball_pos[0] = BALL_RADIUS + PAD_WIDTH # Prevent sticking inside paddle
             ball_vel[0] = -ball_vel[0] * 1.05 # Increase speed slightly on hit
             # Optional: Add slight vertical velocity change based on hit position
             delta_y = ball_pos[1] - paddle1_pos[1]
             ball_vel[1] += delta_y * 0.1
             # Clamp vertical speed to prevent it getting too fast
             ball_vel[1] = max(-abs(ball_vel[0]), min(abs(ball_vel[0]), ball_vel[1]))
             bounce_sound.play()
        else: # Ball missed paddle 1 - Point for right player
            r_score += 1
            score_sound.play()
            if r_score >= WINNING_SCORE:
                winner = "Player 2"
                game_state = GAME_OVER
            else:
                ball_init(True) # Ball goes towards the winner (right player)
            scored = True

    # Right side collision check
    elif ball_pos[0] >= WIDTH - 1 - BALL_RADIUS - PAD_WIDTH:
         # Check if ball is vertically aligned with paddle 2
        if paddle2_rect.collidepoint(ball_pos[0], ball_pos[1]):
            ball_pos[0] = WIDTH - 1 - BALL_RADIUS - PAD_WIDTH # Prevent sticking
            ball_vel[0] = -ball_vel[0] * 1.05 # Increase speed slightly
            # Optional: Add slight vertical velocity change based on hit position
            delta_y = ball_pos[1] - paddle2_pos[1]
            ball_vel[1] += delta_y * 0.1
             # Clamp vertical speed
            ball_vel[1] = max(-abs(ball_vel[0]), min(abs(ball_vel[0]), ball_vel[1]))
            bounce_sound.play()
        else: # Ball missed paddle 2 - Point for left player
            l_score += 1
            score_sound.play()
            if l_score >= WINNING_SCORE:
                winner = "Player 1"
                game_state = GAME_OVER
            else:
                ball_init(False) # Ball goes towards the winner (left player)
            scored = True

    # --- Display Scores ---
    l_score_text = score_font.render(str(l_score), True, YELLOW)
    r_score_text = score_font.render(str(r_score), True, YELLOW)
    canvas.blit(l_score_text, (WIDTH // 4, 20))
    canvas.blit(r_score_text, (WIDTH * 3 // 4 - r_score_text.get_width(), 20))


def keydown(event):
    """ Handle key press events. """
    global paddle1_vel, paddle2_vel, game_state
    # Handle playing state controls
    if game_state == PLAYING:
        if event.key == K_w:
            paddle1_vel = -PADDLE_SPEED
        elif event.key == K_s:
            paddle1_vel = PADDLE_SPEED
        elif event.key == K_UP:
            paddle2_vel = -PADDLE_SPEED
        elif event.key == K_DOWN:
            paddle2_vel = PADDLE_SPEED
    # Handle transitions from START or GAME_OVER
    elif game_state == START_SCREEN:
        full_init() # Reset scores and positions
        game_state = PLAYING
    elif game_state == GAME_OVER:
        game_state = START_SCREEN # Go back to start screen

def keyup(event):
    """ Handle key release events. """
    global paddle1_vel, paddle2_vel
    if game_state == PLAYING:
        if event.key == K_w and paddle1_vel < 0: # Stop only if moving up
            paddle1_vel = 0
        elif event.key == K_s and paddle1_vel > 0: # Stop only if moving down
            paddle1_vel = 0
        elif event.key == K_UP and paddle2_vel < 0: # Stop only if moving up
            paddle2_vel = 0
        elif event.key == K_DOWN and paddle2_vel > 0: # Stop only if moving down
            paddle2_vel = 0

# --- Main Game Loop ---
while True:
    # Event Handling
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == KEYDOWN:
            keydown(event)
        elif event.type == KEYUP:
            keyup(event)

    # Game State Logic & Drawing
    if game_state == START_SCREEN:
        draw_start_screen(window)
    elif game_state == GAME_OVER:
        draw_game_over_screen(window)
    elif game_state == PLAYING:
        draw_playing_field(window)
        pygame.display.update() # Update display only when playing

    # Control Frame Rate
    fps.tick(60) # Target 60 frames per second

