# main.py
"""斗地主界面与动画美化模块（依赖Pygame和logic_card.py）"""
import pygame
import random
import time
import math
from logic_card import *
# ---------------------- release常量 ----------------------
RELEASE = True

def print(*values: object,
    sep: str | None = " ",
    end: str | None = "\n",
    file = None,
    flush = False,
) -> None:
    if RELEASE: return
    print(*values, sep=sep, end=end, file=file, flush=flush)

# ---------------------- 界面常量定义 ----------------------
# 窗口常量
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
FPS = 60
HALF_W = WINDOW_WIDTH // 2
HALF_H = WINDOW_HEIGHT // 2

# 颜色常量（美化升级：增加渐变色、柔和色）
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_BLUE = (0, 100, 255)       # 柔和蓝
COLOR_RED = (220, 0, 0)          # 深红（不刺眼）
COLOR_GRAY = (180, 180, 180)     # 浅灰
COLOR_LIGHT_GRAY = (240, 240, 240)  # 超浅灰
COLOR_GREEN = (0, 255, 0)        # 纯绿
COLOR_LIGHT_GREEN = (50, 255, 50)  # 亮绿（选中边框）
COLOR_YELLOW = (255, 220, 0)     # 金黄
COLOR_ORANGE = (255, 140, 0)     # 橙黄（提示文字）
CARD_BACK_DARK = (101, 67, 33)   # 卡牌背面深棕
CARD_BACK_LIGHT = (139, 69, 19)  # 卡牌背面浅棕
CARD_BORDER = (80, 80, 80)       # 卡牌边框灰

# 卡牌常量（美化升级：增加圆角、缩放比例）
BASE_CARD_WIDTH = 50
BASE_CARD_HEIGHT = 70
BASE_CARD_MARGIN = 8
CARD_SELECT_OFFSET = -15  # 选中卡牌向上偏移
CARD_SELECT_SCALE = 1.05  # 选中卡牌缩放比例
CARD_ROUND_RADIUS = 8     # 卡牌圆角半径
CARD_SHADOW_OFFSET = (2, 2)  # 卡牌阴影偏移

# 按钮常量（美化升级：圆角按钮、悬停色）
BUTTON_WIDTH = 120
BUTTON_HEIGHT = 50
BUTTON_MARGIN = 20
BUTTON_Y = WINDOW_HEIGHT - 100
BUTTON_ROUND = 10
BUTTON_GREEN = (0, 180, 0)
BUTTON_GREEN_HOVER = (0, 220, 0)
BUTTON_RED = (180, 0, 0)
BUTTON_RED_HOVER = (220, 0, 0)

# 动画常量
SHUFFLE_SPEED = 0.03    # 洗牌动画速度
DEAL_SPEED = 0.05       # 发牌动画速度
PLAY_CARD_SPEED = 0.02  # 出牌动画速度
TIP_FADE_SPEED = 5      # 提示文字淡入淡出速度
LANDLORD_CARD_SPEED = 0.03  # 底牌并入动画速度
SORT_CARD_SPEED = 0.02      # 手牌整理动画速度

# ---------------------- 工具函数（动画+绘制美化）----------------------
def draw_rounded_rect(surface, color, rect, radius):
    """绘制圆角矩形（美化卡牌、按钮）"""
    x, y, w, h = rect
    # 绘制中间矩形
    pygame.draw.rect(surface, color, (x + radius, y, w - 2 * radius, h))
    pygame.draw.rect(surface, color, (x, y + radius, w, h - 2 * radius))
    # 绘制四个圆角
    pygame.draw.circle(surface, color, (x + radius, y + radius), radius)
    pygame.draw.circle(surface, color, (x + w - radius, y + radius), radius)
    pygame.draw.circle(surface, color, (x + radius, y + h - radius), radius)
    pygame.draw.circle(surface, color, (x + w - radius, y + h - radius), radius)

def draw_text_with_shadow(surface, font, text, color, pos, shadow_color=COLOR_GRAY):
    """绘制带阴影的文字（美化显示）"""
    x, y = pos
    # 绘制阴影
    shadow_surf = font.render(text, True, shadow_color)
    surface.blit(shadow_surf, (x + 1, y + 1))
    # 绘制主文字
    main_surf = font.render(text, True, color)
    surface.blit(main_surf, (x, y))

def lerp(a, b, t):
    """线性插值（用于动画平滑过渡）"""
    return a + (b - a) * t

