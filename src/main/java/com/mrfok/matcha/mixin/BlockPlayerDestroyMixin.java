package com.mrfok.matcha.mixin;

import com.mrfok.matcha.MatchaEnchantingTableAccess;
import com.mrfok.matcha.MatchaFlavouredPlus;
import java.util.HashSet;
import java.util.Set;
import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(Block.class)
public abstract class BlockPlayerDestroyMixin {
    @Unique
    private static final ThreadLocal<Set<Integer>> matcha$existingDrops =
            ThreadLocal.withInitial(HashSet::new);

    @Inject(method = "playerDestroy", at = @At("HEAD"))
    private void matcha$captureExistingDrops(
            Level level,
            Player player,
            BlockPos pos,
            BlockState state,
            BlockEntity blockEntity,
            ItemStack tool,
            CallbackInfo callbackInfo
    ) {
        Set<Integer> existing = matcha$existingDrops.get();
        existing.clear();
        if (level.isClientSide()
                || !state.is(Blocks.ENCHANTING_TABLE)
                || !(blockEntity instanceof MatchaEnchantingTableAccess)
                || !MatchaFlavouredPlus.hasSilkTouch(level, tool)) {
            return;
        }
        level.getEntities(
                (net.minecraft.world.entity.Entity) null,
                new net.minecraft.world.phys.AABB(pos).inflate(1.5),
                entity -> entity instanceof net.minecraft.world.entity.item.ItemEntity
        ).forEach(entity -> existing.add(entity.getId()));
    }

    @Inject(method = "playerDestroy", at = @At("TAIL"))
    private void matcha$preserveTableUses(
            Level level,
            Player player,
            BlockPos pos,
            BlockState state,
            BlockEntity blockEntity,
            ItemStack tool,
            CallbackInfo callbackInfo
    ) {
        try {
            if (level.isClientSide()
                    || !state.is(Blocks.ENCHANTING_TABLE)
                    || !(blockEntity instanceof MatchaEnchantingTableAccess table)
                    || !MatchaFlavouredPlus.hasSilkTouch(level, tool)) {
                return;
            }
            MatchaFlavouredPlus.preserveCarriedUsesOnDroppedTable(
                    level,
                    pos,
                    table.matcha$getUses(),
                    matcha$existingDrops.get()
            );
        } finally {
            matcha$existingDrops.remove();
        }
    }
}
