import pygame
import random
import sys
import csv
import os
from collections import deque

# ==========================================
# 1. 常量配置 (Constants)
# ==========================================
SCREEN_WIDTH = 1200   # 窗口总宽度
SCREEN_HEIGHT = 900  # 高度
FPS = 60

# 赛道核心逻辑变量
# Core logic variables of the track
TRACK_WIDTH = 520                               # 核心赛道宽度 track width
TRACK_LEFT = (SCREEN_WIDTH - TRACK_WIDTH) // 2  # 赛道左边界   track left boundary
TRACK_RIGHT = TRACK_LEFT + TRACK_WIDTH          # 赛道右边界   track right boundary

# 颜色定义
# Color definition
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 128, 255)
GRAY = (100, 100, 100)
GOLD = (255, 215, 0)
GREEN = (0, 255, 0)
CYAN = (0, 255, 255)

SCORE_FILE = "high_scores.csv"


# ==========================================
# 2. 面向对象：支持图片的下落物基类 (object-oriented)
# ==========================================
class ScrollObject(pygame.sprite.Sprite):
    """所有下落物体的基类，支持动态图片加载与防错降级"""
    """Base class for all falling objects, supports dynamic image loading and error-proofing/fallback."""
    def __init__(self, width, height, image_path, speed, backup_color):
        super().__init__()
        
        # 尝试加载图片，如果失败则降级使用纯色块，确保程序绝对不崩溃
        # try load picture if fail use block to replace
        try:
            raw_img = pygame.image.load(image_path).convert_alpha()
            self.image = pygame.transform.scale(raw_img, (width, height))
        except pygame.error:
            self.image = pygame.Surface((width, height))
            self.image.fill(backup_color)

        self.rect = self.image.get_rect()
        self.rect.x = random.randint(TRACK_LEFT, TRACK_RIGHT - width)
        self.rect.y = random.randint(-100, -40)
        self.speed_y = speed

    def update(self):
        self.rect.y += self.speed_y
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


# ==========================================
# 子类继承：对接 resource 文件夹 (Subclass inheritance, get object picture)
# ==========================================
class Obstacle(ScrollObject):
    def __init__(self, speed):
        # 障碍物 obstacle
        super().__init__(90, 60, "9001Asign3/resource/barrier.png", speed, RED)

class Coin(ScrollObject):
    def __init__(self, speed):
        # 金币 Coin
        super().__init__(50, 50, "9001Asign3/resource/coin.png", speed, GOLD)

class ShieldItem(ScrollObject):
    def __init__(self, speed):
        # 护盾道具 Shield
        super().__init__(60, 60, "9001Asign3/resource/shiled.png", speed, GREEN)

class NitroItem(ScrollObject):
    def __init__(self, speed):
        # 氮气道具 nitro boost
        super().__init__(60, 60, "9001Asign3/resource/nitro.png", speed, CYAN)


