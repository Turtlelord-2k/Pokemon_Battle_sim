import time
import numpy as np
import sys
import enum
import json
import math
import random

ATTACK = 0
SWITCH = 1

movejson = typesjson = pokemonjson = {}
string_1_attack = 'Its super effective!\n'
string_2_attack = 'Its not very effective...\n'

#Stat modification multiplier
stat_stage_multiplier = {-6: 0.25, -5: 0.285, -4: 0.33, -3: 0.4, -2: 0.5, -1: 0.66, 0: 1, 1: 1.5, 2: 2, 3: 2.5, 4: 3, 5: 3.5, 6: 4}
accuracy_stage_multiplier = {-6: 0.33, -5: 0.375, -4: 0.428, -3: 0.5, -2: 0.6, -1: 0.75, 0: 1, 1: 1.33, 2: 1.66, 3: 2, 4: 2.33, 5: 2.66, 6: 3}

#effects number of moves
recoil_moves_list = [49, 199, 254, 255, 263, 270]
weight_moves_list = [197,292]
heal_moves_list = [4, 348, 33, 133, 353]
sleep_moves_list = [2]
confusion_moves_list = [50, 200, 77, 268, 338]
flinch_moves_list = [32, 147, 151]
poison_moves_list = [3, 34, 67, 78, 203, 210]
burn_moves_list = [5, 126, 168, 201, 254, 274]
freeze_moves_list = [6, 261, 275]
paralysis_moves_list = [7, 68, 153, 263, 276]
stat_moves_attacker_list = [139, 140, 141, 183, 205, 219, 230, 277, 296, 335, 51, 52, 53, 54, 55, \
    285, 209, 212, 175, 323, 207, 161, 329, 110, 157, 12, 213, 317, 328, 278, 11, 309, 313, 322, 291]
stat_moves_defender_list = [21, 69, 70, 71, 72, 73, 272, 297, 331, 59, 361, 61, 63, 24, 167, 19, 20, 60, 24, 21, 119, 74]


class Status(enum.Enum):
    none = 0
    sleep = 1
    poison = 2
    paralysis = 3
    burn = 4
    freeze = 5
    bad_poison = 6

def convert(basestats, level=50):
    s = {
        "hp": int(((2 * basestats['hp'] + 100) * level / 100)+10),
        "attack": int(((2 * basestats['attack']) * level / 100)+5),
        "defense": int(((2 * basestats['defense']) * level / 100)+5),
        "spattack": int(((2 * basestats['spattack']) * level / 100)+5),
        "spdefense": int(((2 * basestats['spdefense']) * level / 100)+5),
        "speed": int(((2 * basestats['speed']) * level / 100)+5)
    }
    return s

#Pokemon1 using move_info on Pokemon2
#returns amount of HP damage Pokemon2 takes
def calculate_damage(Pokemon1, Pokemon2, move_info, move_effectiveness):
    critical = weather = burnstatus = other = stab = 1
    crit_chance = 0.035 #0.0625 pseudo random generator makes the default too high rate
    power = move_info['power']
    effect_number = move_info['effect']
    attack = Pokemon1.attack * stat_stage_multiplier[Pokemon1.attackstage]
    defense = Pokemon2.defense * stat_stage_multiplier[Pokemon2.defensestage]
    if move_info['damage_class'] == 'special':
        attack = Pokemon1.spattack * stat_stage_multiplier[Pokemon1.spattackstage]
        defense = Pokemon2.spdefense * stat_stage_multiplier[Pokemon2.spdefensestage]

    if Pokemon1.status == Status.burn and move_info['damage_class'] == 'physical':
        burnstatus = 0.5

    #####special move effects altering power########
    p1_hp_percentage = 100 * Pokemon1.curhealth/Pokemon1.health
    p2_hp_percentage = 100 * Pokemon2.curhealth/Pokemon2.health
    #flail/reversal
    if effect_number == 100:
        if p1_hp_percentage < 4.17:
            power = 200
        elif p1_hp_percentage < 10.42:
            power = 150
        elif p1_hp_percentage < 20.83:
            power = 100
        elif p1_hp_percentage < 35.42:
            power = 80
        elif p1_hp_percentage < 68.75:
            power = 40
        else:
            power = 20
    #acrobatics
    elif effect_number == 318:
        power *= 2
    #brine
    elif effect_number == 222 and p2_hp_percentage <= 50:
        power *= 2
    #sp.moves that target physical
    elif effect_number == 283:
        defense = Pokemon2.defense * stat_stage_multiplier[Pokemon2.defensestage]
    #weight-based moves
    elif effect_number in weight_moves_list:
        power = Pokemon1.calculate_weight_power(Pokemon2, effect_number)
    #endeavor
    elif effect_number == 190 and not(move_effectiveness == 0):
        return max(0, Pokemon2.curhealth - Pokemon1.curhealth)
    #dragon rage
    elif effect_number == 42 and not(move_effectiveness == 0):
        return 40
    #sonic boom
    elif effect_number == 131 and not(move_effectiveness == 0):
        return 20
    #seismic toss
    elif effect_number == 88 and not(move_effectiveness == 0):
        return Pokemon2.level
    #facade
    elif effect_number == 170 and not(Pokemon1.status == Status.none):
        power *= 2
    #foul play
    elif effect_number == 298:
        attack = Pokemon2.attack * stat_stage_multiplier[Pokemon2.attackstage]
    #hex
    elif effect_number == 311 and not(Pokemon2.status == Status.none):
        power *= 2
    #venoshock
    elif effect_number == 284 and (Pokemon2.status == Status.poison or Pokemon2.status == Status.bad_poison):
        power *= 2
    #stored power
    elif effect_number == 306:
        power += (max(0, Pokemon1.attackstage) + max(0, Pokemon1.spattackstage) + max(0, Pokemon1.defensestage) + max(0, Pokemon1.spdefensestage) \
            + max(0, Pokemon1.speedstage) + max(0, Pokemon1.accuracystage)) * 20
    #wake-up slap
    elif effect_number == 218 and Pokemon2.status == Status.sleep:
        Pokemon2.sleep_counter = 0
        Pokemon2.status = Status.none
        print(Pokemon2.name + " has woke up!")
        power *= 2
    #eruption/water spout
    elif effect_number == 191:
        power *= Pokemon1.curhealth/Pokemon1.health
    #recharge moves
    elif effect_number == 81:
        Pokemon1.recharge = move_info['id']
    #OHKO moves
    elif effect_number == 39 and not(move_effectiveness == 0):
        print("It's a one-hit KO!")
        return Pokemon2.curhealth

    if effect_number == 289: #100% critical hit moves
        crit_chance = 1
    elif effect_number == 44 or effect_number == 201 or effect_number == 210: #increased crit rate
        crit_chance = 0.125

    if random.random() <= crit_chance:
        print("A critical hit!")
        critical = 2

    if str(move_info['type']) in pokemonjson[Pokemon1.id]['types']:
        stab = 1.5


    if effect_number == 255: #struggle
        move_effectiveness = 1


    modifier = weather * critical * burnstatus * (random.randint(85,100)*0.01) * stab * move_effectiveness * other
    damage = (((22*power*attack/defense) / 50) + 2) * modifier

    return damage

# Slow text
def delay_print(s):
    for c in s:
        sys.stdout.write(c)
        sys.stdout.flush()
        time.sleep(0.05)

