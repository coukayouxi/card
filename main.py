import pygame
import random
import time

# ---------------------- 常量定义 ----------------------
# 窗口常量
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
FPS = 60

# 颜色常量
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_BLUE = (0, 0, 255)
COLOR_RED = (255, 0, 0)
COLOR_GRAY = (128, 128, 128)
COLOR_GREEN = (0, 255, 0)
COLOR_LIGHT_GREEN = (0, 200, 0)  # 选中边框色
COLOR_YELLOW = (255, 255, 0)
COLOR_ORANGE = (255, 165, 0)  # 提示文字色
CARD_BACK_COLOR = (139, 69, 19)  # 卡牌背面（棕色）

# 卡牌常量（适配手牌完整显示的基础尺寸）
BASE_CARD_WIDTH = 50
BASE_CARD_HEIGHT = 70
BASE_CARD_MARGIN = 8
CARD_SELECT_OFFSET = -15  # 选中卡牌向上偏移量
SUITS = ['♠', '♥', '♣', '♦']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
JOKERS = ['小王', '大王']

# 牌型优先级字典（大王>小王>2>A>K>...>3）
RANK_PRIORITY = {
    '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
    '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14, '2': 15,
    '小王': 16, '大王': 17
}

# 全量牌型常量
CARD_TYPE_SINGLE = "单张"
CARD_TYPE_PAIR = "对子"
CARD_TYPE_SEQUENCE_PAIR = "连对"  # 拖拉机
CARD_TYPE_SEQUENCE_SINGLE = "顺子"  # 单顺
CARD_TYPE_TRIPLE = "三张"
CARD_TYPE_TRIPLE_ONE = "三带一"
CARD_TYPE_TRIPLE_PAIR = "三带一对"
CARD_TYPE_PLANE_NO_WING = "飞机不带翼"
CARD_TYPE_PLANE_SINGLE_WING = "飞机带单翼"
CARD_TYPE_PLANE_PAIR_WING = "飞机带双翼"
CARD_TYPE_BOMB = "炸弹"
CARD_TYPE_JOKER_BOMB = "王炸"
CARD_TYPE_FOUR_TWO_SINGLE = "四带两张单"
CARD_TYPE_FOUR_TWO_PAIR = "四带两对"
CARD_TYPE_INVALID = "非法牌型"
CARD_TYPE_PASS = "过牌"

# 牌型最小要求常量
MIN_SEQUENCE_SINGLE_COUNT = 5  # 顺子最小5张
MIN_SEQUENCE_PAIR_COUNT = 3    # 连对最小3对（6张）
MIN_PLANE_COUNT = 2            # 飞机最小2组（6张）

# 按钮常量
BUTTON_WIDTH = 120
BUTTON_HEIGHT = 50
BUTTON_MARGIN = 20
BUTTON_Y = WINDOW_HEIGHT - 100  # 按钮下移，避免和手牌重叠

