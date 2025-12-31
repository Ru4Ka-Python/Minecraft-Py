class Config:
    # Rendering
    FOV = 70
    RENDER_DISTANCE = 8 # Chunks
    SMOOTH_LIGHTING = True
    CLOUDS = True
    PARTICLES = True
    V_SYNC = True
    
    # Window
    WIDTH = 1280
    HEIGHT = 720
    
    # Physics
    GRAVITY = 20.0
    TERMINAL_VELOCITY = 50.0
    
    # Controls
    CONTROLS = {
        'forward': 'w',
        'back': 's',
        'left': 'a',
        'right': 'd',
        'jump': 'space',
        'sneak': 'lshift',
        'inventory': 'e',
    }
