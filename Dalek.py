import hlt
import logging
import random
import math
from collections import OrderedDict

game = hlt.Game("Dalekv5")

logging.info("Starting my Dalek bot!")

turn = -1
target_ship_id = 0
called = True

# returns list of entities ordered by distance to a specific ship
def sorted_entities(ship):
    entities_by_distance = game_map.nearby_entities_by_distance(ship)
    entities_by_distance = OrderedDict(sorted(entities_by_distance.items(), key=lambda t: t[0]))
    return entities_by_distance


# returns closest empty planet
def closest_empty_planet(ship, index=0):
    entities_by_distance = sorted_entities(ship)
    empty_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if
                     (isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and (not
                      entities_by_distance[distance][0].is_owned()
                      or (entities_by_distance[distance][0].owner is game_map.get_me()
                          and not entities_by_distance[distance][0].is_full())))]
    return empty_planets[index]


# returns list of empty planets
def empty_planets(ship):
    entities_by_distance = sorted_entities(ship)
    empty_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if
                     (isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and not
                     entities_by_distance[distance][0].is_owned())]
    return empty_planets


# returns closest enemy ship
def closest_enemy_ship(ship, index=0):
    entities_by_distance = sorted_entities(ship)
    enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if
                   (isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and
                    entities_by_distance[distance][0] not in game_map.get_me().all_ships())]
    return enemy_ships[index]


# returns all enemy ships
def enemy_ships(ship):
    entities_by_distance = sorted_entities(ship)
    enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if
                   (isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and
                    entities_by_distance[distance][0] not in game_map.get_me().all_ships())]
    return enemy_ships


while True:
    turn += 1
    # TURN START
    # Update the map for the new turn and get the latest version
    game_map = game.update_map()
    # Here we define the set of commands to be sent to the Halite engine at the end of the turn
    command_queue = []
    my_ships = game_map.get_me().all_ships()
    logging.debug('# of ship: %s', len(my_ships))
    # For every ship that I control
    if len(my_ships) < 4:
        for settler in range(0, len(my_ships)):
            if called:
                target_planet = empty_planets(my_ships[0])
                called = False
            if settler is 2:
                rogue_ship = my_ships[2]
                distance = rogue_ship.calculate_distance_between(closest_empty_planet(closest_enemy_ship(rogue_ship)))
                logging.debug('rogue ship start')
                if (target_ship_id is 0 or target_ship_id is closest_enemy_ship(rogue_ship).id) \
                        and distance < 30:
                    logging.debug('distance = %s', distance)
                    action = rogue_ship.navigate(
                        rogue_ship.closest_point_to(closest_enemy_ship(rogue_ship)),
                        game_map,
                        speed=int(hlt.constants.MAX_SPEED),
                        ignore_ships=False
                    )
                    logging.debug('action done')
                    if turn is 5:
                        target_ship_id = closest_enemy_ship(rogue_ship).id
                else:
                    logging.debug('else statement')
                    if rogue_ship.can_dock(closest_empty_planet(rogue_ship)):
                        action = rogue_ship.dock(closest_empty_planet(rogue_ship))
                    else:
                        action = my_ships[settler].navigate(
                            my_ships[settler].closest_point_to(closest_empty_planet(rogue_ship)),
                            game_map,
                            speed=int(hlt.constants.MAX_SPEED),
                            ignore_ships=False)
                logging.debug('if action %s', action)
                if action:
                    command_queue.append(action)
            else:
                logging.debug('else succeed')
                if settler < turn:
                    if my_ships[settler].can_dock(target_planet[settler]):
                        action = my_ships[settler].dock(target_planet[settler])
                    else:
                        action = my_ships[settler].navigate(
                                my_ships[settler].closest_point_to(target_planet[settler]),
                                game_map,
                                speed=int(hlt.constants.MAX_SPEED),
                                ignore_ships=False)
                    if action:
                        command_queue.append(action)
            logging.debug('action done')
    else:
        for current in range(0, len(my_ships)):
            ship = my_ships[current]
            if ship.docking_status != ship.DockingStatus.UNDOCKED:
                # Skip this ship
                check = False
                for dormant_ships in game_map.get_me().all_ships():
                    if dormant_ships.docking_status is ship.DockingStatus.DOCKED:
                        check = True
                        break
                if check:
                    continue
                else:
                    for dormant_ships in game_map.get_me().all_ships():
                        command_queue.append(dormant_ships.undock)
            logging.debug('if docking pass')
            if len(empty_planets(ship)) > 0 and len(my_ships) < 100:
                logging.debug('within 100')
                if len(empty_planets(ship)) > 1:
                    first_planet = closest_empty_planet(ship)
                    second_planet = closest_empty_planet(ship, index=1)
                    map_center_x = game_map.width/2
                    map_center_y = game_map.height/2
                    first_planet_dtcenter = math.hypot(map_center_x - first_planet.x, map_center_y - first_planet.y)
                    second_planet_dtcenter = math.hypot(map_center_x - second_planet.x, map_center_y - second_planet.y)
                    first_planet_dtship = math.hypot(ship.x - first_planet.x, ship.y - first_planet.y)
                    second_planet_dtship = math.hypot(ship.x - second_planet.x, ship.y - second_planet.y)
                    diff_planet_dtc = first_planet_dtcenter - second_planet_dtcenter
                    if second_planet.radius > first_planet.radius and second_planet.radius - first_planet.radius > 3 \
                            and abs(first_planet_dtship - second_planet_dtship) < 15:
                        target_planet = second_planet
                        logging.debug('second planet choice')
                    else:
                        target_planet = first_planet
                        logging.debug('first planet choice')
                else:
                    target_planet = closest_empty_planet(ship)
                if ship.can_dock(target_planet):
                    logging.debug('IF Success')
                    command_queue.append(ship.dock(target_planet))
                else:
                    logging.debug('more three Success')
                    navigate_command = ship.navigate(
                        ship.closest_point_to(target_planet),
                        game_map,
                        speed=int(hlt.constants.MAX_SPEED),
                        ignore_ships=False)
                    if navigate_command:
                        command_queue.append(navigate_command)
            elif len(enemy_ships(ship)) > 0:
                logging.debug('attack mode')
                target_ship = closest_enemy_ship(ship)
                navigate_command = ship.navigate(
                    ship.closest_point_to(target_ship),
                    game_map,
                    speed=int(hlt.constants.MAX_SPEED),
                    max_corrections=180,
                    ignore_ships=False)
                if navigate_command:
                    command_queue.append(navigate_command)
    game.send_command_queue(command_queue)
    # TURN END
# GAME END
