# Valuable Resource Death Loss

## Status

Design approved; implementation is pending a Fabric runtime component.

## Goal

Death should cost a deterministic share of gathered wealth without deleting
tools, armour, progression items, or the storage items that hold resources.

## Rule

For every item ID in the curated `matcha_flavoured_plus:main/death_valuables` item tag:

1. Count every matching item held by the player, including items inside
   shulker boxes, bundles, and supported nested storage items.
2. Calculate the loss with ceiling rounding:

   ```
   loss = ceil(total_count * 0.25)
   ```

3. Remove exactly `loss` items from those inventories.
4. Spawn exactly `loss` items at the death location.

The player keeps the storage container and all non-eligible contents.

Examples:

| Total held | Dropped | Retained |
| ---: | ---: | ---: |
| 1 diamond | 1 | 0 |
| 4 diamonds | 1 | 3 |
| 5 diamonds | 2 | 3 |
| 80 diamonds across inventory and shulkers | 20 | 60 |

The calculation is per item ID, not per stack. Two stacks of 40 diamonds are
treated as 80 diamonds, not as two independent 40-item penalties.

## Classification

The eventual `matcha_flavoured_plus:main/death_valuables` tag should contain mined and processed
resources such as raw metals, ingots, nuggets, gems, dusts, ore drops, rare
mob resources, and equivalent Matcha materials.

It must exclude:

- tools, weapons, armour, and Elytra;
- food, blocks, building materials, and ordinary loot;
- named/progression items, including Tyrael and Divine items;
- shulker boxes, bundles, and other containers themselves.

The item tag is the single source of truth for future balance adjustments.

## Why This Needs Runtime Code

Modern datapacks can select contents of shulker boxes and bundles for loot
generation, but cannot atomically:

1. aggregate each item ID across arbitrary nested inventories,
2. calculate its exact loss once,
3. mutate the original nested stacks by exactly that amount, and
4. spawn the removed stacks at the recorded death location.

Implementing only part of that flow would risk per-stack rounding,
duplication, deletion, or missed container contents. A Fabric death-event
handler can traverse the complete item-component tree and perform the update
as one transaction.

## Implementation Contract

The Fabric handler must:

- run at the actual death location before respawn handling;
- use the `keepInventory` path so untagged items remain with the player;
- recursively traverse `minecraft:container` and
  `minecraft:bundle_contents` components;
- preserve all item components, names, enchantments, and container layout;
- split spawned drops to valid stack sizes;
- make no changes when a player carries no tagged valuables;
- guard against duplicate execution for one death.

## Verification

Before release, test at minimum:

1. 80 diamonds divided between hotbar, inventory, a shulker, and a bundle:
   exactly 20 diamonds drop.
2. One, four, and five eligible items: ceiling rounding matches the table.
3. Tools, armour, Tyrael items, containers, and untagged contents remain.
4. Full inventory and nested storage do not duplicate or delete items.
5. Death in lava, void, and multiplayer still produces one penalty only.
