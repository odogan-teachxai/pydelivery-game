import json
import os
import sys
from dataclasses import dataclass

import pygame


WIDTH, HEIGHT = 960, 640
FPS = 60
SAVE_FILE = "save_data.json"

WHITE = (245, 245, 245)
BLACK = (15, 15, 15)
GRAY = (60, 60, 60)
DARK_GRAY = (35, 35, 35)
GREEN = (80, 160, 80)
ROAD = (110, 110, 110)
BLUE = (70, 120, 210)
ORANGE = (220, 150, 80)
RED = (210, 80, 80)
TAN = (235, 210, 180)


@dataclass
class GameSettings:
    fps_limit: int = 60
    god_mode: bool = False


@dataclass
class DeliveryState:
    money: int = 0
    delivered: int = 0
    failed: int = 0
    level: int = 1
    carrying: bool = False
    pickup_available: bool = True


class Button:
    def __init__(self, rect, label, font):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.font = font

    def draw(self, surface, hover=False):
        color = DARK_GRAY if hover else GRAY
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, BLACK, self.rect, 2, border_radius=8)
        text = self.font.render(self.label, True, WHITE)
        text_rect = text.get_rect(center=self.rect.center)
        surface.blit(text, text_rect)

    def is_hovered(self, pos):
        return self.rect.collidepoint(pos)


class Player:
    def __init__(self, pos):
        self.rect = pygame.Rect(pos[0], pos[1], 28, 28)
        self.speed = 3

    def move(self, dx, dy, obstacles):
        if dx == 0 and dy == 0:
            return
        original = self.rect.copy()
        self.rect.x += dx
        for obstacle in obstacles:
            if self.rect.colliderect(obstacle):
                self.rect.x = original.x
                break
        self.rect.y += dy
        for obstacle in obstacles:
            if self.rect.colliderect(obstacle):
                self.rect.y = original.y
                break
        self.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))


