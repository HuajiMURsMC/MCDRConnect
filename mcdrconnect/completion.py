from types import MethodType

from mcdreforged.api.types import CommandSource, ServerInterface
from mcdreforged.command.builder.common import CommandSuggestions
from mcdreforged.command.command_manager import CommandManager, TraversePurpose

from mcdrconnect.plugin import get_server_command_completion


def suggest_command(self: CommandManager, command: str, source: CommandSource) -> CommandSuggestions:
    suggestions: CommandSuggestions = self._traverse(command, source, TraversePurpose.SUGGEST)
    query_result = get_server_command_completion(source.get_server(), command, len(command))
    if query_result is not None:
        suggestions.extend(query_result)
    return suggestions


def load(server: ServerInterface):
    global suggest_command_backup
    command_manager = server._mcdr_server.command_manager
    suggest_command_backup = command_manager.suggest_command
    command_manager.suggest_command = MethodType(suggest_command, command_manager)


def unload(server: ServerInterface):
    command_manager = server._mcdr_server.command_manager
    if suggest_command_backup is not None:
        command_manager.suggest_command = suggest_command_backup
