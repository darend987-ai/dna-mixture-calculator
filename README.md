# DNA Mixture Volume Calculator

A Streamlit application for planning 2-, 3-, 4-, or 5-contributor DNA mixtures.

The application accepts, for each contributor:

- DNA concentration in ng/µL
- Available DNA extract volume in µL
- Desired mixture parts

The user also enters the desired final mixture volume. The calculator determines the **maximum feasible total DNA mass and final DNA concentration** while maintaining the requested DNA-mass ratio and staying within contributor-volume and final-volume constraints.

> Example: A 1 : 4 : 5 mixture means the contributors provide 10%, 40%, and 50% of the final mixture's total DNA mass. It does **not** mean the liquid volumes must be in a 1 : 4 : 5 ratio.

## Features

- Interactive input for 2 to 5 contributors
- Calculates contributor-specific DNA extract volumes
- Calculates diluent volume
- Calculates final total DNA concentration in ng/µL
- Identifies the contributor or final-volume condition that limits concentration
- Error messages for:
  - invalid measurements
  - duplicate contributor names
  - insufficient available extract volume
  - required contributor volumes below 1 µL
  - contributor extract volumes that exceed the requested final volume
- CSV export of the calculated recipe

## Calculation model

Let:

- `Cᵢ` = contributor i concentration in ng/µL
- `Vᵢ` = available contributor i extract volume in µL
- `pᵢ` = desired contributor i parts
- `Vfinal` = desired final mixture volume in µL

The desired DNA mass fraction for contributor i is:

`fᵢ = pᵢ / Σp`

For every 1 ng of total DNA in the mixture, the required liquid volume from contributor i is:

`uᵢ = fᵢ / Cᵢ`

The maximum total DNA mass is constrained by both:

1. Contributor availability: `Vᵢ / uᵢ`
2. The desired final mixture volume: `Vfinal / Σuᵢ`

The app uses the smaller limiting value, then calculates:

- contributor DNA mass: `Mtotal × fᵢ`
- contributor volume: `(Mtotal × fᵢ) / Cᵢ`
- final concentration: `Mtotal / Vfinal`
- diluent: `Vfinal - Σ contributor volumes`

## Local installation

1. Install Python 3.10 or newer.
2. Clone this repository:

```bash
git clone https://github.com/YOUR-USERNAME/dna-mixture-calculator.git
cd dna-mixture-calculator
```

3. Create and activate a virtual environment:

```bash
python -m venv .venv
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Run the app:

```bash
streamlit run app.py
```

## GitHub / Streamlit Community Cloud deployment

1. Create a new GitHub repository.
2. Upload `app.py`, `requirements.txt`, `.gitignore`, and `README.md`.
3. In Streamlit Community Cloud, create a new app and select:
   - Repository: your GitHub repository
   - Branch: `main`
   - Main file path: `app.py`
4. Deploy.

## Important laboratory note

This tool is intended for calculation and planning. Confirm mixture design, concentration measurements, minimum pipette volumes, dilution strategy, and all laboratory SOP requirements before creating a mixture.
