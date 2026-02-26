import enum
import math
import os
import subprocess
import sys

import pygame

from src.asset_manager import AssetManager
from src.camera import Camera
from src.config import Config
from src.entity_route import EntityRoute
from src.game_backends.backend import GameState
from src.route_tracker import Conditions
from src.scene_in_out import SceneExit, str_to_scene_transition
from src.route_tracker import Flags

class SceneState(enum.Enum):
    ENTERING = 0,
    ENTERED = 1,
    EXITING = 2,
    EXITED = 3

class CatchEvent:
    def __init__(self):
        self.conditions: Conditions | None = None

    def catch(self, scene) -> bool:
        pass

class DispatchEvent:
    def __init__(self):
        self.conditions: Conditions | None = None
        self.wait_for_previous: bool = False
        self.org_wait: float = 0
        self.wait: float = 0
        self.dispatched: bool = False

    def is_complete(self, scene) -> bool:
        pass

    def dispatch(self, scene, manager) -> None:
        self.dispatched = True

    def update(self, scene, dt: float) -> None:
        pass

class DispatchChain:
    def __init__(self, dispatch: list[DispatchEvent]):
        self.dispatches: list[DispatchEvent] = dispatch
        self.dispatches.insert(0, DispatchEvent())

        self.active: bool = False
        self.last_dispatch_index: int = 0
        self.dispatch_index: int = 0

    def start(self, scene, manager):
        if len(self.dispatches) == 1:
            return

        self.last_dispatch_index = 0
        self.dispatch_index = 0

        self.active = True
        while self.dispatches[self.dispatch_index].conditions is not None and \
                not self.dispatches[self.dispatch_index].conditions.satisfied():
            self.dispatch_index += 1
            if self.dispatch_index >= len(self.dispatches):
                self.active = False
                self.dispatch_index = 0
                scene.remove_dispatch_chain(self)
                return
        self.dispatches[self.dispatch_index].dispatch(scene, manager)
        self.last_dispatch_index = self.dispatch_index
        self.dispatch_index += 1

    def update(self, scene, manager, dt: float):
        if not self.active:
            return

        if self.dispatch_index < len(self.dispatches):
            while self.dispatches[self.dispatch_index].conditions is not None and \
                    not self.dispatches[self.dispatch_index].conditions.satisfied():
                self.dispatch_index += 1

        if self.dispatches[self.last_dispatch_index].is_complete(scene) and \
                self.last_dispatch_index == len(self.dispatches) - 1:
            scene.remove_dispatch_chain(self)
            return

        if not self.dispatches[self.last_dispatch_index].is_complete(scene):
            self.dispatches[self.last_dispatch_index].update(scene, dt)

        if self.dispatch_index >= len(self.dispatches):
            return

        if self.dispatches[self.dispatch_index].wait_for_previous:
            if not self.dispatches[self.dispatch_index - 1].is_complete(scene):
                return

        if self.dispatches[self.dispatch_index].org_wait > 0:
            if self.dispatches[self.dispatch_index].wait <= 0:
                self.dispatches[self.dispatch_index].wait = self.dispatches[self.dispatch_index].org_wait
                self.dispatches[self.dispatch_index].dispatch(scene, manager)
                self.last_dispatch_index = self.dispatch_index
                self.dispatch_index += 1
            else:
                self.dispatches[self.dispatch_index].wait -= dt
        else:
            self.dispatches[self.dispatch_index].dispatch(scene, manager)
            self.last_dispatch_index = self.dispatch_index
            self.dispatch_index += 1

class OnPlayerEnter(CatchEvent):
    def __init__(self, rect: pygame.Rect):
        super().__init__()
        self.rect: pygame.Rect = rect

    def catch(self, scene) -> bool:
        return self.rect.collidepoint(scene.player.grid_pos)

