# logic_card.py
"""斗地主纯牌型逻辑模块（无Pygame依赖，仅处理数据和规则）"""

# ---------------------- 核心常量定义（与界面无关）----------------------
# 卡牌基础配置
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

# ---------------------- 纯逻辑工具方法 ----------------------
def get_card_rank(card):
    """提取卡牌的点数（处理花色和大小王）"""
    if card in JOKERS:
        return card
    # 优先匹配长点数"10"，避免拆分
    for rank in RANKS[::-1]:
        if card.endswith(rank):
            return rank
    return card[1:]

def count_rank_occurrences(cards):
    """统计卡牌中点数的出现次数"""
    rank_count = {}
    for card in cards:
        rank = get_card_rank(card)
        rank_count[rank] = rank_count.get(rank, 0) + 1
    return rank_count

def is_rank_continuous(ranks, exclude_2_joker=True):
    """判断点数是否连续（exclude_2_joker：是否排除2和大小王）"""
    # 过滤非法点数（若需要）
    if exclude_2_joker:
        valid_ranks = [r for r in ranks if r not in ['2', '小王', '大王']]
    else:
        valid_ranks = ranks.copy()
    
    if len(valid_ranks) < 2:
        return True if len(valid_ranks) == 1 else False
    
    # 转换为优先级并排序
    try:
        rank_prios = sorted([RANK_PRIORITY[r] for r in valid_ranks])
        # 检查连续性
        for i in range(1, len(rank_prios)):
            if rank_prios[i] - rank_prios[i-1] != 1:
                return False
        return True
    except KeyError:
        return False

def get_max_rank_priority(cards):
    """获取牌组中最大点数的优先级"""
    if not cards:
        return 0
    ranks = [get_card_rank(c) for c in cards]
    return max([RANK_PRIORITY.get(r, 0) for r in ranks])

def judge_card_type(cards):
    """判断牌型（全量合法牌型），返回（牌型，核心优先级，辅助数量）"""
    if not cards:
        return (CARD_TYPE_INVALID, 0, 0)
    
    # 1. 过牌单独处理
    if cards == ["过牌"]:
        return (CARD_TYPE_PASS, 0, 0)
    
    card_count = len(cards)
    rank_count = count_rank_occurrences(cards)
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
        core_prio = RANK_PRIORITY[get_card_rank(cards[0])]
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
        if all(o == 1 for o in occurrences) and is_rank_continuous(ranks):
            max_rank = max(ranks, key=lambda r: RANK_PRIORITY[r])
            core_prio = RANK_PRIORITY[max_rank]
            return (CARD_TYPE_SEQUENCE_SINGLE, core_prio, card_count)
    
    # 7. 连对（拖拉机，≥3对（6张），偶数张，不含2、大小王）
    if card_count >= 2 * MIN_SEQUENCE_PAIR_COUNT and card_count % 2 == 0:
        # 条件：所有点数出现2次、连续、不含2和大小王
        if all(o == 2 for o in occurrences) and is_rank_continuous(ranks):
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
            if is_rank_continuous(ranks):
                max_rank = max(ranks, key=lambda r: RANK_PRIORITY[r])
                core_prio = RANK_PRIORITY[max_rank]
                return (CARD_TYPE_PLANE_NO_WING, core_prio, plane_group_count)
    
    # 12. 飞机带单翼（≥8张，≥2组连续三张+等量单张）
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
                if is_rank_continuous(plane_ranks):
                    max_plane_rank = max(plane_ranks, key=lambda r: RANK_PRIORITY[r])
                    core_prio = RANK_PRIORITY[max_plane_rank]
                    return (CARD_TYPE_PLANE_SINGLE_WING, core_prio, plane_group_count)
    
    # 13. 飞机带双翼（≥10张，≥2组连续三张+等量对子）
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
                if is_rank_continuous(plane_ranks):
                    max_plane_rank = max(plane_ranks, key=lambda r: RANK_PRIORITY[r])
                    core_prio = RANK_PRIORITY[max_plane_rank]
                    return (CARD_TYPE_PLANE_PAIR_WING, core_prio, plane_group_count)
    
    # 14. 四带两张单（6张，4张同点+2张不同单牌）
    if card_count == 6 and unique_rank_count == 3:
        sorted_occur = sorted(occurrences)
        if sorted_occur == [1, 1, 4]:
            four_rank = [r for r, o in rank_count.items() if o == 4][0]
            if four_rank in JOKERS:
                return (CARD_TYPE_INVALID, 0, 0)
            core_prio = RANK_PRIORITY[four_rank]
            return (CARD_TYPE_FOUR_TWO_SINGLE, core_prio, 1)
    
    # 15. 四带两对（8张，4张同点+2副不同对子）
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

