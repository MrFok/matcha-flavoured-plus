package com.mrfok.matcha.mixin;

import com.mrfok.matcha.MatchaEnchantingTableAccess;
import com.mrfok.matcha.MatchaFlavouredPlus;
import net.minecraft.world.level.block.entity.EnchantingTableBlockEntity;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(EnchantingTableBlockEntity.class)
public abstract class EnchantingTableBlockEntityMixin implements MatchaEnchantingTableAccess {
    @Unique
    private int matcha$uses;

    @Override
    public int matcha$getUses() {
        return matcha$uses;
    }

    @Override
    public void matcha$setUses(int uses) {
        matcha$uses = Math.max(0, Math.min(MatchaFlavouredPlus.ENCHANTING_TABLE_LIMIT, uses));
    }

    @Inject(method = "saveAdditional", at = @At("TAIL"))
    private void matcha$saveUses(ValueOutput output, CallbackInfo callbackInfo) {
        if (matcha$uses > 0) {
            output.putInt("matcha_flavoured_plus:enchanting_table_uses", matcha$uses);
        }
    }

    @Inject(method = "loadAdditional", at = @At("TAIL"))
    private void matcha$loadUses(ValueInput input, CallbackInfo callbackInfo) {
        matcha$setUses(input.getIntOr("matcha_flavoured_plus:enchanting_table_uses", 0));
    }
}
