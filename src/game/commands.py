class CommandHandler:
    def __init__(self, game):
        self.game = game

    def execute(self, command_str):
        if not command_str.startswith('/'):
            return f"Chat: {command_str}"
            
        parts = command_str[1:].split()
        cmd = parts[0]
        args = parts[1:]
        
        if cmd == 'gamemode':
            # handle gamemode
            return f"Gamemode set to {args[0]}"
        elif cmd == 'tp':
            # handle teleport
            return f"Teleported to {args}"
        elif cmd == 'time':
            if args[0] == 'set':
                # handle time set
                return f"Time set to {args[1]}"
        
        return "Unknown command"
