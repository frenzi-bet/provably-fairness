
import math
import hmac
import hashlib
import sys
from typing import List
from enum import IntEnum
class Xorshift128Plus:
    def __init__(self, seed):
        # Limit the seed to a 64-bit integer.
        self.state0 = seed & 0xFFFFFFFFFFFFFFFF
        self.state1 = seed & 0xFFFFFFFFFFFFFFFF

    def next(self):
        s1 = self.state0
        s0 = self.state1
        self.state0 = s0
        s1 = (s1 ^ (s1 << 23)) & 0xFFFFFFFFFFFFFFFF
        s1 = (s1 ^ (s1 >> 17)) & 0xFFFFFFFFFFFFFFFF
        s1 = (s1 ^ s0) & 0xFFFFFFFFFFFFFFFF
        s1 = (s1 ^ (s0 >> 26)) & 0xFFFFFFFFFFFFFFFF
        self.state1 = s1
        # Limit the sum of state0 and state1 to 64 bits and convert it to a floating-point number in the range of [0, 1).
        return ((self.state0 + self.state1) & 0xFFFFFFFFFFFFFFFF) / 18446744073709551616.0  # 2^64

def generate_hmac_sha256(server_seed, client_seed):
    hmac_hash = hmac.new(server_seed.encode(), client_seed.encode(), hashlib.sha256)
    return hmac_hash.hexdigest()

def fisher_yates_shuffle(arr, seed):
    # Initialize the random number generator.
    rng = Xorshift128Plus(seed)  
    for i in range(len(arr) - 1, 0, -1):
        nn = rng.next()
        # Generate a random integer within the range of [0, i].
        j = math.floor(nn * (i + 1))  
        # Swap card.
        arr[i], arr[j] = arr[j], arr[i]  
    return arr

def get_seed_md5(seed):
    md5_hash = hashlib.md5()
    md5_hash.update(seed.encode('utf-8'))
    md5_result = md5_hash.hexdigest()
    return md5_result

def generate_random_array(server_seed, client_seed,  arr):
    # Generate an HMAC - SHA256 hash value as a seed.
    seed = int(generate_hmac_sha256(get_seed_md5(server_seed), f"{get_seed_md5(client_seed)}")[0:8], base=16)
    # Shuffle using the Fisher - Yates algorithm.
    shuffled_arr = fisher_yates_shuffle(arr, seed)
    return shuffled_arr

def init_cards():
    cards = []
    for num in range(0, 8):
        for x in range(0, 4):
            for y in range(0, 13):
                cardId = (x + 1) * 100 + (y + 1)
                cards.append(cardId)
    return cards
# A dict of playing cards corresponding to digital IDs.
cards_map = {
    101: "♦A", 102: "♦2", 103: "♦3", 104: "♦4", 105: "♦5", 106: "♦6", 107: "♦7", 108: "♦8",
    109: "♦9", 110: "♦10", 111: "♦J", 112: "♦Q", 113: "♦K",
    201: "♣A", 202: "♣2", 203: "♣3", 204: "♣4", 205: "♣5", 206: "♣6", 207: "♣7", 208: "♣8",
    209: "♣9", 210: "♣10", 211: "♣J", 212: "♣Q", 213: "♣K",
    301: "♥A", 302: "♥2", 303: "♥3", 304: "♥4", 305: "♥5", 306: "♥6", 307: "♥7", 308: "♥8",
    309: "♥9", 310: "♥10", 311: "♥J", 312: "♥Q", 313: "♥K",
    401: "♠A", 402: "♠2", 403: "♠3", 404: "♠4", 405: "♠5", 406: "♠6", 407: "♠7", 408: "♠8",
    409: "♠9", 410: "♠10", 411: "♠J", 412: "♠Q", 413: "♠K",
}

def print_cards(cards : List[int]):
    cards_str = ""
    for card in cards:
        card_str = cards_map[card] or ""
        cards_str = cards_str + card_str + " "
    return cards_str

# Get the points of the playing cards.
def get_cards_value(cards : List[int]):
    sum = 0
    for card in cards:
        v = card % 100
        # The points of 10, J, Q, and K are 0.
        if v >= 10:
            v = 0
        sum += v
    return sum % 10