# Creation Pokemon
class Pokemon:
    def __init__(self, nameid, moves, level=50):
        # Guardar variables como atributos
        self.id = nameid
        self.level = level
        self.name = pokemonjson[nameid]['name']
        self.types = pokemonjson[nameid]['types']
        self.moves = moves
        basestats = pokemonjson[nameid]['stats']
        level50stats = convert(basestats, level)
        #set base stats
        self.attack = self.curattack = level50stats['attack']
        self.spattack = self.curspattack = level50stats['spattack']
        self.defense = self.curdefense = level50stats['defense']
        self.spdefense = self.curspdefense = level50stats['spdefense']
        self.speed = self.curspeed = level50stats['speed']
        self.health = self.curhealth = level50stats['hp']
        self.confusion = self.flinch = self.cursed = False
        self.recharge = self.charge = -1
        self.status = Status.none
        self.sleep_counter = self.confusion_counter = self.badpoison_counter = 0
        self.attackstage = self.defensestage = self.spattackstage = self.spdefensestage = self.speedstage = self.accuracystage = 0

        #might change up something to avoid this
        self.types[0] = str(self.types[0])
        if len(self.types) > 1:
            self.types[1] = str(self.types[1])

    def check_move_hit(self, move_used):
        randomnum = random.randint(1,100)*accuracy_stage_multiplier[self.accuracystage] #random from 1,100 * accuracy modifier
        if randomnum >= (100 - move_used['accuracy']):
            return True
        return False

    def check_faint(self): #checks if fainted and prints out faint statement if true
        if self.curhealth <= 0:
            print("..." + self.name + ' fainted.')
            return True

        return False

    #Applies stat changes depending on effect id on Pokemon:
    def change_stat_stage(self, move_effect):
        stat_string = ""
        if move_effect in [69, 183, 19]:
            self.attackstage = max(-6, self.attackstage - 1)
            stat_string += self.name + "'s attack fell!\n"
        if move_effect in [70, 183, 230, 335, 20, 309]:
            self.defensestage = max(-6, self.defensestage - 1)
            stat_string += self.name + "'s defense fell!\n"
        if move_effect in [72]:
            self.spattackstage = max(-6, self.spattackstage - 1)
            stat_string += self.name + "'s special attack fell!\n"
        if move_effect in [73, 230, 335, 309]:
            self.spdefensestage = max(-6, self.spdefensestage - 1)
            stat_string += self.name + "'s special defense fell!\n"
        if move_effect in [21, 71, 331, 335, 110]:
            self.speedstage = max(-6, self.speedstage - 1)
            stat_string += self.name + "'s speed fell!\n"
        if move_effect in [24, 74]:
            self.accuracystage = max(-6, self.accuracystage - 1)
            stat_string += self.name + "'s accuracy fell!\n"
        if move_effect in [59]:
            self.attackstage = max(-6, self.attackstage - 2)
            stat_string += self.name + "'s attack harshly fell!\n"
        if move_effect in [60]:
            self.defensestage = max(-6, self.defensestage - 2)
            stat_string += self.name + "'s defense harshly fell!\n"
        if move_effect in [205, 361]:
            self.spattackstage = max(-6, self.spattackstage - 2)
            stat_string += self.name + "'s special attack harshly fell!\n"
        if move_effect in [272, 297, 63]:
            self.spdefensestage = max(-6, self.spdefensestage - 2)
            stat_string += self.name + "'s special defense harshly fell!\n"
        if move_effect in [61]:
            self.speedstage = max(-6, self.speedstage - 2)
            stat_string += self.name + "'s speed harshly fell!\n"
        if move_effect in [140, 141, 209, 323, 110, 213, 317, 328, 278, 11, 313]:
            self.attackstage = min(6, self.attackstage + 1)
            stat_string += self.name + "'s attack rose!\n"
        if move_effect in [139, 141, 161, 207, 209, 323, 110, 12, 157]:
            self.defensestage = min(6, self.defensestage + 1)
            stat_string += self.name + "'s defense rose!\n"
        if move_effect in [277, 141, 212, 167, 317, 328, 291]:
            self.spattackstage = min(6, self.spattackstage + 1)
            stat_string += self.name + "'s special attack rose!\n"
        if move_effect in [141, 212, 175, 161, 207, 291]:
            self.spdefensestage = min(6, self.spdefensestage + 1)
            stat_string += self.name + "'s special defense rose!\n"
        if move_effect in [219, 296, 141, 213, 291]:
            self.speedstage = min(6, self.speedstage + 1)
            stat_string += self.name + "'s speed rose!\n"
        if move_effect in [323, 278]:
            self.accuracystage = min(6, self.accuracystage + 1)
            stat_string += self.name + "'s accuracy rose!\n"
        if move_effect in [51, 309, 119]:
            self.attackstage = min(6, self.attackstage + 2)
            stat_string += self.name + "'s attack rose sharply!\n"
        if move_effect in [52]:
            self.defensestage = min(6, self.defensestage + 2)
            stat_string += self.name + "'s defense rose sharply!\n"
        if move_effect in [54, 309]:
            self.spattackstage = min(6, self.spattackstage + 2)
            stat_string += self.name + "'s special attack rose sharply!\n"
        if move_effect in [55]:
            self.spdefensestage = min(6, self.spdefensestage + 2)
            stat_string += self.name + "'s special defense rose sharply!\n"
        if move_effect in [53, 285, 309, 313]:
            self.speedstage = min(6, self.speedstage + 2)
            stat_string += self.name + "'s speed rose sharply!\n"
        if move_effect in [329]:
            self.defensestage = min(6, self.defensestage + 3)
            stat_string += self.name + "'s defense rose drastically!\n"
        if move_effect in [322]:
            self.spattackstage = min(6, self.spattackstage + 3)
            stat_string += self.name + "'s special attack rose drastically!\n"


        print(stat_string)

    #Checks if specific status condition affects Pokemon. Returns True if status can be applied
    def check_status_affect(self, status_condition):
        if not(self.status == Status.none):
            return False
        if status_condition == Status.burn and '11' in self.types:
            return False
        if status_condition == Status.freeze and '15' in self.types:
            return False
        if status_condition == Status.paralysis and '5' in self.types:
            return False
        if status_condition == Status.poison and (('4' in self.types) or ('9' in self.types)):
            return False
        return True

    def get_status_string(self):
        if self.status == Status.paralysis:
            return "[PAR]"
        elif self.status == Status.freeze:
            return "[FRZ]"
        elif self.status == Status.burn:
            return "[BRN]"
        elif self.status == Status.poison or self.status == Status.bad_poison:
            return "[PSN]"
        elif self.status == Status.sleep:
            return "[SLP]"
        return ""

    def calculate_recoil_damage(self, damage, move_effect):
        hurt = 0
        if move_effect == 49 or move_effect == 255:
            hurt = math.floor(damage / 4)
        elif move_effect == 199 or move_effect == 254 or move_effect == 263:
            hurt = math.floor(damage / 3)
        elif move_effect == 270:
            hurt = math.floor(damage / 2)

        self.curhealth -= hurt
        print(self.name + " was hurt " + str(hurt) + "HP (" + str(round(100*hurt/self.health, 2)) + "%) by recoil!")

    def calculate_weight_power(self, Pokemon2, move_effect):
        pokemon1_weight = pokemonjson[self.id]['weight']
        pokemon2_weight = pokemonjson[Pokemon2.id]['weight']
        if move_effect == 197: #only depends defender weight
            if pokemon2_weight < 10:
                return 20
            elif pokemon2_weight < 25:
                return 40
            elif pokemon2_weight < 50:
                return 60
            elif pokemon2_weight < 100:
                return 80
            elif pokemon2_weight < 200:
                return 100
            else:
                return 200
        else:
            relative = pokemon2_weight / pokemon1_weight #move_effect == 292 relative weight
            if relative <= 0.20:
                return 120
            elif relative <= 0.25:
                return 100
            elif relative <= 33.34:
                return 80
            elif relative <= 0.5:
                return 60
            else:
                return 40

    def calculate_heal(self, damage, move_effect):
        healhp = -1
        if damage != -1: #damage is -1 in non damaging moves
            healhp = math.floor(damage * 0.5)
        if move_effect in [4, 353]:
            healhp = math.floor(damage * 0.75)
        else: #up to 50% of max HP
            healhp = math.floor(self.health * 0.5)
        healhp = min(self.health - self.curhealth, healhp) #can't go above max health
        if healhp == 0:
            return
        else:
            self.curhealth += healhp
            print(self.name + " healed " + str(healhp) + "HP (" + str(math.floor(100*healhp/self.health)) + "%)")

    def calculate_recoil_on_miss(self):
        recoil = min(math.floor(self.health/2), self.curhealth)
        self.curhealth -= recoil
        print(self.name + " kept on going and crashed for " + str(recoil) + "HP (" + str(100*recoil/self.health) + "%) recoil damage!")

    #apply status condition stuff end of turn
    def apply_status_damage(self):
        if self.status == Status.poison:
            print(self.name + " took damage from poison.")
            self.curhealth -= math.floor(self.health / 8)
        elif self.status == Status.bad_poison:
            print(self.name + " took damage from poison.")
            self.curhealth -= (math.floor(self.health / 16) * self.badpoison_counter)
            self.badpoison_counter += 1
        elif self.status == Status.burn:
            print(self.name + " took damage from burn.")
            self.curhealth -= math.floor(self.health / 16)
        if self.cursed:
            self.curhealth -= math.floor(self.health * 0.25)

    def apply_status_ailment(self, move_effect):
        if move_effect in burn_moves_list:
            return self.apply_burn()
        elif move_effect in poison_moves_list:
            return self.apply_poison(move_effect)
        elif move_effect in freeze_moves_list:
            return self.apply_freeze()
        elif move_effect in paralysis_moves_list:
            return self.apply_paralysis()
        elif move_effect in sleep_moves_list:
            return self.apply_sleep()
        elif move_effect in confusion_moves_list:
            return self.apply_confusion()
        elif move_effect == 37: #tri attack
            rnum = random.random()
            if rnum <= 0.33:
                return self.apply_burn()
            elif rnum <= 0.67:
                return self.apply_freeze()
            else:
                return self.apply_paralysis()
        return False

    def unapply_status_ailment(self):
        self.status = Status.none
        print(self.name + "'s status is restored")

    #applies paralysis and speed change; might need to apply speed change when pokemon exits and re-enters...
    def apply_paralysis(self):
        #can't be paralyzed if already affected by status condition or if ground type
        if self.check_status_affect(Status.paralysis):
            self.status = Status.paralysis
            self.curspeed = self.curspeed * 0.5
            print(self.name + " is paralyzed! It may not be able to move!")
            return True
        return False

    #unapplies paralysis/speed change
    def unapply_paralysis(self):
        self.status = Status.none
        self.curspeed = self.curspeed * 2

    def apply_sleep(self):
        if self.check_status_affect(Status.sleep):
            self.status = Status.sleep
            self.sleep_counter = random.randint(1,3)
            print(self.name + " has fallen asleep...")
            return True
        return False

    #both regular and bad poison
    def apply_poison(self, effect_num):
        if self.check_status_affect(Status.poison):
            if effect_num == 34:
                self.status = Status.bad_poison
                self.badpoison_counter = 1
                print(self.name + " is badly poisoned!")
            else:
                self.status = Status.poison
                print(self.name + " is poisoned!")
            return True
        return False

    def apply_freeze(self):
        if self.check_status_affect(Status.freeze):
            self.status = Status.freeze
            print(self.name + " is frozen!")
            return True
        return False

    def apply_burn(self):
        if self.check_status_affect(Status.burn):
            self.status = Status.burn
            print(self.name + " is burned!")
            return True
        return False

    def apply_confusion(self):
        if not(self.confusion):
            self.confusion = True
            self.confusion_counter = random.randint(2,5)
            print(self.name + " is confused!")
            return True
        return False

    def apply_curse(self, Pokemon2):
        self.curhealth -= math.floor(0.5 * self.health)
        Pokemon2.cursed = True
        print(self.name + " cut its own HP and laid a curse on " + Pokemon2.name)

    #Reset some modifiers when Pokemon is withdrawn
    def withdraw_pokemon(self):
        self.confusion = self.flinch = self.cursed = False
        self.recharge = self.charge = -1
        self.badpoison_counter = 1
        self.attackstage = self.defensestage = self.spattackstage = self.spdefensestage = \
            self.speedstage = self.accuracystage = 0

    #Status conditions / confusion may prevent pokemon from attacking
    def check_attack_status(self, move):
        if self.flinch:
            self.flinch = False
            print(self.name + " flinched!")
            return False
        if self.status == Status.sleep:
            if self.sleep_counter == 0:
                self.status = Status.none
                print(self.name + " has woke up!")
                return True
            print(self.name + " is still asleep")
            self.sleep_counter -= 1
            #Snore/Sleep Talk
            if move['id'] == 173 or move['id'] == 214:
                return True
            return False

        elif self.status == Status.paralysis:
            if random.random() < 0.25:
                print(self.name + " is paralyzed! It cannot move!")
                return False

        elif self.status == Status.freeze:
            if random.random() <= 0.20 or move['type'] == 10:
                print(self.name + " has defrosted!")
                return True
            print(self.name + " is frozen solid!")
            return False

        if self.confusion:
            if self.confusion_counter == 0:
                self.confusion = False
                print(self.name + " has snapped out of confusion!")
                return True
            print(self.name + " is confused!")
            self.confusion_counter -= 1
            #may hurt itself in confusion
            if random.random() <= 0.50:
                return True
            damage = math.floor((((22*40*self.curattack/self.curdefense) / 50) + 2) * (random.randint(85,100)*0.01))
            self.curhealth -= damage
            print(self.name + " has hurt itself in confusion! (" + str(damage) + "HP)")
            return False

        return True

    def attack_move(self, Pokemon2, index):
        #####self.attack(Pokemon2)
            move_used = movejson[self.moves[index-1]]
            print(self.name ,"used", move_used['name'])
            time.sleep(1)
            #move effect 18/79 are attacks that don't miss
            if not(self.check_move_hit(move_used)) and (move_used['damage_class'] != 'non-damaging') \
                and not(move_used['effect'] == 18) and not(move_used['effect'] == 79):
                print('The attack missed!')
                if move_used['effect'] == 46: #jump kicks
                    self.calculate_recoil_on_miss()

            elif (move_used['damage_class'] != 'non-damaging'):
                move_effectiveness = typesjson[str(move_used['type'])]['offense'][Pokemon2.types[0]]
                if len(Pokemon2.types) > 1: #compound effectiveness if target has 2 types
                    move_effectiveness *= typesjson[str(move_used['type'])]['offense'][Pokemon2.types[1]]

                #Multi-hit attacks
                num_hits = 1
                if move_used['effect'] in [45, 78]:
                    num_hits = 2
                elif move_used['effect'] == 30:
                    num_hits = [2,2,3,3,4,5][math.floor(random.randint(0,5))]
                # Determine damage taken
                damage = 0
                for i in range(num_hits):
                    damage += calculate_damage(self, Pokemon2, move_used, move_effectiveness)
                    Pokemon2.curhealth = math.floor(Pokemon2.curhealth - damage)
                    Pokemon2.curhealth = max(Pokemon2.curhealth, 0)
                time.sleep(.2)
                if (damage < 1):
                    if move_used['effect'] == 46: #jump kicks
                        self.calculate_recoil_on_miss()
                    print("Move had no effect...")
                    return
                else:
                    print("Did " + str(math.ceil(damage)) + "HP damage!")
                    if  move_effectiveness > 0 and move_effectiveness < 1:
                        delay_print(string_2_attack)
                    elif move_effectiveness > 1:
                        delay_print(string_1_attack)
                    if num_hits > 1:
                        print("Hit " + str(num_hits) + " times!\n")

                #recoil damage moves
                if int(move_used['effect']) in recoil_moves_list:
                    self.calculate_recoil_damage(damage, move_used['effect'])
                elif move_used['effect'] == 8:
                    self.curhealth = 0
                elif int(move_used['effect']) in heal_moves_list:
                    self.calculate_heal(damage, move_used['effect'])
                #Confusion
                if move_used['effect'] in confusion_moves_list:
                    if random.random()*100 < move_used['effect_chance']:
                        Pokemon2.apply_confusion()
                #flinch
                if move_used['effect'] in flinch_moves_list:
                    if random.random()*100 < move_used['effect_chance']:
                        Pokemon2.flinch = True
                #status effect moves (burn/poison/paralysis/freeze) or tri-attack
                if move_used['effect'] in (burn_moves_list + freeze_moves_list + poison_moves_list + paralysis_moves_list + [37]):
                    if random.random()*100 < move_used['effect_chance']:
                        Pokemon2.apply_status_ailment(move_used['effect'])
                #stat change moves (increase/decrease you/opponent)
                if move_used['effect'] in stat_moves_attacker_list:
                    if random.random()*100 < move_used['effect_chance']:
                        self.change_stat_stage(move_used['effect'])
                if move_used['effect'] in stat_moves_defender_list:
                    if random.random()*100 < move_used['effect_chance']:
                        Pokemon2.change_stat_stage(move_used['effect'])
                #fire type damaging moves defrost
                if move_used['type'] == 10 and Pokemon2.status == Status.freeze:
                    Pokemon2.status = Status.none
                    print(Pokemon2.name + " is defrosted!")

            elif (move_used['damage_class'] == 'non-damaging'):
                if move_used['id'] == 150: #SPLASH
                    print("But nothing happened!")
                    return
                if move_used['effect'] == 143: #belly drum
                    newhealth = max(0, math.floor(self.curhealth - (0.5*health)))
                    if newhealth != 0:
                        self.curhealth = newhealth
                        self.attackstage = 6
                        print(self.name + " maximized its attack!")
                    else:
                        print("But it failed!")
                        return
                elif move_used['effect'] in heal_moves_list:
                    self.calculate_heal(-1, move_used['effect'])
                #ghost type using curse
                if move_used['effect'] == 110 and (8 in self.types):
                    self.apply_curse(Pokemon2)
                #non-damaging stat moves (on attacker/defender)
                elif move_used['effect'] in stat_moves_attacker_list:
                    self.change_stat_stage(move_used['effect'])
                if move_used['effect'] in stat_moves_defender_list and self.check_move_hit(move_used):
                    Pokemon2.change_stat_stage(move_used['effect'])
                    #check swagger and flatter 119, 167
                    if move_used['effect'] in [119, 167]:
                        if not(Pokemon2.apply_confusion()):
                            print(Pokemon2.name + " is already confused!")
                #non-damaging status condition moves: 68
                if move_used['effect'] in (confusion_moves_list + burn_moves_list + freeze_moves_list + poison_moves_list + paralysis_moves_list + sleep_moves_list):
                    if self.check_move_hit(move_used):
                        if not(Pokemon2.apply_status_ailment(move_used['effect'])):
                            print(Pokemon2.name + " is not affected!")
                    else:
                        print("The attack missed!")

            return


    def fight(self, Pokemon2):
        # Permiso para que dos Pokémon combatan

        # Texto de la pelea
        print("-----POKEMONE BATTLE-----")
        print("Pokemon 1:", self.name)
        print("LVL/ 50")
        print("TYPE/", (typesjson[self.types[0]]['name']))
        print("HP/", self.health)
        print("ATTACK/", self.attack)
        print("DEFENSE/", self.defense)
        print("SP ATTACK/", self.spattack)
        print("SP DEFENSE/", self.spdefense)
        print("SPEED/", self.speed)
        print("\nVS")
        print("Pokemon 2:", Pokemon2.name)
        print("LVL/ 50\n")
        print("TYPE/", (typesjson[Pokemon2.types[0]]['name']))
        print("HP/", Pokemon2.health)
        print("ATTACK/", Pokemon2.attack)
        print("DEFENSE/", Pokemon2.defense)
        print("SP ATTACK/", Pokemon2.spattack)
        print("SP DEFENSE/", Pokemon2.spdefense)
        print("SPEED/", Pokemon2.speed, '\n')


        time.sleep(1)

        # Bucle while mientras tengan vida cada Pokémon
        turn_number = 0
        while (self.curhealth > 0) and (Pokemon2.curhealth > 0):
            #increment turn number; no Pokemon are flinched in the beginning
            turn_number += 1
            self.flinch = Pokemon2.flinch = False

            # Print turn and pokemon info
            print("_____TURN #" + str(turn_number) + "_____")
            print(self.name ,"health:", self.curhealth, self.get_status_string())
            print(Pokemon2.name ,"health:", Pokemon2.curhealth, Pokemon2.get_status_string())

            print("\nMoves for " + self.name )
            for i, x in enumerate(self.moves):
                print(i+1, movejson[x]['name'])
            index = int(input('Pick a move: '))

            print("\nMoves for " + Pokemon2.name)
            for i, x in enumerate(Pokemon2.moves):
                print(i+1, movejson[x]['name'])
            index2 = int(input('Pick a move: '))

            #if outspeed opponent (for equal priority) or your move has higher priority, you go first. Otherwise opponent goes first. 50/50 if speed tie.
            pokemon1speed = self.curspeed * stat_stage_multiplier[self.speedstage]
            pokemon2speed = Pokemon2.curspeed * stat_stage_multiplier[Pokemon2.speedstage]
            if ((movejson[self.moves[index-1]]['priority'] == movejson[Pokemon2.moves[index2-1]]['priority']) and ((pokemon1speed > pokemon2speed) \
                or (pokemon1speed == pokemon2speed and random.random() > .5))) \
                or (movejson[self.moves[index-1]]['priority'] > movejson[Pokemon2.moves[index2-1]]['priority']):

                if self.check_attack_status(movejson[self.moves[index-1]]):
                    self.attack_move(Pokemon2, index)
                if self.check_faint():
                    break
                if Pokemon2.check_faint():
                    break
                if Pokemon2.check_attack_status(movejson[Pokemon2.moves[index2-1]]):
                    Pokemon2.attack_move(self, index2)
                if Pokemon2.check_faint():
                    break
                if self.check_faint():
                    break
            else:
                if Pokemon2.check_attack_status(movejson[Pokemon2.moves[index2-1]]):
                    Pokemon2.attack_move(self, index2)
                if Pokemon2.check_faint():
                    break
                if self.check_faint():
                    break
                if self.check_attack_status(movejson[self.moves[index-1]]):
                    self.attack_move(Pokemon2, index)
                if self.check_faint():
                    break
                if Pokemon2.check_faint():
                    break


            ### status damage
            self.apply_status_damage()
            Pokemon2.apply_status_damage()
            if self.check_faint():
                break

            if Pokemon2.check_faint():
                break


