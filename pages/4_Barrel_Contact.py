import streamlit as st

st.set_page_config(page_title="Barrel Contact", page_icon="🎯", layout="wide")
st.title("Barrel Contact Location (CF View)")
st.caption("Center-field view → coarse zone where the ball met the barrel.")

st.info(
    "Module planned. Output is intentionally a coarse zone (not millimeter-accurate) — "
    "a broadcast CF camera doesn't give us the resolution for finer than that."
)

st.subheader("1. Upload clip")
st.file_uploader(
    "CF view of the swing (mp4, ≥120 fps recommended)",
    type=["mp4", "mov"],
    disabled=True,
)

st.subheader("2. Auto-detect contact frame")
st.write(
    "Contact frame is the frame where the ball's trajectory inverts horizontal velocity "
    "(approaching → departing). Bat barrel is tracked frame-by-frame; the contact point is "
    "the ball-bat intersection at that frame."
)

st.subheader("3. Outputs (zoned)")
c1, c2 = st.columns(2)
c1.metric("Along-bat zone", "—", help="end of bat / sweet spot / off the hands")
c2.metric("Up/down zone", "—", help="top of barrel / center / bottom of barrel")

st.caption("Returns a 3 × 3 zone grid + a confidence score based on bat/ball detection quality.")
