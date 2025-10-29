import sys
import os
import math

from badgeware import screen, PixelFont, shapes, brushes, io, run

# Screen dimensions
WIDTH = 160
HEIGHT = 120

# Game map - 1 is wall, 0 is empty
GAME_MAP = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 1, 1, 1, 0, 0, 0, 1],
    [1, 0, 0, 1, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 1, 0, 0, 0, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]

MAP_WIDTH = len(GAME_MAP[0])
MAP_HEIGHT = len(GAME_MAP)

# Player state
player_x = 2.5
player_y = 2.5
player_angle = 0.0

# Movement speed
MOVE_SPEED = 0.03
ROTATE_SPEED = 0.05

# Raycasting settings
FOV = 60  # Field of view in degrees
NUM_RAYS = 80  # Number of rays to cast (half of screen width for performance)
MAX_DEPTH = 10.0

# Colors
FLOOR_COLOR = (50, 50, 50)
CEILING_COLOR = (30, 30, 50)
WALL_COLOR_DARK = (100, 100, 100)
WALL_COLOR_LIGHT = (150, 150, 150)
SKY_COLOR = (20, 20, 40)

# Load font
small_font = PixelFont.load("/system/assets/fonts/nope.ppf")


def init():
    """Initialize the game"""
    screen.font = small_font


def cast_ray(angle):
    """Cast a single ray and return distance to wall"""
    global player_x, player_y
    
    # Ray direction
    ray_x = math.cos(angle)
    ray_y = math.sin(angle)
    
    # Start from player position
    x = player_x
    y = player_y
    
    # Step along ray
    for depth in range(int(MAX_DEPTH * 10)):
        x += ray_x * 0.1
        y += ray_y * 0.1
        
        # Check map boundaries
        map_x = int(x)
        map_y = int(y)
        
        if map_x < 0 or map_x >= MAP_WIDTH or map_y < 0 or map_y >= MAP_HEIGHT:
            return MAX_DEPTH, False
        
        # Check if ray hit a wall
        if GAME_MAP[map_y][map_x] == 1:
            distance = math.sqrt((x - player_x) ** 2 + (y - player_y) ** 2)
            # Determine if we hit vertical or horizontal wall for shading
            frac_x = x - map_x
            frac_y = y - map_y
            is_vertical = abs(frac_x) < 0.1 or abs(frac_x - 1) < 0.1
            return distance, is_vertical
    
    return MAX_DEPTH, False


def render_3d_view():
    """Render the 3D raycasted view"""
    global player_angle
    
    # Draw ceiling
    screen.brush = brushes.color(*CEILING_COLOR)
    screen.draw(shapes.rectangle(0, 0, WIDTH, HEIGHT // 2))
    
    # Draw floor
    screen.brush = brushes.color(*FLOOR_COLOR)
    screen.draw(shapes.rectangle(0, HEIGHT // 2, WIDTH, HEIGHT // 2))
    
    # Cast rays for 3D view
    ray_angle_step = math.radians(FOV) / NUM_RAYS
    start_angle = player_angle - math.radians(FOV / 2)
    
    for i in range(NUM_RAYS):
        ray_angle = start_angle + i * ray_angle_step
        distance, is_vertical = cast_ray(ray_angle)
        
        # Fix fish-eye effect
        distance *= math.cos(ray_angle - player_angle)
        
        # Calculate wall height based on distance
        if distance > 0:
            wall_height = min((HEIGHT * 0.6) / distance, HEIGHT)
        else:
            wall_height = HEIGHT
        
        # Calculate wall position
        wall_top = (HEIGHT - wall_height) // 2
        wall_bottom = wall_top + wall_height
        
        # Choose wall color based on orientation
        if is_vertical:
            color = WALL_COLOR_LIGHT
        else:
            color = WALL_COLOR_DARK
        
        # Darken based on distance
        brightness = max(0.3, 1.0 - (distance / MAX_DEPTH) * 0.7)
        color = (int(color[0] * brightness), int(color[1] * brightness), int(color[2] * brightness))
        
        # Draw wall slice (2 pixels wide for better performance)
        x = (i * WIDTH) // NUM_RAYS
        width = max(2, WIDTH // NUM_RAYS)
        
        screen.brush = brushes.color(*color)
        screen.draw(shapes.rectangle(x, int(wall_top), width, int(wall_height)))


def render_minimap():
    """Render a small minimap in the corner"""
    global player_x, player_y, player_angle
    
    map_size = 3  # pixels per map tile
    map_offset_x = 5
    map_offset_y = 5
    
    # Draw map
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            if GAME_MAP[y][x] == 1:
                screen.brush = brushes.color(200, 200, 200)
            else:
                screen.brush = brushes.color(50, 50, 50)
            
            screen.draw(shapes.rectangle(
                map_offset_x + x * map_size,
                map_offset_y + y * map_size,
                map_size - 1,
                map_size - 1
            ))
    
    # Draw player
    screen.brush = brushes.color(255, 0, 0)
    player_map_x = int(map_offset_x + player_x * map_size)
    player_map_y = int(map_offset_y + player_y * map_size)
    screen.draw(shapes.circle(player_map_x, player_map_y, 1))
    
    # Draw direction indicator
    dir_x = player_map_x + int(math.cos(player_angle) * 3)
    dir_y = player_map_y + int(math.sin(player_angle) * 3)
    screen.draw(shapes.line(player_map_x, player_map_y, dir_x, dir_y, 1))


def update_player():
    """Update player position based on input"""
    global player_x, player_y, player_angle
    
    # Rotation
    if io.BUTTON_A in io.held:
        player_angle -= ROTATE_SPEED
    if io.BUTTON_C in io.held:
        player_angle += ROTATE_SPEED
    
    # Forward/backward movement
    move_x = 0
    move_y = 0
    
    if io.BUTTON_UP in io.held:
        move_x = math.cos(player_angle) * MOVE_SPEED
        move_y = math.sin(player_angle) * MOVE_SPEED
    if io.BUTTON_DOWN in io.held:
        move_x = -math.cos(player_angle) * MOVE_SPEED
        move_y = -math.sin(player_angle) * MOVE_SPEED
    
    # Collision detection
    new_x = player_x + move_x
    new_y = player_y + move_y
    
    # Check if new position is valid
    if 0 <= int(new_x) < MAP_WIDTH and 0 <= int(new_y) < MAP_HEIGHT:
        if GAME_MAP[int(new_y)][int(new_x)] == 0:
            player_x = new_x
            player_y = new_y


def update():
    """Main update loop"""
    # Update game state
    update_player()
    
    # Render
    render_3d_view()
    render_minimap()
    
    # Draw controls help
    screen.brush = brushes.color(255, 255, 255, 200)
    screen.text("UP/DOWN:Move", 5, HEIGHT - 25)
    screen.text("A/C:Turn", 5, HEIGHT - 15)


if __name__ == "__main__":
    run(update)
