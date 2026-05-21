import streamlit as st

from baseball_cv import routes

st.set_page_config(page_title="Route Efficiency", page_icon="⚾", layout="wide")
st.title("Defensive Route Efficiency")
st.caption("High-home camera view → actual vs optimal route to a batted ball.")

st.subheader("1. Upload clip")
video = st.file_uploader("High-home view of the play (mp4)", type=["mp4", "mov"])
use_mock = video is None
if use_mock:
    st.info("No clip uploaded — showing demo output with mock data.")

st.subheader("2. Field calibration")
cal_col, cal_help = st.columns([1, 1])
with cal_col:
    st.write("Click the four base corners in the first frame to establish a pixel → field-feet homography.")
    st.text_input("Home plate (px)", value="" if not use_mock else "—", disabled=use_mock)
    st.text_input("1B (px)", value="" if not use_mock else "—", disabled=use_mock)
    st.text_input("2B (px)", value="" if not use_mock else "—", disabled=use_mock)
    st.text_input("3B (px)", value="" if not use_mock else "—", disabled=use_mock)
with cal_help:
    st.write(
        "The four bases form a 90 ft square. Calibration converts every pixel "
        "position into feet on the field, so the route metrics are physically meaningful "
        "regardless of broadcast angle or zoom."
    )

st.subheader("3. Mark fielder + ball landing")
c1, c2 = st.columns(2)
fielder_pos = c1.selectbox("Fielder position", ["CF", "LF", "RF", "SS", "2B", "3B"], index=0)
contact_frame = c2.number_input(
    "Contact frame (auto-detected once CV is wired in)", min_value=0, max_value=10_000, value=24
)

if st.button("Run analysis", type="primary"):
    if not use_mock:
        st.warning("Real CV pipeline not yet wired in — falling back to mock output.")
    result = routes.mock_route_result(fielder_pos)

    st.subheader("4. Results")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Route efficiency", f"{result['route_eff_pct']:.1f}%")
    m2.metric("Time to ball", f"{result['time_to_ball_s']:.2f} s")
    m3.metric("Max speed", f"{result['max_speed_mph']:.1f} mph")
    m4.metric("First-step jump", f"{result['first_step_jump_s']:.2f} s")

    st.plotly_chart(routes.plot_route(result), use_container_width=True)

    with st.expander("Raw result JSON"):
        st.json(result)
