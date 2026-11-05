from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

BG, INK, MUTED, LIVED, DIED = "#ffffff", "#1f2933", "#52606d", "#2a78d6", "#c9ccd1"
AGE_ORDER = [f"{a}-{a + 9}" for a in range(0, 70, 10)] + ["70+"]
PORT_NAMES = {"C": "Cherbourg", "Q": "Queenstown", "S": "Southampton"}
CLASS_NAMES = {1: "1st", 2: "2nd", 3: "3rd"}


def survival_table(groups, survived, order):
    """Counts of not survived (0) and survived (1) for each group, keeping empty groups."""
    return pd.crosstab(groups, survived).reindex(index=order, columns=[0, 1], fill_value=0)


def rate_label(died, lived):
    total = died + lived
    if total == 0:
        return ""
    # A percentage from a handful of people misleads, so small groups show the count.
    return f"{lived / total:.1%}" if total >= 10 else f"{lived} of {total}"


def stacked_bars(ax, table, title, subtitle, xlabel, highlight=None, show_rates=True):
    bottom = ax.bar(table.index, table[1], color=LIVED, edgecolor=BG, linewidth=2, label="survived")
    top = ax.bar(table.index, table[0], bottom=table[1], color=DIED, edgecolor=BG, linewidth=2, label="not survived")
    ax.legend(frameon=True, facecolor=BG, edgecolor="none", framealpha=1, fontsize=11.5, loc="upper right", labelcolor=INK)
    if highlight:  # the chosen class stays dark and the others fade
        for bar_ in list(bottom) + list(top):
            if table.index[int(round(bar_.get_x() + bar_.get_width() / 2))] != highlight:
                bar_.set_alpha(0.3)
    if show_rates:
        for i, (died, lived) in enumerate(zip(table[0], table[1])):
            ax.text(i, died + lived, rate_label(died, lived), ha="center", va="bottom", fontsize=12, fontweight="bold", color=INK)
    ax.set_title(title, loc="left", fontsize=15, fontweight="bold", color=INK, pad=26)
    ax.text(0, 1.03, subtitle, transform=ax.transAxes, fontsize=11.5, color=MUTED)
    ax.set_xlabel(xlabel, fontsize=12, color=INK)
    ax.set_ylabel("Number of passengers", fontsize=12, color=INK)
    ax.tick_params(colors=INK, labelsize=11, length=0)
    ax.grid(axis="y", color="#e8eaed")
    ax.set_axisbelow(True)
    ax.set_ylim(0, max((table[0] + table[1]).max(), 1) * 1.45)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.set_facecolor(BG)


def kpi(ax, data, label):
    lived, total = int(data.Survived.sum()), len(data)
    ax.set_xticks([]); ax.set_yticks([]); ax.set_facecolor("#f4f6f8")
    ax.spines[:].set_visible(False)
    big = f"{lived / total:.1%}" if total else "no data"
    ax.text(0.06, 0.62, big, fontsize=26, fontweight="bold", color=INK, va="center", transform=ax.transAxes)
    ax.text(0.94, 0.62, f"{lived} of {total}", fontsize=12, color=MUTED, va="center", ha="right", transform=ax.transAxes)
    ax.text(0.06, 0.2, label, fontsize=12, color=INK, va="center", transform=ax.transAxes)


def badge(fig, x, y, number):
    """Marks where each Activity 3 question is answered."""
    fig.text(x, y, str(number), fontsize=12, fontweight="bold", color=BG, ha="center", va="center",
             bbox={"boxstyle": "circle,pad=0.3", "facecolor": INK, "edgecolor": INK})