# ---------------------- 游戏主类（界面+动画+修正AI逻辑）----------------------
class LandlordGamePygame:
    def __init__(self):
        # 初始化Pygame
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("斗地主")
        self.clock = pygame.time.Clock()
        
        # 字体缓存（避免重复加载导致卡顿）
        self.font_cache = {}  # 格式: {(size, bold): font_object}
        
        # 加载支持中文的字体（美化：增加字体大小选项）
        self.font = self.load_chinese_font(24)
        self.small_font = self.load_chinese_font(16)
        self.large_font = self.load_chinese_font(32, bold=True)
        self.tip_font = self.load_chinese_font(20, bold=True)
        
        # 游戏状态变量
        self.deck = []  # 完整牌组
        self.player_cards = []  # 玩家手牌
        self.ai1_cards = []  # AI1手牌（下方农民）
        self.ai2_cards = []  # AI2手牌（上方农民）
        self.landlord_cards = []  # 地主底牌
        self.landlord = -1  # -1-未确定，0-玩家，1-AI1，2-AI2
        self.game_state = "shuffling"  # shuffling/dealing/calling/playing/over
        self.last_play = {
            "player": "", "cards": [], "type": "", 
            "priority": 0, "count": 0
        }
        
        # 动画相关变量（新增）
        self.tip_text = ""  # 顶部提示信息
        self.tip_alpha = 255  # 提示文字透明度（淡入淡出）
        self.deal_animation_progress = 0  # 发牌动画进度
        self.play_card_animation = None  # 出牌动画（起始/目标位置）
        self.shuffle_offset = []  # 洗牌动画偏移量
        
        # 卡牌选中相关变量
        self.selected_cards = []  # 记录玩家选中的卡牌
        self.player_card_rects = []  # 记录每张玩家手牌的矩形区域
        self.player_card_targets = []  # 玩家手牌目标位置（用于动画）
        # 动态卡牌尺寸（根据手牌数量自适应）
        self.current_card_width = BASE_CARD_WIDTH
        self.current_card_height = BASE_CARD_HEIGHT
        self.current_card_margin = BASE_CARD_MARGIN
        
        # 按钮定义（带圆角）
        self.buttons = {
            "call": pygame.Rect(HALF_W - 200, BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT),
            "giveup_call": pygame.Rect(HALF_W - 60, BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT),
            "play": pygame.Rect(HALF_W + 80, BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT),
            "giveup_play": pygame.Rect(HALF_W + 220, BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT)
        }
        
        # 加载卡牌图片（在初始化游戏之前）
        self.card_images = self.load_card_images()
        
        # 初始化游戏
        self.init_game()
    
    def load_chinese_font(self, font_size, bold=False):
        """加载多系统兼容的中文字体（带缓存，避免重复加载导致卡顿）"""
        # 检查缓存
        cache_key = (font_size, bold)
        if cache_key in self.font_cache:
            return self.font_cache[cache_key]
        
        # 优先使用当前目录下的fonts.ttf字体
        try:
            font = pygame.font.Font("fonts.ttf", font_size)
            self.font_cache[cache_key] = font
            return font
        except (pygame.error, FileNotFoundError):
            pass
        
        # 如果fonts.ttf不存在，尝试系统字体
        font_candidates = [
            "SimSun", "SimHei", "PingFang SC", "Heiti TC",
            "WenQuanYi Zen Hei", "WenQuanYi Micro Hei"
        ]
        
        for font_name in font_candidates:
            try:
                font = pygame.font.SysFont(font_name, font_size, bold=bold)
                self.font_cache[cache_key] = font
                return font
            except (pygame.error, ValueError):
                continue
        
        print("警告：未找到fonts.ttf字体文件和系统自带中文字体，中文可能显示异常！")
        font = pygame.font.Font(None, font_size)
        self.font_cache[cache_key] = font
        return font
    
    def load_card_images(self):
        """不再加载图片，使用纯文字绘制卡牌"""
        return {}

    def draw_card_text(self, x, y, width, height, card):
        """绘制卡牌文字（自适应字体大小，区分花色颜色）"""
        # 绘制白色背景
        draw_rounded_rect(self.screen, COLOR_WHITE, (x, y, width, height), CARD_ROUND_RADIUS)
        
        # 判断卡牌颜色（红色花色：♥、♦；黑色花色：♠、♣）
        if card in JOKERS:
            # 大小王特殊处理
            if card == '大王':
                card_color = COLOR_RED
                card_text = '大王'
            else:
                card_color = COLOR_BLACK
                card_text = '小王'
            
            # 计算自适应字体大小（大王、小王字较多）
            font_size = min(max(int(height * 0.25), 12), 24)
            card_font = self.load_chinese_font(font_size, bold=True)
            
            # 居中显示
            text_surf = card_font.render(card_text, True, card_color)
            text_x = x + (width - text_surf.get_width()) // 2
            text_y = y + (height - text_surf.get_height()) // 2
            self.screen.blit(text_surf, (text_x, text_y))
        else:
            # 普通卡牌
            card_color = COLOR_RED if (card[0] == '♥' or card[0] == '♦') else COLOR_BLACK
            
            # 提取花色和点数
            suit = card[0]
            rank = get_card_rank(card)
            
            # 计算自适应字体大小（根据卡牌尺寸）
            font_size = min(max(int(height * 0.3), 14), 28)
            card_font = self.load_chinese_font(font_size, bold=True)
            
            # 左上角显示花色
            suit_surf = card_font.render(suit, True, card_color)
            self.screen.blit(suit_surf, (x + 4, y + 4))
            
            # 右下角显示点数
            rank_surf = card_font.render(rank, True, card_color)
            rank_x = x + width - rank_surf.get_width() - 4
            rank_y = y + height - rank_surf.get_height() - 4
            self.screen.blit(rank_surf, (rank_x, rank_y))
            
            # 中间显示大号花色（装饰）
            center_font_size = min(max(int(height * 0.5), 24), 40)
            center_font = self.load_chinese_font(center_font_size, bold=True)
            center_surf = center_font.render(suit, True, card_color)
            center_surf.set_alpha(100)  # 半透明
            center_x = x + (width - center_surf.get_width()) // 2
            center_y = y + (height - center_surf.get_height()) // 2
            self.screen.blit(center_surf, (center_x, center_y))
        
        # 绘制卡牌边框
        pygame.draw.rect(self.screen, CARD_BORDER, (x, y, width, height), 1, border_radius=CARD_ROUND_RADIUS)

    def draw_card_back(self, x, y, width, height):
        """绘制卡牌背面（使用渐变颜色）"""
        # 绘制渐变背景
        draw_rounded_rect(self.screen, CARD_BACK_DARK, (x, y, width, height), CARD_ROUND_RADIUS)
        
        # 绘制内部装饰图案（交叉线）
        center_x = x + width // 2
        center_y = y + height // 2
        line_color = CARD_BACK_LIGHT
        pygame.draw.line(self.screen, line_color, (x + 4, y + 4), (x + width - 4, y + height - 4), 2)
        pygame.draw.line(self.screen, line_color, (x + width - 4, y + 4), (x + 4, y + height - 4), 2)
        
        # 绘制卡牌边框
        pygame.draw.rect(self.screen, CARD_BORDER, (x, y, width, height), 1, border_radius=CARD_ROUND_RADIUS)

    # ---------------------- 动画美化：洗牌动画 ----------------------
    def shuffle_deck(self):
        """自动洗牌+流畅洗牌动画（牌堆晃动+颜色渐变+旋转）"""
        self.deck = create_deck()
        self.game_state = "shuffling"
        self.tip_text = ""
        self.shuffle_offset = [(random.randint(-30, 30), random.randint(-30, 30)) for _ in range(50)]
        
        for i in range(60):
            self.screen.fill(COLOR_LIGHT_GRAY)
            # 绘制洗牌文字（带阴影+居中）
            shuffle_text_str = "正在自动洗牌..."
            text_x = HALF_W - self.large_font.size(shuffle_text_str)[0] // 2
            text_y = HALF_H - 100
            draw_text_with_shadow(self.screen, self.large_font, shuffle_text_str, COLOR_RED, (text_x, text_y))
            
            # 绘制晃动的牌堆（渐变颜色+随机旋转）
            for j in range(30):
                # 平滑偏移（随动画进度衰减）
                offset_x = self.shuffle_offset[j][0] * (1 - i * SHUFFLE_SPEED)
                offset_y = self.shuffle_offset[j][1] * (1 - i * SHUFFLE_SPEED)
                x = HALF_W + offset_x
                y = HALF_H + 50 + offset_y
                # 颜色渐变（从深棕到浅棕）
                card_color = (
                    lerp(CARD_BACK_DARK[0], CARD_BACK_LIGHT[0], j/30),
                    lerp(CARD_BACK_DARK[1], CARD_BACK_LIGHT[1], j/30),
                    lerp(CARD_BACK_DARK[2], CARD_BACK_LIGHT[2], j/30)
                )
                # 绘制卡牌（圆角+阴影）
                card_rect = (x, y, self.current_card_width, self.current_card_height)
                # 阴影
                shadow_rect = (x + CARD_SHADOW_OFFSET[0], y + CARD_SHADOW_OFFSET[1], 
                               self.current_card_width, self.current_card_height)
                draw_rounded_rect(self.screen, COLOR_GRAY, shadow_rect, CARD_ROUND_RADIUS)
                # 卡牌背景
                draw_rounded_rect(self.screen, card_color, card_rect, CARD_ROUND_RADIUS)
                # 卡牌边框
                pygame.draw.rect(self.screen, CARD_BORDER, card_rect, 1, border_radius=CARD_ROUND_RADIUS)
            
            pygame.display.flip()
            self.clock.tick(FPS)
            time.sleep(SHUFFLE_SPEED)
        
        random.shuffle(self.deck)

    # ---------------------- 动画美化：发牌动画 ----------------------
    def deal_cards(self):
        """发牌+流畅飞入动画（每张牌飞向目标位置）"""
        self.player_cards.clear()
        self.ai1_cards.clear()
        self.ai2_cards.clear()
        self.landlord_cards.clear()
        self.selected_cards.clear()
        self.tip_text = ""
        self.deal_animation_progress = 0
        
        self.screen.fill(COLOR_LIGHT_GRAY)
        deal_text_str = "正在发牌..."
        text_x = HALF_W - self.large_font.size(deal_text_str)[0] // 2
        text_y = HALF_H - 100
        draw_text_with_shadow(self.screen, self.large_font, deal_text_str, COLOR_BLUE, (text_x, text_y))
        pygame.display.flip()
        time.sleep(1)
        
        # 按斗地主规则发牌
        for i in range(54):
            if self.game_state != "dealing":
                return
            
            card = self.deck[i]
            if i < 17:
                self.ai1_cards.append(card)
            elif i < 34:
                self.ai2_cards.append(card)
            elif i < 51:
                self.player_cards.append(card)
            else:
                self.landlord_cards.append(card)
            
            # 发牌动画（每张牌平滑飞入）
            self.deal_animation_progress = i / 54
            self.calc_adaptive_card_size()
            self.draw_interface()
            pygame.display.flip()
            self.clock.tick(FPS)
            time.sleep(DEAL_SPEED)
        
        # 排序手牌（按RANK_PRIORITY升序）
        sort_key = lambda c: RANK_PRIORITY[get_card_rank(c)]
        # 手牌整理动画（玩家手牌）
        self.animate_card_sorting(self.player_cards, is_player=True)
        # AI手牌整理动画
        self.animate_card_sorting(self.ai1_cards, is_player=False)
        self.animate_card_sorting(self.ai2_cards, is_player=False)
        
        # 最终计算自适应尺寸
        self.calc_adaptive_card_size()
        self.game_state = "calling"
        self.draw_interface()
        pygame.display.flip()

    # ---------------------- 卡牌尺寸自适应（保留原有功能）----------------------
    def calc_adaptive_card_size(self):
        """动态计算自适应卡牌尺寸，确保手牌完整显示在屏幕内"""
        card_count = len(self.player_cards)
        if card_count == 0:
            self.current_card_width = BASE_CARD_WIDTH
            self.current_card_height = BASE_CARD_HEIGHT
            self.current_card_margin = BASE_CARD_MARGIN
            return
        
        # 1. 定义屏幕可用宽度（左右各留50px边距）
        available_screen_width = WINDOW_WIDTH - 100
        
        # 2. 计算当前手牌的总占用宽度（基础尺寸）
        total_base_width = (self.current_card_width * card_count) + (self.current_card_margin * (card_count - 1))
        
        # 3. 判断是否超出可用宽度，若超出则计算缩放比例
        if total_base_width <= available_screen_width:
            self.current_card_width = BASE_CARD_WIDTH
            self.current_card_height = BASE_CARD_HEIGHT
            self.current_card_margin = BASE_CARD_MARGIN
        else:
            scale_ratio = available_screen_width / total_base_width
            # 应用缩放（设置最小尺寸，保证可识别）
            self.current_card_width = max(int(BASE_CARD_WIDTH * scale_ratio), 30)
            self.current_card_height = max(int(BASE_CARD_HEIGHT * scale_ratio), 45)
            self.current_card_margin = max(int(BASE_CARD_MARGIN * scale_ratio), 4)
        
        # 4. 再次验证（极端情况，微调间距）
        final_total_width = (self.current_card_width * card_count) + (self.current_card_margin * (card_count - 1))
        if final_total_width > available_screen_width and card_count > 1:
            self.current_card_margin = max(int((available_screen_width - (self.current_card_width * card_count)) / (card_count - 1)), 2)

    def get_hand_start_x(self):
        """计算手牌起始绘制x坐标，实现居中对齐"""
        card_count = len(self.player_cards)
        if card_count == 0:
            return HALF_W
        
        total_card_width = (self.current_card_width * card_count) + (self.current_card_margin * (card_count - 1))
        start_x = HALF_W - (total_card_width // 2)
        return max(start_x, 50)

    # ---------------------- 动画美化：卡牌绘制（圆角+阴影+选中缩放）----------------------
    def draw_card(self, x, y, card, show_back=False, is_selected=False):
        """绘制单张卡牌（使用文字，区分花色颜色）"""
        # 选中状态：缩放+向上偏移
        scale = CARD_SELECT_SCALE if is_selected else 1.0
        draw_w = int(self.current_card_width * scale)
        draw_h = int(self.current_card_height * scale)
        draw_x = x - (draw_w - self.current_card_width) // 2  # 缩放后居中
        draw_y = y + CARD_SELECT_OFFSET if is_selected else y
        
        # 1. 绘制卡牌阴影
        shadow_x = draw_x + CARD_SHADOW_OFFSET[0]
        shadow_y = draw_y + CARD_SHADOW_OFFSET[1]
        shadow_rect = (shadow_x, shadow_y, draw_w, draw_h)
        draw_rounded_rect(self.screen, COLOR_GRAY, shadow_rect, CARD_ROUND_RADIUS)
        
        # 2. 绘制卡牌（使用文字）
        if show_back:
            # 卡牌背面
            self.draw_card_back(draw_x, draw_y, draw_w, draw_h)
        else:
            # 卡牌正面（使用文字绘制）
            self.draw_card_text(draw_x, draw_y, draw_w, draw_h, card)
        
        # 3. 绘制卡牌边框（选中状态亮绿，否则灰黑）
        border_color = COLOR_LIGHT_GREEN if is_selected else CARD_BORDER
        border_width = 2 if is_selected else 1
        pygame.draw.rect(self.screen, border_color, (draw_x, draw_y, draw_w, draw_h), 
                         border_width, border_radius=CARD_ROUND_RADIUS)
        
        # 返回卡牌实际绘制的矩形区域
        return pygame.Rect(draw_x, draw_y, draw_w, draw_h)

    # ---------------------- 动画美化：底牌并入动画 ----------------------
    def animate_landlord_cards_to_hand(self, target_player_id):
        """底牌并入地主手牌动画（底牌飞向目标位置）"""
        if not self.landlord_cards:
            return
        
        # 计算底牌当前位置
        landlord_start_x = HALF_W - (3 * (self.current_card_width + self.current_card_margin)) // 2
        landlord_start_y = 240
        
        # 计算目标位置（根据地主类型）
        if target_player_id == 0:  # 玩家
            target_x = self.get_hand_start_x()
            target_y = 600
        elif target_player_id == 1:  # AI1
            target_x = 50
            target_y = 490
        else:  # AI2
            target_x = 50
            target_y = 120
        
        # 动画帧数
        animation_frames = 30
        
        for frame in range(animation_frames + 1):
            progress = frame / animation_frames
            # 使用缓动函数让动画更平滑
            ease_progress = progress * progress * (3 - 2 * progress)
            
            # 清空屏幕并绘制完整界面（保持其他玩家的手牌）
            self.screen.fill(COLOR_LIGHT_GRAY)
            # 绘制顶部信息
            info_text_surf = self.get_top_info_text()
            info_x = HALF_W - info_text_surf.get_width() // 2
            self.screen.blit(info_text_surf, (info_x, 20))
            # 绘制中间出牌区域
            self.draw_play_area()
            # 绘制地主底牌区域（但不显示底牌，因为它们正在飞向目标）
            landlord_title_text = "地主底牌"
            landlord_title = self.font.render(landlord_title_text, True, COLOR_RED)
            draw_text_with_shadow(self.screen, self.font, landlord_title_text, COLOR_RED,
                                  (HALF_W - 50, 200))
            # 根据目标玩家绘制其他手牌
            if target_player_id == 0:  # 玩家成为地主，绘制两个AI的手牌
                self.draw_ai_hand(2, 50, 80, 150, 120)  # AI2
                self.draw_ai_hand(1, 50, 450, 150, 490)  # AI1
            elif target_player_id == 1:  # AI1成为地主，绘制AI2和玩家的手牌
                self.draw_ai_hand(2, 50, 80, 150, 120)  # AI2
                self.draw_player_hand()
            else:  # AI2成为地主，绘制AI1和玩家的手牌
                self.draw_ai_hand(1, 50, 450, 150, 490)  # AI1
                self.draw_player_hand()
            # 绘制操作按钮
            if self.game_state == "calling":
                self.draw_operation_buttons()
            
            # 绘制每张底牌从起始位置飞向目标位置
            for i, card in enumerate(self.landlord_cards):
                # 计算当前卡牌的起始x坐标
                start_x = landlord_start_x + i * (self.current_card_width + self.current_card_margin)
                
                # 计算当前帧的位置（插值）
                current_x = int(lerp(start_x, target_x + i * (self.current_card_margin // 2), ease_progress))
                current_y = int(lerp(landlord_start_y, target_y, ease_progress))
                
                # 添加一点旋转效果（通过左右晃动）
                rotation_offset = int(math.sin(progress * math.pi) * 5)
                current_x += rotation_offset
                
                # 绘制卡牌（带缩放效果，靠近目标时变小）
                scale = 1.0 - (ease_progress * 0.2)
                draw_w = int(self.current_card_width * scale)
                draw_h = int(self.current_card_height * scale)
                draw_x = current_x - (draw_w - self.current_card_width) // 2
                draw_y = current_y - (draw_h - self.current_card_height) // 2
                
                self.draw_card_sized(draw_x, draw_y, draw_w, draw_h, card)
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        # 动画结束，底牌已并入手牌
        self.landlord_cards.clear()
    
    def draw_card_sized(self, x, y, width, height, card):
        """绘制指定尺寸的卡牌（使用文字，用于动画）"""
        # 绘制阴影
        shadow_x = x + CARD_SHADOW_OFFSET[0]
        shadow_y = y + CARD_SHADOW_OFFSET[1]
        shadow_rect = (shadow_x, shadow_y, width, height)
        draw_rounded_rect(self.screen, COLOR_GRAY, shadow_rect, CARD_ROUND_RADIUS)
        
        # 绘制卡牌（使用文字）
        self.draw_card_text(x, y, width, height, card)
        
        # 绘制卡牌边框
        pygame.draw.rect(self.screen, CARD_BORDER, (x, y, width, height), 1, border_radius=CARD_ROUND_RADIUS)

    # ---------------------- 动画美化：手牌整理动画 ----------------------
    def animate_card_sorting(self, cards, is_player=True):
        """手牌整理动画（从乱序平滑移动到排序状态）"""
        if not cards:
            return
        
        # 保存排序前的状态
        old_positions = []
        if is_player:
            start_x = self.get_hand_start_x()
            for i, card in enumerate(cards):
                old_positions.append({
                    'card': card,
                    'x': start_x + i * (self.current_card_width + self.current_card_margin),
                    'y': 600
                })
        else:
            # AI手牌位置
            target_y = 490 if len(cards) == len(self.ai1_cards) else 120
            for i, card in enumerate(cards):
                old_positions.append({
                    'card': card,
                    'x': 50 + i * 45,
                    'y': target_y
                })
        
        # 排序手牌
        sorted_key = lambda c: RANK_PRIORITY[get_card_rank(c)]
        sorted_cards = sorted(cards, key=sorted_key)
        
        # 计算排序后的目标位置
        if is_player:
            # 重新计算自适应尺寸（可能因排序而改变）
            self.calc_adaptive_card_size()
            new_start_x = self.get_hand_start_x()
            new_y = 600
        else:
            new_start_x = 50
            new_y = 490 if len(cards) == len(self.ai1_cards) else 120
        
        # 建立排序前后的对应关系
        new_positions = []
        for i, card in enumerate(sorted_cards):
            if is_player:
                target_x = new_start_x + i * (self.current_card_width + self.current_card_margin)
            else:
                target_x = new_start_x + i * 45
            
            # 找到该卡牌在旧位置中的索引
            old_index = next(idx for idx, old_pos in enumerate(old_positions) if old_pos['card'] == card)
            old_pos = old_positions[old_index]
            
            new_positions.append({
                'card': card,
                'old_x': old_pos['x'],
                'old_y': old_pos['y'],
                'new_x': target_x,
                'new_y': new_y
            })
        
        # 动画帧数
        animation_frames = 40
        
        for frame in range(animation_frames + 1):
            progress = frame / animation_frames
            # 使用缓动函数
            ease_progress = 1 - (1 - progress) * (1 - progress)
            
            # 清空屏幕并绘制完整界面
            self.screen.fill(COLOR_LIGHT_GRAY)
            # 绘制顶部信息
            info_text_surf = self.get_top_info_text()
            info_x = HALF_W - info_text_surf.get_width() // 2
            self.screen.blit(info_text_surf, (info_x, 20))
            # 绘制地主底牌
            self.draw_landlord_cards()
            # 绘制中间出牌区域
            self.draw_play_area()
            # 绘制AI手牌（根据 is_player 决定是否绘制）
            if is_player:
                # 正在整理玩家手牌，绘制两个AI的手牌
                self.draw_ai_hand(2, 50, 80, 150, 120)  # AI2
                self.draw_ai_hand(1, 50, 450, 150, 490)  # AI1
            else:
                # 正在整理AI手牌，绘制另一个AI的手牌和玩家手牌
                is_ai1 = (len(cards) == len(self.ai1_cards))
                if is_ai1:
                    # 整理AI1，绘制AI2和玩家
                    self.draw_ai_hand(2, 50, 80, 150, 120)  # AI2
                    self.draw_player_hand()
                else:
                    # 整理AI2，绘制AI1和玩家
                    self.draw_ai_hand(1, 50, 450, 150, 490)  # AI1
                    self.draw_player_hand()
            # 绘制操作按钮
            if self.game_state == "calling":
                self.draw_operation_buttons()
            
            # 绘制每张卡牌在移动过程中的位置（覆盖在对应位置上）
            for pos_info in new_positions:
                current_x = int(lerp(pos_info['old_x'], pos_info['new_x'], ease_progress))
                current_y = int(lerp(pos_info['old_y'], pos_info['new_y'], ease_progress))
                
                # 添加一点旋转效果
                rotation_offset = int(math.sin(progress * math.pi * 2) * 3)
                current_x += rotation_offset
                
                self.draw_card(current_x, current_y, pos_info['card'])
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        # 动画结束，实际更新手牌顺序
        if is_player:
            self.player_cards.clear()
            self.player_cards.extend(sorted_cards)
        else:
            if len(cards) == len(self.ai1_cards):
                self.ai1_cards.clear()
                self.ai1_cards.extend(sorted_cards)
            else:
                self.ai2_cards.clear()
                self.ai2_cards.extend(sorted_cards)

    # ---------------------- 卡牌选中检测（保留原有功能）----------------------
    def check_card_click(self, mouse_pos):
        """检测鼠标是否点击了玩家手牌，切换选中状态"""
        if self.game_state != "playing" or self.last_play["player"] == "玩家":
            return
        
        for card_rect, card in zip(self.player_card_rects, self.player_cards):
            if card_rect.collidepoint(mouse_pos):
                if card in self.selected_cards:
                    self.selected_cards.remove(card)
                else:
                    self.selected_cards.append(card)
                self.tip_text = ""
                self.tip_alpha = 255
                break

    # ---------------------- 动画美化：界面绘制（保留原有功能）----------------------
    def draw_interface(self):
        """绘制完整游戏界面（美化：浅灰背景+圆角元素+文字阴影+提示淡入淡出）"""
        # 填充背景（柔和浅灰）
        self.screen.fill(COLOR_LIGHT_GRAY)
        
        # 绘制顶部信息栏（带阴影）
        info_text_surf = self.get_top_info_text()
        info_x = HALF_W - info_text_surf.get_width() // 2
        self.screen.blit(info_text_surf, (info_x, 20))
        
        # 绘制顶部提示文字（淡入淡出+橙色+阴影）
        if self.tip_text:
            self.tip_alpha = max(0, min(255, self.tip_alpha - TIP_FADE_SPEED))
            tip_surface = self.tip_font.render(self.tip_text, True, COLOR_ORANGE)
            tip_surface.set_alpha(self.tip_alpha)
            tip_x = HALF_W - tip_surface.get_width() // 2
            draw_text_with_shadow(self.screen, self.tip_font, self.tip_text, COLOR_ORANGE, (tip_x, 60))
        
        # 1. 绘制上方AI2手牌（农民2）
        self.draw_ai_hand(2, 50, 80, 150, 120)
        
        # 2. 绘制地主底牌（修正：调用正确方法）
        self.draw_landlord_cards()
        
        # 3. 绘制中间出牌区域（圆角矩形+阴影）
        self.draw_play_area()
        
        # 4. 绘制下方AI1手牌（农民1）
        self.draw_ai_hand(1, 50, 450, 150, 490)
        
        # 5. 绘制玩家手牌（居中+自适应+选中效果）
        self.draw_player_hand()
        
        # 6. 绘制操作按钮（圆角+悬停色+阴影）
        self.draw_operation_buttons()

    def get_top_info_text(self):
        """获取顶部游戏状态信息文本（带阴影）"""
        if self.game_state == "shuffling":
            return self.large_font.render("正在自动洗牌...", True, COLOR_RED)
        elif self.game_state == "dealing":
            return self.large_font.render("正在发牌...", True, COLOR_BLUE)
        elif self.game_state == "calling":
            return self.large_font.render("请选择：叫地主 / 不叫", True, COLOR_BLACK)
        elif self.game_state == "playing":
            landlord_text = "你" if self.landlord == 0 else f"AI{self.landlord}"
            current_turn = "玩家" if self.last_play["player"] != "玩家" else "AI"
            return self.large_font.render(f"{landlord_text}是地主，当前回合：{current_turn}", True, COLOR_YELLOW)
        else:
            return self.large_font.render("游戏结束，即将重新开始...", True, COLOR_GREEN)

    def draw_ai_hand(self, ai_id, title_x, title_y, card_start_x, card_y):
        """绘制AI手牌（背面显示+美化）"""
        ai_cards = self.ai1_cards if ai_id == 1 else self.ai2_cards
        # 修正：先定义原始文本字符串
        ai_title_text = f"AI农民{ai_id}（{'下方' if ai_id == 1 else '上方'}）"
        # 渲染Surface（保留原逻辑）
        ai_title = self.font.render(ai_title_text, True, COLOR_BLACK)
        # 传递原始文本字符串，删除.get_text()
        draw_text_with_shadow(self.screen, self.font, ai_title_text, COLOR_BLACK, (title_x, title_y))
        
        # 绘制AI手牌（固定小尺寸，避免超出屏幕）
        ai_card_width = 40
        ai_card_margin = 5
        current_x = card_start_x
        
        for _ in ai_cards:
            self.draw_card(current_x, card_y, "", show_back=True)
            current_x += ai_card_width + ai_card_margin
            if current_x + ai_card_width > WINDOW_WIDTH - 50:
                break

    def draw_landlord_cards(self):
        """绘制地主底牌（美化+圆角）"""
        # 修正：定义原始文本字符串
        landlord_title_text = "地主底牌"
        landlord_title = self.font.render(landlord_title_text, True, COLOR_RED)
        draw_text_with_shadow(self.screen, self.font, landlord_title_text, COLOR_RED, 
                              (HALF_W - 50, 200))
        landlord_x = HALF_W - (3 * (self.current_card_width + self.current_card_margin)) // 2
        
        if self.landlord == -1:
            # 未确定地主，显示背面
            for _ in range(3):
                self.draw_card(landlord_x, 240, "", show_back=True)
                landlord_x += self.current_card_width + self.current_card_margin
        elif self.landlord == 0:
            # 玩家是地主，提示底牌已加入手牌
            # 修正：定义原始文本字符串
            owned_text_text = "已归属玩家（已加入你的手牌）"
            owned_text = self.font.render(owned_text_text, True, COLOR_GREEN)
            text_x = HALF_W - self.font.size(owned_text_text)[0] // 2
            draw_text_with_shadow(self.screen, self.font, owned_text_text, COLOR_GREEN, 
                                  (text_x, 240))
        else:
            # AI是地主，显示底牌
            for card in self.landlord_cards:
                self.draw_card(landlord_x, 240, card)
                landlord_x += self.current_card_width + self.current_card_margin

    def draw_play_area(self):
        """绘制中间出牌区域（美化：圆角矩形+阴影）"""
        play_area = pygame.Rect(200, 300, 800, 100)
        # 绘制阴影
        shadow_area = pygame.Rect(202, 302, 800, 100)
        draw_rounded_rect(self.screen, COLOR_GRAY, shadow_area, 10)
        # 绘制主区域
        draw_rounded_rect(self.screen, COLOR_WHITE, play_area, 10)
        # 绘制边框
        pygame.draw.rect(self.screen, COLOR_BLACK, play_area, 2, border_radius=10)
        
        # 绘制上一轮出牌的卡牌（不是文字）
        if self.last_play["cards"] and self.last_play["type"] != CARD_TYPE_PASS:
            # 计算卡牌居中显示的起始位置
            card_count = len(self.last_play["cards"])
            # 使用当前卡牌宽度和间距
            total_width = card_count * self.current_card_width + (card_count - 1) * 10
            start_x = HALF_W - total_width // 2
            card_y = 325  # 垂直居中
            
            # 绘制每张卡牌
            for i, card in enumerate(self.last_play["cards"]):
                card_x = start_x + i * (self.current_card_width + 10)
                # 使用缩小的卡牌尺寸（0.8倍）
                scale = 0.8
                draw_w = int(self.current_card_width * scale)
                draw_h = int(self.current_card_height * scale)
                draw_x = card_x + (self.current_card_width - draw_w) // 2
                draw_y = card_y + (self.current_card_height - draw_h) // 2
                
                # 绘制卡牌
                self.draw_card_sized(draw_x, draw_y, draw_w, draw_h, card)
            
            # 在卡牌下方显示玩家和牌型信息
            player_text = f"{self.last_play['player']} 出牌："
            type_text = f" {self.last_play['type']}"
            draw_text_with_shadow(self.screen, self.font, player_text + type_text, COLOR_BLACK, (250, 380))
        elif self.last_play["type"] == CARD_TYPE_PASS:
            # 过牌时显示文字
            pass_text = f"{self.last_play['player']} 过牌"
            draw_text_with_shadow(self.screen, self.font, pass_text, COLOR_RED, (HALF_W - self.font.size(pass_text)[0] // 2, 340))
        else:
            # 无出牌
            play_content = "等待出牌..."
            draw_text_with_shadow(self.screen, self.font, play_content, COLOR_GRAY, (HALF_W - self.font.size(play_content)[0] // 2, 340))

    def draw_player_hand(self):
        """绘制玩家手牌（美化+选中动画）"""
        self.player_card_rects.clear()
        # 修正：定义原始文本字符串
        player_title_text = "你的手牌（点击选中，绿色边框+抬高）"
        player_title = self.font.render(player_title_text, True, COLOR_BLUE)
        text_x = HALF_W - self.font.size(player_title_text)[0] // 2
        draw_text_with_shadow(self.screen, self.font, player_title_text, COLOR_BLUE, 
                              (text_x, 550))
        
        # 计算手牌起始坐标
        player_start_x = self.get_hand_start_x()
        player_y = 600
        
        # 绘制每张手牌并记录矩形区域
        for card in self.player_cards:
            is_selected = card in self.selected_cards
            card_rect = self.draw_card(player_start_x, player_y, card, is_selected=is_selected)
            self.player_card_rects.append(card_rect)
            player_start_x += self.current_card_width + self.current_card_margin

    def draw_operation_buttons(self):
        """绘制操作按钮（美化：圆角+悬停色+阴影）"""
        mouse_pos = pygame.mouse.get_pos()
        
        if self.game_state == "calling":
            # 叫地主按钮（绿）
            call_hover = self.buttons["call"].collidepoint(mouse_pos)
            call_color = BUTTON_GREEN_HOVER if call_hover else BUTTON_GREEN
            # 阴影
            draw_rounded_rect(self.screen, COLOR_GRAY, (self.buttons["call"].x+2, self.buttons["call"].y+2, 
                                                        BUTTON_WIDTH, BUTTON_HEIGHT), BUTTON_ROUND)
            # 按钮背景
            draw_rounded_rect(self.screen, call_color, self.buttons["call"], BUTTON_ROUND)
            # 按钮文字
            draw_text_with_shadow(self.screen, self.font, "叫地主", COLOR_WHITE, 
                                  (self.buttons["call"].x + 20, self.buttons["call"].y + 10))
            
            # 不叫按钮（红）
            giveup_call_hover = self.buttons["giveup_call"].collidepoint(mouse_pos)
            giveup_call_color = BUTTON_RED_HOVER if giveup_call_hover else BUTTON_RED
            draw_rounded_rect(self.screen, COLOR_GRAY, (self.buttons["giveup_call"].x+2, self.buttons["giveup_call"].y+2, 
                                                        BUTTON_WIDTH, BUTTON_HEIGHT), BUTTON_ROUND)
            draw_rounded_rect(self.screen, giveup_call_color, self.buttons["giveup_call"], BUTTON_ROUND)
            draw_text_with_shadow(self.screen, self.font, "不叫", COLOR_WHITE, 
                                  (self.buttons["giveup_call"].x + 30, self.buttons["giveup_call"].y + 10))
        
        if self.game_state == "playing" and self.last_play["player"] != "玩家":
            # 出牌按钮（绿）
            play_hover = self.buttons["play"].collidepoint(mouse_pos)
            play_color = BUTTON_GREEN_HOVER if play_hover else BUTTON_GREEN
            draw_rounded_rect(self.screen, COLOR_GRAY, (self.buttons["play"].x+2, self.buttons["play"].y+2, 
                                                        BUTTON_WIDTH, BUTTON_HEIGHT), BUTTON_ROUND)
            draw_rounded_rect(self.screen, play_color, self.buttons["play"], BUTTON_ROUND)
            draw_text_with_shadow(self.screen, self.font, "出牌", COLOR_WHITE, 
                                  (self.buttons["play"].x + 40, self.buttons["play"].y + 10))
            
            # 过牌按钮（红）
            giveup_play_hover = self.buttons["giveup_play"].collidepoint(mouse_pos)
            giveup_play_color = BUTTON_RED_HOVER if giveup_play_hover else BUTTON_RED
            draw_rounded_rect(self.screen, COLOR_GRAY, (self.buttons["giveup_play"].x+2, self.buttons["giveup_play"].y+2, 
                                                        BUTTON_WIDTH, BUTTON_HEIGHT), BUTTON_ROUND)
            draw_rounded_rect(self.screen, giveup_play_color, self.buttons["giveup_play"], BUTTON_ROUND)
            draw_text_with_shadow(self.screen, self.font, "过", COLOR_WHITE, 
                                  (self.buttons["giveup_play"].x + 50, self.buttons["giveup_play"].y + 10))

    # ---------------------- 核心修正：AI出牌逻辑（解决炸弹压制+主动过牌）----------------------
    def get_ai_legal_plays(self, ai_cards):
        """获取AI的所有合法牌型（补充王炸提取，完善合法牌型）"""
        legal_plays = []
        card_count = len(ai_cards)
        if card_count == 0:
            return legal_plays
        
        # 先按点数排序AI手牌，方便提取连续牌型
        sorted_ai_cards = sorted(ai_cards, key=lambda c: RANK_PRIORITY[get_card_rank(c)])
        ai_card_set = set(sorted_ai_cards)
        
        # 1. 提取王炸（最高优先级）
        if '小王' in ai_card_set and '大王' in ai_card_set:
            joker_bomb = ['小王', '大王']
            legal_plays.append(joker_bomb)
        
        # 2. 提取所有单张
        for i in range(card_count):
            single_card = [sorted_ai_cards[i]]
            if judge_card_type(single_card)[0] != CARD_TYPE_INVALID:
                legal_plays.append(single_card)
        
        # 3. 提取所有对子
        for i in range(card_count - 1):
            card1_rank = get_card_rank(sorted_ai_cards[i])
            card2_rank = get_card_rank(sorted_ai_cards[i+1])
            if card1_rank == card2_rank:
                pair_cards = [sorted_ai_cards[i], sorted_ai_cards[i+1]]
                legal_plays.append(pair_cards)
        
        # 4. 提取所有三张
        for i in range(card_count - 2):
            card1_rank = get_card_rank(sorted_ai_cards[i])
            card2_rank = get_card_rank(sorted_ai_cards[i+1])
            card3_rank = get_card_rank(sorted_ai_cards[i+2])
            if card1_rank == card2_rank == card3_rank:
                triple_cards = [sorted_ai_cards[i], sorted_ai_cards[i+1], sorted_ai_cards[i+2]]
                legal_plays.append(triple_cards)
        
        # 5. 提取所有普通炸弹
        for i in range(card_count - 3):
            ranks = [get_card_rank(sorted_ai_cards[i+j]) for j in range(4)]
            if len(set(ranks)) == 1:
                bomb_cards = sorted_ai_cards[i:i+4]
                legal_plays.append(bomb_cards)
        
        # 6. 提取复杂牌型（顺子、连对、飞机等）
        min_seq_single_len = MIN_SEQUENCE_SINGLE_COUNT
        for start in range(card_count - min_seq_single_len + 1):
            for end in range(start + min_seq_single_len - 1, card_count):
                sequence_cards = sorted_ai_cards[start:end+1]
                if judge_card_type(sequence_cards)[0] == CARD_TYPE_SEQUENCE_SINGLE:
                    legal_plays.append(sequence_cards)
        
        # 去重并返回（按优先级降序排序，方便AI优先选大牌）
        unique_plays = []
        seen = set()
        for play in legal_plays:
            play_tuple = tuple(play)
            if play_tuple not in seen:
                seen.add(play_tuple)
                unique_plays.append(play)
        
        # 按牌型优先级降序排序（王炸>炸弹>普通牌型）
        def play_priority_key(play):
            p_type, p_prio, _ = judge_card_type(play)
            if p_type == CARD_TYPE_JOKER_BOMB:
                return 1000 + p_prio
            elif p_type == CARD_TYPE_BOMB:
                return 100 + p_prio
            else:
                return p_prio
        
        unique_plays.sort(key=play_priority_key, reverse=True)
        return unique_plays

    def show_ai_notice(self, notice_text):
        """显示AI操作提示（美化+居中+阴影）"""
        self.screen.fill(COLOR_LIGHT_GRAY)
        text_x = HALF_W - self.large_font.size(notice_text)[0] // 2
        text_y = HALF_H
        draw_text_with_shadow(self.screen, self.large_font, notice_text, COLOR_RED, (text_x, text_y))
        pygame.display.flip()
        time.sleep(2)

    def ai_call_landlord(self):
        """AI自动叫地主逻辑"""
        self.screen.fill(COLOR_LIGHT_GRAY)
        self.show_ai_notice("等待AI叫地主...")
        
        # 定义AI叫地主的判断条件
        def should_call(cards):
            rank_count = count_rank_occurrences(cards)
            if '小王' in rank_count and '大王' in rank_count:
                return True
            if any(count == 4 for count in rank_count.values()):
                return True
            if rank_count.get('2', 0) >= 2:
                return True
            if rank_count.get('小王', 0) + rank_count.get('大王', 0) >= 1:
                return True
            return False
        
        # AI1叫地主判断
        if should_call(self.ai1_cards):
            self.landlord = 1
            # 底牌并入动画
            self.animate_landlord_cards_to_hand(1)
            self.ai1_cards.extend(self.landlord_cards)
            self.landlord_cards.clear()
            # 手牌整理动画
            self.animate_card_sorting(self.ai1_cards, is_player=False)
            
            self.ai1_cards.sort(key=lambda c: RANK_PRIORITY[get_card_rank(c)])
            self.show_ai_notice(f"AI农民1选择叫地主，成为地主！")
            self.game_state = "playing"
            self.ai_play_card(1)
            return
        
        # AI2叫地主判断
        if should_call(self.ai2_cards):
            self.landlord = 2
            # 底牌并入动画
            self.animate_landlord_cards_to_hand(2)
            self.ai2_cards.extend(self.landlord_cards)
            self.landlord_cards.clear()
            # 手牌整理动画
            self.animate_card_sorting(self.ai2_cards, is_player=False)
            
            self.ai2_cards.sort(key=lambda c: RANK_PRIORITY[get_card_rank(c)])
            self.show_ai_notice(f"AI农民2选择叫地主，成为地主！")
            self.game_state = "playing"
            self.ai_play_card(2)
            return
        
        # 所有玩家都不叫，重新洗牌
        self.show_ai_notice("所有玩家都不叫地主，重新开始！")
        self.reset_game()

    def ai_play_card(self, ai_id):
        """AI自动出牌逻辑（核心修正：炸弹压制+主动过牌）"""
        self.game_state = "playing"
        self.show_ai_notice(f"AI{ai_id}正在出牌...")
        
        # 选择AI手牌
        ai_cards = self.ai1_cards if ai_id == 1 else self.ai2_cards
        if not ai_cards:
            self.check_win()
            return
        
        # 1. 获取AI所有合法牌型（已按优先级降序排序）
        legal_plays = self.get_ai_legal_plays(ai_cards)
        if not legal_plays:
            # 无合法牌，强制过牌
            self.last_play = {
                "player": f"AI{ai_id}", "cards": ["过牌"], 
                "type": CARD_TYPE_PASS, "priority": 0, "count": 0
            }
            self.draw_interface()
            pygame.display.flip()
            time.sleep(1)
            return
        
        # 2. 筛选能压制上一轮的牌型（核心：严格遵循压制规则）
        able_to_suppress = []
        for candidate in legal_plays:
            is_able, _ = is_card_able_to_play(candidate, self.last_play)
            if is_able:
                able_to_suppress.append(candidate)
        
        # 3. 出牌决策（优先级：能压制的牌 > 过牌（无压制牌时） > 首轮小牌）
        play_cards = []
        last_has_valid_card = bool(self.last_play["cards"]) and self.last_play["type"] != CARD_TYPE_PASS
        
        if able_to_suppress:
            # 有压制牌，优先选最小的压制牌（保留大牌）
            # 按优先级升序排序，选第一个（最小压制牌）
            able_to_suppress.sort(key=lambda p: get_max_rank_priority(p))
            play_cards = able_to_suppress[0]
        elif last_has_valid_card:
            # 有合法牌但无压制牌，主动过牌（符合斗地主规则）
            self.last_play = {
                "player": f"AI{ai_id}", "cards": ["过牌"], 
                "type": CARD_TYPE_PASS, "priority": 0, "count": 0
            }
            self.draw_interface()
            pygame.display.flip()
            time.sleep(1)
            return
        else:
            # 首轮出牌，选最小的合法牌（避免盲目出大牌）
            legal_plays.sort(key=lambda p: get_max_rank_priority(p))
            play_cards = legal_plays[0]
        
        # 4. 从AI手牌中移除已出的牌
        for card in play_cards:
            if card in ai_cards:
                ai_cards.remove(card)
        
        # 5. 更新上一轮出牌信息
        card_type, card_priority, card_count = judge_card_type(play_cards)
        self.last_play = {
            "player": f"AI{ai_id}", "cards": play_cards,
            "type": card_type, "priority": card_priority, "count": card_count
        }
        
        # 6. 刷新界面并延时
        self.calc_adaptive_card_size()
        self.draw_interface()
        pygame.display.flip()
        time.sleep(1)
        
        # 7. 检查获胜
        if self.check_win():
            return
        
        # 8. 切换到玩家回合
        self.game_state = "playing"
        self.draw_interface()
        pygame.display.flip()

    # ---------------------- 玩家操作（保留原有功能）----------------------
    def player_call_landlord(self):
        """玩家叫地主"""
        self.landlord = 0
        # 底牌并入动画
        self.animate_landlord_cards_to_hand(0)
        # 底牌并入手牌
        self.player_cards.extend(self.landlord_cards)
        self.landlord_cards.clear()
        # 手牌整理动画
        self.animate_card_sorting(self.player_cards, is_player=True)
        
        self.calc_adaptive_card_size()
        self.game_state = "playing"
        self.last_play = {
            "player": "AI", "cards": [], "type": "", 
            "priority": 0, "count": 0
        }
        self.draw_interface()
        pygame.display.flip()
        time.sleep(1)

    def player_giveup_landlord(self):
        """玩家不叫地主"""
        self.game_state = "calling"
        self.ai_call_landlord()

    def player_play_card(self):
        """玩家出牌"""
        if not self.player_cards:
            return
        
        play_cards = self.selected_cards.copy() if self.selected_cards else [self.player_cards[0]]
        is_able, tip = is_card_able_to_play(play_cards, self.last_play)
        
        if not is_able:
            self.tip_text = tip
            self.tip_alpha = 255
            self.draw_interface()
            pygame.display.flip()
            return
        
        if play_cards != ["过牌"]:
            card_type, card_priority, card_count = judge_card_type(play_cards)
            for card in play_cards:
                if card in self.player_cards:
                    self.player_cards.remove(card)
            
            self.selected_cards.clear()
            self.tip_text = ""
            self.tip_alpha = 255
            
            self.last_play = {
                "player": "玩家", "cards": play_cards,
                "type": card_type, "priority": card_priority, "count": card_count
            }
            
            self.calc_adaptive_card_size()
        else:
            self.selected_cards.clear()
            self.tip_text = ""
            self.tip_alpha = 255
            self.last_play = {
                "player": "玩家", "cards": ["过牌"], 
                "type": CARD_TYPE_PASS, "priority": 0, "count": 0
            }
        
        self.draw_interface()
        pygame.display.flip()
        time.sleep(1)
        
        if self.check_win():
            return
        
        self.game_state = "playing"
        self.show_ai_notice("等待AI出牌...")
        ai_id = 1 if self.landlord != 1 else 2
        self.ai_play_card(ai_id)

    def player_giveup_card(self):
        """玩家过牌"""
        self.selected_cards.clear()
        self.tip_text = ""
        self.tip_alpha = 255
        self.last_play = {
            "player": "玩家", "cards": ["过牌"], 
            "type": CARD_TYPE_PASS, "priority": 0, "count": 0
        }
        self.draw_interface()
        pygame.display.flip()
        time.sleep(1)
        
        ai_id = 1 if self.landlord != 1 else 2
        self.ai_play_card(ai_id)

    # ---------------------- 获胜检测与游戏重置 ----------------------
    def check_win(self):
        """检查是否有玩家获胜"""
        # 玩家获胜
        if not self.player_cards:
            self.show_ai_notice("恭喜你！获得游戏胜利！")
            self.reset_game()
            return True
        # AI1获胜
        elif not self.ai1_cards:
            self.show_ai_notice("AI农民1获得游戏胜利！")
            self.reset_game()
            return True
        # AI2获胜
        elif not self.ai2_cards:
            self.show_ai_notice("AI农民2获得游戏胜利！")
            self.reset_game()
            return True
        return False

    def reset_game(self):
        """重置游戏，重新开始"""
        self.landlord = -1
        self.game_state = "shuffling"
        self.last_play = {
            "player": "", "cards": [], "type": "", 
            "priority": 0, "count": 0
        }
        self.selected_cards.clear()
        self.tip_text = ""
        self.tip_alpha = 255
        
        # 恢复基础卡牌尺寸
        self.current_card_width = BASE_CARD_WIDTH
        self.current_card_height = BASE_CARD_HEIGHT
        self.current_card_margin = BASE_CARD_MARGIN
        
        # 重新洗牌发牌
        self.shuffle_deck()
        self.game_state = "dealing"
        self.deal_cards()
    
    def init_game(self):
        """初始化游戏流程（洗牌+发牌）"""
        self.shuffle_deck()
        self.game_state = "dealing"
        self.deal_cards()

    # ---------------------- 游戏主循环（保留原有功能）----------------------
    def run(self):
        """游戏主循环"""
        running = True
        while running:
            self.clock.tick(FPS)
            
            # 事件处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    # 先检测卡牌点击
                    self.check_card_click(mouse_pos)
                    
                    # 再检测按钮点击
                    if self.game_state == "calling":
                        if self.buttons["call"].collidepoint(mouse_pos):
                            self.player_call_landlord()
                        elif self.buttons["giveup_call"].collidepoint(mouse_pos):
                            self.player_giveup_landlord()
                    elif self.game_state == "playing" and self.last_play["player"] != "玩家":
                        if self.buttons["play"].collidepoint(mouse_pos):
                            self.player_play_card()
                        elif self.buttons["giveup_play"].collidepoint(mouse_pos):
                            self.player_giveup_card()
            
            # 绘制界面（非洗牌/结束状态）
            if self.game_state not in ["shuffling", "over"]:
                self.draw_interface()
            
            # 更新显示
            pygame.display.flip()
        
        # 退出Pygame
        pygame.quit()

# ---------------------- 运行游戏 ----------------------
if __name__ == "__main__":
    # 安装pygame命令：pip install pygame
    game = LandlordGamePygame()
    game.run()