import os
import sys
from typing import Dict, List, Tuple

import pygame

from game_logic import Arrow, DIRECTIONS, find_arrow, is_path_clear, can_solve

# ----------------------------- 窗口与常量 -----------------------------
WIDTH, HEIGHT = 1280, 1024
GRID = 5
FPS = 60
MAX_MISTAKES = 3

ROOT = os.path.dirname(os.path.abspath(__file__))
MATERIAL = os.path.join(ROOT, "assets", "UI")                     # 贴图素材目录
MUSIC_PATH = os.path.join(ROOT, "assets", "music", "bgm.mp3")     # BGM（实为 MP3）

# ----------------------------- 关卡数据 -----------------------------
# 每关都是一个 (row, col, direction) 列表，direction 取 U/D/L/R。
# 三个关卡都经过 can_solve 校验，保证存在可通关顺序。
LEVELS = [
    [
        (0, 2, "R"), (2, 2, "U"), (4, 4, "L"),
        (2, 4, "D"), (1, 0, "R"), (3, 0, "U"),
    ],
    [
        (3, 4, "U"), (4, 2, "R"), (2, 4, "L"),
        (4, 1, "U"), (0, 1, "U"), (3, 0, "L"),
        (1, 1, "U"), (1, 2, "D"), (1, 3, "D"),
    ],
    [
        (4, 0, "R"), (4, 1, "R"), (4, 4, "R"),
        (4, 3, "D"), (0, 2, "R"), (3, 3, "D"),
        (0, 0, "R"), (0, 4, "D"), (3, 1, "D"),
    ],
]

for i, level in enumerate(LEVELS, 1):
    arrows = [Arrow(*item) for item in level]
    if not can_solve(arrows):
        raise RuntimeError(f"Level {i} is not solvable")


# ----------------------------- 素材文件名 -----------------------------
BG_START = "起始页.jpg"
BG_GAME = "空棋盘.png"       # 游戏界面（含 5x5 棋盘）
BG_WIN = "过关.jpg"
BG_FAIL = "失败.jpg"
BG_RULES = "游戏规则界面.jpg"
BG_HINT = "提示.jpg"

ARROW_IMG = "箭头.jpg"
# 箭头.jpg 里朝上的箭头所在区域 (x, y, w, h)，已按透明像素测出
ARROW_BBOX = (98, 62, 902, 1392)

# 空棋盘.png 里的棋盘网格线（原图像素坐标），6 条竖线 + 6 条横线 = 5x5 格
GRID_X = [106, 321, 534, 746, 958, 1172]
GRID_Y = [103, 322, 535, 747, 958, 1175]

# ----------------------------- 按钮布局 -----------------------------
# 每个按钮： (贴图文件名, 页面原生 x, y, 宽, 高, 动作)
# 位置/尺寸通过模板匹配从页面图里测出，正好覆盖页面中已有的按钮。
BUTTONS = {
    "start": [
        ("开始游戏按钮.png", 504, 588, 515, 137, "start"),
        ("游戏规则按钮.png", 555, 748, 437, 120, "rules"),
    ],
    "rules": [
        ("返回按钮.png", 492, 826, 489, 159, "back"),
    ],
    "win": [
        ("下一关按钮.png", 429, 735, 588, 158, "next"),
        ("返回主菜单按钮.png", 455, 916, 570, 130, "menu"),
    ],
    "fail": [
        ("重新开始按钮.png", 406, 672, 638, 159, "restart"),
        ("返回主菜单按钮.png", 406, 854, 637, 155, "menu"),
    ],
    "hint": [
        ("好的按钮.png", 577, 508, 302, 115, "back"),
    ],
}

