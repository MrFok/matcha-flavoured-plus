package com.mrfok.matcha.mixin.client;

import net.minecraft.client.DeltaTracker;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.contextualbar.ExperienceBar;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(ExperienceBar.class)
public abstract class ExperienceBarMixin {
    @Inject(method = "extractBackground", at = @At("HEAD"), cancellable = true)
    private void matcha$hideExperienceBackground(
            GuiGraphicsExtractor graphics,
            DeltaTracker deltaTracker,
            CallbackInfo callbackInfo
    ) {
        callbackInfo.cancel();
    }

    @Inject(method = "extractRenderState", at = @At("HEAD"), cancellable = true)
    private void matcha$hideExperienceProgress(
            GuiGraphicsExtractor graphics,
            DeltaTracker deltaTracker,
            CallbackInfo callbackInfo
    ) {
        callbackInfo.cancel();
    }
}
