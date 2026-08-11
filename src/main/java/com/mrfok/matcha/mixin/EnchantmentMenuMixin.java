package com.mrfok.matcha.mixin;

import com.mrfok.matcha.MatchaEnchantmentMenuAccess;
import com.mrfok.matcha.MatchaEnchantmentBookSlot;
import com.mrfok.matcha.MatchaEnchantingTableAccess;
import com.mrfok.matcha.MatchaFlavouredPlus;
import net.minecraft.world.Container;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.inventory.DataSlot;
import net.minecraft.world.inventory.EnchantmentMenu;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.entity.BlockEntity;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.ModifyArg;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import org.objectweb.asm.Opcodes;

@Mixin(EnchantmentMenu.class)
public abstract class EnchantmentMenuMixin implements MatchaEnchantmentMenuAccess {
    @Shadow
    @Final
    private ContainerLevelAccess access;

    @Shadow
    @Final
    private Container enchantSlots;

    @Unique
    private DataSlot matcha$remainingUses;

    @Inject(
            method = "<init>(ILnet/minecraft/world/entity/player/Inventory;Lnet/minecraft/world/inventory/ContainerLevelAccess;)V",
            at = @At("TAIL")
    )
    private void matcha$initRemainingUses(
            int containerId,
            Inventory inventory,
            ContainerLevelAccess access,
            CallbackInfo callbackInfo
    ) {
        DataSlot remainingUses = DataSlot.standalone();
        remainingUses.set(MatchaFlavouredPlus.ENCHANTING_TABLE_LIMIT);
        matcha$remainingUses = ((AbstractContainerMenuInvoker) (Object) this)
                .matcha$invokeAddDataSlot(remainingUses);
        matcha$refreshRemainingUses();
    }

    @ModifyArg(
            method = "<init>(ILnet/minecraft/world/entity/player/Inventory;Lnet/minecraft/world/inventory/ContainerLevelAccess;)V",
            at = @At(
                    value = "INVOKE",
                    target = "Lnet/minecraft/world/inventory/EnchantmentMenu;addSlot(Lnet/minecraft/world/inventory/Slot;)Lnet/minecraft/world/inventory/Slot;",
                    ordinal = 0
            ),
            index = 0
    )
    private Slot matcha$replaceInputSlot(Slot vanillaSlot) {
        return new MatchaEnchantmentBookSlot(
                vanillaSlot.container,
                vanillaSlot.getContainerSlot(),
                vanillaSlot.x,
                vanillaSlot.y
        );
    }

    @Inject(method = "slotsChanged", at = @At("TAIL"))
    private void matcha$refreshAfterSlotChange(
            Container container,
            CallbackInfo callbackInfo
    ) {
        matcha$refreshRemainingUses();
    }

    @Unique
    private void matcha$refreshRemainingUses() {
        if (matcha$remainingUses == null) {
            return;
        }
        int used = access.evaluate(
                (level, pos) -> {
                    BlockEntity blockEntity = level.getBlockEntity(pos);
                    return blockEntity instanceof MatchaEnchantingTableAccess table
                            ? table.matcha$getUses()
                            : -1;
                },
                -1
        );
        // ContainerLevelAccess.NULL is used by the client-side menu and returns
        // the fallback. Only the server can read the block entity; leaving the
        // client value untouched here preserves the value synchronized through
        // AbstractContainerMenu's registered DataSlot.
        if (used >= 0) {
            matcha$remainingUses.set(Math.max(
                    0,
                    MatchaFlavouredPlus.ENCHANTING_TABLE_LIMIT - used
            ));
        }
    }

    @Override
    public int matcha$getRemainingUses() {
        return matcha$remainingUses == null
                ? MatchaFlavouredPlus.ENCHANTING_TABLE_LIMIT
                : Math.max(0, Math.min(
                        MatchaFlavouredPlus.ENCHANTING_TABLE_LIMIT,
                        matcha$remainingUses.get()
                ));
    }

    @Inject(method = "clickMenuButton", at = @At("HEAD"), cancellable = true)
    private void matcha$denyExhaustedTable(Player player, int button, CallbackInfoReturnable<Boolean> callbackInfo) {
        ItemStack input = enchantSlots.getItem(0);
        if (!input.isEmpty() && !input.is(Items.BOOK)) {
            callbackInfo.setReturnValue(false);
            return;
        }
        // Client-side EnchantmentMenu instances have ContainerLevelAccess.NULL.
        // The server owns the block entity and is the only side that can enforce
        // the persisted use counter authoritatively.
        if (player.level().isClientSide()) {
            return;
        }
        boolean usable = access.evaluate(
                (level, pos) -> MatchaFlavouredPlus.isUsableEnchantingTable(level, pos),
                false
        );
        if (!usable) {
            callbackInfo.setReturnValue(false);
        }
    }

    @Redirect(
            method = "clickMenuButton",
            at = @At(
                    value = "FIELD",
                    target = "Lnet/minecraft/world/entity/player/Player;experienceLevel:I",
                    opcode = Opcodes.GETFIELD
            )
    )
    private int matcha$ignoreExperienceRequirement(Player player) {
        return Integer.MAX_VALUE;
    }

    @ModifyArg(
            method = "lambda$clickMenuButton$0",
            at = @At(
                    value = "INVOKE",
                    target = "Lnet/minecraft/world/entity/player/Player;onEnchantmentPerformed(Lnet/minecraft/world/item/ItemStack;I)V"
            ),
            index = 1
    )
    private int matcha$doNotConsumeExperience(int vanillaCost) {
        return 0;
    }

    @Inject(method = "clickMenuButton", at = @At("RETURN"))
    private void matcha$countSuccessfulEnchant(
            Player player,
            int button,
            CallbackInfoReturnable<Boolean> callbackInfo
    ) {
        if (!callbackInfo.getReturnValueZ()) {
            return;
        }
        access.execute((level, pos) -> MatchaFlavouredPlus.recordEnchant(level, pos, player));
        matcha$refreshRemainingUses();
    }
}
