# PokemonBattleAI

Pokemon Specs

## How to run simulator
Do `python3 pokemonsim.py`. Also at the bottom of script, you can add your own or use the pre-made Pokemons (change `[POKEMON1OBJECT].fight([POKEMON2OBJECT])`).
All supported moves found in `supported_moves.csv`
Move IDs found in `moves.json`, Pokemon numbers found `pokemon.json`. Venusaur.fight(Mewtwo).


## Running AI stuff
(todo in the future)

# Status updates of project
```
December 21: Added Minimax agent to Trainer class
July 9: Added effects for recharging moves/tri-attack/curse/dragon rage/sonic boom, added badly poison mechanics
July 8: Implemented various moves and move effects for semi-common moves
July 7: Finished 6v6 implementation (did some testing battles). Updated input/output interface.
July 6: Implemented Trainer Class and functionality. Switch-in functions and checks implemented; not inserted in game logic yet
June 30: Did lots of testing on stat and status moves. Fixed some mechanics (healing moves/critical hit) and bugs in accuracy. Added selfdestructing move mechanics for jokes. Added supported moves csv. Added more Pokemon samples to prepare for 6v6 implementation
June 29: Added non damaging stat moves + non damaging status condition moves. Fixed some bugs for STAB, healing moves, and stat condition lists.
June 24: 1v1 battling works (some move effects not implemented yet - still need more tests). Added some Pokemon to test around. Level 50 stats now automatically calculated for each Pokemon. 
June 23 (II): Status moves should be fully implemented now. Stat boosting moves should be fully implemented. Basic 1v1 mechanics should be complete. Basic non-damaging moves not in effect yet. Maybe test a bit more
June 23: Added confusion effects to moves. Mechanics for acrobatics/struggle implemented. Implemented recoil-on-miss mechanics. Confusion moves and mechanics seem to be working.
June 22: Added critical hit chances. Added mechanics for status conditions, and updated turn structuring. Did not fully test status moves yet (still have to update move effects)
June 19: Updated some special/physical distinguishment. Updated attack damage calculations a bit
```

Data files based from https://github.com/fonse/pokemon-battle

Backbone skeleton turn based battling and classes from https://github.com/cesaralvrz/Pokemon-Battle-Simulator

## Todo
Make simulation code/structure/documentation look prettier
Can enter game from different states of Pokemons if needed for AI
Can log game progress into files/variables if needed for AI
Add mechanics for charging moves (sky attack)/locked-in moves (outrage)/ switching moves (u-turn/batonpass/roar/dragon tail)????? if needed?????

## To test
random game mechanics in 6v6 that might have been missed earlier
new move mechanics?

### Translations to Keep Track?
Note: all will use level 50 defaults 0EV/0IV so just round down each calculation

normal 1
fighting 2
flying 3
poison 4
ground 5
rock 6
bug 7
ghost 8
steel 9
fire 10
water 11
grass 12
electric 13
psychic 14
ice 15
dragon 16
dark 17
fairy 18
