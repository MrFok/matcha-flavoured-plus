package com.mrfok.matcha;

import net.minecraft.world.Container;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

/** Input slot used by Matcha's book-only enchanting table. */
public final class MatchaEnchantmentBookSlot extends Slot {
    public MatchaEnchantmentBookSlot(Container container, int slot, int x, int y) {
        super(container, slot, x, y);
    }

    @Override
    public boolean mayPlace(ItemStack stack) {
        return stack.is(Items.BOOK);
    }

    @Override
    public int getMaxStackSize() {
        return 1;
    }
}