def draw_dashboard(choice):
    """Draw the one-screen dashboard. choice is "All", "1st", "2nd" or "3rd"."""
    data = df if choice == "All" else df[df.Pclass.map(CLASS_NAMES) == choice]
    known = data.dropna(subset=["Age"])
    bands = pd.cut(known.Age, list(range(0, 80, 10)) + [81], right=False, labels=AGE_ORDER)
    is_all = choice == "All"

    fig, axes = plt.subplot_mosaic([["k1", "k2", "k3", "k4"], ["class", "age", "age", "port"]],
                                   figsize=(16, 8.4), height_ratios=[1, 3.6], facecolor=BG)
    fig.subplots_adjust(left=0.06, right=0.985, top=0.98, bottom=0.2, hspace=0.46, wspace=0.24)

    badge(fig, 0.03, axes["k1"].get_position().y0 + axes["k1"].get_position().height / 2, 3)
    kpi(axes["k1"], data, "of passengers survived")
    kpi(axes["k2"], known[(known.Age >= 13) & (known.Sex == "female")], "of women survived")
    kpi(axes["k3"], known[known.Age < 13], "of children under 13 survived")
    kpi(axes["k4"], known[(known.Age >= 13) & (known.Sex == "male")], "of men survived")

    badge(fig, 0.03, axes["class"].get_position().y1 + 0.05, 4)
    classes = survival_table(df.Pclass.map(CLASS_NAMES), df.Survived, list(CLASS_NAMES.values()))
    stacked_bars(axes["class"], classes, "Better class, better odds", "% on top = share who survived",
                 "Ticket class", highlight=None if is_all else choice)

    ages = survival_table(bands, known.Survived, AGE_ORDER)
    stacked_bars(axes["age"], ages, "Young children had the best odds" if is_all else "Survival by age",
                 "Passengers with a known age", "Age (years)", show_rates=False)
    kids = known[known.Age < 10]
    if len(kids):
        lived = kids.Survived.sum()
        axes["age"].annotate(f"{rate_label(len(kids) - lived, lived)} of\nunder-10s\nsurvived", xy=(0, len(kids)),
                             xytext=(-0.35, axes["age"].get_ylim()[1] * 0.62), ha="left", fontsize=12, fontweight="bold", color=INK,
                             arrowprops={"arrowstyle": "->", "color": INK, "linewidth": 1.4})

    ports = survival_table(data.Embarked.map(PORT_NAMES), data.Survived, list(PORT_NAMES.values()))
    stacked_bars(axes["port"], ports, "Cherbourg did best" if is_all else "Survival by boarding port",
                 "% on top = share who survived", "Boarding port")

    badge(fig, 0.03, 0.06, 1)
    fig.text(0.06, 0.06, "This dashboard is for museum visitors, many of whom have never studied\nstatistics and will only stop at the screen for about a minute.",
             fontsize=12.5, color=INK, va="center")
    badge(fig, 0.52, 0.06, 6)
    fig.text(0.55, 0.06, "I built it in Python with Streamlit because it is free, reuses my Activity 1 code,\nand gives visitors a link they can open without running any code.",
             fontsize=12.5, color=INK, va="center")
    return fig


@st.cache_data
def load_data():
    data = pd.read_csv(Path(__file__).parent / "train.csv")
    assert len(data) == 891 and data.Survived.sum() == 342  # same data as Activity 1
    return data


def keep_a_button_selected():
    # Clicking the chosen button again would otherwise leave no button selected.
    if st.session_state.choice is None:
        st.session_state.choice = "All"


def number(n):
    return (f'<span style="display:inline-block;width:1.7em;height:1.7em;line-height:1.7em;border-radius:50%;'
            f'background:{INK};color:{BG};text-align:center;font-weight:700;font-size:.95rem;margin-right:.6em">{n}</span>')


st.set_page_config(page_title="Titanic Survival Dashboard", layout="wide")
df = load_data()

left, right = st.columns([3, 2], vertical_alignment="center")
left.markdown(f'''<div style="display:flex;align-items:center">{number(2)}
<div style="font-size:1.9rem;font-weight:700;line-height:1.25;color:{INK}">Women, children and first-class passengers<br>
were the most likely to survive the Titanic</div></div>''', unsafe_allow_html=True)
with right:
    badge_col, filter_col = st.columns([1, 12], vertical_alignment="center")
    badge_col.markdown(number(5), unsafe_allow_html=True)
    st.session_state.setdefault("choice", "All")
    choice = filter_col.segmented_control("Filter: ticket class", ["All", "1st", "2nd", "3rd"], key="choice",
                                          on_change=keep_a_button_selected)

st.pyplot(draw_dashboard(choice), clear_figure=True)