class DeliveryGame:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Delivery Runner")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font_title = pygame.font.SysFont("arial", 46, bold=True)
        self.font = pygame.font.SysFont("arial", 28)
        self.font_small = pygame.font.SysFont("arial", 22)
        self.settings = GameSettings()
        self.state = DeliveryState()
        self.mode = "menu"
        self.last_mode = "menu"
        self.player = Player((120, 120))
        self.delivery_log = []
        self.delivery_time_limit = 25.0
        self.delivery_timer = 0.0
        self.package_rect = None
        self.safe_spawn = pygame.Rect(80, 80, 28, 28)
        self.safe_package_spawn = pygame.Rect(120, 120, 20, 16)
        self.safe_pickup_spawn = pygame.Rect(160, 420, 32, 32)
        self.safe_dropoff_spawn = pygame.Rect(760, 140, 40, 40)
        self.levels = self.build_levels()
        self.apply_level(self.state.level)
        self.buttons = {}
        self.create_buttons()
        self.load_game(auto=True)

    def build_levels(self):
        return {
            1: {
                "pickup": pygame.Rect(160, 420, 32, 32),
                "dropoff": pygame.Rect(760, 140, 40, 40),
                "time_limit": 25.0,
                "obstacles": [
                    pygame.Rect(260, 80, 80, 120),
                    pygame.Rect(420, 60, 120, 80),
                    pygame.Rect(580, 220, 60, 180),
                    pygame.Rect(160, 260, 120, 60),
                    pygame.Rect(300, 380, 90, 140),
                    pygame.Rect(520, 420, 200, 80),
                    pygame.Rect(700, 330, 90, 60),
                    pygame.Rect(80, 520, 120, 70),
                ],
            },
            2: {
                "pickup": pygame.Rect(120, 140, 32, 32),
                "dropoff": pygame.Rect(820, 500, 40, 40),
                "time_limit": 21.0,
                "obstacles": [
                    pygame.Rect(80, 80, 140, 70),
                    pygame.Rect(260, 60, 90, 180),
                    pygame.Rect(380, 120, 70, 140),
                    pygame.Rect(520, 80, 150, 70),
                    pygame.Rect(700, 140, 90, 170),
                    pygame.Rect(180, 260, 120, 60),
                    pygame.Rect(340, 280, 120, 60),
                    pygame.Rect(520, 280, 120, 60),
                    pygame.Rect(700, 300, 120, 60),
                    pygame.Rect(120, 400, 140, 90),
                    pygame.Rect(320, 430, 100, 110),
                    pygame.Rect(520, 420, 140, 90),
                    pygame.Rect(720, 420, 120, 120),
                ],
            },
            3: {
                "pickup": pygame.Rect(100, 520, 32, 32),
                "dropoff": pygame.Rect(820, 120, 40, 40),
                "time_limit": 18.0,
                "obstacles": [
                    pygame.Rect(60, 60, 160, 60),
                    pygame.Rect(250, 40, 70, 140),
                    pygame.Rect(360, 80, 80, 140),
                    pygame.Rect(480, 40, 70, 140),
                    pygame.Rect(600, 80, 80, 140),
                    pygame.Rect(720, 40, 120, 70),
                    pygame.Rect(120, 180, 140, 70),
                    pygame.Rect(300, 210, 120, 60),
                    pygame.Rect(470, 210, 120, 60),
                    pygame.Rect(640, 210, 160, 70),
                    pygame.Rect(80, 300, 140, 70),
                    pygame.Rect(260, 320, 120, 60),
                    pygame.Rect(440, 320, 120, 60),
                    pygame.Rect(620, 320, 160, 70),
                    pygame.Rect(120, 420, 140, 70),
                    pygame.Rect(320, 440, 120, 60),
                    pygame.Rect(520, 440, 120, 60),
                    pygame.Rect(720, 440, 120, 80),
                    pygame.Rect(240, 520, 140, 70),
                    pygame.Rect(460, 520, 120, 70),
                    pygame.Rect(640, 520, 160, 70),
                ],
            },
        }

    def apply_level(self, level):
        level_data = self.levels.get(level, self.levels[1])
        self.state.level = level
        self.pickup = level_data["pickup"].copy()
        self.dropoff = level_data["dropoff"].copy()
        self.obstacles = [rect.copy() for rect in level_data["obstacles"]]
        self.delivery_time_limit = level_data["time_limit"]
        self.delivery_timer = 0.0
        self.package_rect = None
        self.ensure_valid_positions()

    def ensure_valid_positions(self):
        self.pickup = self.find_safe_rect(self.pickup, self.safe_pickup_spawn)
        self.dropoff = self.find_safe_rect(self.dropoff, self.safe_dropoff_spawn)
        self.player.rect = self.find_safe_rect(self.player.rect, self.safe_spawn)
        if self.package_rect:
            self.package_rect = self.find_safe_rect(self.package_rect, self.safe_package_spawn)

    def find_safe_rect(self, rect, fallback_rect):
        if not self.rect_collides(rect):
            return rect
        safe_rect = self.find_nearest_safe(rect)
        if safe_rect:
            return safe_rect
        return fallback_rect.copy()

    def rect_collides(self, rect):
        if rect.left < 0 or rect.right > WIDTH or rect.top < 0 or rect.bottom > HEIGHT:
            return True
        return any(rect.colliderect(obstacle) for obstacle in self.obstacles)

    def find_nearest_safe(self, rect):
        search = [
            (0, 0),
            (40, 0), (-40, 0), (0, 40), (0, -40),
            (80, 0), (-80, 0), (0, 80), (0, -80),
            (120, 0), (-120, 0), (0, 120), (0, -120),
            (40, 40), (-40, -40), (40, -40), (-40, 40),
            (80, 80), (-80, -80), (80, -80), (-80, 80),
            (120, 120), (-120, -120), (120, -120), (-120, 120),
        ]
        for dx, dy in search:
            candidate = rect.copy()
            candidate.x += dx
            candidate.y += dy
            candidate.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))
            if not self.rect_collides(candidate):
                return candidate
        return None

    def create_buttons(self):
        center_x = WIDTH // 2 - 130
        y = 220
        labels = ["Start New Game", "Load", "Settings", "Quit"]
        for label in labels:
            key = label.lower().replace(" ", "-")
            self.buttons[key] = Button((center_x, y, 260, 50), label, self.font)
            y += 70

    def save_game(self):
        data = {
            "money": self.state.money,
            "delivered": self.state.delivered,
            "failed": self.state.failed,
            "level": self.state.level,
            "carrying": self.state.carrying,
            "pickup_available": self.state.pickup_available,
            "delivery_timer": self.delivery_timer,
            "package_pos": [self.package_rect.x, self.package_rect.y] if self.package_rect else None,
            "settings": {"fps_limit": self.settings.fps_limit, "god_mode": self.settings.god_mode},
        }
        with open(SAVE_FILE, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)

    def load_game(self, auto=False):
        if not os.path.exists(SAVE_FILE):
            if not auto:
                self.delivery_log.append("No save found yet.")
            return
        with open(SAVE_FILE, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        self.state.money = int(data.get("money", 0))
        self.state.delivered = int(data.get("delivered", 0))
        self.state.failed = int(data.get("failed", 0))
        self.state.level = int(data.get("level", 1))
        self.state.carrying = bool(data.get("carrying", False))
        self.state.pickup_available = bool(data.get("pickup_available", True))
        self.delivery_timer = float(data.get("delivery_timer", 0.0))
        package_pos = data.get("package_pos")
        if package_pos:
            self.package_rect = pygame.Rect(package_pos[0], package_pos[1], 20, 16)
        else:
            self.package_rect = None
        settings = data.get("settings", {})
        self.settings.fps_limit = int(settings.get("fps_limit", FPS))
        if self.settings.fps_limit not in {15, 30, 60}:
            self.settings.fps_limit = FPS
        self.settings.god_mode = bool(settings.get("god_mode", False))
        self.apply_level(self.state.level)
        self.ensure_valid_positions()
        if self.delivery_timer > 0:
            self.delivery_log.append("Delivery in progress - timer resumed.")
        if not auto:
            self.delivery_log.append("Loaded saved progress.")


    def update(self):
        if self.mode == "gameplay":
            self.update_gameplay()
            self.update_delivery_timer()

    def update_gameplay(self):
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_d] - keys[pygame.K_a]) * self.player.speed
        dy = (keys[pygame.K_s] - keys[pygame.K_w]) * self.player.speed
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071
        if self.settings.god_mode:
            self.player.rect.x += dx
            self.player.rect.y += dy
            self.player.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))
        else:
            self.player.move(dx, dy, self.obstacles)

    def update_delivery_timer(self):
        if self.delivery_timer <= 0:
            return
        delta = self.clock.get_time() / 1000.0
        if delta <= 0:
            return
        self.delivery_timer -= delta
        if self.delivery_timer <= 0:
            self.fail_delivery("Delivery failed - time ran out.")

    def toggle_god_mode(self):
        if self.settings.god_mode and self.player_inside_obstacle():
            self.trigger_punishment()
            return
        self.settings.god_mode = not self.settings.god_mode
        if not self.settings.god_mode and self.player_inside_obstacle():
            self.trigger_punishment()

    def set_mode(self, mode):
        if mode == "settings":
            self.last_mode = self.mode
        self.mode = mode

    def player_inside_obstacle(self):
        return any(self.player.rect.colliderect(obstacle) for obstacle in self.obstacles)

    def trigger_punishment(self):
        self.draw_punishment()
        self.delete_save()
        pygame.display.flip()
        pygame.time.delay(1200)
        pygame.quit()
        sys.exit()

    def delete_save(self):
        if os.path.exists(SAVE_FILE):
            os.remove(SAVE_FILE)

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.save_game()
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.mode == "gameplay":
                    self.set_mode("pause")
                elif self.mode in {"pause", "log", "settings"}:
                    self.set_mode("menu" if self.mode == "settings" else "gameplay")
            if event.key == pygame.K_TAB and self.mode == "gameplay":
                self.set_mode("log")
            if event.key == pygame.K_e and self.mode == "gameplay":
                self.handle_delivery()
            if event.key == pygame.K_F1 and self.mode == "gameplay":
                self.set_mode("settings")
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.mode == "menu":
                self.handle_menu_click(event.pos)
            elif self.mode == "pause":
                self.handle_pause_click(event.pos)
            elif self.mode == "settings":
                self.handle_settings_click(event.pos)
            elif self.mode == "log":
                self.set_mode("gameplay")

    def handle_delivery(self):
        if self.state.carrying:
            if self.player.rect.colliderect(self.dropoff):
                self.complete_delivery()
            else:
                self.drop_package()
            return
        if self.state.pickup_available and self.player.rect.colliderect(self.pickup):
            self.pickup_package()
        elif self.package_rect and self.player.rect.colliderect(self.package_rect):
            self.pickup_package(from_ground=True)

    def pickup_package(self, from_ground=False):
        self.state.carrying = True
        self.state.pickup_available = False
        self.delivery_timer = self.delivery_time_limit
        if from_ground:
            self.package_rect = None
            self.delivery_log.append("Picked up the dropped package.")
        else:
            self.delivery_log.append("Picked up package.")

    def drop_package(self):
        self.state.carrying = False
        self.package_rect = pygame.Rect(
            self.player.rect.centerx - 10,
            self.player.rect.centery + 6,
            20,
            16,
        )
        self.delivery_log.append("Dropped package on the street.")

    def complete_delivery(self):
        self.state.carrying = False
        self.state.pickup_available = True
        self.delivery_timer = 0.0
        self.package_rect = None
        self.state.money += 35
        self.state.delivered += 1
        self.delivery_log.append("Delivery complete! Earned $35.")
        self.check_level_progression()
        self.save_game()

    def fail_delivery(self, message):
        self.state.carrying = False
        self.state.pickup_available = True
        self.delivery_timer = 0.0
        self.package_rect = None
        self.state.failed += 1
        self.delivery_log.append(message)
        self.save_game()

    def check_level_progression(self):
        next_level = min(3, (self.state.delivered // 3) + 1)
        if next_level != self.state.level:
            self.apply_level(next_level)
            self.delivery_log.append(f"Advanced to level {next_level}!")

    def handle_menu_click(self, pos):
        for key, button in self.buttons.items():
            if button.is_hovered(pos):
                if key == "start-new-game":
                    self.start_new_game()
                    self.set_mode("gameplay")
                elif key == "load":
                    self.load_game()
                    self.set_mode("gameplay")
                elif key == "settings":
                    self.set_mode("settings")
                elif key == "quit":
                    self.save_game()
                    pygame.quit()
                    sys.exit()

    def handle_pause_click(self, pos):
        resume_button = self.get_pause_buttons()[0]
        if resume_button.is_hovered(pos):
            self.set_mode("gameplay")
        elif self.get_pause_buttons()[1].is_hovered(pos):
            self.set_mode("menu")

    def start_new_game(self):
        self.state = DeliveryState()
        self.settings.god_mode = False
        self.delivery_log = ["Started a new game."]
        self.delivery_timer = 0.0
        self.package_rect = None
        self.apply_level(1)
        self.player.rect.topleft = (self.safe_spawn.x, self.safe_spawn.y)
        self.ensure_valid_positions()
        self.save_game()

    def handle_settings_click(self, pos):
        fps_rects, god_rect, back_rect = self.get_settings_buttons()
        for fps_value, rect in fps_rects.items():
            if rect.collidepoint(pos):
                self.settings.fps_limit = fps_value
                self.save_game()
                return
        if god_rect.collidepoint(pos):
            self.toggle_god_mode()
            if self.mode == "punishment":
                return
            self.save_game()
            return
        if back_rect.collidepoint(pos):
            self.save_game()
            self.set_mode("gameplay" if self.last_mode == "gameplay" else "menu")

    def draw(self):
        if self.mode == "menu":
            self.draw_menu()
        elif self.mode == "gameplay":
            self.draw_gameplay()
        elif self.mode == "pause":
            self.draw_gameplay()
            self.draw_pause()
        elif self.mode == "log":
            self.draw_gameplay()
            self.draw_log()
        elif self.mode == "settings":
            self.draw_settings()
        elif self.mode == "punishment":
            self.draw_punishment()

    def draw_menu(self):
        self.screen.fill(DARK_GRAY)
        title = self.font_title.render("Delivery Runner", True, WHITE)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 120)))
        mouse = pygame.mouse.get_pos()
        for button in self.buttons.values():
            button.draw(self.screen, button.is_hovered(mouse))
        self.draw_footer("Main Menu")

    def draw_gameplay(self):
        self.screen.fill(GREEN)
        self.draw_roads()
        for obstacle in self.obstacles:
            pygame.draw.rect(self.screen, DARK_GRAY, obstacle)
        pygame.draw.rect(self.screen, BLUE, self.dropoff)
        if self.state.pickup_available:
            pygame.draw.rect(self.screen, ORANGE, self.pickup)
        self.draw_player()
        if self.state.carrying:
            self.draw_package(self.player.rect)
        elif self.package_rect:
            self.draw_package(self.package_rect)
        self.draw_hud()
        self.draw_footer("Gameplay - TAB Delivery Log, ESC Pause, F1 Settings")

    def draw_roads(self):
        pygame.draw.rect(self.screen, ROAD, (0, 130, WIDTH, 90))
        pygame.draw.rect(self.screen, ROAD, (0, 320, WIDTH, 100))
        pygame.draw.rect(self.screen, ROAD, (200, 0, 120, HEIGHT))
        pygame.draw.rect(self.screen, ROAD, (560, 0, 120, HEIGHT))

    def draw_player(self):
        head_center = (self.player.rect.centerx, self.player.rect.y + 6)
        torso_top = (self.player.rect.centerx, self.player.rect.y + 12)
        torso_bottom = (self.player.rect.centerx, self.player.rect.y + 26)
        left_hand = (self.player.rect.centerx - 10, self.player.rect.y + 16)
        right_hand = (self.player.rect.centerx + 10, self.player.rect.y + 16)
        left_foot = (self.player.rect.centerx - 6, self.player.rect.y + 30)
        right_foot = (self.player.rect.centerx + 6, self.player.rect.y + 30)
        pygame.draw.circle(self.screen, TAN, head_center, 6)
        pygame.draw.line(self.screen, BLACK, torso_top, torso_bottom, 3)
        pygame.draw.line(self.screen, BLACK, torso_top, left_hand, 3)
        pygame.draw.line(self.screen, BLACK, torso_top, right_hand, 3)
        pygame.draw.line(self.screen, BLACK, torso_bottom, left_foot, 3)
        pygame.draw.line(self.screen, BLACK, torso_bottom, right_foot, 3)
        pygame.draw.circle(self.screen, BLACK, (head_center[0] - 2, head_center[1] - 2), 1)
        pygame.draw.circle(self.screen, BLACK, (head_center[0] + 2, head_center[1] - 2), 1)

    def draw_package(self, target_rect):
        if target_rect == self.player.rect:
            package = pygame.Rect(self.player.rect.centerx - 10, self.player.rect.y + 14, 20, 14)
        else:
            package = target_rect.copy()
        pygame.draw.rect(self.screen, ORANGE, package, border_radius=3)
        pygame.draw.line(self.screen, BLACK, (package.left, package.centery), (package.right, package.centery), 2)

    def draw_hud(self):
        if self.state.carrying:
            objective = "Objective: Deliver to the drop-off"
        elif self.state.pickup_available:
            objective = "Objective: Pick up the package"
        else:
            objective = "Objective: Retrieve dropped package"
        timer_text = "Timer: --" if self.delivery_timer <= 0 else f"Timer: {max(self.delivery_timer, 0):.1f}s"
        money_text = f"Money: ${self.state.money}"
        deliveries_text = f"Delivered: {self.state.delivered}  Failed: {self.state.failed}"
        level_text = f"Level: {self.state.level}/3"
        self.screen.blit(self.font_small.render(objective, True, BLACK), (20, 18))
        self.screen.blit(self.font_small.render(timer_text, True, BLACK), (20, 42))
        self.screen.blit(self.font_small.render(money_text, True, BLACK), (20, 66))
        self.screen.blit(self.font_small.render(deliveries_text, True, BLACK), (20, 90))
        self.screen.blit(self.font_small.render(level_text, True, BLACK), (20, 114))

    def draw_punishment(self):
        self.screen.fill(WHITE)
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        if (pygame.time.get_ticks() // 300) % 2 == 0:
            message = self.font_title.render("YOU CHEATER!", True, WHITE)
            self.screen.blit(message, message.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

    def draw_pause(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        title = self.font_title.render("Paused", True, WHITE)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 140)))
        for button in self.get_pause_buttons():
            button.draw(self.screen, button.is_hovered(pygame.mouse.get_pos()))
        self.draw_footer("Pause Menu")

    def draw_log(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        title = self.font_title.render("Delivery Log", True, WHITE)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 100)))
        y = 170
        entries = self.delivery_log[-8:]
        if not entries:
            entries = ["No deliveries yet."]
        for entry in entries:
            text = self.font.render(entry, True, WHITE)
            self.screen.blit(text, (120, y))
            y += 40
        tip = self.font_small.render("Click or press ESC to return", True, WHITE)
        self.screen.blit(tip, tip.get_rect(center=(WIDTH // 2, HEIGHT - 60)))
        self.draw_footer("Delivery Log")

    def draw_settings(self):
        self.screen.fill(DARK_GRAY)
        title = self.font_title.render("Settings", True, WHITE)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 120)))
        fps_rects, god_rect, back_rect = self.get_settings_buttons()
        for fps_value, rect in fps_rects.items():
            color = BLUE if self.settings.fps_limit == fps_value else GRAY
            pygame.draw.rect(self.screen, color, rect, border_radius=8)
            pygame.draw.rect(self.screen, BLACK, rect, 2, border_radius=8)
            label = f"FPS Limit: {fps_value}"
            self.screen.blit(self.font.render(label, True, WHITE), (rect.x + 18, rect.y + 10))
        god_color = ORANGE if self.settings.god_mode else GRAY
        pygame.draw.rect(self.screen, god_color, god_rect, border_radius=8)
        pygame.draw.rect(self.screen, BLACK, god_rect, 2, border_radius=8)
        god_label = f"God Mode: {'On' if self.settings.god_mode else 'Off'}"
        self.screen.blit(self.font.render(god_label, True, WHITE), (god_rect.x + 18, god_rect.y + 10))
        pygame.draw.rect(self.screen, GRAY, back_rect, border_radius=8)
        pygame.draw.rect(self.screen, BLACK, back_rect, 2, border_radius=8)
        self.screen.blit(self.font.render("Back", True, WHITE), (back_rect.x + 80, back_rect.y + 10))
        self.draw_footer("Settings")

    def draw_footer(self, label):
        footer = self.font_small.render(label, True, WHITE)
        self.screen.blit(footer, (20, HEIGHT - 30))

    def get_pause_buttons(self):
        resume = Button((WIDTH // 2 - 130, 240, 260, 50), "Resume", self.font)
        menu = Button((WIDTH // 2 - 130, 310, 260, 50), "Main Menu", self.font)
        return [resume, menu]

    def get_settings_buttons(self):
        fps_rects = {
            15: pygame.Rect(WIDTH // 2 - 160, 190, 320, 55),
            30: pygame.Rect(WIDTH // 2 - 160, 260, 320, 55),
            60: pygame.Rect(WIDTH // 2 - 160, 330, 320, 55),
        }
        god_rect = pygame.Rect(WIDTH // 2 - 160, 400, 320, 55)
        back_rect = pygame.Rect(WIDTH // 2 - 90, 480, 180, 50)
        return fps_rects, god_rect, back_rect

    def run(self):
        while True:
            for event in pygame.event.get():
                self.handle_event(event)
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(self.settings.fps_limit)


if __name__ == "__main__":
    DeliveryGame().run()
