package com.mrfok.matcha.mixin.client;

import com.mrfok.matcha.MatchaEnchantmentMenuAccess;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.inventory.EnchantmentScreen;
import net.minecraft.client.gui.screens.inventory.MenuAccess;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.network.chat.Component;
import net.minecraft.world.inventory.AbstractContainerMenu;
import org.objectweb.asm.Opcodes;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(EnchantmentScreen.class)
public abstract class EnchantmentScreenMixin {
    @Inject(method = "extractBackground", at = @At("TAIL"))
    private void matcha$drawBookBudget(
            GuiGraphicsExtractor graphics,
            int mouseX,
            int mouseY,
            float partialTicks,
            CallbackInfo callbackInfo
    ) {
        AbstractContainerMenu menu = ((MenuAccess<?>) (Object) this).getMenu();
        if (!(menu instanceof MatchaEnchantmentMenuAccess matchaMenu)) {
            return;
        }

        Font font = Minecraft.getInstance().font;
        int remaining = matchaMenu.matcha$getRemainingUses();
        Component label = Component.literal(remaining + " left");
        int color = remaining <= 2 ? 0xFFFF5555 : 0xFF55FFFF;
        int labelWidth = font.width(label);
        int x = Math.max(4, graphics.guiWidth() - labelWidth - 8);
        int y = Math.max(4, graphics.guiHeight() - 17);
        graphics.fill(x - 4, y - 3, x + labelWidth + 4, y + 12, 0xB0000000);
        graphics.text(font, label, x, y, color);
    }

    @Redirect(
            method = "extractBackground",
            at = @At(
                    value = "FIELD",
                    target = "Lnet/minecraft/client/player/LocalPlayer;experienceLevel:I",
                    opcode = Opcodes.GETFIELD
            )
    )
    private int matcha$ignoreDisplayedExperienceForChoices(LocalPlayer player) {
        // The server-side menu already removes the XP gate. Keep the client
        // preview enabled too, otherwise zero-level players see disabled
        // enchantment slots even though clicking them is valid.
        return Integer.MAX_VALUE;
    }

    @Redirect(
            method = "extractRenderState",
            at = @At(
                    value = "FIELD",
                    target = "Lnet/minecraft/client/player/LocalPlayer;experienceLevel:I",
                    opcode = Opcodes.GETFIELD
            )
    )
    private int matcha$ignoreDisplayedExperienceForTooltip(LocalPlayer player) {
        return Integer.MAX_VALUE;
    }
}
