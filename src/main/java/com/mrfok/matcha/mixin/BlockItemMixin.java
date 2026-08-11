package com.mrfok.matcha.mixin;

import com.mrfok.matcha.MatchaFlavouredPlus;
import com.mrfok.matcha.MatchaEnchantingTableAccess;
import net.minecraft.core.BlockPos;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(BlockItem.class)
public abstract class BlockItemMixin {
    @Inject(
            method = "place",
            at = @At(
                    value = "INVOKE",
                    target = "Lnet/minecraft/world/item/ItemStack;consume(ILnet/minecraft/world/entity/LivingEntity;)V",
                    shift = At.Shift.BEFORE
            )
    )
    private void matcha$restoreTableUses(
            BlockPlaceContext context,
            CallbackInfoReturnable<InteractionResult> callbackInfo
    ) {
        ItemStack placedStack = context.getItemInHand();
        if (!placedStack.is(Items.ENCHANTING_TABLE)) {
            return;
        }
        Level level = context.getLevel();
        if (level.isClientSide()) {
            return;
        }
        // This injection runs after placement but before vanilla consumes the
        // held stack. At RETURN a one-count stack is already empty, which lost
        // the carried use count in the previous implementation.
        int uses = MatchaFlavouredPlus.getCarriedUses(placedStack);
        if (uses <= 0) {
            return;
        }
        BlockPos pos = context.getClickedPos();
        BlockEntity blockEntity = level.getBlockEntity(pos);
        if (blockEntity instanceof MatchaEnchantingTableAccess table) {
            table.matcha$setUses(uses);
            blockEntity.setChanged();
        }
    }
}
