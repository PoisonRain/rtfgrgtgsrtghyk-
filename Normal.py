from elf_kingdom import *
from Portals import *
from newMath import move_point_by_angle

# constants
DEFENSE_MANA_CAP = 100  # limit to when we stop defending due to low mana
MANE_DRAIN_RANGE = 1500  # the distance of checking if there is a creature in range of the enemy castel we dont want to spawn from
LAVA_DRAIN_MANA_LIMIT = 100  # needs tweaking of course
ENEMY_LOW_MANA_ATTACK = 50  # the limit to become a more aggresive version of normal while considering to enemy mana
NORMAL_ATTACK_MODE_MANA_CAP = 100  # the limit to become a more aggresive version of normal while considering our mana
CASTLE_DEFENSE = 3000  # range of which elfs will try to destroy enemy portals, TODO: make it using range of map
ELF_DEFENSE_BOOST_RANGE = 400  # range of attack targets portal will spawn defense to help the elfs
ELF_DEFENSE_BOOST_MANA = 100  # mana cap to spawn defense to help elfs attack
ENEMY_FOUNTAIN_NO_PORTALS_RANGE = 400  # range of an enemy fountain of which there can be no enemy portals for us to
PORTAL_SELF_DEFENSE_MANA_CAP = 100  # mana cap we must have for portals to defend itself


# attack it( on elf's way back to base)  # wtf is this?