class Trainer:
    #pokemons is array of pokemon team
    def __init__(self, pokemons, name, depth = 3):
        if not(len(pokemons) >= 6):
            print('Can only have team of up to 6 Pokemon')
        elif len(pokemons) == 0:
            print('Need pokemon in your team')

        self.name = name
        self.pokemons = pokemons
        self.alive_pokemon = []
        for p in self.pokemons:
            self.alive_pokemon.append(p)
        self.fainted_pokemon = []
        self.active_pokemon = pokemons[0]

        self.token = None                                   

        # self.is_ai = False
        self.is_ai = True
        self.choices = []
        self.win_value = 1000000
        self.max_play_depth = depth

        self.last_move = None

        # Trainer2 = Trainer2

    def is_turn(self):
        return self.token

    def set_turn(self, _token):
        self.token = _token

    #returns whether trainer has lost match
    def lost_match(self):
        if len(self.alive_pokemon) == 0:
            return True
        return False

    def getpromptstring(self):
        print("\n------" + self.name + "------  (%d/%d Pokemon left)" %(len(self.alive_pokemon), len(self.pokemons)))
        print("Active Pokemon: %s -- Health: %s/%s  %s" \
            %(self.active_pokemon.name, self.active_pokemon.curhealth, self.active_pokemon.health, self.active_pokemon.get_status_string()))
        if (len(self.alive_pokemon) > 1):
            return "Choose an Action (enter any other option to run away):\n1. Fight\n2. Switch Pokemon\nEnter choice: "
        return "Choose an Action (enter any other option to run away):\n1. Fight\nEnter choice: "

    #update trainer pokemon; active pokemon fainted
    def update_fainted_pokemon(self):
        self.fainted_pokemon.append(self.active_pokemon)
        for p in self.alive_pokemon:
            if p in self.fainted_pokemon:
                self.alive_pokemon.remove(p)

    #prompt to get index of pokemon to switch
    def get_switch_pokemon_choice(self):
        while True:
            print('Select a Pokemon to switch (enter number): ')
            for n in range(len(self.alive_pokemon)):
                p = self.alive_pokemon[n]
                active_string = ''
                if p == self.active_pokemon:
                    active_string = '\t[[Active Pokemon]]'
                print(str(n+1) + ': ' + p.name + '\t\t' + str(p.curhealth) + 'HP ' + p.get_status_string() + active_string)

            pindex = int(input('\nPokemon number: '))
            if self.alive_pokemon[pindex-1] == self.active_pokemon:
                print('\n------Cannot switch into current active pokemon------')
            else:
                return pindex

    def switch_pokemon(self, pindex, faintflag=0):
        p_selected = self.alive_pokemon[pindex-1]
        self.active_pokemon.withdraw_pokemon()
        if faintflag == 0:
            print('\n' + self.name + ' withdrew ' + self.active_pokemon.name + '! Sent out ' + p_selected.name + '!')
        else:
            print('\n' + self.name + ' sent out ' + p_selected.name + '!')
        self.active_pokemon = p_selected

    def get_possible_choices(self):
        possible_choices = [ ]

        for move in self.active_pokemon.moves:
            if move != None:
                possible_choices.append(move)

    ## self trainer active pokemon attack Trainer2's active pokemon
    def attack(self, Trainer2, index):
        switched_flag = 0
        if self.active_pokemon.recharge != -1:
            print(self.active_pokemon.name + " has to recharge!")
            self.active_pokemon.recharge = -1
            return switched_flag

        if self.active_pokemon.check_attack_status(movejson[self.active_pokemon.moves[index-1]]):
            self.active_pokemon.attack_move(Trainer2.active_pokemon, index)
            if self.active_pokemon.check_faint():
                self.update_fainted_pokemon()
                if self.lost_match():
                    print('Match lost placeholder')
                    quit()
                else:
                    i = self.get_switch_pokemon_choice()
                    self.switch_pokemon(i, 1)
            if Trainer2.active_pokemon.check_faint():
                Trainer2.update_fainted_pokemon()
                switched_flag = 1
                if Trainer2.lost_match():
                    print('Match lost placeholder')
                    quit()
                else:
                    i = Trainer2.get_switch_pokemon_choice()
                    Trainer2.switch_pokemon(i, 1)

        return switched_flag

    def fight(self, Trainer2):

        # Initial battle text
        print("-----POKEMONE BATTLE (LVL 50)-----")
        trainer1text = self.name + " ( "
        trainer2text = Trainer2.name + "  ( "
        for p in self.pokemons:
            trainer1text += p.name + " "
        for p2 in Trainer2.pokemons:
            trainer2text += p2.name + " "
        trainer1text += " )"
        trainer2text += " )"
        print(trainer1text)
        print("-----------------VS----------------")
        print(trainer2text)

        time.sleep(1)

        # Match loop
        turn_number = 0
        while not(self.lost_match()) or not(Trainer2.lost_match()):
            index1 = index2 = pindex1 = pindex2 = \
                player1choice = player2choice = -10 #index for move chosen/pokemon swapped reset

            #increment turn number; no Pokemon are flinched in the beginning
            turn_number += 1
            self.active_pokemon.flinch = Trainer2.active_pokemon.flinch = False

            # Print turn and pokemon info
            print("\n_____TURN #" + str(turn_number) + "_____")

            if self.active_pokemon.recharge == -1:
                #Trainer 1 makes their move
                player1choice = int(input(self.getpromptstring()))
                if player1choice == 1:
                    print("\nMoves for " + self.active_pokemon.name)
                    for i, x in enumerate(self.active_pokemon.moves):
                        print(i+1, movejson[x]['name'])
                    index1 = int(input('Pick a move: '))
                elif player1choice == 2 and len(self.alive_pokemon) > 1:
                    pindex1 = self.get_switch_pokemon_choice()
                else:
                    print(self.name + ' ran away...took the L')
                    exit()
            else:
                player1choice = 1
                index1 = 1

            if Trainer2.active_pokemon.recharge == -1:
                #Trainer 2 makes their move
                player2choice = int(input(Trainer2.getpromptstring()))
                if player2choice == 1:
                    print("\nMoves for " + Trainer2.active_pokemon.name)
                    for i, x in enumerate(Trainer2.active_pokemon.moves):
                        print(i+1, movejson[x]['name'])
                    index2 = int(input('Pick a move: '))
                elif player2choice == 2 and len(Trainer2.alive_pokemon) > 1:
                    pindex2 = Trainer2.get_switch_pokemon_choice()
                else:
                    print(Trainer2.name + ' ran away...took the L')
                    exit()
            else:
                player2choice = 1
                index2 = 1

            if player1choice == 2 and player2choice == 2: #both players switch out
                self.switch_pokemon(pindex1)
                Trainer2.switch_pokemon(pindex2)
            elif player1choice == 2: #only player2 attacks
                self.switch_pokemon(pindex1)
                Trainer2.attack(self, index2)
            elif player2choice == 2: #player1 attacks
                Trainer2.switch_pokemon(pindex2)
                self.attack(Trainer2, index1)
            else: #both attacks
                #if outspeed opponent (for equal priority) or your move has higher priority, you go first. Otherwise opponent goes first. 50/50 if speed tie.
                pokemon1speed = self.active_pokemon.curspeed * stat_stage_multiplier[self.active_pokemon.speedstage]
                pokemon2speed = Trainer2.active_pokemon.curspeed * stat_stage_multiplier[Trainer2.active_pokemon.speedstage]
                if ((movejson[self.active_pokemon.moves[index1-1]]['priority'] == movejson[Trainer2.active_pokemon.moves[index2-1]]['priority']) \
                    and ((pokemon1speed > pokemon2speed) or (pokemon1speed == pokemon2speed and random.random() > .5))) \
                    or (movejson[self.active_pokemon.moves[index1-1]]['priority'] > movejson[Trainer2.active_pokemon.moves[index2-1]]['priority']):
                    #self trainer attacks first; if it kills, then trainer2 can't attack
                    switch_flag = self.attack(Trainer2, index1)
                    if switch_flag == 0:
                        Trainer2.attack(self, index2)
                else:
                    #trainer2 attacks first
                    switch_flag = Trainer2.attack(self, index2)
                    if switch_flag == 0:
                        self.attack(Trainer2, index1)

            ### status damage
            self.active_pokemon.apply_status_damage()
            Trainer2.active_pokemon.apply_status_damage()

            if self.active_pokemon.check_faint():
                self.update_fainted_pokemon()
                if self.lost_match():
                    print('Match lost placeholder')
                    quit()
                else:
                    i = self.get_switch_pokemon_choice()
                    self.switch_pokemon(i, 1)
            if Trainer2.active_pokemon.check_faint():
                Trainer2.update_fainted_pokemon()
                if Trainer2.lost_match():
                    print('Match lost placeholder')
                    quit()
                else:
                    i = Trainer2.get_switch_pokemon_choice()
                    Trainer2.switch_pokemon(i, 1)


    def greedyattack(self, Trainer2, index):
        switched_flag = 0
        if self.active_pokemon.recharge != -1:
            print(self.active_pokemon.name + " has to recharge!")
            self.active_pokemon.recharge = -1
            return switched_flag

        if self.active_pokemon.check_attack_status(movejson[self.active_pokemon.moves[index-1]]):
            self.active_pokemon.attack_move(Trainer2.active_pokemon, index)
            if self.active_pokemon.check_faint():
                self.update_fainted_pokemon()
                if self.lost_match():
                    print('Match lost placeholder')
                    quit()
                else:
                    i = self.get_switch_pokemon_choice()
                    self.switch_pokemon(i, 1)
            if Trainer2.active_pokemon.check_faint():
                Trainer2.update_fainted_pokemon()
                switched_flag = 1
                if Trainer2.lost_match():
                    print('Match lost placeholder')
                    quit()
                else:
                    # Always 1 for bot
                    i = 1
                    Trainer2.switch_pokemon(i, 1)

        return switched_flag


    def greedyfight(self, Trainer2):

        # Initial battle text
        print("-----POKEMONE BATTLE (LVL 50)-----")
        trainer1text = self.name + " ( "
        trainer2text = Trainer2.name + "  ( "
        for p in self.pokemons:
            trainer1text += p.name + " "
        for p2 in Trainer2.pokemons:
            trainer2text += p2.name + " "
        trainer1text += " )"
        trainer2text += " )"
        print(trainer1text)
        print("-----------------VS----------------")
        print(trainer2text)

        time.sleep(1)

        # Match loop
        turn_number = 0
        while not(self.lost_match()) or not(Trainer2.lost_match()):
            index1 = index2 = pindex1 = pindex2 = \
                player1choice = player2choice = -10 #index for move chosen/pokemon swapped reset

            #increment turn number; no Pokemon are flinched in the beginning
            turn_number += 1
            self.active_pokemon.flinch = Trainer2.active_pokemon.flinch = False

            # Print turn and pokemon info
            print("\n_____TURN #" + str(turn_number) + "_____")

            if self.active_pokemon.recharge == -1:
                #Trainer 1 makes their move
                player1choice = int(input(self.getpromptstring()))
                if player1choice == 1:
                    print("\nMoves for " + self.active_pokemon.name)
                    for i, x in enumerate(self.active_pokemon.moves):
                        print(i+1, movejson[x]['name'])
                    index1 = int(input('Pick a move: '))
                elif player1choice == 2 and len(self.alive_pokemon) > 1:
                    pindex1 = self.get_switch_pokemon_choice()
                else:
                    print(self.name + ' ran away...took the L')
                    exit()
            else:
                player1choice = 1
                index1 = 1

            if Trainer2.active_pokemon.recharge == -1:
                #Trainer 2 makes their move
                print("Bot Chooses Action to Fight")
                player2choice = 1
                if player2choice == 1:
                    print("\nMoves for " + Trainer2.active_pokemon.name)
                    for i, x in enumerate(Trainer2.active_pokemon.moves):
                        print(i+1, movejson[x]['name'])

                    maxIndex = 1
                    move_used = movejson[Trainer2.active_pokemon.moves[i-1]]
                    maxpower = move_used['power']
                    for i in range(2, 5):
                        move_used = movejson[Trainer2.active_pokemon.moves[i-1]]
                        power = move_used['power']
                        if power > maxpower:
                            maxIndex = i
                            maxpower = power
                    index2 = maxIndex
                    print(f'Picking The GreedyAttack move: {index2}')
                elif player2choice == 2 and len(Trainer2.alive_pokemon) > 1:
                    # 1 to be default for Bot
                    # pindex2 = Trainer2.get_switch_pokemon_choice()
                    pindex2 = 1
                else:
                    print(Trainer2.name + ' ran away...took the L')
                    exit()
            else:
                player2choice = 1
                index2 = 1

            if player1choice == 2 and player2choice == 2: #both players switch out
                self.switch_pokemon(pindex1)
                Trainer2.switch_pokemon(pindex2)
            elif player1choice == 2: #only player2 attacks
                self.switch_pokemon(pindex1)
                Trainer2.greedyattack(self, index2)
            elif player2choice == 2: #player1 attacks
                Trainer2.switch_pokemon(pindex2)
                self.greedyattack(Trainer2, index1)
            else: #both attacks
                #if outspeed opponent (for equal priority) or your move has higher priority, you go first. Otherwise opponent goes first. 50/50 if speed tie.
                pokemon1speed = self.active_pokemon.curspeed * stat_stage_multiplier[self.active_pokemon.speedstage]
                pokemon2speed = Trainer2.active_pokemon.curspeed * stat_stage_multiplier[Trainer2.active_pokemon.speedstage]
                if ((movejson[self.active_pokemon.moves[index1-1]]['priority'] == movejson[Trainer2.active_pokemon.moves[index2-1]]['priority']) \
                    and ((pokemon1speed > pokemon2speed) or (pokemon1speed == pokemon2speed and random.random() > .5))) \
                    or (movejson[self.active_pokemon.moves[index1-1]]['priority'] > movejson[Trainer2.active_pokemon.moves[index2-1]]['priority']):
                    #self trainer attacks first; if it kills, then trainer2 can't attack
                    switch_flag = self.attack(Trainer2, index1)
                    if switch_flag == 0:
                        Trainer2.greedyattack(self, index2)
                else:
                    #trainer2 attacks first
                    switch_flag = Trainer2.attack(self, index2)
                    if switch_flag == 0:
                        self.greedyattack(Trainer2, index1)

            ### status damage
            self.active_pokemon.apply_status_damage()
            Trainer2.active_pokemon.apply_status_damage()

            if self.active_pokemon.check_faint():
                self.update_fainted_pokemon()
                if self.lost_match():
                    print('Match lost placeholder')
                    quit()
                else:
                    i = self.get_switch_pokemon_choice()
                    self.switch_pokemon(i, 1)
            if Trainer2.active_pokemon.check_faint():
                Trainer2.update_fainted_pokemon()
                if Trainer2.lost_match():
                    print('Match lost placeholder')
                    quit()
                else:
                    # 1 to be default for Bot
                    # i = Trainer2.get_switch_pokemon_choice()
                    i = 1
                    Trainer2.switch_pokemon(i, 1)

    def smartgreedyattack(self, Trainer2, index):
        switched_flag = 0
        if self.active_pokemon.recharge != -1:
            print(self.active_pokemon.name + " has to recharge!")
            self.active_pokemon.recharge = -1
            return switched_flag

        if self.active_pokemon.check_attack_status(movejson[self.active_pokemon.moves[index-1]]):
            self.active_pokemon.attack_move(Trainer2.active_pokemon, index)
            if self.active_pokemon.check_faint():
                self.update_fainted_pokemon()
                if self.lost_match():
                    print('Match lost placeholder')
                    quit()
                else:
                    i = self.get_switch_pokemon_choice()
                    self.switch_pokemon(i, 1)
            if Trainer2.active_pokemon.check_faint():
                Trainer2.update_fainted_pokemon()
                switched_flag = 1
                if Trainer2.lost_match():
                    print('Match lost placeholder')
                    quit()
                else:
                    # Always 1 for bot
                    i = 1
                    Trainer2.switch_pokemon(i, 1)

        return switched_flag


    def smartgreedyfight(self, Trainer2):

        # Initial battle text
        print("-----POKEMONE BATTLE (LVL 50)-----")
        trainer1text = self.name + " ( "
        trainer2text = Trainer2.name + "  ( "
        for p in self.pokemons:
            trainer1text += p.name + " "
        for p2 in Trainer2.pokemons:
            trainer2text += p2.name + " "
        trainer1text += " )"
        trainer2text += " )"
        print(trainer1text)
        print("-----------------VS----------------")
        print(trainer2text)

        time.sleep(1)

        # Match loop
        turn_number = 0
        while not(self.lost_match()) or not(Trainer2.lost_match()):
            index1 = index2 = pindex1 = pindex2 = \
                player1choice = player2choice = -10 #index for move chosen/pokemon swapped reset

            #increment turn number; no Pokemon are flinched in the beginning
            turn_number += 1
            self.active_pokemon.flinch = Trainer2.active_pokemon.flinch = False

            # Print turn and pokemon info
            print("\n_____TURN #" + str(turn_number) + "_____")

            if self.active_pokemon.recharge == -1:
                #Trainer 1 makes their move
                player1choice = int(input(self.getpromptstring()))
                if player1choice == 1:
                    print("\nMoves for " + self.active_pokemon.name)
                    for i, x in enumerate(self.active_pokemon.moves):
                        print(i+1, movejson[x]['name'])
                    index1 = int(input('Pick a move: '))
                elif player1choice == 2 and len(self.alive_pokemon) > 1:
                    pindex1 = self.get_switch_pokemon_choice()
                else:
                    print(self.name + ' ran away...took the L')
                    exit()
            else:
                player1choice = 1
                index1 = 1

            if Trainer2.active_pokemon.recharge == -1:
                #Trainer 2 makes their move
                print("Bot Chooses Action to Fight")
                player2choice = 1
                if player2choice == 1:
                    print("\nMoves for " + Trainer2.active_pokemon.name)
                    for i, x in enumerate(Trainer2.active_pokemon.moves):
                        print(i+1, movejson[x]['name'])

                    maxIndex = 1
                    move_used = movejson[Trainer2.active_pokemon.moves[maxIndex-1]]
                    move_effectiveness1 = typesjson[str(move_used['type'])]['offense'][self.active_pokemon.types[0]]
                    if len(self.active_pokemon.types) > 1: #compound effectiveness if target has 2 types
                        move_effectiveness1 *= typesjson[str(move_used['type'])]['offense'][self.active_pokemon.types[1]]
                    maxdamage = calculate_damage(Trainer2.active_pokemon, self.active_pokemon, move_used, move_effectiveness1)
                    for i in range(2, 5):
                        move_used = movejson[Trainer2.active_pokemon.moves[i-1]]
                        move_effectiveness1 = typesjson[str(move_used['type'])]['offense'][self.active_pokemon.types[0]]
                        if len(self.active_pokemon.types) > 1: #compound effectiveness if target has 2 types
                            move_effectiveness1 *= typesjson[str(move_used['type'])]['offense'][self.active_pokemon.types[1]]
                        damagee = calculate_damage(Trainer2.active_pokemon,  self.active_pokemon, move_used, move_effectiveness1)
                        if damagee > maxdamage:
                            maxIndex = i
                            maxdamage = damagee
                    index2 = maxIndex
                    print(f'Picking The SmartGreedy move: {index2}')
                elif player2choice == 2 and len(Trainer2.alive_pokemon) > 1:
                    # 1 to be default for Bot
                    # pindex2 = Trainer2.get_switch_pokemon_choice()
                    pindex2 = 1
                else:
                    print(Trainer2.name + ' ran away...took the L')
                    exit()
            else:
                player2choice = 1
                index2 = 1

            if player1choice == 2 and player2choice == 2: #both players switch out
                self.switch_pokemon(pindex1)
                Trainer2.switch_pokemon(pindex2)
            elif player1choice == 2: #only player2 attacks
                self.switch_pokemon(pindex1)
                Trainer2.smartgreedyattack(self, index2)
            elif player2choice == 2: #player1 attacks
                Trainer2.switch_pokemon(pindex2)
                self.smartgreedyattack(Trainer2, index1)
            else: #both attacks
                #if outspeed opponent (for equal priority) or your move has higher priority, you go first. Otherwise opponent goes first. 50/50 if speed tie.
                pokemon1speed = self.active_pokemon.curspeed * stat_stage_multiplier[self.active_pokemon.speedstage]
                pokemon2speed = Trainer2.active_pokemon.curspeed * stat_stage_multiplier[Trainer2.active_pokemon.speedstage]
                if ((movejson[self.active_pokemon.moves[index1-1]]['priority'] == movejson[Trainer2.active_pokemon.moves[index2-1]]['priority']) \
                    and ((pokemon1speed > pokemon2speed) or (pokemon1speed == pokemon2speed and random.random() > .5))) \
                    or (movejson[self.active_pokemon.moves[index1-1]]['priority'] > movejson[Trainer2.active_pokemon.moves[index2-1]]['priority']):
                    #self trainer attacks first; if it kills, then trainer2 can't attack
                    switch_flag = self.attack(Trainer2, index1)
                    if switch_flag == 0:
                        Trainer2.smartgreedyattack(self, index2)
                else:
                    #trainer2 attacks first
                    switch_flag = Trainer2.attack(self, index2)
                    if switch_flag == 0:
                        self.smartgreedyattack(Trainer2, index1)

            ### status damage
            self.active_pokemon.apply_status_damage()
            Trainer2.active_pokemon.apply_status_damage()

            if self.active_pokemon.check_faint():
                self.update_fainted_pokemon()
                if self.lost_match():
                    print('Match lost placeholder')
                    quit()
                else:
                    i = self.get_switch_pokemon_choice()
                    self.switch_pokemon(i, 1)
            if Trainer2.active_pokemon.check_faint():
                Trainer2.update_fainted_pokemon()
                if Trainer2.lost_match():
                    print('Match lost placeholder')
                    quit()
                else:
                    # 1 to be default for Bot
                    # i = Trainer2.get_switch_pokemon_choice()
                    i = 1
                    Trainer2.switch_pokemon(i, 1)


    def verify_fainted_switch(self):
        if self.lost_match() == False:
            if self.active_pokemon.check_faint() == True:
                self.update_fainted_pokemon()
                i = 0
                self.switch_pokemon(0, 1)
        

    def evaluate(self, move, Trainer2):        
        # self vars
        s_hp = 0
        s_hp_full = 0
        s_stats = 0
        s_status = 0
        s_fainted = 0

        for pkmn in self.pokemons:
            s_hp += pkmn.curhealth
            s_hp_full += pkmn.health
            s_stats += pkmn.attack + pkmn.defense + pkmn.spattack + pkmn.spdefense + pkmn.speed

            if pkmn.status != None and pkmn.check_faint() == False:
                s_status += 1

            if pkmn.check_faint() != False:
                s_fainted += 1

        t_hp = 0
        t_hp_full = 0
        t_stats = 0
        t_status = 0
        t_fainted = 0

        for pkmn in Trainer2.pokemons:
            t_hp += pkmn.curhealth
            t_hp_full += pkmn.health
            t_stats += pkmn.attack + pkmn.defense + pkmn.spattack + pkmn.spdefense + pkmn.speed

            if pkmn.status != None and pkmn.check_faint() == False:
                t_status += 1

            if pkmn.check_faint() != False:
                t_fainted += 1
        
        hp_diff = (s_hp_full - t_hp_full) - (s_hp - t_hp)
        status_diff = t_status - s_status
        stats_diff = s_stats - t_stats
        fainted_diff = t_fainted - s_fainted
        # move_effectiveness = movejson[move]['type']
        move_used = movejson[move]
        move_effectiveness1 = typesjson[str(move_used['type'])]['offense'][self.active_pokemon.types[0]]
        if len(self.active_pokemon.types) > 1: #compound effectiveness if target has 2 types
            move_effectiveness1 *= typesjson[str(move_used['type'])]['offense'][self.active_pokemon.types[1]]
        # move_damage = self.in_battle.calculate_damage(move, Trainer2.in_battle)
        move_damage = calculate_damage(self.active_pokemon, Trainer2.active_pokemon, move_used, move_effectiveness1)

        print('hp_diff:', hp_diff)
        print('status_diff:', status_diff)
        print('stats_diff:', stats_diff)
        print('fainted_diff:', fainted_diff)
        print('possible move:', movejson[str(move)]['name'])
        print('possible damage:', move_damage)

        value = hp_diff * .35 + move_damage * .35 + status_diff * 100 * .25 + stats_diff * 100 * .05 + fainted_diff * 100

        if move == self.last_move:
            value -= 100

        # type1 = pkmn_types.get_effectiveness(move.typing, Trainer2.in_battle.typing[0])
        type1 = typesjson[Trainer2.active_pokemon.types[0]]['defense'][self.active_pokemon.types[0]]
        type2 = 1
        type3 = 1
        type4 = 1

        if len(self.active_pokemon.types) == 2:
            type2 = typesjson[Trainer2.active_pokemon.types[0]]['defense'][self.active_pokemon.types[1]]
            if len(Trainer2.active_pokemon.types) == 2:
                type3 = typesjson[Trainer2.active_pokemon.types[1]]['defense'][self.active_pokemon.types[0]]
                type4 = typesjson[Trainer2.active_pokemon.types[1]]['defense'][self.active_pokemon.types[1]]

        # effectiveness bonus/malus
        if type1 * type2 * type3 * type4 > 4:
            value += 100
        elif type1 * type2 * type3 * type4 > 1 and type1 * type2 * type3 * type4 <= 4:
            value += 50
        elif type1 * type2 * type3 * type4 > 0.25 and type1 * type2 * type3 * type4 <= 1:
            value -= 50
        elif type1 * type2 * type3 * type4 <= 0.25:
            value -= 100        

        print('value: {value}\n'.format(value = value))

        return value       

    def get_choice(self, Trainer2):
        self.verify_fainted_switch()
        choosen_action = None
        while choosen_action == None:
            # possible_choices = self.get_possible_choices()
            print("\nMoves for " + self.active_pokemon.name)
            for i, x in enumerate(self.active_pokemon.moves):
                print(i+1, movejson[x]['name'])

            # if len(possible_choices) >= 1:
            best_action = self.active_pokemon.moves[0]
            best_val = -float('inf')
            for action in self.active_pokemon.moves:
                val = self.minimax(self.max_play_depth, action, True, Trainer2)
                if val >= best_val:
                    best_action = action
                    best_val = val
                
                choosen_action = best_action
                self.last_move = choosen_action
                print(choosen_action)
        
                
    
    def minimax(self, depth, action, is_maximizing, Trainer2):
        print('\n--- NODE DEPTH: {depth} ---'.format(depth = depth))
        if self.lost_match() or Trainer2.lost_match():
            if self.lost_match():
                return -self.win_val
            else:
                return self.win_val
        elif depth == 0:
            return self.evaluate(action, Trainer2)

        if is_maximizing:
            best_val = -float('inf')
            for move in self.active_pokemon.moves:
                val = self.minimax(depth - 1, move, False, Trainer2)
                best_val = max(best_val, val)
            return best_val
        else:
            best_val = float('inf')
            for move in Trainer2.active_pokemon.moves:
                val = self.minimax(depth - 1, move, True, Trainer2)
                best_val = min(best_val, val)
            return best_val
        
    def minimaxattack(self, Trainer2, index):
        switched_flag = 0
        if self.active_pokemon.recharge != -1:
            print(self.active_pokemon.name + " has to recharge!")
            self.active_pokemon.recharge = -1
            return switched_flag

        if self.active_pokemon.check_attack_status(movejson[self.active_pokemon.moves[index-1]]):
            self.active_pokemon.attack_move(Trainer2.active_pokemon, index)
            if self.active_pokemon.check_faint():
                self.update_fainted_pokemon()
                if self.lost_match():
                    print('Match lost placeholder')
                    quit()
                else:
                    i = self.get_switch_pokemon_choice()
                    self.switch_pokemon(i, 1)
            if Trainer2.active_pokemon.check_faint():
                Trainer2.update_fainted_pokemon()
                switched_flag = 1
                if Trainer2.lost_match():
                    print('Match lost placeholder')
                    quit()
                else:
                    # Always 1 for bot
                    i = 1
                    Trainer2.switch_pokemon(i, 1)

        return switched_flag
    
    def minimaxfight(self, Trainer2):

        # Initial battle text
        print("-----POKEMONE BATTLE (LVL 50)-----")
        trainer1text = self.name + " ( "
        trainer2text = Trainer2.name + "  ( "
        for p in self.pokemons:
            trainer1text += p.name + " "
        for p2 in Trainer2.pokemons:
            trainer2text += p2.name + " "
        trainer1text += " )"
        trainer2text += " )"
        print(trainer1text)
        print("-----------------VS----------------")
        print(trainer2text)

        time.sleep(1)

        turn_number = 0
        while not(self.lost_match()) or not(Trainer2.lost_match()):
            index1 = index2 = pindex1 = pindex2 = \
                player1choice = -10
            player2choice = 1
                
            turn_number += 1
            self.active_pokemon.flinch = Trainer2.active_pokemon.flinch = False

            if self.active_pokemon.recharge == -1:
                #Trainer 1 makes their move
                player1choice = int(input(self.getpromptstring()))
                if player1choice == 1:
                    print("\nMoves for " + self.active_pokemon.name)
                    for i, x in enumerate(self.active_pokemon.moves):
                        print(i+1, movejson[x]['name'])
                    index1 = int(input('Pick a move: '))
                elif player1choice == 2 and len(self.alive_pokemon) > 1:
                    pindex1 = self.get_switch_pokemon_choice()
                else:
                    print(self.name + ' ran away...took the L')
                    exit()
            else:
                player1choice = 1
                index1 = 1

            if Trainer2.active_pokemon.recharge == -1:
                #Trainer 2 makes their move
                if player2choice == 1:
                    print("Bot Chooses Action to Fight")
                    Trainer2.get_choice(self)
                    index2 = Trainer2.active_pokemon.moves.index(Trainer2.last_move)
                elif player2choice == 2 and len(Trainer2.alive_pokemon) > 1:
                    # 1 to be default for Bot
                    # pindex2 = Trainer2.get_switch_pokemon_choice()
                    pindex2 = 1
                else:
                    print(Trainer2.name + ' ran away...took the L')
                    exit()
            else:
                player2choice = 1
                index2 = 1

            if player1choice == 2 and player2choice == 2: #both players switch out
                self.switch_pokemon(pindex1)
                Trainer2.switch_pokemon(pindex2)
            elif player1choice == 2: #only player2 attacks
                self.switch_pokemon(pindex1)
                Trainer2.minimaxattack(self, index2)
            elif player2choice == 2: #player1 attacks
                Trainer2.switch_pokemon(pindex2)
                self.minimaxattack(Trainer2, index1)
            else: #both attacks
                #if outspeed opponent (for equal priority) or your move has higher priority, you go first. Otherwise opponent goes first. 50/50 if speed tie.
                pokemon1speed = self.active_pokemon.curspeed * stat_stage_multiplier[self.active_pokemon.speedstage]
                pokemon2speed = Trainer2.active_pokemon.curspeed * stat_stage_multiplier[Trainer2.active_pokemon.speedstage]
                if ((movejson[self.active_pokemon.moves[index1-1]]['priority'] == movejson[Trainer2.active_pokemon.moves[index2-1]]['priority']) \
                    and ((pokemon1speed > pokemon2speed) or (pokemon1speed == pokemon2speed and random.random() > .5))) \
                    or (movejson[self.active_pokemon.moves[index1-1]]['priority'] > movejson[Trainer2.active_pokemon.moves[index2-1]]['priority']):
                    #self trainer attacks first; if it kills, then trainer2 can't attack
                    switch_flag = self.attack(Trainer2, index1)
                    if switch_flag == 0:
                        Trainer2.minimaxattack(self, index2)
                else:
                    #trainer2 attacks first
                    switch_flag = Trainer2.attack(self, index2)
                    if switch_flag == 0:
                        self.minimaxattack(Trainer2, index1)

            ### status damage
            self.active_pokemon.apply_status_damage()
            Trainer2.active_pokemon.apply_status_damage()

            if self.active_pokemon.check_faint():
                self.update_fainted_pokemon()
                if self.lost_match():
                    print('Match lost placeholder')
                    quit()
                else:
                    i = self.get_switch_pokemon_choice()
                    self.switch_pokemon(i, 1)
            if Trainer2.active_pokemon.check_faint():
                Trainer2.verify_fainted_switch()
            if Trainer2.lost_match():
                print('Match lost placeholder')
                quit()


