# Dataset Generator

A Python-based desktop application with a graphical interface (GUI) designed to generate synthetic image datasets of manometers from real photographs. It allows users to extract manometer needles, clean the background, mark geometric limits (minimum/maximum values and angles), and automatically produce combinatorial datasets using various dials and needles.

## Features
- **Module 1: Needle Extraction** - Segment and extract needles from original photographs interactively.
- **Module 2: Manometer Geometry** - Define the center of rotation, minimum value, and maximum value points.
- **Module 3: Needle Normalization** - Adjust needle pivot points to align them properly for rotation.
- **Module 4: Background Cleaning** - Inpaint and remove the needle from the original dial image to create a clean background.
- **Module 5: Combinatorial Generation** - Combine multiple clean dials and normalized needles to generate large, truly randomized datasets simulating any value between the defined min and max.
- **Randomization:** Uses true randomization for each generation task to ensure that the dataset varies entirely across different runs, dials, and needles.

## Technologies Used
- Python
- PySide6 (for the graphical interface)
- OpenCV (for image processing, masking, and inpainting)
- NumPy
- Pillow (PIL)

## Project Structure
- `manometer_app/`: Main application directory, containing core logic, views, and custom widgets.
- `assets/`: Contains the original images, clean dials, masks, and intermediate files.
- `generated_dataset/`: Output directory where the combinatorial dataset is saved.
- `generate_dataset.py`, `process_originals.py`, `manual_annotate.py`, `auto_annotate.py`: Helper CLI scripts.
- `augmentations.py`: Handles graphical enhancements like shadows, lighting, and reflections.

## Usage
Run the main PySide6 application to start the GUI. 
Use the UI modules sequentially:
1. Extract needles.
2. Define manometer geometry.
3. Normalize your needles.
4. Clean your manometer dials.
5. Generate combinatorial datasets in the final module.

## Output
The final combinatorial module produces a folder containing:
- `images/`: The synthesized manometers with needles superimposed.
- `labels/`: Corresponding JSON/TXT files with ground truth data (value, angle, center, and bounding boxes).
