package io.github.juanluci.starling;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Build;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.WindowInsets;
import android.view.WindowInsetsController;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

/**
 * Hexa Launcher home screen. The launch gate deliberately remains closed until the
 * native engine reports a verified Minecraft 1.21.10 build; it must never start the
 * repository's current 26.3 engine under a 1.21.10 label.
 */
public final class HexaHomeActivity extends Activity {
    private static final boolean MINECRAFT_1_21_10_ENGINE_READY = false;
    private static final int BACKGROUND = 0xFF0B1110;
    private static final int PANEL = 0xFF17211D;
    private static final int GREEN = 0xFF79E36D;
    private static final int TEXT = 0xFFF1F7F0;
    private static final int MUTED = 0xFF9AA99C;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(BACKGROUND);
        getWindow().setNavigationBarColor(BACKGROUND);
        getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                        | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION);
        setContentView(createHome());
    }

    private View createHome() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        root.setPadding(dp(28), dp(32), dp(28), dp(32));
        root.setBackgroundColor(BACKGROUND);

        LogoView logo = new LogoView();
        root.addView(logo, new LinearLayout.LayoutParams(dp(124), dp(124)));

        TextView title = new TextView(this);
        title.setText("HEXA LAUNCHER");
        title.setTextColor(TEXT);
        title.setTextSize(25);
        title.setTypeface(Typeface.create("sans-serif-black", Typeface.BOLD));
        title.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams titleParams =
                new LinearLayout.LayoutParams(-1, -2);
        titleParams.topMargin = dp(22);
        root.addView(title, titleParams);

        TextView subtitle = new TextView(this);
        subtitle.setText("MINECRAFT JAVA EDITION 1.21.10");
        subtitle.setTextColor(MUTED);
        subtitle.setTextSize(11);
        subtitle.setLetterSpacing(0.12f);
        subtitle.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams subtitleParams =
                new LinearLayout.LayoutParams(-1, -2);
        subtitleParams.topMargin = dp(8);
        root.addView(subtitle, subtitleParams);

        Button launch = new Button(this);
        launch.setAllCaps(false);
        launch.setText("Launch 1.21.10 (Rust)");
        launch.setTextSize(16);
        launch.setTypeface(Typeface.create("sans-serif-medium", Typeface.BOLD));
        launch.setTextColor(BACKGROUND);
        GradientDrawable button = new GradientDrawable();
        button.setColor(GREEN);
        button.setCornerRadius(dp(14));
        launch.setBackground(button);
        launch.setElevation(dp(5));
        LinearLayout.LayoutParams buttonParams =
                new LinearLayout.LayoutParams(-1, dp(58));
        buttonParams.topMargin = dp(42);
        root.addView(launch, buttonParams);

        launch.setOnClickListener(v -> {
            if (!MINECRAFT_1_21_10_ENGINE_READY) {
                Toast.makeText(this,
                        "1.21.10 Rust engine is still being ported. The 26.3 engine is blocked.",
                        Toast.LENGTH_LONG).show();
                return;
            }
            startActivity(new Intent(this, LauncherActivity.class));
        });
        return root;
    }

    private int dp(float value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    private final class LogoView extends View {
        private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Path hex = new Path();
        private final Path glyph = new Path();
        private final RectF bounds = new RectF();

        LogoView() {
            super(HexaHomeActivity.this);
        }

        @Override
        protected void onDraw(Canvas canvas) {
            super.onDraw(canvas);
            float w = getWidth();
            float h = getHeight();
            float cx = w * 0.5f;
            float cy = h * 0.5f;
            float r = Math.min(w, h) * 0.43f;
            hex.reset();
            for (int i = 0; i < 6; i++) {
                double a = Math.PI / 3.0 * i - Math.PI / 6.0;
                float x = cx + (float) Math.cos(a) * r;
                float y = cy + (float) Math.sin(a) * r;
                if (i == 0) hex.moveTo(x, y); else hex.lineTo(x, y);
            }
            hex.close();

            paint.setStyle(Paint.Style.FILL);
            paint.setColor(PANEL);
            canvas.drawPath(hex, paint);
            paint.setStyle(Paint.Style.STROKE);
            paint.setStrokeWidth(dp(3));
            paint.setColor(GREEN);
            canvas.drawPath(hex, paint);

            paint.setStyle(Paint.Style.STROKE);
            paint.setStrokeWidth(dp(10));
            paint.setStrokeCap(Paint.Cap.SQUARE);
            paint.setStrokeJoin(Paint.Join.BEVEL);
            paint.setColor(GREEN);
            glyph.reset();
            glyph.moveTo(cx - r * 0.34f, cy - r * 0.42f);
            glyph.lineTo(cx - r * 0.34f, cy + r * 0.42f);
            glyph.moveTo(cx + r * 0.34f, cy - r * 0.42f);
            glyph.lineTo(cx + r * 0.34f, cy + r * 0.42f);
            glyph.moveTo(cx - r * 0.34f, cy);
            glyph.lineTo(cx + r * 0.34f, cy);
            canvas.drawPath(glyph, paint);
        }
    }
}
