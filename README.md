# Baseball Computer Vision

Multi-module CV analysis for baseball video. Streamlit UI with one page per module.

## Modules

| Module | Camera view | Status |
|---|---|---|
| Route Efficiency | High home | UI scaffolded (MVP focus) |
| Baserunner Lead + Pop Time | Behind 1B / overhead | Planned |
| Bat Speed | Side view | Planned |
| Barrel Contact Location | Center field | Planned |

## Run locally

```
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Layout

```
streamlit_app.py       Landing page
pages/                 One file per module (Streamlit multi-page)
baseball_cv/           CV core: geometry, per-module metrics, plotting
requirements.txt
```

The CV core exposes pure-function metrics and plotting. The Streamlit pages currently
call mock generators so the UX is reviewable end-to-end; real detection/tracking
(YOLOv8 + ByteTrack is the planned default) will be added per module as sample
footage arrives.
