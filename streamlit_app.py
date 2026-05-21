import streamlit as st

st.set_page_config(page_title="Baseball CV", page_icon="⚾", layout="wide")

st.title("Baseball Computer Vision")
st.write("Multi-module CV analysis for baseball video. Pick a module from the sidebar.")

st.markdown(
    """
### Modules

| Module | Camera view | Status |
|---|---|---|
| **Route Efficiency** | High home | UI scaffolded (MVP focus) |
| **Baserunner Lead + Pop Time** | Behind 1B / overhead | Planned |
| **Bat Speed** | Side view | Planned |
| **Barrel Contact Location** | Center field | Planned |

Each module takes an uploaded `.mp4` clip and produces structured metrics.
"""
)

st.info(
    "This is a UI scaffold. Flows are wired up with mock outputs so the UX is reviewable "
    "end-to-end. Real CV models will be plugged in once sample footage is available."
)

with st.expander("Architecture overview"):
    st.markdown(
        """
- **Frontend**: Streamlit multi-page app, one page per module.
- **CV core** (`baseball_cv/`): pure-Python helpers for field geometry (homography),
  per-module metrics, and plotting. Detection/tracking will be added as separate
  callables (YOLOv8 + ByteTrack are the current default).
- **Inputs**: uploaded MP4s (broadcast, Trackman, phone). Each module specifies the
  required camera view in its page.
- **Outputs**: numeric metrics + a per-module visualization. Results are also
  returned as JSON so they can be exported later.
"""
    )
