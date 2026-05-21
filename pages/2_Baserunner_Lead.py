import streamlit as st

st.set_page_config(page_title="Baserunner Lead", page_icon="🏃", layout="wide")
st.title("Baserunner Lead + Time to Second")
st.caption("Behind-1B / overhead view → lead distance off the bag and projected pop time.")

st.info("Module planned. The flow below shows the intended UX; outputs are placeholders.")

st.subheader("1. Upload clip")
st.file_uploader("Pre-pitch view of 1B (mp4)", type=["mp4", "mov"], disabled=True)

st.subheader("2. Calibration")
st.write(
    "Click 1B and 2B in the first frame. The 90 ft baseline calibrates pixels to feet "
    "along the baseline so lead distance is measured perpendicular to the bag."
)
st.text_input("1B (px)", disabled=True)
st.text_input("2B (px)", disabled=True)

st.subheader("3. Point at the runner")
st.write("Click the runner. Distance is measured to the back edge of 1B along the 1B→2B line.")

st.subheader("4. Outputs")
m1, m2, m3 = st.columns(3)
m1.metric("Primary lead", "— ft")
m2.metric("Secondary lead", "— ft")
m3.metric("Projected time to 2B", "— s")

st.caption(
    "Time-to-2B model: empirical sprint speed (default 27 ft/s, runner-tunable) "
    "applied to remaining 90 ft − lead, plus a small acceleration term from the secondary lead."
)
