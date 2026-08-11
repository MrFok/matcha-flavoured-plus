package com.mrfok.matcha.mixin.client;

import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.Hud;
import net.minecraft.client.multiplayer.MultiPlayerGameMode;
import net.minecraft.world.entity.player.Player;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(Hud.class)
public abstract class HudMixin {
    @Inject(method = "extractFood", at = @At("HEAD"), cancellable = true)
    private void matcha$hideFoodBar(
            GuiGraphicsExtractor graphics,
            Player player,
            int y,
            int x,
            CallbackInfo callbackInfo
    ) {
        callbackInfo.cancel();
    }

    @Redirect(
            method = "nextContextualInfoState",
            at = @At(
                    value = "INVOKE",
                    target = "Lnet/minecraft/client/multiplayer/MultiPlayerGameMode;hasExperience()Z"
            )
    )
    private boolean matcha$hideExperienceContext(MultiPlayerGameMode gameMode) {
        return false;
    }

    @Redirect(
            method = "extractHotbarAndDecorations",
            at = @At(
                    value = "INVOKE",
                    target = "Lnet/minecraft/client/multiplayer/MultiPlayerGameMode;hasExperience()Z"
            )
    )
    private boolean matcha$hideExperienceLevel(MultiPlayerGameMode gameMode) {
        return false;
    }

    @Redirect(
            method = "extractHotbarAndDecorations",
            at = @At(
                    value = "INVOKE",
                    target = "Lnet/minecraft/client/gui/contextualbar/ContextualBar;extractExperienceLevel(Lnet/minecraft/client/gui/GuiGraphicsExtractor;Lnet/minecraft/client/gui/Font;I)V"
            )
    )
    private static void matcha$skipExperienceLevel(
            GuiGraphicsExtractor graphics,
            Font font,
            int experienceLevel
    ) {
        // Matcha enchanting does not spend XP; suppress the otherwise stale
        // vanilla level number along with the contextual XP bar.
    }
}