# ---------------------- 游戏类实现 ----------------------
class LandlordGamePygame:
    def __init__(self):
        # 初始化Pygame
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Python 斗地主（完整版·支持所有合法牌型）")
        self.clock = pygame.time.Clock()
        
        # 加载支持中文的字体
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
        # 上一轮出牌信息（牌型+优先级+牌数/组数，用于压制判断）
        self.last_play = {
            "player": "", "cards": [], "type": "", 
            "priority": 0, "count": 0  # count：顺子长度/连对对数/飞机组数等
        }
        self.tip_text = ""  # 顶部提示信息（非法牌型等）
        
        # 卡牌选中相关变量
        self.selected_cards = []  # 记录玩家选中的卡牌
        self.player_card_rects = []  # 记录每张玩家手牌的矩形区域
        # 动态卡牌尺寸（根据手牌数量自适应）
        self.current_card_width = BASE_CARD_WIDTH
        self.current_card_height = BASE_CARD_HEIGHT
        self.current_card_margin = BASE_CARD_MARGIN
        
        # 按钮定义
        self.buttons = {
            "call": pygame.Rect(WINDOW_WIDTH//2 - 200, BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT),
            "giveup_call": pygame.Rect(WINDOW_WIDTH//2 - 60, BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT),
            "play": pygame.Rect(WINDOW_WIDTH//2 + 80, BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT),
            "giveup_play": pygame.Rect(WINDOW_WIDTH//2 + 220, BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT)
        }
        
        # 初始化游戏
        self.init_game()
    
    def load_chinese_font(self, font_size, bold=False):
        """加载多系统兼容的中文字体"""
        font_candidates = [
            "SimSun", "SimHei", "PingFang SC", "Heiti TC",
            "WenQuanYi Zen Hei", "WenQuanYi Micro Hei"
        ]
        
        for font_name in font_candidates:
            try:
                return pygame.font.SysFont(font_name, font_size, bold=bold)
            except (pygame.error, ValueError):
                continue
        
        print("警告：未找到系统自带中文字体，中文可能显示异常！")
        return pygame.font.Font(None, font_size)

    def create_deck(self):
        """创建完整的54张扑克牌组"""
        deck = []
        for suit in SUITS:
            for rank in RANKS:
                deck.append(f"{suit}{rank}")
        deck.extend(JOKERS)
        return deck

    def shuffle_deck(self):
        """自动洗牌+洗牌动画"""
        self.deck = self.create_deck()
        self.game_state = "shuffling"
        self.tip_text = ""
        
        for i in range(50):
            self.screen.fill(COLOR_WHITE)
            shuffle_text = self.large_font.render("正在自动洗牌...", True, COLOR_RED)
            self.screen.blit(shuffle_text, (WINDOW_WIDTH//2 - shuffle_text.get_width()//2, WINDOW_HEIGHT//2))
            
            # 绘制晃动的牌堆
            for j in range(10):
                x = WINDOW_WIDTH//2 + random.randint(-20, 20)
                y = WINDOW_HEIGHT//2 + 50 + random.randint(-20, 20)
                pygame.draw.rect(self.screen, CARD_BACK_COLOR, (x, y, self.current_card_width, self.current_card_height))
                pygame.draw.rect(self.screen, COLOR_BLACK, (x, y, self.current_card_width, self.current_card_height), 2)
            
            pygame.display.flip()
            self.clock.tick(FPS)
            time.sleep(0.05)
        
        random.shuffle(self.deck)
        self.game_state = "dealing"

    def deal_cards(self):
        """发牌+发牌动画（逐步分发卡牌）"""
        self.player_cards.clear()
        self.ai1_cards.clear()
        self.ai2_cards.clear()
        self.landlord_cards.clear()
        self.selected_cards.clear()
        self.tip_text = ""
        
        self.screen.fill(COLOR_WHITE)
        deal_text = self.large_font.render("正在发牌...", True, COLOR_BLUE)
        self.screen.blit(deal_text, (WINDOW_WIDTH//2 - deal_text.get_width()//2, WINDOW_HEIGHT//2))
        pygame.display.flip()
        time.sleep(1)
        
        # 按斗地主规则发牌（54张：玩家17+AI117+AI217+底牌3）
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
            
            # 发牌动画（每3张刷新一次界面）
            if i % 3 == 0:
                self.calc_adaptive_card_size()  # 动态计算卡牌尺寸
                self.draw_interface()
                pygame.display.flip()
                self.clock.tick(FPS)
                time.sleep(0.08)
        
        # 排序手牌（按RANK_PRIORITY升序，大王>小王>2>A>...>3）
        sort_key = lambda c: RANK_PRIORITY[self.get_card_rank(c)]
        self.player_cards.sort(key=sort_key)
        self.ai1_cards.sort(key=sort_key)
        self.ai2_cards.sort(key=sort_key)
        
        # 最终计算自适应尺寸
        self.calc_adaptive_card_size()
        self.game_state = "calling"
        self.draw_interface()
        pygame.display.flip()

    def get_card_rank(self, card):
        """提取卡牌的点数（处理花色和大小王）"""
        if card in JOKERS:
            return card
        # 提取点数（优先匹配长点数"10"，避免拆分）
        for rank in RANKS[::-1]:
            if card.endswith(rank):
                return rank
        return card[1:]

    def count_rank_occurrences(self, cards):
        """统计卡牌中点数的出现次数"""
        rank_count = {}
        for card in cards:
            rank = self.get_card_rank(card)
            rank_count[rank] = rank_count.get(rank, 0) + 1
        return rank_count

    def is_rank_continuous(self, ranks, exclude_2_joker=True):
        """判断点数是否连续（exclude_2_joker：是否排除2和大小王）"""
        # 过滤非法点数（若需要）
        if exclude_2_joker:
            valid_ranks = [r for r in ranks if r not in ['2', '小王', '大王']]
        else:
            valid_ranks = ranks.copy()
        
        if len(valid_ranks) < 2:
            return True if len(valid_ranks) == 1 else False
        
        # 转换为优先级并排序
        rank_prios = sorted([RANK_PRIORITY[r] for r in valid_ranks])
        # 验证连续性
        for i in range(1, len(rank_prios)):
            if rank_prios[i] - rank_prios[i-1] != 1:
                return False
        return True

    def get_max_rank_priority(self, cards):
        """获取牌组中最大点数的优先级"""
        if not cards:
            return 0
        ranks = [self.get_card_rank(c) for c in cards]
        return max([RANK_PRIORITY[r] for r in ranks])

    def judge_card_type(self, cards):
        """判断牌型（全量合法牌型），返回（牌型，核心优先级，辅助数量）"""
        if not cards:
            return (CARD_TYPE_INVALID, 0, 0)
        
        # 1. 过牌单独处理
        if cards == ["过牌"]:
            return (CARD_TYPE_PASS, 0, 0)
        
        card_count = len(cards)
        rank_count = self.count_rank_occurrences(cards)
        ranks = list(rank_count.keys())
        occurrences = list(rank_count.values())
        unique_rank_count = len(ranks)
        
        # 2. 王炸（唯一2张，包含小王+大王）
        if card_count == 2 and set(cards) == set(JOKERS):
            return (CARD_TYPE_JOKER_BOMB, RANK_PRIORITY["大王"], 1)
        
        # 3. 普通炸弹（4张同点数，不含大小王）
        if card_count == 4 and unique_rank_count == 1 and occurrences[0] == 4:
            core_prio = RANK_PRIORITY[ranks[0]]
            return (CARD_TYPE_BOMB, core_prio, 1)
        
        # 4. 单张（1张任意牌）
        if card_count == 1:
            core_prio = RANK_PRIORITY[self.get_card_rank(cards[0])]
            return (CARD_TYPE_SINGLE, core_prio, 1)
        
        # 5. 对子（2张同点数，不含大小王）
        if card_count == 2 and unique_rank_count == 1 and occurrences[0] == 2:
            if ranks[0] in JOKERS:
                return (CARD_TYPE_INVALID, 0, 0)
            core_prio = RANK_PRIORITY[ranks[0]]
            return (CARD_TYPE_PAIR, core_prio, 1)
        
        # 6. 顺子（单顺，≥5张连续单牌，不含2、大小王）
        if card_count >= MIN_SEQUENCE_SINGLE_COUNT and unique_rank_count == card_count:
            # 条件：所有点数出现1次、连续、不含2和大小王
            if all(o == 1 for o in occurrences) and self.is_rank_continuous(ranks):
                max_rank = max(ranks, key=lambda r: RANK_PRIORITY[r])
                core_prio = RANK_PRIORITY[max_rank]
                return (CARD_TYPE_SEQUENCE_SINGLE, core_prio, card_count)
        
        # 7. 连对（拖拉机，≥3对（6张），偶数张，不含2、大小王）
        if card_count >= 2 * MIN_SEQUENCE_PAIR_COUNT and card_count % 2 == 0:
            # 条件：所有点数出现2次、连续、不含2和大小王
            if all(o == 2 for o in occurrences) and self.is_rank_continuous(ranks):
                pair_count = card_count // 2
                max_rank = max(ranks, key=lambda r: RANK_PRIORITY[r])
                core_prio = RANK_PRIORITY[max_rank]
                return (CARD_TYPE_SEQUENCE_PAIR, core_prio, pair_count)
        
        # 8. 三张（3张同点数，不含大小王）
        if card_count == 3 and unique_rank_count == 1 and occurrences[0] == 3:
            if ranks[0] in JOKERS:
                return (CARD_TYPE_INVALID, 0, 0)
            core_prio = RANK_PRIORITY[ranks[0]]
            return (CARD_TYPE_TRIPLE, core_prio, 1)
        
        # 9. 三带一（4张，3张同点+1张单牌）
        if card_count == 4 and unique_rank_count == 2:
            sorted_occur = sorted(occurrences)
            if sorted_occur == [1, 3]:
                # 提取三张的点数（核心优先级）
                triple_rank = ranks[0] if occurrences[0] == 3 else ranks[1]
                if triple_rank in JOKERS:
                    return (CARD_TYPE_INVALID, 0, 0)
                core_prio = RANK_PRIORITY[triple_rank]
                return (CARD_TYPE_TRIPLE_ONE, core_prio, 1)
        
        # 10. 三带一对（5张，3张同点+1对对子）
        if card_count == 5 and unique_rank_count == 2:
            sorted_occur = sorted(occurrences)
            if sorted_occur == [2, 3]:
                triple_rank = ranks[0] if occurrences[0] == 3 else ranks[1]
                pair_rank = ranks[0] if occurrences[0] == 2 else ranks[1]
                if triple_rank in JOKERS or pair_rank in JOKERS:
                    return (CARD_TYPE_INVALID, 0, 0)
                core_prio = RANK_PRIORITY[triple_rank]
                return (CARD_TYPE_TRIPLE_PAIR, core_prio, 1)
        
        # 11. 飞机不带翼（≥6张，≥2组连续三张，不含2、大小王）
        if card_count >= 3 * MIN_PLANE_COUNT and card_count % 3 == 0:
            plane_group_count = card_count // 3
            # 条件：所有点数出现3次、组数≥2、点数连续
            if all(o == 3 for o in occurrences) and len(ranks) == plane_group_count and plane_group_count >= MIN_PLANE_COUNT:
                if self.is_rank_continuous(ranks):
                    max_rank = max(ranks, key=lambda r: RANK_PRIORITY[r])
                    core_prio = RANK_PRIORITY[max_rank]
                    return (CARD_TYPE_PLANE_NO_WING, core_prio, plane_group_count)
        
        # 12. 飞机带单翼（≥8张，≥2组连续三张+等量单张，不含2、大小王）
        if card_count >= 3 * MIN_PLANE_COUNT + MIN_PLANE_COUNT:
            plane_group_count = None
            # 统计点数出现次数：3次（三张）、1次（单张）
            occur_3_count = sum(1 for o in occurrences if o == 3)
            occur_1_count = sum(1 for o in occurrences if o == 1)
            # 条件：组数=3次点数数量=1次点数数量≥2、总牌数=3*组数+1*组数
            if occur_3_count == occur_1_count and occur_3_count >= MIN_PLANE_COUNT:
                plane_group_count = occur_3_count
                total_needed = 3 * plane_group_count + 1 * plane_group_count
                if card_count == total_needed:
                    # 提取三张的点数并验证连续性
                    plane_ranks = [r for r, o in rank_count.items() if o == 3]
                    if self.is_rank_continuous(plane_ranks):
                        max_plane_rank = max(plane_ranks, key=lambda r: RANK_PRIORITY[r])
                        core_prio = RANK_PRIORITY[max_plane_rank]
                        return (CARD_TYPE_PLANE_SINGLE_WING, core_prio, plane_group_count)
        
        # 13. 飞机带双翼（≥10张，≥2组连续三张+等量对子，不含2、大小王）
        if card_count >= 3 * MIN_PLANE_COUNT + 2 * MIN_PLANE_COUNT:
            plane_group_count = None
            # 统计点数出现次数：3次（三张）、2次（对子）
            occur_3_count = sum(1 for o in occurrences if o == 3)
            occur_2_count = sum(1 for o in occurrences if o == 2)
            # 条件：组数=3次点数数量=2次点数数量≥2、总牌数=3*组数+2*组数
            if occur_3_count == occur_2_count and occur_3_count >= MIN_PLANE_COUNT:
                plane_group_count = occur_3_count
                total_needed = 3 * plane_group_count + 2 * plane_group_count
                if card_count == total_needed:
                    # 提取三张的点数并验证连续性
                    plane_ranks = [r for r, o in rank_count.items() if o == 3]
                    if self.is_rank_continuous(plane_ranks):
                        max_plane_rank = max(plane_ranks, key=lambda r: RANK_PRIORITY[r])
                        core_prio = RANK_PRIORITY[max_plane_rank]
                        return (CARD_TYPE_PLANE_PAIR_WING, core_prio, plane_group_count)
        
        # 14. 四带两张单（6张，4张同点+2张不同单牌，不含王炸）
        if card_count == 6 and unique_rank_count == 3:
            sorted_occur = sorted(occurrences)
            if sorted_occur == [1, 1, 4]:
                four_rank = [r for r, o in rank_count.items() if o == 4][0]
                if four_rank in JOKERS:
                    return (CARD_TYPE_INVALID, 0, 0)
                core_prio = RANK_PRIORITY[four_rank]
                return (CARD_TYPE_FOUR_TWO_SINGLE, core_prio, 1)
        
        # 15. 四带两对（8张，4张同点+2副不同对子，不含王炸）
        if card_count == 8 and unique_rank_count == 3:
            sorted_occur = sorted(occurrences)
            if sorted_occur == [2, 2, 4]:
                four_rank = [r for r, o in rank_count.items() if o == 4][0]
                if four_rank in JOKERS:
                    return (CARD_TYPE_INVALID, 0, 0)
                core_prio = RANK_PRIORITY[four_rank]
                return (CARD_TYPE_FOUR_TWO_PAIR, core_prio, 1)
        
        # 16. 非法牌型
        return (CARD_TYPE_INVALID, 0, 0)

    def is_card_able_to_play(self, current_cards):
        """判断当前牌是否能出（覆盖所有牌型的压制规则）"""
        # 第一步：判断是否为合法牌型（过牌除外）
        if current_cards != ["过牌"]:
            current_type, current_priority, current_count = self.judge_card_type(current_cards)
            if current_type == CARD_TYPE_INVALID:
                self.tip_text = "非法牌型，请重新选择！"
                return False
        else:
            # 过牌始终合法
            self.tip_text = ""
            return True
        
        # 第二步：判断是否为首轮（上一轮无出牌），首轮合法牌型可直接出
        last_cards = self.last_play["cards"]
        last_type = self.last_play["type"]
        if not last_cards or last_type == "" or last_type == CARD_TYPE_PASS:
            self.tip_text = ""
            return True
        
        # 第三步：提取当前牌和上一轮牌的关键信息
        current_type, current_priority, current_count = self.judge_card_type(current_cards)
        last_priority = self.last_play["priority"]
        last_count = self.last_play["count"]
        
        # 规则1：王炸可压一切
        if current_type == CARD_TYPE_JOKER_BOMB:
            self.tip_text = ""
            return True
        
        # 规则2：炸弹的压制逻辑（仅能被王炸、更大的炸弹压制）
        if last_type == CARD_TYPE_JOKER_BOMB:
            self.tip_text = "上一轮是王炸，仅能出王炸压制！"
            return False
        
        if last_type == CARD_TYPE_BOMB:
            if current_type != CARD_TYPE_BOMB:
                self.tip_text = "上一轮是炸弹，仅能出更大的炸弹或王炸压制！"
                return False
            else:
                if current_priority > last_priority:
                    self.tip_text = ""
                    return True
                else:
                    last_rank = self.get_card_rank(last_cards[0])
                    self.tip_text = f"炸弹大小不足，需大于{last_rank}！"
                    return False
        
        # 规则3：普通牌型的压制逻辑（同类型+数量匹配+优先级更高，或炸弹/王炸）
        normal_types = [
            CARD_TYPE_SINGLE, CARD_TYPE_PAIR, CARD_TYPE_SEQUENCE_PAIR,
            CARD_TYPE_SEQUENCE_SINGLE, CARD_TYPE_TRIPLE, CARD_TYPE_TRIPLE_ONE,
            CARD_TYPE_TRIPLE_PAIR, CARD_TYPE_PLANE_NO_WING, CARD_TYPE_PLANE_SINGLE_WING,
            CARD_TYPE_PLANE_PAIR_WING, CARD_TYPE_FOUR_TWO_SINGLE, CARD_TYPE_FOUR_TWO_PAIR
        ]
        
        if last_type in normal_types:
            # 3.1 炸弹可压所有普通牌型
            if current_type == CARD_TYPE_BOMB:
                self.tip_text = ""
                return True
            
            # 3.2 必须为同类型牌型
            if current_type != last_type:
                self.tip_text = f"上一轮是{last_type}，需出同类型牌型或炸弹/王炸！"
                return False
            
            # 3.3 复杂牌型需数量匹配（顺子长度/连对对数/飞机组数等）
            if current_count != last_count:
                type_tips = {
                    CARD_TYPE_SEQUENCE_SINGLE: f"顺子长度（{last_count}张）",
                    CARD_TYPE_SEQUENCE_PAIR: f"连对对数（{last_count}对）",
                    CARD_TYPE_PLANE_NO_WING: f"飞机组数（{last_count}组）",
                    CARD_TYPE_PLANE_SINGLE_WING: f"飞机组数（{last_count}组）",
                    CARD_TYPE_PLANE_PAIR_WING: f"飞机组数（{last_count}组）"
                }
                tip = type_tips.get(last_type, "牌数")
                self.tip_text = f"上一轮{tip}不符，需出相同{tip}的{last_type}或炸弹/王炸！"
                return False
            
            # 3.4 同类型同数量，比较核心优先级
            if current_priority > last_priority:
                self.tip_text = ""
                return True
            else:
                # 优化提示信息
                if last_type in [CARD_TYPE_SEQUENCE_SINGLE, CARD_TYPE_SEQUENCE_PAIR,
                                 CARD_TYPE_PLANE_NO_WING, CARD_TYPE_PLANE_SINGLE_WING,
                                 CARD_TYPE_PLANE_PAIR_WING]:
                    last_max_rank = max([self.get_card_rank(c) for c in last_cards],
                                        key=lambda r: RANK_PRIORITY[r])
                    self.tip_text = f"{last_type}大小不足，最大点数需大于{last_max_rank}！"
                else:
                    last_rank = self.get_card_rank(last_cards[0])
                    self.tip_text = f"{last_type}大小不足，需大于{last_rank}！"
                return False
        
        # 其他未覆盖情况（默认非法）
        self.tip_text = "无法压制上一轮牌型，请重新选择！"
        return False

    def calc_adaptive_card_size(self):
        """动态计算自适应卡牌尺寸，确保手牌完整显示在屏幕内"""
        card_count = len(self.player_cards)
        if card_count == 0:
            # 无手牌时恢复基础尺寸
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
            # 未超出，保持基础尺寸
            self.current_card_width = BASE_CARD_WIDTH
            self.current_card_height = BASE_CARD_HEIGHT
            self.current_card_margin = BASE_CARD_MARGIN
        else:
            # 超出，计算缩放比例（确保总宽度≤可用宽度）
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
            return WINDOW_WIDTH // 2
        
        # 计算总占用宽度
        total_card_width = (self.current_card_width * card_count) + (self.current_card_margin * (card_count - 1))
        # 居中对齐
        start_x = (WINDOW_WIDTH // 2) - (total_card_width // 2)
        
        # 确保起始x坐标≥50（左边界留边距）
        return max(start_x, 50)

    def card_sort_key(self, card):
        """卡牌排序键（按RANK_PRIORITY）"""
        rank = self.get_card_rank(card)
        return RANK_PRIORITY.get(rank, 0)

    def draw_card(self, x, y, card, show_back=False, is_selected=False):
        """绘制单张卡牌（适配动态尺寸）"""
        # 选中卡牌向上偏移
        draw_y = y + CARD_SELECT_OFFSET if is_selected else y
        
        # 绘制卡牌背景
        if show_back:
            pygame.draw.rect(self.screen, CARD_BACK_COLOR, (x, draw_y, self.current_card_width, self.current_card_height))
        else:
            pygame.draw.rect(self.screen, COLOR_WHITE, (x, draw_y, self.current_card_width, self.current_card_height))
        
        # 绘制卡牌边框
        border_color = COLOR_LIGHT_GREEN if is_selected else COLOR_BLACK
        border_width = 2 if is_selected else 1
        pygame.draw.rect(self.screen, border_color, (x, draw_y, self.current_card_width, self.current_card_height), border_width)
        
        # 绘制卡牌文字（花色+点数，适配动态尺寸）
        if not show_back:
            card_color = COLOR_RED if (card[0] == '♥' or card[0] == '♦') else COLOR_BLACK
            # 左侧花色/大小王
            suit_content = card[0] if card[0] in SUITS else card
            suit_text = self.small_font.render(suit_content, True, card_color)
            self.screen.blit(suit_text, (x + 5, draw_y + 5))
            
            # 右侧点数（大小王不显示额外点数）
            if card not in JOKERS:
                rank = self.get_card_rank(card)
                rank_text = self.small_font.render(rank, True, card_color)
                rank_x = x + self.current_card_width - rank_text.get_width() - 5
                rank_y = draw_y + self.current_card_height - rank_text.get_height() - 5
                self.screen.blit(rank_text, (rank_x, rank_y))
        
        # 返回卡牌实际绘制的矩形区域
        return pygame.Rect(x, draw_y, self.current_card_width, self.current_card_height)

    def check_card_click(self, mouse_pos):
        """检测鼠标是否点击了玩家手牌，切换选中状态"""
        if self.game_state != "playing" or self.last_play["player"] == "玩家":
            return
        
        # 遍历每张手牌的矩形区域
        for card_rect, card in zip(self.player_card_rects, self.player_cards):
            if card_rect.collidepoint(mouse_pos):
                # 切换选中状态
                if card in self.selected_cards:
                    self.selected_cards.remove(card)
                else:
                    self.selected_cards.append(card)
                self.tip_text = ""
                break

    def draw_interface(self):
        """绘制完整游戏界面（支持所有牌型的显示和提示）"""
        # 填充背景
        self.screen.fill(COLOR_WHITE)
        
        # 绘制顶部信息栏
        info_text = self.get_top_info_text()
        self.screen.blit(info_text, (WINDOW_WIDTH//2 - info_text.get_width()//2, 20))
        
        # 绘制顶部提示文字
        if self.tip_text:
            tip_surface = self.tip_font.render(self.tip_text, True, COLOR_ORANGE)
            self.screen.blit(tip_surface, (WINDOW_WIDTH//2 - tip_surface.get_width()//2, 60))
        
        # 1. 绘制上方AI2手牌（农民2）
        self.draw_ai_hand(2, 50, 80, 150, 120)
        
        # 2. 绘制地主底牌
        self.draw_landlord_cards()
        
        # 3. 绘制中间出牌区域（显示上一轮牌型）
        self.draw_play_area()
        
        # 4. 绘制下方AI1手牌（农民1）
        self.draw_ai_hand(1, 50, 450, 150, 490)
        
        # 5. 绘制玩家手牌（居中+自适应+选中效果）
        self.draw_player_hand()
        
        # 6. 绘制操作按钮
        self.draw_operation_buttons()

    def get_top_info_text(self):
        """获取顶部游戏状态信息文本"""
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
        """绘制AI手牌（背面显示）"""
        ai_cards = self.ai1_cards if ai_id == 1 else self.ai2_cards
        ai_title = self.font.render(f"AI农民{ai_id}（{'下方' if ai_id == 1 else '上方'}）", True, COLOR_BLACK)
        self.screen.blit(ai_title, (title_x, title_y))
        
        # 绘制AI手牌（固定小尺寸，避免超出屏幕）
        ai_card_width = 40
        ai_card_margin = 5
        current_x = card_start_x
        
        for _ in ai_cards:
            self.draw_card(current_x, card_y, "", show_back=True)
            current_x += ai_card_width + ai_card_margin
            # 超出屏幕则停止绘制（简化显示）
            if current_x + ai_card_width > WINDOW_WIDTH - 50:
                break

    def draw_landlord_cards(self):
        """绘制地主底牌"""
        landlord_title = self.font.render("地主底牌", True, COLOR_RED)
        self.screen.blit(landlord_title, (WINDOW_WIDTH//2 - 50, 200))
        landlord_x = WINDOW_WIDTH//2 - (3 * (self.current_card_width + self.current_card_margin))//2
        
        if self.landlord == -1:
            # 未确定地主，显示背面
            for _ in range(3):
                self.draw_card(landlord_x, 240, "", show_back=True)
                landlord_x += self.current_card_width + self.current_card_margin
        elif self.landlord == 0:
            # 玩家是地主，提示底牌已加入手牌
            owned_text = self.font.render("已归属玩家（已加入你的手牌）", True, COLOR_GREEN)
            self.screen.blit(owned_text, (WINDOW_WIDTH//2 - owned_text.get_width()//2, 240))
        else:
            # AI是地主，显示底牌
            for card in self.landlord_cards:
                self.draw_card(landlord_x, 240, card)
                landlord_x += self.current_card_width + self.current_card_margin

    def draw_play_area(self):
        """绘制中间出牌区域"""
        play_area = pygame.Rect(200, 300, 800, 100)
        pygame.draw.rect(self.screen, COLOR_GRAY, play_area, 2)
        
        # 组装出牌信息文本
        if self.last_play["cards"]:
            play_cards_text = '  '.join(self.last_play["cards"])
            play_type_text = f"（{self.last_play['type']}）" if self.last_play["type"] != CARD_TYPE_PASS else ""
            play_content = f"上一轮出牌：{self.last_play['player']} - {play_cards_text}{play_type_text}"
        else:
            play_content = "上一轮出牌：无"
        
        play_title = self.font.render(play_content, True, COLOR_BLACK)
        self.screen.blit(play_title, (250, 330))

    def draw_player_hand(self):
        """绘制玩家手牌"""
        self.player_card_rects.clear()
        player_title = self.font.render("你的手牌", True, COLOR_BLUE)
        self.screen.blit(player_title, (WINDOW_WIDTH//2 - player_title.get_width()//2, 550))
        
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
        """绘制操作按钮（叫地主/不叫/出牌/过）"""
        if self.game_state == "calling":
            # 叫地主阶段按钮
            pygame.draw.rect(self.screen, COLOR_GREEN, self.buttons["call"])
            pygame.draw.rect(self.screen, COLOR_RED, self.buttons["giveup_call"])
            
            call_text = self.font.render("叫地主", True, COLOR_WHITE)
            giveup_call_text = self.font.render("不叫", True, COLOR_WHITE)
            
            self.screen.blit(call_text, (self.buttons["call"].x + 20, self.buttons["call"].y + 10))
            self.screen.blit(giveup_call_text, (self.buttons["giveup_call"].x + 30, self.buttons["giveup_call"].y + 10))
        
        if self.game_state == "playing" and self.last_play["player"] != "玩家":
            # 出牌阶段按钮
            pygame.draw.rect(self.screen, COLOR_GREEN, self.buttons["play"])
            pygame.draw.rect(self.screen, COLOR_RED, self.buttons["giveup_play"])
            
            play_text = self.font.render("出牌", True, COLOR_WHITE)
            giveup_play_text = self.font.render("过", True, COLOR_WHITE)
            
            self.screen.blit(play_text, (self.buttons["play"].x + 40, self.buttons["play"].y + 10))
            self.screen.blit(giveup_play_text, (self.buttons["giveup_play"].x + 50, self.buttons["giveup_play"].y + 10))

    def get_ai_legal_plays(self, ai_cards):
        """获取AI的所有合法牌型（支持全量牌型）"""
        legal_plays = []
        card_count = len(ai_cards)
        if card_count == 0:
            return legal_plays
        
        # 先按点数排序AI手牌，方便提取连续牌型
        sorted_ai_cards = sorted(ai_cards, key=self.card_sort_key)
        
        # 1. 提取所有单张
        for i in range(card_count):
            single_card = [sorted_ai_cards[i]]
            if self.judge_card_type(single_card)[0] != CARD_TYPE_INVALID:
                legal_plays.append(single_card)
        
        # 2. 提取所有对子
        for i in range(card_count - 1):
            card1_rank = self.get_card_rank(sorted_ai_cards[i])
            card2_rank = self.get_card_rank(sorted_ai_cards[i+1])
            if card1_rank == card2_rank:
                pair_cards = [sorted_ai_cards[i], sorted_ai_cards[i+1]]
                legal_plays.append(pair_cards)
        
        # 3. 提取所有三张
        for i in range(card_count - 2):
            card1_rank = self.get_card_rank(sorted_ai_cards[i])
            card2_rank = self.get_card_rank(sorted_ai_cards[i+1])
            card3_rank = self.get_card_rank(sorted_ai_cards[i+2])
            if card1_rank == card2_rank == card3_rank:
                triple_cards = [sorted_ai_cards[i], sorted_ai_cards[i+1], sorted_ai_cards[i+2]]
                legal_plays.append(triple_cards)
        
        # 4. 提取所有炸弹
        for i in range(card_count - 3):
            ranks = [self.get_card_rank(sorted_ai_cards[i+j]) for j in range(4)]
            if len(set(ranks)) == 1:
                bomb_cards = sorted_ai_cards[i:i+4]
                legal_plays.append(bomb_cards)
        
        # 5. 提取复杂牌型（顺子、连对、飞机等）- 简化提取，优先匹配最小尺寸
        # 5.1 顺子（最小5张）
        for start in range(card_count - MIN_SEQUENCE_SINGLE_COUNT + 1):
            for end in range(start + MIN_SEQUENCE_SINGLE_COUNT - 1, card_count):
                sequence_cards = sorted_ai_cards[start:end+1]
                if self.judge_card_type(sequence_cards)[0] == CARD_TYPE_SEQUENCE_SINGLE:
                    legal_plays.append(sequence_cards)
        
        # 5.2 连对（最小6张，3对）
        min_seq_pair_len = 2 * MIN_SEQUENCE_PAIR_COUNT
        for start in range(card_count - min_seq_pair_len + 1):
            for end in range(start + min_seq_pair_len - 1, card_count, 2):
                pair_seq_cards = sorted_ai_cards[start:end+1]
                if self.judge_card_type(pair_seq_cards)[0] == CARD_TYPE_SEQUENCE_PAIR:
                    legal_plays.append(pair_seq_cards)
        
        # 5.3 飞机及其他复杂牌型（简化提取，确保AI能打出基础复杂牌型）
        min_plane_len = 3 * MIN_PLANE_COUNT
        for start in range(card_count - min_plane_len + 1):
            for end in range(start + min_plane_len - 1, card_count):
                plane_cards = sorted_ai_cards[start:end+1]
                card_type = self.judge_card_type(plane_cards)[0]
                if card_type in [CARD_TYPE_PLANE_NO_WING, CARD_TYPE_PLANE_SINGLE_WING, CARD_TYPE_PLANE_PAIR_WING]:
                    legal_plays.append(plane_cards)
        
        # 6. 提取四带二牌型
        for start in range(card_count - 5):  # 四带二最小6张
            for end in range(start + 5, card_count):
                four_two_cards = sorted_ai_cards[start:end+1]
                card_type = self.judge_card_type(four_two_cards)[0]
                if card_type in [CARD_TYPE_FOUR_TWO_SINGLE, CARD_TYPE_FOUR_TWO_PAIR]:
                    legal_plays.append(four_two_cards)
        
        # 去重并返回
        return [list(t) for t in set(tuple(p) for p in legal_plays)]

    def ai_call_landlord(self):
        """AI自动叫地主逻辑（优先选择有大牌、炸弹的手牌）"""
        self.screen.fill(COLOR_WHITE)
        ai_text = self.large_font.render("等待AI叫地主...", True, COLOR_BLACK)
        self.screen.blit(ai_text, (WINDOW_WIDTH//2 - ai_text.get_width()//2, WINDOW_HEIGHT//2))
        pygame.display.flip()
        time.sleep(1)
        
        # 定义AI叫地主的判断条件（有王炸、普通炸弹、2张以上2、1张以上王）
        def should_call(cards):
            rank_count = self.count_rank_occurrences(cards)
            # 有王炸
            if '小王' in rank_count and '大王' in rank_count:
                return True
            # 有普通炸弹
            if any(count == 4 for count in rank_count.values()):
                return True
            # 有2张以上2
            if rank_count.get('2', 0) >= 2:
                return True
            # 有1张以上王
            if rank_count.get('小王', 0) + rank_count.get('大王', 0) >= 1:
                return True
            return False
        
        # AI1叫地主判断
        if should_call(self.ai1_cards):
            self.landlord = 1
            self.ai1_cards.extend(self.landlord_cards)
            self.ai1_cards.sort(key=self.card_sort_key)
            self.show_ai_notice(f"AI农民1选择叫地主，成为地主！")
            self.game_state = "playing"
            self.ai_play_card(1)
            return
        
        # AI2叫地主判断
        if should_call(self.ai2_cards):
            self.landlord = 2
            self.ai2_cards.extend(self.landlord_cards)
            self.ai2_cards.sort(key=self.card_sort_key)
            self.show_ai_notice(f"AI农民2选择叫地主，成为地主！")
            self.game_state = "playing"
            self.ai_play_card(2)
            return
        
        # 所有玩家都不叫，重新洗牌
        self.show_ai_notice("所有玩家都不叫地主，重新开始！")
        self.reset_game()

    def show_ai_notice(self, notice_text):
        """显示AI操作提示并延时"""
        self.screen.fill(COLOR_WHITE)
        notice_surface = self.large_font.render(notice_text, True, COLOR_RED)
        self.screen.blit(notice_surface, (WINDOW_WIDTH//2 - notice_surface.get_width()//2, WINDOW_HEIGHT//2))
        pygame.display.flip()
        time.sleep(2)

    def ai_play_card(self, ai_id):
        """AI自动出牌逻辑（支持全量牌型，优先压制玩家）"""
        self.game_state = "playing"
        self.show_ai_notice(f"AI{ai_id}正在出牌...")
        
        # 选择AI手牌
        ai_cards = self.ai1_cards if ai_id == 1 else self.ai2_cards
        if not ai_cards:
            self.check_win()
            return
        
        # 获取AI所有合法牌型
        legal_plays = self.get_ai_legal_plays(ai_cards)
        play_cards = []
        
        # 优先筛选能压制上一轮的牌型
        for candidate in legal_plays:
            if self.is_card_able_to_play(candidate):
                play_cards = candidate
                break
        
        # 若无压制牌型，选择最小合法牌（首轮）或过牌
        if not play_cards and legal_plays:
            play_cards = sorted(legal_plays, key=lambda c: self.get_max_rank_priority(c))[0]
        elif not play_cards:
            self.last_play = {
                "player": f"AI{ai_id}", "cards": ["过牌"], 
                "type": CARD_TYPE_PASS, "priority": 0, "count": 0
            }
            self.draw_interface()
            pygame.display.flip()
            time.sleep(1)
            return
        
        # 从AI手牌中移除已出的牌
        for card in play_cards:
            if card in ai_cards:
                ai_cards.remove(card)
        
        # 更新上一轮出牌信息
        card_type, card_priority, card_count = self.judge_card_type(play_cards)
        self.last_play = {
            "player": f"AI{ai_id}", "cards": play_cards,
            "type": card_type, "priority": card_priority, "count": card_count
        }
        
        # 刷新界面并延时
        self.calc_adaptive_card_size()
        self.draw_interface()
        pygame.display.flip()
        time.sleep(1)
        
        # 检查获胜
        if self.check_win():
            return
        
        # 切换到玩家回合
        self.game_state = "playing"
        self.draw_interface()
        pygame.display.flip()

    def player_call_landlord(self):
        """玩家叫地主（底牌加入手牌并重新排序）"""
        self.landlord = 0
        self.player_cards.extend(self.landlord_cards)
        self.landlord_cards.clear()
        self.player_cards.sort(key=self.card_sort_key)
        
        # 重新计算自适应卡牌尺寸
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
        """玩家出牌（支持全量牌型，验证合法性）"""
        if not self.player_cards:
            return
        
        # 确定要出的牌（选中的牌或首张牌）
        play_cards = self.selected_cards.copy() if self.selected_cards else [self.player_cards[0]]
        
        # 第一步：校验出牌合法性
        if not self.is_card_able_to_play(play_cards):
            self.draw_interface()
            pygame.display.flip()
            return
        
        # 第二步：合法则处理出牌
        if play_cards != ["过牌"]:
            # 提取牌型信息
            card_type, card_priority, card_count = self.judge_card_type(play_cards)
            
            # 从玩家手牌中移除已出的牌
            for card in play_cards:
                if card in self.player_cards:
                    self.player_cards.remove(card)
            
            # 清空选中状态和提示
            self.selected_cards.clear()
            self.tip_text = ""
            
            # 更新上一轮出牌信息
            self.last_play = {
                "player": "玩家", "cards": play_cards,
                "type": card_type, "priority": card_priority, "count": card_count
            }
            
            # 重新计算自适应卡牌尺寸
            self.calc_adaptive_card_size()
        else:
            # 过牌处理
            self.selected_cards.clear()
            self.tip_text = ""
            self.last_play = {
                "player": "玩家", "cards": ["过牌"], 
                "type": CARD_TYPE_PASS, "priority": 0, "count": 0
            }
        
        # 刷新界面并延时
        self.draw_interface()
        pygame.display.flip()
        time.sleep(1)
        
        # 检查获胜
        if self.check_win():
            return
        
        # 切换到AI回合
        self.game_state = "playing"
        self.show_ai_notice("等待AI出牌...")
        
        # 确定要出牌的AI
        ai_id = 1 if self.landlord != 1 else 2
        self.ai_play_card(ai_id)

    def player_giveup_card(self):
        """玩家过牌"""
        self.selected_cards.clear()
        self.tip_text = ""
        self.last_play = {
            "player": "玩家", "cards": ["过牌"], 
            "type": CARD_TYPE_PASS, "priority": 0, "count": 0
        }
        self.draw_interface()
        pygame.display.flip()
        time.sleep(1)
        
        # 切换到AI回合
        ai_id = 1 if self.landlord != 1 else 2
        self.ai_play_card(ai_id)

    def check_win(self):
        """检查是否有玩家获胜"""
        # 玩家获胜
        if not self.player_cards:
            self.show_win_notice("恭喜你！获得游戏胜利！", COLOR_GREEN)
            self.reset_game()
            return True
        # AI1获胜
        elif not self.ai1_cards:
            self.show_win_notice("AI农民1获得游戏胜利！", COLOR_RED)
            self.reset_game()
            return True
        # AI2获胜
        elif not self.ai2_cards:
            self.show_win_notice("AI农民2获得游戏胜利！", COLOR_RED)
            self.reset_game()
            return True
        return False

    def show_win_notice(self, win_text, color):
        """显示获胜提示并延时"""
        self.screen.fill(COLOR_WHITE)
        win_surface = self.large_font.render(win_text, True, color)
        self.screen.blit(win_surface, (WINDOW_WIDTH//2 - win_surface.get_width()//2, WINDOW_HEIGHT//2))
        pygame.display.flip()
        time.sleep(3)

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
        
        # 恢复基础卡牌尺寸
        self.current_card_width = BASE_CARD_WIDTH
        self.current_card_height = BASE_CARD_HEIGHT
        self.current_card_margin = BASE_CARD_MARGIN
        
        # 重新洗牌发牌
        self.shuffle_deck()
        self.deal_cards()
    
    def init_game(self):
        """初始化游戏流程（洗牌+发牌）"""
        self.shuffle_deck()
        self.deal_cards()

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