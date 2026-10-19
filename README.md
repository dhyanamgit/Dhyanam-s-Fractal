
# Newton Fractal Explorer

A Python project where you can explore Newton fractals by zooming in and moving around the image. I made this to experiment with fractals and see how much detail can come out of a simple mathematical formula.

## Features

- Zoom in and out of the fractal
- Move around to explore different areas
- Three different colours for the three roots
- Low-resolution previews while exploring
- Higher-resolution rendering when you stop moving
- Background rendering to keep the window responsive
- More iterations at higher zoom levels

## Requirements

You need Python installed, along with `pygame` and `numpy`.

Install the libraries using:

```bash
pip install pygame numpy
```

## Running the project

Clone or download this repository, open a terminal in the project folder, and run:

```bash
python fractal.py
```

If your file has a different name, replace `fractal.py` with that filename.

## Controls

| Control | Action |
|---|---|
| Mouse wheel | Zoom in or out |
| Left-click | Zoom in at the cursor |
| Right-click and drag | Move around |
| `+` | Zoom in |
| `-` | Zoom out |
| `R` | Reset the view |
| `Esc` | Exit |

## How it works

The fractal is based on Newton's method applied to the equation:

\[
z^3 - 1 = 0
\]

Every point on the screen represents a complex number. The program repeatedly applies Newton's method to see which of the equation's three roots the point approaches.

Each root has its own colour, and the boundaries between the different regions create the fractal patterns.

NumPy handles the calculations, while Pygame displays the image and handles the controls.

## What I learned

This project gave me a chance to work with complex numbers, NumPy arrays, Pygame, and threading. I also experimented with making zooming smoother by rendering a quick preview first and then calculating the full-resolution image.

## Ideas for later

- Add more colour schemes
- Save the current fractal as an image
- Add adjustable rendering quality
- Experiment with different equations
- Improve detail at extreme zoom levels

Feel free to explore the code and make changes!
