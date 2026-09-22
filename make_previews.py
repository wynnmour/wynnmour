"""无头生成各界面预览截图，用于人工核对按钮贴图是否与原页面重叠、白底是否去掉。"""
import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame

from main import Game

ROOT = os.path.dirname(os.path.abspath(__file__))


def snap(g, name, draw_fn):
    draw_fn()
    out = os.path.join(ROOT, f"preview_{name}.png")
    pygame.image.save(g.screen, out)
    print("saved:", out)


def main():
    g = Game()

    g.scene = "start"; snap(g, "start", g.draw_start)
    g.scene = "rules"; snap(g, "rules", g.draw_rules)
    g.scene = "game";  snap(g, "game",  g.draw_game)
    g.scene = "hint";  snap(g, "hint",  g.draw_hint)
    g.scene = "win";   snap(g, "win",   lambda: g.draw_result(True))
    g.scene = "fail";  snap(g, "fail",  lambda: g.draw_result(False))

    pygame.quit()
    print("done")


if __name__ == "__main__":
    main()
