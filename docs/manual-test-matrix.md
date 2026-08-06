# Manual Minecraft 26.2 test matrix

Run these checks in unmodified vanilla Minecraft 26.2 with the combined ZIP in
the world's `datapacks` directory and the client's `resourcepacks` directory.

| Fix | Required check | Pass condition |
| --- | --- | --- |
| Sleep initialization | Start a new world and sleep before using `/reload` or reconnecting. | The configured sleep behavior works on the first session. |
| Multiplayer Heart Containers | Start the server before two players join. Confirm both receive a `Hearts` score of 20, then give and acquire containers independently. Kill one player after increasing their health. | Each container and death changes only the triggering player; late joiners never lose a container because their score is missing. |
| Plain sweet berries | Consume berries from `/give`, a harvested bush, a trade/bundle, and a fox drop. | Every normal `minecraft:sweet_berries` stack grants the same regeneration effect. |
| Smithing enchantments | Run `/function main:smithing_enchantments/test/give_regression_kit`, craft one output, keep it elsewhere in the inventory, then craft the same upgrade again. | Each new output keeps compatible base enchantments and gains material minimums; the previously crafted item is unchanged on later crafts. |
| Feather Falling pearl protection | Throw ender pearls with no boots, ordinary boots, and Feather Falling boots. | Only Feather Falling prevents ender-pearl damage; ordinary fall damage remains reduced according to the enchantment level. |

Also run `/reload` and inspect the game log for pack parsing errors before
release.
