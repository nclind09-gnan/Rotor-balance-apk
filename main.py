"""
Rotor Balance Calculator - Android app (Kivy)
Single-plane, influence-coefficient (vector) method.

Angle convention: measured CLOCKWISE from the phase reference mark
(keyphasor), as viewed from the sensor end.
"""

import cmath
import math

from kivy.app import App
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView

Window.clearcolor = (0.078, 0.086, 0.094, 1)


# ---------- balancing math ----------
def to_complex(mag, theta_clock_deg):
    phi = -math.radians(theta_clock_deg)
    return cmath.rect(mag, phi)


def to_clock_deg(z):
    mag, phi = cmath.polar(z)
    theta = (-math.degrees(phi)) % 360
    return mag, theta


def clock_position(theta_deg):
    hour = round(theta_deg / 30) % 12
    return 12 if hour == 0 else hour


# ---------- UI ----------
class LabeledInput(BoxLayout):
    def __init__(self, label_text, hint_text="", **kwargs):
        super().__init__(orientation="vertical", size_hint_y=None, height=dp(64), **kwargs)
        self.label = Label(
            text=label_text,
            size_hint_y=None,
            height=dp(20),
            font_size=dp(12),
            color=(0.6, 0.64, 0.66, 1),
            halign="left",
        )
        self.label.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        self.input = TextInput(
            hint_text=hint_text,
            multiline=False,
            input_filter="float",
            size_hint_y=None,
            height=dp(42),
            font_size=dp(16),
            background_color=(0.11, 0.12, 0.13, 1),
            foreground_color=(0.94, 0.67, 0.24, 1),
            cursor_color=(0.94, 0.67, 0.24, 1),
            padding=(dp(10), dp(10)),
        )
        self.add_widget(self.label)
        self.add_widget(self.input)

    @property
    def value(self):
        try:
            return float(self.input.text)
        except ValueError:
            return None


class BalanceApp(App):
    def build(self):
        self.title = "Rotor Balance"
        root = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))

        scroll = ScrollView()
        form = GridLayout(cols=1, spacing=dp(10), size_hint_y=None, padding=(0, 0, 0, dp(20)))
        form.bind(minimum_height=form.setter("height"))

        title = Label(
            text=(
                "[b][color=F0AA3C]Rotor Balance Calculator[/color][/b]\n"
                "[size=12][color=8B9198]Single plane \u00b7 influence coefficient method[/color][/size]"
            ),
            markup=True,
            size_hint_y=None,
            height=dp(56),
            halign="left",
            valign="top",
        )
        title.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        form.add_widget(title)

        note = Label(
            text=(
                "[color=8B9198][size=12]Angles measured clockwise from the "
                "phase reference mark, as viewed from the sensor end.[/size][/color]"
            ),
            markup=True,
            size_hint_y=None,
            height=dp(40),
            halign="left",
            valign="top",
        )
        note.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        form.add_widget(note)

        self.o_amp = LabeledInput("ORIGINAL VIBRATION AMPLITUDE", "e.g. 4.2")
        self.o_phase = LabeledInput("ORIGINAL PHASE ANGLE (deg)", "e.g. 48")
        self.t_wt = LabeledInput("TRIAL WEIGHT MASS", "e.g. 5.0")
        self.t_angle = LabeledInput("TRIAL WEIGHT PLACEMENT ANGLE (deg)", "e.g. 90")
        self.tr_amp = LabeledInput("VIBRATION AMPLITUDE WITH TRIAL WEIGHT", "e.g. 2.1")
        self.tr_phase = LabeledInput("PHASE ANGLE WITH TRIAL WEIGHT (deg)", "e.g. 310")

        for w in (self.o_amp, self.o_phase, self.t_wt, self.t_angle, self.tr_amp, self.tr_phase):
            form.add_widget(w)

        self.compute_btn = Button(
            text="Compute Correction Weight",
            size_hint_y=None,
            height=dp(50),
            background_color=(0.94, 0.67, 0.24, 1),
            color=(0.08, 0.09, 0.1, 1),
            bold=True,
        )
        self.compute_btn.bind(on_press=self.compute)
        form.add_widget(self.compute_btn)

        self.result_label = Label(
            text="",
            markup=True,
            size_hint_y=None,
            halign="left",
            valign="top",
            font_size=dp(14),
        )
        self.result_label.bind(
            texture_size=lambda inst, val: setattr(inst, "height", val[1] + dp(10))
        )
        self.result_label.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
        form.add_widget(self.result_label)

        scroll.add_widget(form)
        root.add_widget(scroll)
        return root

    def compute(self, instance):
        vals = [
            self.o_amp.value,
            self.o_phase.value,
            self.t_wt.value,
            self.t_angle.value,
            self.tr_amp.value,
            self.tr_phase.value,
        ]
        if any(v is None for v in vals):
            self.result_label.text = "[color=E06C5C]Please fill in every field with a number.[/color]"
            return
        o_amp, o_phase, t_wt, t_angle, tr_amp, tr_phase = vals

        if t_wt <= 0:
            self.result_label.text = "[color=E06C5C]Trial weight must be greater than zero.[/color]"
            return

        O = to_complex(o_amp, o_phase)
        OT = to_complex(tr_amp, tr_phase)
        T = to_complex(t_wt, t_angle)
        E = OT - O

        if abs(E) < 1e-6:
            self.result_label.text = (
                "[color=F0AA3C]The trial weight barely changed the vibration reading. "
                "Try a heavier trial weight or a different placement angle.[/color]"
            )
            return

        S = E / T
        Wc = -O / S
        residual = O + S * Wc

        e_mag, e_ang = to_clock_deg(E)
        s_mag, s_ang = to_clock_deg(S)
        wc_mag, wc_ang = to_clock_deg(Wc)
        res_mag, _ = to_clock_deg(residual)

        self.result_label.text = (
            f"[b][color=7FBF8C]CORRECTION WEIGHT: {wc_mag:.2f} @ {wc_ang:.1f}\u00b0 "
            f"(~{clock_position(wc_ang)} o'clock)[/color][/b]\n\n"
            f"[color=8B9198]Effect vector (E): {e_mag:.3f} @ {e_ang:.1f}\u00b0\n"
            f"Sensitivity (S = E/T): {s_mag:.3f} @ {s_ang:.1f}\u00b0\n"
            f"Predicted residual vibration: {res_mag:.3f}[/color]\n\n"
            "Remove the trial weight, then install the correction weight\n"
            "at the stated angle (clockwise from the reference mark)."
        )


if __name__ == "__main__":
    BalanceApp().run()
