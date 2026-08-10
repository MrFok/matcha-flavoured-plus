package com.mrfok.matcha.mixin;

import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.DataSlot;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Invoker;

/**
 * Exposes the protected data-slot registration method from the class that
 * actually declares it. EnchantmentMenu inherits this method, so shadowing it
 * from an EnchantmentMenu-targeted mixin is invalid under Mixin's strict
 * target-member lookup.
 */
@Mixin(AbstractContainerMenu.class)
public interface AbstractContainerMenuInvoker {
    @Invoker("addDataSlot")
    DataSlot matcha$invokeAddDataSlot(DataSlot dataSlot);
}