# ----------------------------- 游戏界面 HUD -----------------------------
# 气泡中心坐标（屏幕坐标）。游戏界面背景为 1280x1290 的空棋盘，等比缩放居中，
# 上方留白区域用来放 HUD：关卡在左上角、剩余箭头/剩余生命在棋盘正上方、重开在右上角。
LEVEL_BUBBLE = (95, 42)        # “第 X 关”气泡（左上角，桃粉）
ARROW_BUBBLE = (470, 42)       # “剩余箭头”气泡（棋盘正上方左侧，米白）
LIFE_BUBBLE = (810, 42)        # “剩余生命”气泡（棋盘正上方右侧，米白）
RESTART_BUBBLE = (1195, 42)    # “重开”按钮（右上角，桃粉）

# 气泡配色
PEACH = (240, 128, 155)        # 桃粉色气泡
PEACH_EDGE = (205, 85, 120)    # 桃粉气泡描边
CREAM = (255, 245, 228)        # 米白色气泡
CREAM_EDGE = (238, 143, 112)   # 米白气泡描边
BROWN = (95, 52, 45)           # 深棕色文字


def font(size, bold=False):
    """优先使用系统中文字体，保证中文正常显示。"""
    candidates = [
        r"C:\\Windows\\Fonts\\msyhbd.ttc" if bold else r"C:\\Windows\\Fonts\\msyh.ttc",
        r"C:\\Windows\\Fonts\\simhei.ttf",
        "/System/Library/Fonts/PingFang.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    for path in candidates:
        if os.path.exists(path):
            return pygame.font.Font(path, size)
    return pygame.font.SysFont("arial", size, bold=bold)


class Button:
    """一个可点击的贴图按钮。"""
    __slots__ = ("surface", "rect")

    def __init__(self, surface, rect):
        self.surface = surface
        self.rect = rect

    def draw(self, screen):
        screen.blit(self.surface, self.rect)

    def hit(self, pos):
        return self.rect.collidepoint(pos)


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("我炒，冰！！！")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.title_font = font(54, True)
        self.big_font = font(40, True)
        self.mid_font = font(28, True)
        self.small_font = font(22)

        # 加载各场景背景（等比缩放并居中）
        self.scene_bg: Dict[str, Tuple[pygame.Surface, int, int, float]] = {}
        for key, fn in [
            ("start", BG_START), ("game", BG_GAME), ("win", BG_WIN),
            ("fail", BG_FAIL), ("rules", BG_RULES), ("hint", BG_HINT),
        ]:
            self.scene_bg[key] = self.load_scene(fn)

        self.sprites = self.make_arrow_sprites()
        self.buttons = self.make_buttons()

        # BGM
        self.music_on = True
        if os.path.exists(MUSIC_PATH):
            try:
                pygame.mixer.music.load(MUSIC_PATH)
                pygame.mixer.music.set_volume(0.55)
                pygame.mixer.music.play(-1)
            except pygame.error:
                self.music_on = False

        self.scene = "start"
        self.level_index = 0
        self.mistakes = MAX_MISTAKES
        self.arrows: List[Arrow] = []
        self.removed = set()
        self.animations = []
        self.shakes = {}
        self.message = ""
        self.message_timer = 0
        self.show_hint = False
        # “重开”按钮点击区域（游戏右上角，桃粉气泡）
        self.restart_rect = self.bubble_rect("重开", RESTART_BUBBLE, self.mid_font)
        self.reset_level()

    # ------------------------- 素材加载 -------------------------
    def load_scene(self, filename):
        """等比缩放背景到窗口内并居中，返回 (完整窗口表面, x偏移, y偏移, 缩放)。"""
        img = pygame.image.load(os.path.join(MATERIAL, filename)).convert()
        w, h = img.get_size()
        scale = min(WIDTH / w, HEIGHT / h)
        nw, nh = int(w * scale), int(h * scale)
        scaled = pygame.transform.smoothscale(img, (nw, nh))
        ox, oy = (WIDTH - nw) // 2, (HEIGHT - nh) // 2
        # 用背景左上角颜色填充留白，避免黑边
        full = pygame.Surface((WIDTH, HEIGHT))
        full.fill(img.get_at((0, 0)))
        full.blit(scaled, (ox, oy))
        return full, ox, oy, scale

    def load_button(self, filename, target_w, target_h):
        """加载已去白底的按钮贴图（透明 PNG）并缩放到目标屏幕尺寸。"""
        img = pygame.image.load(os.path.join(MATERIAL, filename)).convert_alpha()
        return pygame.transform.smoothscale(img, (target_w, target_h))

    def make_arrow_sprites(self):
        """从单张朝上的箭头贴图，旋转出上下左右四个方向。"""
        _, ox, oy, scale = self.scene_bg["game"]
        cell_h = (GRID_Y[1] - GRID_Y[0]) * scale
        img = pygame.image.load(os.path.join(MATERIAL, ARROW_IMG)).convert_alpha()
        x, y, w, h = ARROW_BBOX
        arrow = img.subsurface(pygame.Rect(x, y, w, h))
        target_h = int(cell_h * 0.82)
        target_w = int(target_h * w / h)
        base = pygame.transform.smoothscale(arrow, (target_w, target_h))
        # pygame.transform.rotate 逆时针为正：上=0，右=顺时针90=-90，下=180，左=90
        return {
            "U": base,
            "R": pygame.transform.rotate(base, -90),
            "D": pygame.transform.rotate(base, 180),
            "L": pygame.transform.rotate(base, 90),
        }

    def make_buttons(self):
        btns = {}
        for scene, entries in BUTTONS.items():
            _, ox, oy, scale = self.scene_bg[scene]
            for (fn, nx, ny, nw, nh, action) in entries:
                sw, sh = int(nw * scale), int(nh * scale)
                surf = self.load_button(fn, sw, sh)
                sx, sy = ox + nx * scale, oy + ny * scale
                btns[(scene, action)] = Button(surf, pygame.Rect(sx, sy, sw, sh))
        return btns

    # ------------------------- 游戏流程 -------------------------
    def reset_level(self):
        self.arrows = [Arrow(*x) for x in LEVELS[self.level_index]]
        self.removed = set()
        self.animations = []
        self.shakes = {}
        self.mistakes = MAX_MISTAKES
        self.message = ""
        self.message_timer = 0

    def restart(self):
        self.reset_level()
        self.scene = "game"

    def next_level(self):
        if self.level_index < len(LEVELS) - 1:
            self.level_index += 1
            self.reset_level()
            self.scene = "game"
        else:
            self.scene = "start"
            self.level_index = 0
            self.reset_level()

    # ------------------------- 坐标换算 -------------------------
    def cell_center(self, row, col):
        _, ox, oy, scale = self.scene_bg["game"]
        nx = (GRID_X[col] + GRID_X[col + 1]) / 2
        ny = (GRID_Y[row] + GRID_Y[row + 1]) / 2
        return ox + nx * scale, oy + ny * scale

    def arrow_at_mouse(self, pos):
        _, ox, oy, scale = self.scene_bg["game"]
        nx = (pos[0] - ox) / scale
        ny = (pos[1] - oy) / scale
        if not (GRID_X[0] <= nx <= GRID_X[-1] and GRID_Y[0] <= ny <= GRID_Y[-1]):
            return None
        col = next((c for c in range(GRID) if GRID_X[c] <= nx <= GRID_X[c + 1]), None)
        row = next((r for r in range(GRID) if GRID_Y[r] <= ny <= GRID_Y[r + 1]), None)
        if col is None or row is None:
            return None
        return find_arrow(self.arrows, row, col)

    # ------------------------- 核心交互 -------------------------
    def click_arrow(self, arrow):
        if not arrow or arrow in self.animations or arrow in self.removed:
            return
        if is_path_clear(self.arrows, arrow):
            dr, dc = DIRECTIONS[arrow.direction]
            self.animations.append({"arrow": arrow, "t": 0.0, "dr": dr, "dc": dc})
            self.removed.add(arrow)
        else:
            self.mistakes -= 1
            self.shakes[arrow] = 0.28
            self.message = "哎呀！前面有冰淇淋挡住啦！"
            self.message_timer = 1.0
            if self.mistakes <= 0:
                self.scene = "fail"

    def update(self, dt):
        for a in list(self.animations):
            a["t"] += dt / 0.42
            if a["t"] >= 1:
                self.animations.remove(a)
                self.arrows.remove(a["arrow"])
        for arrow in list(self.shakes):
            self.shakes[arrow] -= dt
            if self.shakes[arrow] <= 0:
                del self.shakes[arrow]
        if self.message_timer > 0:
            self.message_timer -= dt
        if self.scene == "game" and not self.arrows and not self.animations:
            self.scene = "win"

    # ------------------------- 绘制辅助 -------------------------
    def draw_text(self, text, center, fnt, color=(255, 255, 255), outline=(95, 52, 45)):
        """带描边的文字，保证在任意背景上都清晰。"""
        base = fnt.render(text, True, color)
        shadow = fnt.render(text, True, outline)
        r = base.get_rect(center=center)
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (2, 2), (-2, 2), (2, -2)]:
            self.screen.blit(shadow, shadow.get_rect(center=(center[0] + dx, center[1] + dy)))
        self.screen.blit(base, r)

    def draw_center_text(self, text, y, fnt, color=(115, 60, 50)):
        surf = fnt.render(text, True, color)
        self.screen.blit(surf, surf.get_rect(center=(WIDTH // 2, y)))

    def bubble_rect(self, text, center, fnt, pad_x=20, pad_y=10):
        """按文字尺寸计算一个胶囊形气泡的矩形（圆角）。"""
        tw, th = fnt.size(text)
        r = pygame.Rect(0, 0, tw + pad_x * 2, th + pad_y * 2)
        r.center = center
        return r

    def draw_bubble(self, text, rect, fnt, fill, text_color, edge=None):
        """画一个胶囊形气泡：填充 + 描边 + 居中文字。"""
        pygame.draw.rect(self.screen, fill, rect, border_radius=rect.h // 2)
        if edge:
            pygame.draw.rect(self.screen, edge, rect, 2, border_radius=rect.h // 2)
        surf = fnt.render(text, True, text_color)
        self.screen.blit(surf, surf.get_rect(center=rect.center))

    def draw_buttons(self, scene):
        for (s, _), btn in self.buttons.items():
            if s == scene:
                btn.draw(self.screen)

    # ------------------------- 各场景绘制 -------------------------
    def draw_start(self):
        self.screen.blit(self.scene_bg["start"][0], (0, 0))
        self.draw_buttons("start")

    def draw_rules(self):
        self.screen.blit(self.scene_bg["rules"][0], (0, 0))
        self.draw_buttons("rules")

    def draw_hint(self):
        self.screen.blit(self.scene_bg["hint"][0], (0, 0))
        self.draw_buttons("hint")

    def draw_game(self):
        self.screen.blit(self.scene_bg["game"][0], (0, 0))

        # 顶部 HUD：关卡（左上桃粉）/ 剩余箭头·剩余生命（棋盘正上方米白）/ 重开（右上桃粉）
        self.draw_bubble(f"第 {self.level_index + 1} 关",
                         self.bubble_rect(f"第 {self.level_index + 1} 关", LEVEL_BUBBLE, self.mid_font),
                         self.mid_font, PEACH, (255, 255, 255), PEACH_EDGE)
        remaining = len(self.arrows) + len(self.animations)
        self.draw_bubble(f"剩余箭头：{remaining}",
                         self.bubble_rect(f"剩余箭头：{remaining}", ARROW_BUBBLE, self.small_font),
                         self.small_font, CREAM, BROWN, CREAM_EDGE)
        dots = "".join("●" if i < self.mistakes else "○" for i in range(MAX_MISTAKES))
        self.draw_bubble(f"剩余生命：{dots}",
                         self.bubble_rect(f"剩余生命：{dots}", LIFE_BUBBLE, self.small_font),
                         self.small_font, CREAM, BROWN, CREAM_EDGE)
        self.draw_bubble("重开", self.restart_rect, self.mid_font, PEACH, (255, 255, 255), PEACH_EDGE)

        # 箭头（含碰撞晃动）
        for arrow in self.arrows:
            x, y = self.cell_center(arrow.row, arrow.col)
            if arrow in self.shakes:
                phase = int(self.shakes[arrow] * 80) % 2
                x += -8 if phase == 0 else 8
            spr = self.sprites[arrow.direction]
            self.screen.blit(spr, spr.get_rect(center=(x, y)))

        # 飞出动画
        _, ox, oy, scale = self.scene_bg["game"]
        fly = (GRID_X[-1] - GRID_X[0]) * scale * 0.8
        for a in self.animations:
            arrow = a["arrow"]
            t = min(1.0, a["t"])
            x, y = self.cell_center(arrow.row, arrow.col)
            x += a["dc"] * fly * t
            y += a["dr"] * fly * t
            spr = self.sprites[arrow.direction]
            self.screen.blit(spr, spr.get_rect(center=(x, y)))

        # 碰撞提示（棋盘下方）
        if self.message_timer > 0:
            box = pygame.Rect(340, 955, 600, 60)
            pygame.draw.rect(self.screen, (255, 245, 228), box, border_radius=28)
            pygame.draw.rect(self.screen, (238, 143, 112), box, 3, border_radius=28)
            self.draw_center_text(self.message, box.centery, self.small_font, (145, 70, 55))

    def draw_result(self, win=True):
        # 过关/失败文案已直接画在背景贴图里，这里只贴背景和按钮。
        self.screen.blit(self.scene_bg["win" if win else "fail"][0], (0, 0))
        self.draw_buttons("win" if win else "fail")

    # ------------------------- 点击处理 -------------------------
    def handle_click(self, pos):
        if self.scene == "hint":
            for (s, action), btn in self.buttons.items():
                if s == "hint" and btn.hit(pos):
                    self.show_hint = False
                    self.scene = "game"
                    return
            self.show_hint = False
            self.scene = "game"
            return

        for (s, action), btn in self.buttons.items():
            if s == self.scene and btn.hit(pos):
                self.do_action(action)
                return

        # 游戏界面里点棋盘 = 选箭头；点右上角“重开”则本关重新开始
        if self.scene == "game":
            if self.restart_rect.collidepoint(pos):
                self.restart()
                return
            self.click_arrow(self.arrow_at_mouse(pos))

    def do_action(self, action):
        if action == "start":
            self.level_index = 0
            self.reset_level()
            self.scene = "game"
        elif action == "rules":
            self.scene = "rules"
        elif action == "back":
            self.scene = "start"
        elif action == "restart":
            self.restart()
        elif action == "next":
            if self.level_index < len(LEVELS) - 1:
                self.next_level()
            else:
                self.scene = "start"
        elif action == "menu":
            self.scene = "start"

    def toggle_music(self):
        if not pygame.mixer.get_init():
            return
        if self.music_on:
            pygame.mixer.music.pause()
            self.music_on = False
        else:
            pygame.mixer.music.unpause()
            self.music_on = True

    # ------------------------- 主循环 -------------------------
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r and self.scene == "game":
                        self.restart()
                    elif event.key == pygame.K_h and self.scene == "game":
                        self.show_hint = True
                        self.scene = "hint"
                    elif event.key == pygame.K_m:
                        self.toggle_music()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_click(event.pos)

            self.update(dt)
            if self.scene == "start":
                self.draw_start()
            elif self.scene == "rules":
                self.draw_rules()
            elif self.scene == "hint":
                self.draw_hint()
            elif self.scene == "game":
                self.draw_game()
            elif self.scene == "win":
                self.draw_result(True)
            elif self.scene == "fail":
                self.draw_result(False)
            pygame.display.flip()
        pygame.quit()


if __name__ == "__main__":
    Game().run()
