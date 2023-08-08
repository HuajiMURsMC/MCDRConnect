import json
from types import MethodType
from typing import Dict, Optional

from mcdreforged.api.types import (CommandSource, PluginServerInterface,
                                   ServerInterface, Version)
from mcdreforged.api.utils.serializer import Serializable
from mcdreforged.command.builder.common import (CommandSuggestion,
                                                CommandSuggestions)
from mcdreforged.command.command_manager import CommandManager, TraversePurpose

from mcdrconnect.config import Config

config: Optional[Config] = None
cached_version: Optional['ServerVersion'] = None
suggest_command_backup: Optional[MethodType] = None


class ServerVersion(Serializable):
    version: str
    semver: Version


def query_data(server: ServerInterface, id_: str, data: str = "") -> Optional[str]:
    return server.rcon_query(f'mcdrconnectgetdata {id_} "{data}"')


def get_server_command_completion(server: ServerInterface, input_: str, cursor: int) -> Optional[CommandSuggestions]:
    result = query_data(server, "mcdrconnect.command_completion", json.dumps({"input": input_, "cursor": cursor}))
    if not result:
        return
    try:
        suggestions_obj: Dict[str, str] = json.loads(result)
    except Exception:
        return
    suggestions = CommandSuggestions()
    for suggest_segment, command_read in suggestions_obj.items():
        suggestion = CommandSuggestion(command_read, suggest_segment)
        suggestions.append(suggestion)
    return suggestions


def get_server_version(server: ServerInterface) -> Optional[ServerVersion]:
    if cached_version is not None:
        return cached_version
    result = query_data(server, "mcdrconnect.server_version")
    if not result:
        return
    return ServerVersion.deserialize(json.loads(result))


def suggest_command(self: CommandManager, command: str, source: CommandSource) -> CommandSuggestions:
    suggestions: CommandSuggestions = self._traverse(command, source, TraversePurpose.SUGGEST)
    query_result = get_server_command_completion(source.get_server(), command, len(command))
    if query_result is not None:
        suggestions.extend(query_result)
    return suggestions


def on_load(server: PluginServerInterface, old):
    global config, cached_version, suggest_command_backup
    config = server.load_config_simple(target_class=Config)
    if old.cached_version is not None:
        cached_version = old.cached_version
    if config.advanced_completion:
        command_manager = server._mcdr_server.command_manager
        suggest_command_backup = command_manager.suggest_command
        command_manager.suggest_command = MethodType(suggest_command, command_manager)


def on_unload(server: PluginServerInterface):
    if config.advanced_completion:
        command_manager = server._mcdr_server.command_manager
        if suggest_command_backup is not None:
            command_manager.suggest_command = suggest_command_backup