class OnEntityEnter(CatchEvent):
    def __init__(self, ids: list[str], rect: pygame.Rect):
        super().__init__()
        self.ids: list[str] = ids
        self.rect: pygame.Rect = rect

    def catch(self, scene) -> bool:
        for identifier in self.ids:
            if (entity := scene.entities_dict.get(identifier, None)) is not None and \
                    self.rect.colliderect(pygame.Rect(entity.grid_pos, entity.hit_box)):
                return True
        return False

class OnSceneLoad(CatchEvent):
    def __init__(self):
        super().__init__()

    def catch(self, scene) -> bool:
        return True

class OnSceneStart(CatchEvent):
    def __init__(self):
        super().__init__()

    def catch(self, scene) -> bool:
        return scene.state == SceneState.ENTERED

class OnSceneExit(CatchEvent):
    def __init__(self):
        super().__init__()

    def catch(self, scene) -> bool:
        return scene.state == SceneState.EXITED


class ExitScene(DispatchEvent):
    def __init__(self, transition: str, transition_time: float, next_scene: str, entrance: str):
        super().__init__()
        self.exit: SceneExit = SceneExit(
            rect=pygame.Rect(0, 0, 0, 0),
            require_interact=False,
            transition=str_to_scene_transition(transition),
            transition_time=transition_time,
            next_scene=next_scene,
            next_entrance=entrance,
            conditions=Conditions([], [], [])
        )

    def is_complete(self, scene) -> bool:
        return self.dispatched

    def dispatch(self, scene, manager) -> None:
        scene.exiting_through = self.exit
        scene.state = SceneState.EXITING

class StartRunningScene(DispatchEvent):
    def __init__(self, game, params: dict):
        super().__init__()

        self.game = game
        self.params: dict = params

    def is_complete(self, scene) -> bool:
        return self.dispatched

    def dispatch(self, scene, manager) -> None:
        self.dispatched = True
        self.game.set_backend(GameState.RUNNING_SCENE, self.params)

class EndGame(DispatchEvent):
    def __init__(self, game):
        super().__init__()

        self.game = game

    def is_complete(self, scene) -> bool:
        return self.dispatched

    def dispatch(self, scene, manager) -> None:
        self.dispatched = True
        self.game.end_game()

class ModifyFlags(DispatchEvent):
    def __init__(self, how: str, value: str):
        super().__init__()
        self.how: str = how
        self.value: str = value

    def is_complete(self, scene) -> bool:
        return self.dispatched

    def dispatch(self, scene, manager) -> None:
        Flags.modify(self.value, self.how)
        self.dispatched = True


class AddEntity(DispatchEvent):
    def __init__(self, ids: list[str]):
        super().__init__()
        self.ids: list[str] = ids

    def is_complete(self, scene) -> bool:
        return self.dispatched

    def dispatch(self, scene, manager) -> None:
        for identifier in self.ids:
            if scene.entities_dict.get(identifier) is not None:
                scene.entities.append(scene.entities_dict.get(identifier))
        self.dispatched = True

class RemoveEntity(DispatchEvent):
    def __init__(self, ids: list[str]):
        super().__init__()
        self.ids: list[str] = ids

    def is_complete(self, scene) -> bool:
        return self.dispatched

    def dispatch(self, scene, manager) -> None:
        for identifier in self.ids:
            scene.entities.remove(scene.entities_dict.get(identifier))
        self.dispatched = True

class SetEntityRoute(DispatchEvent):
    def __init__(self, entity_id: str, route_id: str):
        super().__init__()
        self.entity_id: str = entity_id
        self.route_id: str = route_id

    def is_complete(self, scene) -> bool:
        return self.dispatched

    def dispatch(self, scene, manager) -> None:
        if scene.entities_dict.get(self.entity_id) is not None:
            scene.entities_dict.get(self.entity_id).set_route(self.route_id)
        self.dispatched = True