def is_card_able_to_play(current_cards, last_play):
    """
    判断当前牌是否能出（覆盖所有牌型的压制规则）
    :param current_cards: 当前要出的牌
    :param last_play: 上一轮出牌信息（dict，包含type/priority/count）
    :return: (是否合法, 提示文字)
    """
    # 提取上一轮信息
    last_type = last_play.get("type", "")
    last_priority = last_play.get("priority", 0)
    last_count = last_play.get("count", 0)
    last_cards = last_play.get("cards", [])
    
    # 第一步：判断是否为合法牌型（过牌除外）
    if current_cards != ["过牌"]:
        current_type, current_priority, current_count = judge_card_type(current_cards)
        if current_type == CARD_TYPE_INVALID:
            return (False, "非法牌型，请重新选择！")
    else:
        # 过牌始终合法
        return (True, "")
    
    # 第二步：判断是否为首轮（上一轮无出牌），首轮合法牌型可直接出
    if not last_cards or last_type == "" or last_type == CARD_TYPE_PASS:
        return (True, "")
    
    # 第三步：提取当前牌关键信息
    current_type, current_priority, current_count = judge_card_type(current_cards)
    current_card_count = len(current_cards)
    
    # 规则1：王炸可压一切
    if current_type == CARD_TYPE_JOKER_BOMB:
        return (True, "")
    
    # 规则2：炸弹的压制逻辑（仅能被王炸、更大的炸弹压制）
    if last_type == CARD_TYPE_JOKER_BOMB:
        return (False, "上一轮是王炸，仅能出王炸压制！")
    
    if last_type == CARD_TYPE_BOMB:
        if current_type != CARD_TYPE_BOMB:
            return (False, "上一轮是炸弹，仅能出更大的炸弹或王炸压制！")
        else:
            if current_priority > last_priority:
                return (True, "")
            else:
                last_rank = get_card_rank(last_cards[0])
                return (False, f"炸弹大小不足，需大于{last_rank}！")
    
    # 规则3：普通牌型的压制逻辑
    normal_types = [
        CARD_TYPE_SINGLE, CARD_TYPE_PAIR, CARD_TYPE_SEQUENCE_PAIR,
        CARD_TYPE_SEQUENCE_SINGLE, CARD_TYPE_TRIPLE, CARD_TYPE_TRIPLE_ONE,
        CARD_TYPE_TRIPLE_PAIR, CARD_TYPE_PLANE_NO_WING, CARD_TYPE_PLANE_SINGLE_WING,
        CARD_TYPE_PLANE_PAIR_WING, CARD_TYPE_FOUR_TWO_SINGLE, CARD_TYPE_FOUR_TWO_PAIR
    ]
    
    if last_type in normal_types:
        # 3.1 炸弹可压所有普通牌型
        if current_type == CARD_TYPE_BOMB or current_type == CARD_TYPE_JOKER_BOMB:
            return (True, "")
        
        # 3.2 必须为同类型牌型
        if current_type != last_type:
            return (False, f"上一轮是{last_type}，需出同类型牌型或炸弹/王炸！")
        
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
            return (False, f"上一轮{tip}不符，需出相同{tip}的{last_type}或炸弹/王炸！")
        
        # 3.4 同类型同数量，比较核心优先级
        if current_priority > last_priority:
            return (True, "")
        else:
            # 优化提示信息
            if last_type in [CARD_TYPE_SEQUENCE_SINGLE, CARD_TYPE_SEQUENCE_PAIR,
                             CARD_TYPE_PLANE_NO_WING, CARD_TYPE_PLANE_SINGLE_WING,
                             CARD_TYPE_PLANE_PAIR_WING]:
                last_max_rank = max([get_card_rank(c) for c in last_cards],
                                    key=lambda r: RANK_PRIORITY[r])
                return (False, f"{last_type}大小不足，最大点数需大于{last_max_rank}！")
            else:
                last_rank = get_card_rank(last_cards[0])
                return (False, f"{last_type}大小不足，需大于{last_rank}！")
    
    # 其他未覆盖情况（默认非法）
    return (False, "无法压制上一轮牌型，请重新选择！")

def create_deck():
    """创建完整的54张扑克牌组"""
    deck = []
    for suit in SUITS:
        for rank in RANKS:
            deck.append(f"{suit}{rank}")
    deck.extend(JOKERS)
    return deck