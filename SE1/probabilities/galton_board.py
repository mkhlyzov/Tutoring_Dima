#!/usr/bin/env python3
"""
Galton Board simulator (single-file) with:
 - Larger bucket counters
 - Bead size adjustable dynamically
 - Animation speed adjustable dynamically (mouse drag)
 - Button labels always visible on macOS
"""

import tkinter as tk
from tkinter import ttk
import random
import math

# --- Configuration defaults ---
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600
TOP_MARGIN = 40
BOTTOM_MARGIN = 120
SIDE_MARGIN = 40
DEFAULT_BUCKETS = 9
MAX_BUCKETS = 20
DEFAULT_BEAD_SIZE = 10
DEFAULT_SPEED = 6        # pixels per frame

PEG_RADIUS = 5
PEG_COLOR = "#555"
BUCKET_COLOR = "#222"
COUNTER_FONT = ("Helvetica", 16, "bold")   # Larger!
LABEL_FONT = ("Helvetica", 10)
BEAD_COLOR = "#c62828"

FRAME_DELAY_MS = 16      # ~60 FPS


class GaltonBoardApp:
    def __init__(self, root):
        self.root = root
        root.title("Galton Board Simulator")

        # Fix macOS button text visibility
        style = ttk.Style()
        style.configure("TButton", foreground="black")

        self.buckets = tk.IntVar(value=DEFAULT_BUCKETS)
        self.bead_size = tk.IntVar(value=DEFAULT_BEAD_SIZE)
        self.speed = tk.IntVar(value=DEFAULT_SPEED)

        self.counts = []
        self.animating = False
        self.current_bead = None
        self.after_id = None

        self._build_ui()
        self._redraw_board()

    # ---------------- UI -------------------
    def _build_ui(self):
        control_frame = ttk.Frame(self.root)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=8, pady=8)

        ttk.Label(control_frame, text="Buckets:", font=LABEL_FONT).pack(side=tk.LEFT)
        self.spin_buckets = ttk.Spinbox(
            control_frame, from_=1, to=MAX_BUCKETS, width=4,
            textvariable=self.buckets, command=self._on_buckets_changed
        )
        self.spin_buckets.pack(side=tk.LEFT, padx=(4, 12))

        ttk.Label(control_frame, text="Bead Size:", font=LABEL_FONT).pack(side=tk.LEFT)
        tk.Scale(
            control_frame, from_=10, to=80, orient=tk.HORIZONTAL,
            variable=self.bead_size, showvalue=True, length=120
        ).pack(side=tk.LEFT, padx=(4, 12))

        ttk.Label(control_frame, text="Speed:", font=LABEL_FONT).pack(side=tk.LEFT)
        tk.Scale(
            control_frame, from_=5, to=40, orient=tk.HORIZONTAL,
            variable=self.speed, showvalue=True, length=120
        ).pack(side=tk.LEFT, padx=(4, 12))

        self.btn_drop = ttk.Button(control_frame, text="Drop 1 bead", command=self.drop_one_bead)
        self.btn_drop.pack(side=tk.LEFT, padx=6)

        self.btn_reset = ttk.Button(control_frame, text="Reset", command=self.reset_board)
        self.btn_reset.pack(side=tk.LEFT, padx=6)

        self.status_label = ttk.Label(control_frame, text="", font=LABEL_FONT)
        self.status_label.pack(side=tk.LEFT, padx=12)

        self.canvas = tk.Canvas(self.root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg="#f8f8f8")
        self.canvas.pack(padx=8, pady=(0, 8))

        self.root.bind("<Configure>", self._on_resize)

    # ---------------- Board Drawing -------------------
    def _on_resize(self, event):
        if event.widget == self.root:
            self._redraw_board()

    def _on_buckets_changed(self):
        if not self.animating:
            self._redraw_board()

    def _redraw_board(self):
        self.canvas.delete("all")
        self.canvas.update_idletasks()

        self.canvas_width = max(300, self.canvas.winfo_width())
        self.canvas_height = max(300, self.canvas.winfo_height())

        self.bucket_count = int(self.buckets.get())
        self.rows = max(0, self.bucket_count - 1)

        available_width = self.canvas_width - 2 * SIDE_MARGIN
        self.bucket_w = available_width / self.bucket_count
        self.bucket_centers = [
            SIDE_MARGIN + self.bucket_w * (i + 0.5)
            for i in range(self.bucket_count)
        ]
        self.center_x = self.canvas_width / 2

        if self.rows > 0:
            board_height = self.canvas_height - (TOP_MARGIN + BOTTOM_MARGIN)
            self.row_spacing = board_height / (self.rows + 1)
            self.row_ys = [TOP_MARGIN + self.row_spacing * (i + 1) for i in range(self.rows)]
        else:
            self.row_spacing = 0
            self.row_ys = []

        self._draw_pegs()
        self.counts = [0] * self.bucket_count
        self._draw_buckets()

    def _draw_pegs(self):
        for r in range(self.rows):
            peg_count = r + 1
            row_y = self.row_ys[r]
            for i in range(peg_count):
                x = SIDE_MARGIN + (self.bucket_w *
                                   (((self.bucket_count - peg_count) / 2.0) + i + 0.5))
                self.canvas.create_oval(
                    x - PEG_RADIUS, row_y - PEG_RADIUS,
                    x + PEG_RADIUS, row_y + PEG_RADIUS,
                    fill=PEG_COLOR, outline=""
                )

    def _draw_buckets(self):
        y_top = self.canvas_height - BOTTOM_MARGIN
        y_bottom = self.canvas_height - 12

        for i, cx in enumerate(self.bucket_centers):
            x0 = cx - self.bucket_w / 2
            x1 = cx + self.bucket_w / 2

            self.canvas.create_rectangle(x0, y_top, x1, y_bottom,
                                         outline=BUCKET_COLOR, width=2)

            # Larger, bold, high-visibility counters
            self.canvas.create_rectangle(
                cx - 18, y_top - 26, cx + 18, y_top - 2,
                fill="white", outline=""
            )
            self.canvas.create_text(
                cx, y_top - 14, text=str(self.counts[i]),
                font=COUNTER_FONT, fill="#000"
            )

            self.canvas.create_text(cx, y_bottom + 14, text=str(i),
                                    font=LABEL_FONT, fill="#333")

    # ---------------- Animation -------------------
    def drop_one_bead(self):
        if self.animating:
            return
        self.animating = True
        self._set_controls_state(tk.DISABLED)

        bead_r = self.bead_size.get() / 2

        # Determine the random left/right sequence
        choices = []
        rights = 0
        segments = []

        start_x = self.center_x
        start_y = TOP_MARGIN - 12
        segments.append((start_x, start_y))

        dp = self.bucket_w / 2
        for i in range(1, self.rows + 1):
            step = random.choice([0, 1])
            rights += step
            choices.append(step)
            x = self.center_x + (2 * rights - i) * dp
            y = self.row_ys[i - 1]
            segments.append((x, y))

        final_bucket = rights
        final_x = self.bucket_centers[final_bucket]
        final_y = self.canvas_height - BOTTOM_MARGIN + 16
        segments.append((final_x, final_y))

        bead = self.canvas.create_oval(
            start_x - bead_r, start_y - bead_r,
            start_x + bead_r, start_y + bead_r,
            fill=BEAD_COLOR, outline=""
        )

        self._animate_segment(bead, segments, 0, final_bucket, bead_r)

    def _animate_segment(self, bead_id, pts, idx, final_bucket, bead_r):
        if idx >= len(pts) - 1:
            self._on_landed(final_bucket)
            return

        x0, y0 = pts[idx]
        x1, y1 = pts[idx + 1]

        dx = x1 - x0
        dy = y1 - y0
        dist = math.hypot(dx, dy)

        speed = self.speed.get()
        steps = max(1, int(dist / speed))
        step_dx = dx / steps
        step_dy = dy / steps
        step = 0

        def move_step():
            nonlocal step
            if step >= steps:
                self.canvas.coords(
                    bead_id,
                    x1 - bead_r, y1 - bead_r,
                    x1 + bead_r, y1 + bead_r
                )
                self.after_id = self.root.after(
                    30,
                    lambda: self._animate_segment(bead_id, pts, idx + 1, final_bucket, bead_r)
                )
                return

            self.canvas.move(bead_id, step_dx, step_dy)
            step += 1
            self.after_id = self.root.after(16, move_step)

        move_step()

    def _on_landed(self, bucket_idx):
        self.counts[bucket_idx] += 1
        self.canvas.delete("all")
        self._draw_pegs()
        self._draw_buckets()

        self.animating = False
        self._set_controls_state(tk.NORMAL)
        self.status_label.config(text=f"Bead landed in bucket {bucket_idx}")

    def reset_board(self):
        if self.animating:
            return
        self.counts = [0] * self.bucket_count
        self.canvas.delete("all")
        self._draw_pegs()
        self._draw_buckets()
        self.status_label.config(text="Reset complete")

    def _set_controls_state(self, state):
        self.spin_buckets.config(state=state)
        self.btn_drop.config(state=state)
        self.btn_reset.config(state=state)


# ---------------- MAIN -------------------
def main():
    root = tk.Tk()
    GaltonBoardApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