class Normal:
    """
     the normal mode, theoreticlly the mode we will be in most of the time. aims to reduce enemy mana and maintain
     our attack portals and portals in general
     TODO: maintain / build mana fountains
     TODO: add uses for spells
     """

    def __init__(self, game, elfDict, aggressive, start):
        """

        :param aggressive: instance of aggressive mode, used to make attack portals
        :var portals: instance of portals class, used to control portals + some utilities functions
        """
        self.game = game
        self.my_elves = [elf for elf in elfDict.values() if not elf.elf.already_acted]
        self.switch_sides = -1  # switching side on the normal line
        self.dirDict = {}
        self.old_my_portals = []
        self.aggressive = aggressive
        self.my_castle = game.get_my_castle()
        self.start = start

        self.portals = Portals(game, game.get_my_portals())  # create an instance of portals object to summon etc.

    @staticmethod
    def portal_on_location(game, loc):
        """
        get a location and checks if there is a portal(friendly) there
        :param game: the game instance
        :param loc: the location on which the portal(friendly) should be
        :return: True if there is a portal there, False else
        """
        my_portals = game.get_my_portals()
        for portal in my_portals:
            if portal.location.equals(loc):
                return True
        return False
    
    @staticmethod
    def fountain_on_location(game, loc):
        """
        get a location and checks if there is a fountain(friendly) there
        :param game: the game instance
        :param loc: the location on which the fountain(friendly) should be
        :return: True if there is a fountain there, False else
        """
        my_fountains = game.get_my_mana_fountains()
        for fountain in my_fountains:
            if fountain.location.equals(loc):
                return True
        return False

    def do_normal(self, game, elfDict):
        """
        updates normal
        does all of what the normal mode is meant to do, defend, drain mana, maintain portals.
        :param elfDict: usable elfs
        :return: elfs being used
        """
        self.normal_update(game, elfDict)
        self.aggressive.update_attack_portals(game)

        self.portals.dumb_portal_defense(PORTAL_SELF_DEFENSE_MANA_CAP)
        self.normal_defense()  # defend the castle (if there are enemies in range)
        self.aggressive.build_portals(game, elfDict)  # build the flanking poratls, might need to be in
        self.start.do_start(game, elfDict)  # maintain defense portals and fountains

        self.normal_elf_defendcastle(elfDict)  # destroy buildings in range of defense radius(CASTLE_DEFENSE)

        # drain enemy mana if our mana is above our set limite
        self.new_mana_bait(LAVA_DRAIN_MANA_LIMIT)
        #self.normal_portal_defense(self.game.get_my_portals())  # test dis mojo


        # if self.game.get_enemy_mana() < ENEMY_LOW_MANA_ATTACK and self.game.get_my_mana() > NORMAL_ATTACK_MODE_MANA_CAP:  # attack more? might be used more
        #     self.normal_attack_lowMana(self.attackDict)  # become more aggresive in normal if the enemy is low on
            # on mana and we have enough.


    def normal_portal_defense(self, portals):
        """
        summon defense if the mana cap is met and there is enemies to defend from
        :param portals: list of portals to defend
        :return: nuffin
        """
        for portal in portals:
            self.portals.defend_portal(portal, PORTAL_SELF_DEFENSE_MANA_CAP)

    def normal_defense(self):
        """
        defend the castle if are above the mana cap using the Portals class
        """
        if self.game.get_my_mana() > DEFENSE_MANA_CAP:
            self.portals.dumb_castle_defense(DEFENSE_MANA_CAP)
            self.portals.dumb_portal_defense(PORTAL_SELF_DEFENSE_MANA_CAP)

    def new_mana_bait(self, mana_cap):
        lava, ice = False, False
        if self.game.get_my_mana() > mana_cap:
            portals = self.portals.closest_portals_sorted(self.game.get_enemy_castle())
            if len(portals) == 0:
                return False
            if len(self.game.get_my_lava_giants()) == 0 and len(self.game.get_enemy_ice_trolls()) == 0:
                lava, ice = True, True
            else:
                closest_creature = self.sorted_map_objects(self.game.get_enemy_castle(),(self.game.get_my_lava_giants(), self.game.get_enemy_ice_trolls()))
                if self.game.get_enemy_castle().distance(closest_creature[0]) > MANE_DRAIN_RANGE:
                    lava, ice = True, True
            if lava and ice and portals[0].can_summon_lava_giant():
                portals[0].summon_lava_giant()
                lava, ice = False, False

    def normal_update(self, game, elfDict):
        """
        Update everything that changes between turns or needs updating
        :param game: updated instance of game
        :param elfDict: usable elfs
        """
        self.game = game  # update game
        self.my_elves = [elf for elf in elfDict.values() if not elf.elf.already_acted]  # update self.my_elves
        self.game = game  # update self.game
        self.portals.portals_update(game)  # update portals (the object)
        self.my_castle = game.get_my_castle()

    def normal_enemy_mana_drain(self, attack_portals):
        """
        send a lava golem if: there is no lava golem near the enemy castel already and no enemy ice troll
        drains enemy mana
        :param attack_portals: portals used to attack
        """
        lava, ice = True, True
        for creature in self.game.get_my_lava_giants():
            if creature.distance(self.game.get_enemy_castle()) < MANE_DRAIN_RANGE:
                lava = False
        for creature in self.game.get_enemy_ice_trolls():
            if creature.distance(self.game.get_enemy_castle()) < MANE_DRAIN_RANGE:
                ice = False
        if (ice == False and lava == False):
            for portal in attack_portals:
                if portal.can_summon_lava_giant():
                    portal.summon_lava_giant()
                    lava, ice = True, True

    def normal_attack_lowMana(self, attack_portals):
        """
        when enemy has low mana increese attack according to the attack list
        instead of the mana drain spam.
        :param attack_portals: portals used to attack
        """
        self.portals.poratls_attack(attack_portals, NORMAL_ATTACK_MODE_MANA_CAP)

    def build_portals(self, elfDict, attackDict):
        """
        build portals at the designated flanking points using aggressive
        :param elfDict: usable elfs
        :param attackDict: portals used to attack
        :return: elfs being used
        """
        flanking_elves = self.aggressive.outside_aggressive_buildportals(self.game, elfDict,
                                                                         attackDict)  # game, elfDict, attackDict
        return flanking_elves
        # enemy_castle = self.game.get_enemy_castle()
        # flanking_elves = []
        # distance_from_tgt = 900
        #
        # if len(self.attackDict) < 2:  # if there are not enough portals
        #     for elf in self.my_elves[0:2]:  # build portals with all elves (atm builds with only 1):
        #         location_to_move = elf.move_normal(enemy_castle.location, distance_from_tgt, self.dirDict[elf.elf.unique_id])
        #         if elf.elf.location.equals(location_to_move):  # check if elf is in designated location
        #             if elf.elf.can_build_portal():  # if able to built portal
        #                 elf.elf.build_portal()
        #                 elf.was_building = True
        #         else:  # if not at location to build move to the location
        #             elf.move(location_to_move)
        #         flanking_elves.append(elf)
        # return flanking_elves

    def normal_elf_defendcastle(self, elfDict):
        """
        use the elfs to defend the castle, break portals and fountains near the castle, use both elfs to destroy faster
        and take less damage logic: normal is all about preparing to attack we want elfs to have their health
        if there are nearby portals and enemies to defend the elfs from the portal will summon defense, currently
        only one (due to change need to be tested in game and see how it is)
        :param elfDict:
        :return:
        """
        self.my_elves = [elf for elf in elfDict.values() if not elf.elf.already_acted]  # update self.my_elves
        enemy_poratls = self.game.get_enemy_portals()
        enemy_fountains = self.game.get_enemy_mana_fountains()
        if self.game.get_enemy_portals() is None:
            enemy_poratls = []
        if self.game.get_enemy_mana_fountains() is None:
            enemy_fountains = []
        targets = self.sorted_map_objects(self.game.get_my_castle(), (enemy_fountains, enemy_poratls))  # get a sorted
        # list of targets, closest to the castle, can append whatever priority you want after sorting to have certain
        # buildings higher priority
        for target in targets:
            if self.my_castle.distance(target) < CASTLE_DEFENSE:
                for i in range(2):  # use 2 elfs (assuming they add more elfs in the future)
                    if target is not None:
                        if len(self.my_elves) > i and not self.my_elves[i].elf.already_acted:
                            fountains_on_path = self.get_fountains_on_path(self.my_elves[i])
                            if len(fountains_on_path) > 0:
                                self.my_elves[i].attack(fountains_on_path[0])
                            else:
                                self.my_elves[i].attack(target)
                            if self.game.get_my_mana() > ELF_DEFENSE_BOOST_MANA:  # summon defense to help the elfs if there is a need
                                defense_portals = self.portals.closest_portals_sorted(target)
                                if len(defense_portals) > 0 and defense_portals[0].distance(
                                        target) < ELF_DEFENSE_BOOST_RANGE:
                                    enemies = self.portals.enemy_creatures_in_radius(400, target)
                                    if enemies[1] > 0 or enemies[2] > 0:
                                        self.portals.summon_defense(defense_portals[0])

    def sorted_map_objects(self, point, objects):
        """
        get a tuple of lists of map objects and a point and sort them closest to point first
        :param point: location on the map to sort from, needs to be map object
        :param objects: map objects tuple of lists
        :return: sorted_objects the sorted list of map object closest being first
        """
        # print objects
        # print len(objects)
        if isinstance(objects, list):
            sorted_objects = objects
        else:
            sorted_objects = [j for i in objects for j in i]
        if len(sorted_objects) > 0:
            sorted_objects.sort(key=lambda x: x.distance(point.get_location()), reverse=False)
        return sorted_objects

    def get_fountains_on_path(self, elf):
        fountains = []
        d = (self.game.get_enemy_mana_fountains())
        for fountain in self.sorted_map_objects(elf.elf, d):
            if fountain.distance(self.game.get_my_castle()) < elf.elf.distance(self.game.get_my_castle()) and len(
                    self.portals.portals_around_map_object(fountain, ENEMY_FOUNTAIN_NO_PORTALS_RANGE,
                                                           self.game.get_enemy_portals())) == 0:
                fountains.append(fountain)
        return fountains