class BeginEntityDialogue(DispatchEvent):
    def __init__(self, entity_id: str, dialogue_id: str):
        super().__init__()
        self.entity_id: str = entity_id
        self.dialogue_id: str = dialogue_id

    def is_complete(self, scene) -> bool:
        return scene.dialogue is None and self.dispatched

    def dispatch(self, scene, manager) -> None:
        self.dispatched = True
        dialogue = scene.entities_dict.get(self.entity_id).interact(scene.player, self.dialogue_id)
        if dialogue is not None:
            scene.dialogue = dialogue
            if scene.dialogue.start(scene, manager):
                scene.dialogue = None
                return
            if scene.background_music is not None:
                scene.background_music.set_volume(scene.background_music.get_volume() / 3)

class BeginIndependentDialogue(DispatchEvent):
    def __init__(self, dialogue):
        super().__init__()
        self.dialogue = dialogue

    def is_complete(self, scene) -> bool:
        return scene.dialogue is None and self.dispatched

    def dispatch(self, scene, manager) -> None:
        self.dispatched = True
        scene.dialogue = self.dialogue
        if scene.dialogue.start(scene, manager):
            scene.dialogue = None
            return
        if scene.background_music is not None:
            scene.background_music.set_volume(scene.background_music.get_volume() / 3)

class EndDialogueAbruptly(DispatchEvent):
    def __init__(self):
        super().__init__()

    def is_complete(self, scene) -> bool:
        return self.dispatched

    def dispatch(self, scene, manager) -> None:
        if scene.dialogue is not None:
            scene.dialogue.reset()
            if (entity := scene.entities_dict.get(scene.dialogue.entity_id, None)) is not None:
                entity.block = False
                entity.current_dialogue = None
            scene.dialogue = None
            if scene.background_music is not None:
                scene.background_music.set_volume(scene.background_music.get_volume() * 3)
        self.dispatched = True

class MoveCameraPosition(DispatchEvent):
    def __init__(self, pos: pygame.Vector2, duration: float):
        super().__init__()
        self.pos: pygame.Vector2 = pos * Config.TILE_SIZE - Camera.WINDOW_CENTER
        self.duration: float = duration

        self.start_pos: pygame.Vector2 = pygame.Vector2(0, 0)
        self.elapsed: float = 0
        self.fraction: float = 0

    def is_complete(self, scene) -> bool:
        return self.fraction == 1.0 and self.dispatched

    def dispatch(self, scene, manager) -> None:
        Camera.TRACK = None
        self.start_pos = Camera.POS.copy()
        self.dispatched = True

    def update(self, scene, dt: float) -> None:
        if not self.dispatched:
            return

        if self.duration == 0:
            self.fraction = 1
            t: float = 1.0
        else:
            self.fraction = min(self.elapsed / self.duration, 1.0)
            t: float = -(math.cos(math.pi * self.fraction) - 1) / 2  # EASE IN-OUT

        Camera.POS = self.start_pos.lerp(self.pos, t)
        self.elapsed += dt

class MoveCameraEntity(DispatchEvent):
    def __init__(self, entity_id: str, duration: float):
        super().__init__()
        self.entity_id: str = entity_id
        self.duration: float = duration

        self.target_pos: pygame.Vector2 = pygame.Vector2(0, 0)
        self.start_pos: pygame.Vector2 = pygame.Vector2(0, 0)
        self.elapsed: float = 0
        self.fraction: float = 0

    def is_complete(self, scene) -> bool:
        return Camera.POS == self.target_pos and self.dispatched

    def dispatch(self, scene, manager) -> None:
        Camera.TRACK = None
        self.target_pos = scene.entities_dict.get(self.entity_id).pos - Camera.WINDOW_CENTER
        self.start_pos = Camera.POS.copy()
        self.dispatched = True

    def update(self, scene, dt: float) -> None:
        if not self.dispatched:
            return

        t: float = -(math.cos(math.pi * self.fraction) - 1) / 2  # EASE IN-OUT
        Camera.POS = self.start_pos.lerp(self.target_pos, t)

        self.elapsed += dt
        self.fraction = min(self.elapsed / self.duration, 1.0)

