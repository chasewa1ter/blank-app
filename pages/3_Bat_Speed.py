import streamlit as st

st.set_page_config(page_title="Bat Speed", page_icon="🏏", layout="wide")
st.title("Bat Speed (Side View)")
st.caption("Side-view swing → bat speed from swing initiation to impact.")

st.info("Module planned. The flow below shows the intended UX; outputs are placeholders.")

st.subheader("1. Upload clip")
st.file_uploader(
    "Side view of the swing (mp4, ≥120 fps recommended)",
    type=["mp4", "mov"],
    disabled=True,
)

st.subheader("2. Set scale")
st.write("Bat length gives us pixels-per-inch and lets us compute the barrel tip speed.")
st.number_input("Bat length (in)", value=33.0, disabled=True)
st.number_input("Camera frame rate (fps)", value=120.0, disabled=True)

st.subheader("3. Mark swing window")
st.write(
    "Swing initiation and impact frames are auto-detected by tracking bat angular velocity "
    "(zero-crossing → first sustained rise → peak). User can override."
)

st.subheader("4. Outputs")
m1, m2, m3 = st.columns(3)
m1.metric("Peak bat speed (barrel)", "— mph")
m2.metric("Time to contact", "— s")
m3.metric("Avg rotational speed", "— deg/s")