# ==========================================
# 3. 玩家赛车类（集成特效控制）Class Player (Integrated special effects control)
# ==========================================
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # 赛车图片
        # Car photo
        try:
            raw_car = pygame.image.load("9001Asign3/resource/CAR.png").convert_alpha()
            self.image = pygame.transform.scale(raw_car, (90, 144))
        except pygame.error:
            self.image = pygame.Surface((90, 144))
            self.image.fill(BLUE)

        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 20
        self.speed_x = 8

        # 特效状态控制
        # Effect status control
        self.has_shield = False
        self.has_nitro = False
        
        # 记录过去几帧的坐标，用来画氮气霓虹拖尾
        # Effect of Nitrogen Neon Trailer
        self.history_positions = deque(maxlen=6)

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= self.speed_x
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += self.speed_x

        # 将赛车的活动范围死死锁在中间的赛道内
        # Limit the Scope of activities of Car
        if self.rect.left < TRACK_LEFT:
            self.rect.left = TRACK_LEFT
        if self.rect.right > TRACK_RIGHT:
            self.rect.right = TRACK_RIGHT

        # 处于氮气状态时记录轨迹
        # Record trajectory while in booost
        if self.has_nitro:
            self.history_positions.append(self.rect.topleft)
        else:
            if self.history_positions:
                self.history_positions.popleft()

    def draw_player_and_effects(self, screen):
        # 绘制氮气霓虹幻影拖尾 (Draw Ghost Trail)
        if self.has_nitro and len(self.history_positions) > 0:
            pos_list = list(self.history_positions)
            for i, pos in enumerate(pos_list):
                alpha = int((i + 1) / len(pos_list) * 120)
                trail_surf = self.image.copy()
                trail_surf.fill((0, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MULT)
                screen.blit(trail_surf, pos)

        # 绘制赛车本体
        # Draw Car object
        screen.blit(self.image, self.rect)

        # 绘制车尾蓝色动力火焰
        # Draw blue flames at the rear of the car when boost
        if self.has_nitro:
            jitter_w = random.randint(-2, 2)
            jitter_h = random.randint(-4, 4)
            # 使用自带的代码自画火焰，无需额外素材
            # Draw by built-in code, no need photo resource
            flame_surf = pygame.Surface((20 + jitter_w, 40 + jitter_h), pygame.SRCALPHA)
            pygame.draw.polygon(flame_surf, (0, 191, 255, 200), [(10, 40), (0, 0), (20, 0)])
            flame_x = self.rect.centerx - flame_surf.get_width() // 2
            flame_y = self.rect.bottom - 5
            screen.blit(flame_surf, (flame_x, flame_y))

        # 绘制科技感半透明护盾球
        # Draw energy shield
        if self.has_shield:
            # 让护盾直径永远等于赛车高度的 1.3 倍左右
            # Define shield diameter(car height *1.3)
            shield_size = int(self.rect.height * 1.3)
            
            shield_surf = pygame.Surface((shield_size, shield_size), pygame.SRCALPHA)
            
            # 计算半径
            # radius cal
            radius = shield_size // 2
            # 绘制内圈和外圈
            pygame.draw.circle(shield_surf, (0, 200, 255, 40), (radius, radius), radius - 2)
            pygame.draw.circle(shield_surf, (100, 240, 255, 200), (radius, radius), radius - 2, 2)
            
            # 依然精准对齐赛车的中心
            # find middle point of car
            shield_x = self.rect.centerx - radius
            shield_y = self.rect.centery - radius
            screen.blit(shield_surf, (shield_x, shield_y))


# ==========================================
# 4. 游戏引擎主逻辑类 (Game engine main logic class)
# ==========================================
class GameEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Flash Race")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 42)
        self.title_font = pygame.font.SysFont("Arial", 80, bold=True)
        
        self.state = "MENU" 
        self.is_running = True
        self.high_scores = []
        
        self.player_input_name = ""
        self.needs_name_entry = False

        self.hurt_flash_timer = 0

        self.menu_bg = None
        self.play_bg = None
        self.go_bg = None
        self.bg_scroll_y = 0  # 滚动坐标初始化 init Scroll coordinate

        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Cover 模式：宽度填满，等比缩放高度
        # Fills the width, scales the height proportionally. Make background suit
        def load_cover_bg(image_name):
            bg_path = os.path.join(current_dir, "resource", image_name)
            try:
                raw_bg = pygame.image.load(bg_path).convert()
                raw_w, raw_h = raw_bg.get_size()
                
                # 强制宽度等于屏幕总宽
                # Width of image = window width
                target_w = SCREEN_WIDTH 
                # 算比例，让高度等比放大
                # calculate ratio to zoom image
                ratio = target_w / raw_w
                target_h = int(raw_h * ratio)
                
                # 如果缩放后的高度比屏幕矮（这通常发生在原图太扁的情况），则反过来以高度为准
                # If the scaled image is shorter than the screen height, then revert to height adaptation.
                if target_h < SCREEN_HEIGHT:
                    target_h = SCREEN_HEIGHT
                    ratio = target_h / raw_h
                    target_w = int(raw_w * ratio)
                
                # 返回缩放后的精美大图
                # return image after scaling
                return pygame.transform.scale(raw_bg, (target_w, target_h))
            except pygame.error:
                return None

        # 加载你的大写封面背景 Load (LOAD_BG.png)
        self.menu_bg = load_cover_bg("LOAD_BG.png")

        # 加载游戏进行中的背景 Load (PLAY_BG)
        self.play_bg = load_cover_bg("PLAY_BG.jpg")

        # 加载游戏结束的背景 Load (GAMEOVER_BG)
        self.go_bg = load_cover_bg("OVER_BG.JPG")

        if self.play_bg:
            # 初始显示最底部：屏幕高度 - 图片放大后的高度
            # init Showing the bottom: Screen height - Image zoomed in height
            self.bg_scroll_y = SCREEN_HEIGHT - self.play_bg.get_height()

    def load_high_scores(self):
        self.high_scores = []
        if not os.path.exists(SCORE_FILE):
            return
        try:
            with open(SCORE_FILE, mode='r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) == 2:
                        self.high_scores.append((row[0], int(row[1])))
            self.high_scores.sort(key=lambda x: x[1], reverse=True)
            self.high_scores = self.high_scores[:5]
        except (IOError, ValueError):
            self.high_scores = []

    def save_high_score(self, name, score):
        self.high_scores.append((name, int(score)))
        self.high_scores.sort(key=lambda x: x[1], reverse=True)
        self.high_scores = self.high_scores[:5]
        try:
            with open(SCORE_FILE, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for row in self.high_scores:
                    writer.writerow(row)
        except IOError:
            pass

    def reset_game(self):
        self.score = 0
        self.coins_collected = 0
        self.base_speed = 5
        self.score_recorded = False
        self.player_input_name = ""
        self.needs_name_entry = False

        self.hp = 3
        self.has_nitro_inventory = False  
        self.nitro_timer = 0

        # 精灵分组管理
        # sprites group management
        self.all_sprites = pygame.sprite.Group()
        self.obstacles = pygame.sprite.Group()
        self.coins = pygame.sprite.Group()
        self.shields = pygame.sprite.Group()
        self.nitros = pygame.sprite.Group()

        self.player = Player()
        # 为了让玩家的动态特效不被基础图层覆盖，不把player放进常规渲染组
        # To prevent the player's dynamic effects from being covered by the base layer,
        # the player is not placed in the regular rendering group.
        # 我们在更新时手动更新玩家，在渲染时手动绘制玩家
        # We manually update the player during the update process and manually draw the player during the rendering process.
        self.SPAWN_EVENT = pygame.USEREVENT + 1
        pygame.time.set_timer(self.SPAWN_EVENT, 800)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
                return

            if self.state == "MENU":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    self.reset_game()
                    self.state = "PLAYING"

            elif self.state == "PLAYING":
                if event.type == self.SPAWN_EVENT:
                    current_drop_speed = self.base_speed * 2 if self.player.has_nitro else self.base_speed
                    
                    rand_val = random.random()
                    if rand_val < 0.65:       
                        obs = Obstacle(current_drop_speed)
                        self.obstacles.add(obs)
                        self.all_sprites.add(obs)
                    elif rand_val < 0.90:    
                        coin = Coin(current_drop_speed)
                        self.coins.add(coin)
                        self.all_sprites.add(coin)
                    elif rand_val < 0.95:    
                        shd = ShieldItem(current_drop_speed)
                        self.shields.add(shd)
                        self.all_sprites.add(shd)
                    else:                    
                        ntr = NitroItem(current_drop_speed)
                        self.nitros.add(ntr)
                        self.all_sprites.add(ntr)

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and self.has_nitro_inventory and not self.player.has_nitro:
                        self.has_nitro_inventory = False
                        self.player.has_nitro = True
                        self.player.speed_x = 12 # 冲刺加移速 increase movement speed when boost
                        self.nitro_timer = FPS * 2 

            elif self.state == "GAME_OVER":
                if event.type == pygame.KEYDOWN:
                    if self.needs_name_entry:
                        if event.key == pygame.K_RETURN:
                            final_name = self.player_input_name.strip()
                            if not final_name:
                                final_name = "Noname"
                            self.save_high_score(final_name, int(self.score))
                            self.needs_name_entry = False
                        elif event.key == pygame.K_BACKSPACE:
                            self.player_input_name = self.player_input_name[:-1]
                        else:
                            if len(self.player_input_name) < 10:
                                if event.unicode.isalnum() or event.unicode in " _-":
                                    self.player_input_name += event.unicode
                    else:
                        if event.key == pygame.K_RETURN:
                            self.state = "MENU"

    def update(self):
        if self.state == "PLAYING":
            # 玩家物理状态单独更新
            # Player physical status updated separately
            self.player.update()

            # ----------------------------------------------------
            # 让背景随着游戏当前速度动态向下滚动
            # Make the background scroll downwards dynamically with the current game speed.
            # ----------------------------------------------------
            if self.play_bg:
                # 滚动的速度直接与当前物体的下落速度（self.base_speed）挂钩
                # The scrolling speed is directly related to the current object's falling speed (self.base_speed)
                # 如果处于氮气爆发状态，速度直接翻倍！
                # If in nitro burst mode, the speed is doubled!
                current_scroll_speed = self.base_speed * 2 if self.player.has_nitro else self.base_speed
                
                # 坐标向下累加
                # Increment coordinates downwards
                self.bg_scroll_y += current_scroll_speed
                
                # 【闭环重置判定】如果第一张图的顶端已经移出了屏幕底端
                # [Closed-loop reset judgment] If the top of the first image has moved out of the bottom of the screen
                if self.bg_scroll_y >= SCREEN_HEIGHT:
                    # 瞬间重置回初始对齐底部的状态
                    # Instantly resets to the initial bottom-aligned state, achieving infinite loop.
                    self.bg_scroll_y = SCREEN_HEIGHT - self.play_bg.get_height()
            # ----------------------------------------------------

            # 氮气计时器逻辑
            #boost timer logic
            if self.player.has_nitro:
                self.nitro_timer -= 1
                
                # 确保即使是刚按下的瞬间，所有屏幕里的老物体也全线加速
                # Ensure that even the instant the button is pressed, all old objects on the screen accelerate across the board.
                for sprite in self.all_sprites:
                    if isinstance(sprite, ScrollObject):
                        sprite.speed_y = self.base_speed * 2

                if self.nitro_timer <= 0:
                    self.player.has_nitro = False
                    self.player.speed_x = 8
                    
                    # 氮气结束瞬间，让屏幕里遗留的所有物体速度降回正常状态
                    # The instant the nitro burst ends, all objects remaining on the screen return to normal speed.
                    for sprite in self.all_sprites:
                        if isinstance(sprite, ScrollObject):
                            sprite.speed_y = self.base_speed

            # 速度提升与加分速率
            # Speed ​​Boost and Bonus Rate
            self.base_speed = 8 + int((self.score ** 1.2) // 20)
            score_gain = (2 / FPS) if self.player.has_nitro else (1 / FPS)
            self.score += score_gain

            # 基础下落物更新
            # Basic Obstacle Item Update
            self.all_sprites.update()

            # 碰撞检测
            # Collision check
            # A. 金币 Coin
            coin_hits = pygame.sprite.spritecollide(self.player, self.coins, True)
            self.coins_collected += len(coin_hits)

            # B. 护盾 Shield
            if pygame.sprite.spritecollide(self.player, self.shields, True):
                self.player.has_shield = True

            # C. 氮气 Nitro
            if pygame.sprite.spritecollide(self.player, self.nitros, True):
                if not self.player.has_nitro:
                    self.has_nitro_inventory = True

            # D. 障碍物 Obstacle
            obs_hits = pygame.sprite.spritecollide(self.player, self.obstacles, True)
            for _ in obs_hits:
                if self.player.has_nitro:
                    continue 
                if self.player.has_shield:
                    self.player.has_shield = False 
                else:
                    self.hp -= 1
                    self.hurt_flash_timer = 10
                    if self.hp <= 0:
                        self.score += self.coins_collected * 5
                        self.state = "GAME_OVER"
                        self.load_high_scores()
                        if len(self.high_scores) < 5 or int(self.score) > self.high_scores[-1][1]:
                            self.needs_name_entry = True
                        break

    def render(self):
        self.screen.fill(BLACK)

        # ---- MENU 状态 ----
        if self.state == "MENU":
            if self.menu_bg:
                bg_y = -780
                self.screen.blit(self.menu_bg, (0, bg_y))
            title_text = self.title_font.render("FLASH RACE", True, CYAN)
            hint_text = self.font.render("Press ENTER to Start", True, GOLD)
            self.screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 80))
            self.screen.blit(hint_text, (SCREEN_WIDTH // 2 - hint_text.get_width() // 2, SCREEN_HEIGHT - 100))

        # ---- PLAYING 状态 ----
        elif self.state == "PLAYING":
            if self.play_bg:
                bg_height = self.play_bg.get_height()
                
                self.screen.blit(self.play_bg, (0, self.bg_scroll_y))
                
                self.screen.blit(self.play_bg, (0, self.bg_scroll_y - bg_height))
            else:
                self.screen.fill(BLACK)

            if self.player.has_nitro and pygame.time.get_ticks() % 200 < 100:
                # 创建一个透明图层叠加
                # Create a transparent layer overlay
                flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                flash_surf.fill((15, 15, 35))
                flash_surf.set_alpha(100) # transparency
                self.screen.blit(flash_surf, (0, 0))

            # 绘制障碍物和道具图片
            # Draw pictures of obstacles and props
            self.all_sprites.draw(self.screen)
            
            # 绘制玩家及所有叠加粒子状态特效
            # Draw player and all overlaid particle state effects
            self.player.draw_player_and_effects(self.screen)
            
            # 渲染 UI (直接画在 self.screen 上)
            # Render the UI (draw directly on self.screen)
            score_text = self.font.render(f"Score: {int(self.score)}", True, WHITE)
            coin_text = self.font.render(f"Coins: {self.coins_collected}", True, GOLD)
            self.screen.blit(score_text, (20, 20))
            coin_x = SCREEN_WIDTH - coin_text.get_width() - 20
            self.screen.blit(coin_text, (coin_x, 20))

            # 血条 HP location
            UI_BOTTOM_Y = SCREEN_HEIGHT - 60 
            
            hp_label = self.font.render("HP: ", True, WHITE)
            text_h = hp_label.get_height()
            self.screen.blit(hp_label, (20, UI_BOTTOM_Y))

            start_x = 90
            vertical_center = UI_BOTTOM_Y + (text_h - 20) // 2

            # 定义平行四边形的倾斜度 (偏移量)
            # Define the tilt (offset) of a parallelogram. Shape of HP
            offset = 10 
            width = 30
            height = 20
            
            for i in range(3):
                # 如果当前 index 小于当前血量，显示红色，否则显示深灰（扣血状态）
                # health depletion status
                color = RED if i < self.hp else (50, 50, 50)
                
                # 倾斜逻辑：x 坐标加上 offset
                # Tilt logic: x coordinate plus offset
                x_pos = start_x + i * 50 # 每个血槽间距拉大到 50 Spacing between each blood bar
                points = [
                    (x_pos, vertical_center + height),
                    (x_pos + offset, vertical_center),
                    (x_pos + offset + width, vertical_center),
                    (x_pos + width, vertical_center + height)
                ]
                
                # 绘制边框
                # Draw borders
                pygame.draw.polygon(self.screen, WHITE, points, 2)
                # 绘制填充
                # draw fill
                pygame.draw.polygon(self.screen, color, points)

            # 氮气提示
            # Nitrogen warning
            if self.has_nitro_inventory:
                nitro_text = self.font.render("[SPACE] BOOST", True, CYAN)
                self.screen.blit(nitro_text, (TRACK_RIGHT + 20, UI_BOTTOM_Y))
            elif self.player.has_nitro:
                nitro_text = self.font.render("BOOSTING!!!", True, CYAN)
                self.screen.blit(nitro_text, (TRACK_RIGHT + 20, UI_BOTTOM_Y))

        # ---- GAME_OVER 状态 ----
        elif self.state == "GAME_OVER":
            if self.go_bg:
                go_y = -580
                self.screen.blit(self.go_bg, (0, go_y))

            # 使用 y_offset 来统一管理行间距，随时调整一个数字即可改变整体紧凑度
            # Use y_offset to uniformly manage line spacing; adjusting a single number can change the overall compactness.
            current_y = 100 
            line_gap = 50   # 基础行间距 Basic line gap

            # 1. 大标题
            # 1. Main Title
            go_text = self.title_font.render("GAME OVER", True, RED)
            self.screen.blit(go_text, (SCREEN_WIDTH // 2 - go_text.get_width() // 2, current_y))
            current_y += 100 # 标题后留出大一点的空隙

            # 2. 得分与金币信息
            # 2. Score and Coin Information
            your_score_text = self.font.render(f"Final Score: {int(self.score)}", True, WHITE)
            end_coin_text = self.font.render(f"Coins Collected: {self.coins_collected}", True, GOLD)
            
            self.screen.blit(your_score_text, (SCREEN_WIDTH // 2 - your_score_text.get_width() // 2, current_y))
            current_y += line_gap
            self.screen.blit(end_coin_text, (SCREEN_WIDTH // 2 - end_coin_text.get_width() // 2, current_y))
            current_y += line_gap * 1.5 # 排行榜前多留出一点空间 Gap at the top of the leaderboard

            # 3. 排行榜或输入框逻辑
            # 3. Leaderboard or Input Box Logic
            if self.needs_name_entry:
                # 输入框状态下的排版
                # Layout in input box mode
                prompt_text = self.font.render("NEW HIGH SCORE! Enter your name:", True, GOLD)
                self.screen.blit(prompt_text, (SCREEN_WIDTH // 2 - prompt_text.get_width() // 2, current_y))
                current_y += 70
                
                display_name = self.player_input_name + ("_" if pygame.time.get_ticks() % 1000 < 500 else "")
                name_text = self.title_font.render(self.player_input_name or "_", True, BLUE)
                self.screen.blit(name_text, (SCREEN_WIDTH // 2 - name_text.get_width() // 2, current_y))
            else:
                # 正常排行榜状态
                # Normal leaderboard status
                leaderboard_title = self.font.render("--- TOP 5 LEADERBOARD ---", True, GOLD)
                self.screen.blit(leaderboard_title, (SCREEN_WIDTH // 2 - leaderboard_title.get_width() // 2, current_y))
                current_y += 60

                # 4. 排行榜列表 (使用固定的列对齐)
                # 4. Leaderboard List (using fixed column alignment)
                score_x = SCREEN_WIDTH // 2 + 190 
                for i, (name, score) in enumerate(self.high_scores):
                    # 名字左对齐
                    # Left-aligned names
                    name_line = f"{i+1}. {name}"
                    name_text = self.font.render(name_line, True, WHITE)
                    self.screen.blit(name_text, (SCREEN_WIDTH // 2 - 200, current_y))
                    
                    # 分数右对齐
                    # Right-aligned Score
                    score_text = self.font.render(str(score), True, WHITE)
                    self.screen.blit(score_text, (score_x - score_text.get_width(), current_y))
                    
                    current_y += 45 # 每一行名字之间留出 45px

            # 4. 底部提示
            # 4. Bottom Tip
            hint_text = self.font.render("Press ENTER to Main Menu", True, GRAY)
            self.screen.blit(hint_text, (SCREEN_WIDTH // 2 - hint_text.get_width() // 2, SCREEN_HEIGHT - 80))

        # 碰撞闪烁特效 (在所有物体之上)
        # Collision Flashing Effect (Above All Objects)
        if self.hurt_flash_timer > 0:
            self.hurt_flash_timer -= 1
            # 创建一个全屏覆盖的红色半透明 Surface
            # Create a full-screen, semi-transparent red Surface
            flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            flash_surf.fill(RED)
            # 设置透明度，根据剩余帧数逐渐变淡
            # Set the transparency to gradually fade based on the remaining frames.
            flash_surf.set_alpha(self.hurt_flash_timer * 15) 
            self.screen.blit(flash_surf, (0, 0))

        pygame.display.flip()

    def run(self):
        while self.is_running:
            self.clock.tick(FPS)
            self.handle_events()
            self.update()
            self.render()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = GameEngine()
    game.run()