class MoveCameraFollowEntity(DispatchEvent):
    def __init__(self, entity_id: str):
        super().__init__()
        self.entity_id: str = entity_id

    def is_complete(self, scene) -> bool:
        return self.dispatched

    def dispatch(self, scene, manager) -> None:
        Camera.TRACK = scene.entities_dict.get(self.entity_id)
        self.dispatched = True

class MovePlayer(DispatchEvent):
    def __init__(self, route: EntityRoute):
        super().__init__()
        self.route: EntityRoute = route

    def is_complete(self, scene) -> bool:
        return scene.player.current_route is None

    def dispatch(self, scene, manager) -> None:
        scene.player.controls_disabled = True
        scene.player.routes["ROUTE"] = self.route
        scene.player.set_route("ROUTE")
        self.dispatched = True

class ResetCamera(DispatchEvent):
    def __init__(self):
        super().__init__()

    def is_complete(self, scene) -> bool:
        return self.dispatched

    def dispatch(self, scene, manager) -> None:
        Camera.TRACK = scene.player
        self.dispatched = True

class ShakeCamera(DispatchEvent):
    def __init__(self, time: float, intensity: int):
        super().__init__()
        self.time: float = time
        self.intensity: int = intensity

    def is_complete(self, scene) -> bool:
        return self.dispatched

    def dispatch(self, scene, manager) -> None:
        Camera.shake_camera(intensity_x=self.intensity, intensity_y=self.intensity, duration=self.time)
        self.dispatched = True

class EndCameraShake(DispatchEvent):
    def __init__(self):
        super().__init__()

    def is_complete(self, scene) -> bool:
        return self.dispatched

    def dispatch(self, scene, manager) -> None:
        Camera.shake_camera(duration=0)
        self.dispatched = True

class PlayAudio(DispatchEvent):
    def __init__(self, audio_id: str, volume: float):
        super().__init__()
        self.audio_id: str = audio_id
        self.volume: float = volume

        self.sound: pygame.mixer.Sound | None = None

    def is_complete(self, scene) -> bool:
        return self.dispatched

    def dispatch(self, scene, manager) -> None:
        self.sound = AssetManager.get_audio(self.audio_id)
        self.sound = pygame.mixer.Sound(self.sound)
        if self.sound is not None:
            self.sound.set_volume(self.volume)
            self.sound.play()
        self.dispatched = True

class LaunchScript(DispatchEvent):
    def __init__(self, script_path: str):
        super().__init__()
        self.script_path: str = script_path

    def is_complete(self, scene) -> bool:
        return self.dispatched

    def dispatch(self, scene, manager) -> None:
        abs_path = os.path.abspath(self.script_path)
        subprocess.run([sys.executable, abs_path], check=False)
        self.dispatched = True

class ShowAttackChoice(DispatchEvent):
    def __init__(self, peace_path: str, war_path: str):
        super().__init__()
        self.peace_path: str = peace_path
        self.war_path: str = war_path

    def is_complete(self, scene) -> bool:
        return self.dispatched

    def dispatch(self, scene, manager) -> None:
        scene.start_attack_choice(self.peace_path, self.war_path)
        self.dispatched = True

class EnableTrigger(DispatchEvent):
    def __init__(self, trigger_id: str):
        super().__init__()
        self.trigger_id: str = trigger_id

    def is_complete(self, scene) -> bool:
        return self.dispatched

    def dispatch(self, scene, manager) -> None:
        scene.triggers.get(self.trigger_id).disabled = False
        self.dispatched = True

class DisableTrigger(DispatchEvent):
    def __init__(self, trigger_id: str):
        super().__init__()
        self.trigger_id: str = trigger_id

    def is_complete(self, scene) -> bool:
        return self.dispatched

    def dispatch(self, scene, manager) -> None:
        scene.triggers.get(self.trigger_id).disabled = True
        self.dispatched = True
