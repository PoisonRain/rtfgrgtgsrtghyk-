from elf_kingdom import *
from Elf import *
from Start import Start
from Aggressive import Aggressive
from Normal import Normal
from Defense import Defense
import flanking

# old state:
old_my_castle_health_3_turns = []
old_my_portals = []
elfDict = {}  # key: elf unique id; value: Elf instance
attackDict = {}  # key: portal unique id; value: portal instance
alreadyNormal = False
nrmI = None
agrI = None
srtI = None
defI = None
max_dist_from_castle = 12000
defence_portal_dist = 2000  # portals we consider as our defence portals


def update_attackDict(game, my_elves, my_portals):
    global attackDict, old_my_portals, max_dist_from_castle
    attack_portal = None
    if my_portals:
        for uid in attackDict.keys():  # delete destroyed portals
            if uid not in [portal.unique_id for portal in my_portals]:
                del attackDict[uid]

        for elf in my_elves:  # add new attack portals
            if elf.elf.is_building is False and elf.was_building is True:
                for portal in my_portals:
                    # d = portal.location
                    if portal not in old_my_portals and portal.distance(game.get_enemy_castle()) < max_dist_from_castle:
                        attack_portal = portal
                        break
                if attack_portal is not None:
                    attackDict[attack_portal.unique_id] = attack_portal
                elf.was_building = False
    else:
        attackDict.clear()


def update_elfDict(game, my_elves):
    global elfDict
    if my_elves:  # add new and delete old elves from the dictionary
        for elf in my_elves:  # add new
            if elf.unique_id not in elfDict.keys():
                elfDict[elf.unique_id] = Elf(game, elf)

        for uid in elfDict.keys():  # delete old
            if uid not in [elf.unique_id for elf in my_elves]:
                del elfDict[uid]
    else:  # if we have no elves just clear the dictionary
        elfDict.clear()

    for elf in elfDict.values():  # update game for all elf objects
        elf.game = game


def must_have_portals(game, elfDict):
    """
    :return: true if we have all the portals we consider as must have, else returns false
    """

    # variable future to change
    defence_portal_amout = 1

    global defence_portal_dist
    my_castle = game.get_my_castle()
    my_portals = game.get_my_portals()
    defence_portals = [portal for portal in my_portals if portal.location.distance(my_castle) <= defence_portal_dist]
    if len(defence_portals) < defence_portal_amout:  # need more defence portals
        return False
    return True


def need_defence(game):
    pass


def do_turn(game):
    # vars
    global elfDict, attackDict, agrI, nrmI, srtI, defI, old_my_portals, old_my_castle_health_3_turns
    my_elves = game.get_my_living_elves()
    my_portals = game.get_my_portals()
    enemy_castle = game.get_enemy_castle()
    my_castle = game.get_my_castle()
    flank_elves = []  # list of all elves that try to flank and build a portal
    if agrI is None:
        agrI = Aggressive(game, elfDict, attackDict)
    if srtI is None:
        srtI = Start(game, elfDict)
    if nrmI is None:
        nrmI = Normal(game, elfDict, attackDict, agrI)
    if defI is None:
        defI = Defense(game, elfDict)

    if game.turn == 1:
        flanking.initialize(my_elves)

    update_elfDict(game, my_elves)  # update elfDict

    # fix None
    if my_portals is None:  # sets list to list if its null
        my_portals = []

    agrI.do_aggressive(game, elfDict, attackDict)
    #choosing an attack mode:
    if need_defence(game):
        defI.do_defense(game, elfDict)
        print "Strat: defence"
    if not alreadyNormal and len(my_portals) < 7 and game.turn < (my_castle.location.distance(enemy_castle) / 100):
        srtI.do_start(game, elfDict)
        print "Strat: start"
    elif must_have_portals(game, my_portals) and ((game.get_enemy_mana() < 100 and my_castle.current_health > 75) or (
            enemy_castle.current_health and my_castle.current_health > 75)):
        flank_elves = agrI.do_aggressive(game, elfDict, attackDict)
        print "Strat: aggressive"
    else:
        flank_elves = nrmI.do_normal(game, elfDict, attackDict)
        print "Strat: normal"
    update_attackDict(game, flank_elves, game.get_my_portals())  # updating attackDict

    # update old state:
    old_my_portals = my_portals
    old_my_castle_health_3_turns.append(my_castle.current_health)
    old_my_castle_health_3_turns = old_my_castle_health_3_turns[:3]
    for elf in elfDict.values():
        elf.old_health_2_turns.append(elf.elf.current_health)
        elf.old_health_2_turns = elf.old_health_2_turns[:2]