if __name__ == '__main__':
    with open('moves.json') as json_file:
        movejson = json.load(json_file)

    with open('types.json') as json_file:
        typesjson = json.load(json_file)

    with open('pokemon.json') as json_file:
        pokemonjson = json.load(json_file)


    # Sample 1.0 --- Sample Pokemon to use (damaging moves only for now)
    Bulbasaur = Pokemon('1', ['22', '75', '33', '73'])
    Ivysaur = Pokemon('2', ['22', '75', '331', '73'])
    Venusaur = Pokemon('3', ['188', '202', '34', '89'])
    Charmander = Pokemon('4', ['52', '10', '33', '411'])
    Charmeleon = Pokemon('5', ['52', '10', '53', '7'])
    Charizard = Pokemon('6', ['89', '394', '337', '411'])
    Squirtle = Pokemon('7', ['61', '33', '29', '57'])
    Wartortle = Pokemon('8', ['61', '55', '29', '57'])
    Blastoise = Pokemon('9', ['399', '396', '58', '56'])

    Zubat = Pokemon('41', ['44', '305', '17', '141'])
    Gengar = Pokemon('94', ['399', '247', '85', '412'])
    Pikachu = Pokemon('25', ['344', '98', '231', '435'])
    Pidgeot = Pokemon('18', ['542', '257', '211', '98'])
    Beedrill = Pokemon('15', ['398', '529', '280', '41'])
    Machamp = Pokemon('68', ['370', '418', '9', '8'])
    Snorlax = Pokemon('143', ['38', '89', '7', '484'])
    Mewtwo = Pokemon('150', ['94', '411', '126', '247'])

    # Sample 2.0 --- Sample pokemon with mix of non damge status/stat moves + damaging moves
    Chansey = Pokemon('113', ['105', '109', '207', '451']) #non damaging healing moves + stat boosting? + status moves
    Groudon = Pokemon('383', ['322', '86', '414', '103']) #stat boost moves, attacking
    Registeel = Pokemon('379', ['139', '261', '334', '97']) #all non damaging
    Tyranitar = Pokemon('248', ['468', '464', '504', '411']) #variety stat/damaging
    Palkia = Pokemon('484', ['410', '460', '347', '434']) #damaging w/effects

    #Sample 3.0 --- Mix of Pokemon gen1-gen4
    Sceptile = Pokemon('254', ['348', '406', '235', '536'])
    Lucario = Pokemon('448', ['370', '183', '442', '14'])
    Infernape = Pokemon('392', ['53', '409', '595', '261'])
    Wailord = Pokemon('321', ['57', '453', '417', '317'])
    Golem = Pokemon('76', ['444', '89', '431', '153'])
    Articuno = Pokemon('144', ['59', '613', '97', '524'])
    Dusknoir = Pokemon('477', ['421', '95', '441', '342'])
    Lugia = Pokemon('249', ['177', '354', '324', '92'])
    Metagross = Pokemon('376', ['309', '334', '326', '232'])
    Rayquaza = Pokemon('384', ['407', '403', '533', '434'])
    Gyarados = Pokemon('130', ['349', '350', '245', '127'])
    Weavile = Pokemon('461', ['420', '400', '136', '422'])
    Bronzong = Pokemon('437', ['347','430', '60', '95'])
    Dugtrio = Pokemon('51', ['89', '120', '29', '351'])
    Hitmonchan = Pokemon('107', ['7', '8', '9', '24'])
    Dragonite = Pokemon('149', ['245', '337', '434', '542'])
    Salamence = Pokemon('373', ['304', '434', '56', '126'])
    Steelix = Pokemon('208', ['89', '231', '422', '157'])
    Spiritomb = Pokemon('442', ['247', '399', '105', '261'])
    Raikou = Pokemon('243', ['85', '411', '326', '242'])
    Deoxys = Pokemon('386', ['354', '58', '53', '412'])
    Marshtomp = Pokemon('259', ['482', '308', '414', '92'])


    p1 = Dusknoir
    p2 = Weavile
    #p1.fight(p2)

    #battle configuration
    team1 = [Marshtomp, Mewtwo, Golem, Blastoise, Beedrill, Pidgeot]
    team2 = [Deoxys, Lugia, Lucario, Rayquaza, Dragonite, Charizard]

    greedy = False
    smartgreedy = False
    baseCode = False
    minimax = True
    # Cofig for greedy approach
    if greedy:
        garyoak = Trainer(team1, 'Gary')
        ashketchum = Trainer(team2, 'Ash')
        garyoak.greedyfight(ashketchum)

    # Config for Smarter greedy
    if smartgreedy:
        garyoak = Trainer(team1, 'Gary')
        ashketchum = Trainer(team2, 'Ash')
        garyoak.smartgreedyfight(ashketchum)

    # Config for the original baseCode
    if baseCode:
        garyoak = Trainer(team1, 'Gary')
        ashketchum = Trainer(team2, 'Ash')
        garyoak.fight(ashketchum)

    if minimax:
        garyoak = Trainer(team1, 'Gary')
        ashketchum = Trainer(team2, 'Ash')
        garyoak.minimaxfight(ashketchum)
