package com.mrfok.matcha;

import java.util.List;
import java.util.Optional;
import java.util.Set;

import net.fabricmc.api.ModInitializer;
import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.enchantment.Enchantment;
import net.minecraft.world.item.enchantment.EnchantmentHelper;
import net.minecraft.world.item.enchantment.Enchantments;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.tags.EnchantmentTags;
import net.minecraft.core.BlockPos;
import net.minecraft.world.phys.AABB;

public final class MatchaFlavouredPlus implements ModInitializer {
    public static final int ENCHANTING_TABLE_LIMIT = 10;
    public static final String MATCHA_DATA = "matcha_flavoured_plus";
    public static final String ENCHANTING_TABLE_USES = "enchanting_table_uses";

    @Override
    public void onInitialize() {
    }

    public static boolean isUsableEnchantingTable(Level level, BlockPos pos) {
        if (!level.getBlockState(pos).is(Blocks.ENCHANTING_TABLE)) {
            return false;
        }
        BlockEntity blockEntity = level.getBlockEntity(pos);
        return blockEntity instanceof MatchaEnchantingTableAccess table
                && table.matcha$getUses() < ENCHANTING_TABLE_LIMIT;
    }

    public static void recordEnchant(Level level, BlockPos pos, Player player) {
        if (level.isClientSide()) {
            return;
        }
        BlockEntity blockEntity = level.getBlockEntity(pos);
        if (!(blockEntity instanceof MatchaEnchantingTableAccess table)) {
            return;
        }

        int uses = Math.min(ENCHANTING_TABLE_LIMIT, table.matcha$getUses() + 1);
        table.matcha$setUses(uses);
        blockEntity.setChanged();
        if (uses >= ENCHANTING_TABLE_LIMIT) {
            // The table itself is exhausted, so this path must not consult the
            // player's held tool or accidentally return a Silk Touch table.
            level.destroyBlock(pos, false, player, 0);
            dropExhaustedTableRewards(level, pos);
        }
    }

    private static void dropExhaustedTableRewards(Level level, BlockPos pos) {
        Block.popResource(level, pos, new ItemStack(Items.OBSIDIAN, 4));

        Registry<Enchantment> enchantments = level.registryAccess().lookupOrThrow(Registries.ENCHANTMENT);
        var tableEnchantments = enchantments.get(EnchantmentTags.IN_ENCHANTING_TABLE);
        int bookCount = 2 + level.getRandom().nextInt(4);
        for (int index = 0; index < bookCount; index++) {
            ItemStack enchantedBook = EnchantmentHelper.enchantItem(
                    level.getRandom(),
                    new ItemStack(Items.BOOK),
                    30,
                    level.registryAccess(),
                    tableEnchantments
            );
            Block.popResource(level, pos, enchantedBook);
        }
    }

    public static int getCarriedUses(ItemStack stack) {
        CustomData data = stack.getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY);
        CompoundTag matcha = data.copyTag().getCompoundOrEmpty(MATCHA_DATA);
        return Math.max(0, Math.min(ENCHANTING_TABLE_LIMIT, matcha.getIntOr(ENCHANTING_TABLE_USES, 0)));
    }

    public static void setCarriedUses(ItemStack stack, int uses) {
        if (uses <= 0) {
            return;
        }
        CompoundTag root = stack.getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY).copyTag();
        CompoundTag matcha = root.getCompoundOrEmpty(MATCHA_DATA);
        matcha.putInt(ENCHANTING_TABLE_USES, Math.min(ENCHANTING_TABLE_LIMIT, uses));
        root.put(MATCHA_DATA, matcha);
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(root));
    }

    public static void preserveCarriedUsesOnDroppedTable(
            Level level,
            BlockPos pos,
            int uses,
            Set<Integer> existingEntityIds
    ) {
        if (level.isClientSide() || uses <= 0) {
            return;
        }
        List<Entity> drops = level.getEntities(
                (Entity) null,
                new AABB(pos).inflate(1.5),
                entity -> entity instanceof ItemEntity
        );
        for (Entity entity : drops) {
            if (!(entity instanceof ItemEntity itemEntity)) {
                continue;
            }
            if (existingEntityIds.contains(itemEntity.getId())) {
                continue;
            }
            ItemStack stack = itemEntity.getItem();
            if (stack.is(Items.ENCHANTING_TABLE)) {
                setCarriedUses(stack, uses);
                itemEntity.setItem(stack);
                return;
            }
        }
    }

    public static boolean hasSilkTouch(Level level, ItemStack stack) {
        Registry<Enchantment> enchantments = level.registryAccess().lookupOrThrow(Registries.ENCHANTMENT);
        Optional<Holder.Reference<Enchantment>> silkTouch = enchantments.get(Enchantments.SILK_TOUCH.identifier());
        return silkTouch.isPresent() && EnchantmentHelper.getItemEnchantmentLevel(silkTouch.get(), stack) > 0;
    }
}