class BaccaratSide(IntEnum):
    Banker = 1,
    Player = 2 

def get_result_str(result, special):
        result_str = ["", "Banker Win", "Player Win", "Tie"]
        res = result_str[result]
        if special == 7:
            res = " Dragon 7"
        if special == 8:
            res = " Panda 8"
        return res
def get_result(player_cards, banker_cards):
    result  = 3
    special = 0
    player_value = get_cards_value(player_cards)
    bank_value = get_cards_value(banker_cards)
    if bank_value > player_value:
        result = 1
        if bank_value == 7 and len(banker_cards) == 3:
            special = 7
    elif bank_value < player_value:
        result = 2
        if player_value == 8 and len(player_cards) == 3:
            special = 8
    return result, special

# Check whether it is necessary to draw additional cards.
def check_additional(card_side: BaccaratSide, player_cards, banker_cards):
    player_value = get_cards_value(player_cards)
    banker_value = get_cards_value(banker_cards)
    if len(player_cards) == 2 and len(banker_cards) == 2 and player_value in [8, 9] or banker_value in [8, 9]:
        return False
    if card_side == BaccaratSide.Player:
        if player_value <= 5:
            return True
    elif card_side == BaccaratSide.Banker:
        if banker_value <= 2:
            return True
        if banker_value >= 7:
            return False
        if len(player_cards) >= 3:
            player_three_value = get_cards_value([player_cards[2]])
            if banker_value == 3:
                return player_three_value != 8
            if banker_value == 4:
                return player_three_value >= 2 and player_three_value <= 7
            if banker_value == 5:
                return player_three_value >= 4 and player_three_value <= 7
            if banker_value == 6:
                return player_three_value >= 6 and player_three_value <= 7
        else:
            if banker_value <= 5:
                return True
    return False

def provably_fairness(client_seed:str, server_seed:str, nonce:int):
    if not client_seed or len(client_seed) != 8:
        print("The client seed must be an 8-character string.")
        return
    if not server_seed or len(server_seed) != 32:
        print("The server seed must be an 32-character string.")
        return
    if not nonce or nonce <= 0 or nonce > 104:
        print("The nonce must be in the range of 1 - 104. Note that a maximum of 104 hands of cards can be dealt from 8 decks of cards.")
        return
    print("Initialize the cards.")
    cards = init_cards()
    print("Shuffling the cards.")
    shuffled_cards = generate_random_array(server_seed, client_seed, cards)
    banker_cards = []
    player_cards = []
    while nonce > 0:
        banker_cards = []
        player_cards = []
        # dealing cards.
        if len(shuffled_cards) >= 4:
            player_cards.append(shuffled_cards.pop(0))
            banker_cards.append(shuffled_cards.pop(0))
            player_cards.append(shuffled_cards.pop(0))
            banker_cards.append(shuffled_cards.pop(0))
        else:
            print("Error. There aren't enough playing cards left.")
            break
        # draw additional cards
        if check_additional(BaccaratSide.Player, player_cards, banker_cards):
            if len(shuffled_cards) > 0:
                player_cards.append(shuffled_cards.pop(0))
            else:
                print("Error. There aren't enough playing cards left.")
                break
        if check_additional(BaccaratSide.Banker, player_cards, banker_cards):
            if len(shuffled_cards) > 0:
                banker_cards.append(shuffled_cards.pop(0))
            else:
                print("Error. There aren't enough playing cards left.")
                break
        # get result
        if nonce == 1:
            print(f"player cards:{print_cards(player_cards)}")
            print(f"banker cards:{print_cards(banker_cards)}")
            result, special = get_result(player_cards, banker_cards)
            result_str = get_result_str(result, special)
            print(f"resut:{result_str}")
            break
        nonce = nonce - 1


if __name__ == "__main__":
    args = sys.argv
    if len(args) >= 4:
        #Obtain parameters through the command line.
        client_seed = str(args[1])
        server_seed = str(args[2])
        nonce = int(args[3])
        provably_fairness(client_seed, server_seed, 1)
    else:
        #Write the parameters in the code.
        client_seed = "Your client seed"
        server_seed = "Your server seed"
        nonce = 1
        provably_fairness(client_seed, server_seed, 1)