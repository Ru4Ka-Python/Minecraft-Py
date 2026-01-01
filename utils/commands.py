"""
Command system for Minecraft clone.
Implements slash commands for console-like interaction.
"""

import re
from typing import Callable, List, Dict, Optional
from dataclasses import dataclass


class Command:
    """Represents a command with its handler and metadata."""
    
    def __init__(self, name: str, handler: Callable, description: str = "",
                 usage: str = "", aliases: List[str] = None):
        """Initialize command."""
        self.name = name
        self.handler = handler
        self.description = description
        self.usage = usage
        self.aliases = aliases if aliases else []
        
        # Permission level (0 = all, 1 = creative, 2 = operator)
        self.permission = 0


class CommandManager:
    """Manages command registration and execution."""
    
    def __init__(self):
        """Initialize command manager."""
        self.commands: Dict[str, Command] = {}
        self._register_default_commands()
    
    def register(self, command: Command) -> None:
        """Register a command."""
        self.commands[command.name] = command
        for alias in command.aliases:
            self.commands[alias] = command
    
    def _register_default_commands(self) -> None:
        """Register default commands."""
        # Help command
        self.register(Command(
            name='help',
            handler=self._cmd_help,
            description='Show help for commands',
            usage='/help [command]'
        ))
        
        # Game mode commands
        self.register(Command(
            name='gamemode',
            handler=self._cmd_gamemode,
            description='Change game mode',
            usage='/gamemode <survival|creative|adventure|spectator>',
            aliases=['gm']
        ))
        
        # Teleport command
        self.register(Command(
            name='tp',
            handler=self._cmd_tp,
            description='Teleport player',
            usage='/tp [player] <x> <y> <z>',
            aliases=['teleport']
        ))
        
        # Give command
        self.register(Command(
            name='give',
            handler=self._cmd_give,
            description='Give items to player',
            usage='/give <player> <item> [amount]',
            aliases=['i', 'item']
        ))
        
        # Time commands
        self.register(Command(
            name='time',
            handler=self._cmd_time,
            description='Set or query world time',
            usage='/time <set|add> <value>'
        ))
        
        # Weather commands
        self.register(Command(
            name='weather',
            handler=self._cmd_weather,
            description='Set weather',
            usage='/weather <clear|rain|thunder> [duration]'
        ))
        
        # Kill command
        self.register(Command(
            name='kill',
            handler=self._cmd_kill,
            description='Kill player or entity',
            usage='/kill [player]'
        ))
        
        # Spawnpoint command
        self.register(Command(
            name='spawnpoint',
            handler=self._cmd_spawnpoint,
            description='Set spawn point',
            usage='/spawnpoint [player] [x] [y] [z]'
        ))
        
        # Clear inventory command
        self.register(Command(
            name='clear',
            handler=self._cmd_clear,
            description='Clear inventory',
            usage='/clear [player] [item] [data]'
        ))
        
        # Daytime command
        self.register(Command(
            name='day',
            handler=self._cmd_day,
            description='Set time to day',
            usage='/day'
        ))
        
        # Night command
        self.register(Command(
            name='night',
            handler=self._cmd_night,
            description='Set time to night',
            usage='/night'
        ))
        
        # Say command
        self.register(Command(
            name='say',
            handler=self._cmd_say,
            description='Send message to all players',
            usage='/say <message>'
        ))
        
        # Tell command
        self.register(Command(
            name='tell',
            handler=self._cmd_tell,
            description='Send private message',
            usage='/tell <player> <message>',
            aliases=['msg', 'w', 'whisper']
        ))
        
        # Seed command
        self.register(Command(
            name='seed',
            handler=self._cmd_seed,
            description='Show world seed',
            usage='/seed'
        ))
        
        # Difficulty command
        self.register(Command(
            name='difficulty',
            handler=self._cmd_difficulty,
            description='Set difficulty',
            usage='/difficulty <peaceful|easy|normal|hard>'
        ))
        
        # Op/deop commands
        self.register(Command(
            name='op',
            handler=self._cmd_op,
            description='Grant operator status',
            usage='/op <player>',
            permission=2
        ))
        
        self.register(Command(
            name='deop',
            handler=self._cmd_deop,
            description='Revoke operator status',
            usage='/deop <player>',
            permission=2
        ))
        
        # Ban/unban commands
        self.register(Command(
            name='ban',
            handler=self._cmd_ban,
            description='Ban player',
            usage='/ban <player> [reason]',
            permission=2
        ))
        
        self.register(Command(
            name='pardon',
            handler=self._cmd_pardon,
            description='Unban player',
            usage='/pardon <player>',
            permission=2
        ))
    
    def execute(self, sender, message: str) -> str:
        """Execute a command from a message."""
        # Parse command
        if not message.startswith('/'):
            return None
        
        message = message[1:].strip()
        
        # Split into parts
        parts = message.split()
        
        if not parts:
            return "Usage: /command [args]"
        
        command_name = parts[0].lower()
        args = parts[1:]
        
        # Find command
        command = self.commands.get(command_name)
        
        if command is None:
            return f"Unknown command: {command_name}"
        
        # Check permission
        if not self._check_permission(sender, command):
            return "You don't have permission to use this command"
        
        # Execute command
        try:
            result = command.handler(sender, args)
            return result
        except Exception as e:
            return f"Error executing command: {str(e)}"
    
    def _check_permission(self, sender, command: Command) -> bool:
        """Check if sender has permission for command."""
        # Simplified permission check
        if command.permission == 0:
            return True
        
        # Would check player permissions here
        return False
    
    def get_help(self, command_name: str = None) -> str:
        """Get help for a command or all commands."""
        if command_name:
            command = self.commands.get(command_name.lower())
            if command is None:
                return f"Unknown command: {command_name}"
            
            help_text = f"/{command.name}"
            if command.usage:
                help_text += f" {command.usage}"
            help_text += f"\n{command.description}"
            
            if command.aliases:
                help_text += f"\nAliases: {', '.join(command.aliases)}"
            
            return help_text
        
        # List all commands
        help_text = "Available commands:\n"
        
        for name, command in sorted(self.commands.items()):
            if name != command.name:
                continue  # Skip aliases
            
            help_text += f"/{command.name}"
            if command.usage:
                help_text += f" {command.usage}"
            help_text += f" - {command.description}\n"
        
        return help_text
    
    # Command handlers
    def _cmd_help(self, sender, args) -> str:
        """Handle /help command."""
        if args:
            return self.get_help(args[0])
        return self.get_help()
    
    def _cmd_gamemode(self, sender, args) -> str:
        """Handle /gamemode command."""
        if not args:
            return "Usage: /gamemode <survival|creative|adventure|spectator>"
        
        mode = args[0].lower()
        
        if mode in ('s', 'survival', '0'):
            mode = 'survival'
        elif mode in ('c', 'creative', '1'):
            mode = 'creative'
        elif mode in ('a', 'adventure', '2'):
            mode = 'adventure'
        elif mode in ('sp', 'spectator', '3'):
            mode = 'spectator'
        else:
            return f"Unknown game mode: {args[0]}"
        
        # Would change player game mode
        return f"Game mode set to {mode}"
    
    def _cmd_tp(self, sender, args) -> str:
        """Handle /tp command."""
        if len(args) < 3:
            return "Usage: /tp [player] <x> <y> <z>"
        
        # Parse coordinates
        try:
            x = float(args[-3])
            y = float(args[-2])
            z = float(args[-1])
        except ValueError:
            return "Invalid coordinates"
        
        return f"Teleported to ({x}, {y}, {z})"
    
    def _cmd_give(self, sender, args) -> str:
        """Handle /give command."""
        if len(args) < 2:
            return "Usage: /give <player> <item> [amount]"
        
        player = args[0]
        item = args[1]
        amount = int(args[2]) if len(args) > 2 else 1
        
        return f"Gave {amount} x {item} to {player}"
    
    def _cmd_time(self, sender, args) -> str:
        """Handle /time command."""
        if len(args) < 2:
            return "Usage: /time <set|add> <value>"
        
        action = args[0].lower()
        try:
            value = int(args[1])
        except ValueError:
            return "Invalid time value"
        
        if action == 'set':
            return f"Time set to {value}"
        elif action == 'add':
            return f"Time added {value}"
        else:
            return "Usage: /time <set|add> <value>"
    
    def _cmd_weather(self, sender, args) -> str:
        """Handle /weather command."""
        if not args:
            return "Usage: /weather <clear|rain|thunder> [duration]"
        
        weather = args[0].lower()
        duration = int(args[1]) if len(args) > 1 else 6000
        
        if weather not in ('clear', 'rain', 'thunder'):
            return "Usage: /weather <clear|rain|thunder> [duration]"
        
        return f"Weather set to {weather} for {duration} ticks"
    
    def _cmd_kill(self, sender, args) -> str:
        """Handle /kill command."""
        return "Killed"
    
    def _cmd_spawnpoint(self, sender, args) -> str:
        """Handle /spawnpoint command."""
        return "Spawn point set"
    
    def _cmd_clear(self, sender, args) -> str:
        """Handle /clear command."""
        return "Inventory cleared"
    
    def _cmd_day(self, sender, args) -> str:
        """Handle /day command."""
        return "Time set to 1000 (day)"
    
    def _cmd_night(self, sender, args) -> str:
        """Handle /night command."""
        return "Time set to 13000 (night)"
    
    def _cmd_say(self, sender, args) -> str:
        """Handle /say command."""
        if not args:
            return "Usage: /say <message>"
        
        message = ' '.join(args)
        return f"[Server] {sender.name}: {message}"
    
    def _cmd_tell(self, sender, args) -> str:
        """Handle /tell command."""
        if len(args) < 2:
            return "Usage: /tell <player> <message>"
        
        player = args[0]
        message = ' '.join(args[1:])
        
        return f"Message sent to {player}"
    
    def _cmd_seed(self, sender, args) -> str:
        """Handle /seed command."""
        return "Seed: 12345"
    
    def _cmd_difficulty(self, sender, args) -> str:
        """Handle /difficulty command."""
        if not args:
            return "Usage: /difficulty <peaceful|easy|normal|hard>"
        
        difficulty = args[0].lower()
        
        if difficulty in ('p', 'peaceful', '0'):
            return "Difficulty set to Peaceful"
        elif difficulty in ('e', 'easy', '1'):
            return "Difficulty set to Easy"
        elif difficulty in ('n', 'normal', '2'):
            return "Difficulty set to Normal"
        elif difficulty in ('h', 'hard', '3'):
            return "Difficulty set to Hard"
        else:
            return "Usage: /difficulty <peaceful|easy|normal|hard>"
    
    def _cmd_op(self, sender, args) -> str:
        """Handle /op command."""
        if not args:
            return "Usage: /op <player>"
        
        player = args[0]
        return f"{player} is now operator"
    
    def _cmd_deop(self, sender, args) -> str:
        """Handle /deop command."""
        if not args:
            return "Usage: /deop <player>"
        
        player = args[0]
        return f"{player} is no longer operator"
    
    def _cmd_ban(self, sender, args) -> str:
        """Handle /ban command."""
        if not args:
            return "Usage: /ban <player> [reason]"
        
        player = args[0]
        reason = ' '.join(args[1:]) if len(args) > 1 else "Banned by an operator"
        
        return f"{player} has been banned: {reason}"
    
    def _cmd_pardon(self, sender, args) -> str:
        """Handle /pardon command."""
        if not args:
            return "Usage: /pardon <player>"
        
        player = args[0]
        return f"{player} has been unbanned"
