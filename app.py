import math
from typing import List

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

MIN_PIPETTABLE_VOLUME_UL = 1.0
NUMERIC_TOLERANCE = 1e-9

st.set_page_config(
    page_title="DNA Mixture Volume Calculator",
    page_icon="🧬",
    layout="centered",
)

# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------


def contributor_label(index: int) -> str:
    """Return A, B, C, D, or E for a contributor index."""
    return chr(ord("A") + index)


def format_ul(value: float) -> str:
    """Format a volume with three decimal places."""
    return f"{value:.3f} µL"


def format_ng(value: float) -> str:
    """Format a mass with four decimal places."""
    return f"{value:.4f} ng"


def format_ng_per_ul(value: float) -> str:
    """Format a concentration with four decimal places."""
    return f"{value:.4f} ng/µL"


def calculate_mixture(df: pd.DataFrame, final_volume_ul: float) -> dict:
    """
    Calculate the highest achievable total DNA mass and final concentration
    while preserving the user-entered DNA mass ratio.

    The final mixture is constrained by:
      - Each contributor's available extract volume
      - The desired final mixture volume
      - The requested contributor DNA mass fractions

    Returns a dictionary containing the results table and summary values.
    """
    results = df.copy()

    total_parts = results["Parts"].sum()
    results["DNA_mass_fraction"] = results["Parts"] / total_parts

    # Required extract volume per 1 ng of total mixture DNA.
    # units: (fraction / ng/µL) = µL/ng
    results["uL_required_per_ng_total_DNA"] = (
        results["DNA_mass_fraction"] / results["Concentration_ng_per_uL"]
    )

    # Maximum total mixture DNA mass that each contributor could support
    # without exceeding the contributor's available extract volume.
    results["Max_total_DNA_mass_supported_by_contributor_ng"] = (
        results["Available_volume_uL"]
        / results["uL_required_per_ng_total_DNA"]
    )

    # Maximum total mixture DNA mass permitted by final volume alone.
    total_uL_per_ng = results["uL_required_per_ng_total_DNA"].sum()
    max_total_DNA_mass_supported_by_final_volume_ng = (
        final_volume_ul / total_uL_per_ng
    )

    # The smaller constraint determines the maximum feasible DNA mass.
    max_total_DNA_mass_by_contributors_ng = (
        results["Max_total_DNA_mass_supported_by_contributor_ng"].min()
    )

    max_total_DNA_mass_ng = min(
        max_total_DNA_mass_by_contributors_ng,
        max_total_DNA_mass_supported_by_final_volume_ng,
    )

    results["Target_DNA_mass_ng"] = (
        max_total_DNA_mass_ng * results["DNA_mass_fraction"]
    )

    results["Required_extract_volume_uL"] = (
        results["Target_DNA_mass_ng"]
        / results["Concentration_ng_per_uL"]
    )

    results["Remaining_extract_volume_uL"] = (
        results["Available_volume_uL"]
        - results["Required_extract_volume_uL"]
    )

    total_extract_volume_ul = results["Required_extract_volume_uL"].sum()
    diluent_volume_ul = final_volume_ul - total_extract_volume_ul
    final_concentration_ng_per_ul = max_total_DNA_mass_ng / final_volume_ul

    contributor_limiter_mask = (
        results["Max_total_DNA_mass_supported_by_contributor_ng"]
        <= max_total_DNA_mass_ng + NUMERIC_TOLERANCE
    )
    final_volume_is_limiter = math.isclose(
        max_total_DNA_mass_ng,
        max_total_DNA_mass_supported_by_final_volume_ng,
        rel_tol=0.0,
        abs_tol=NUMERIC_TOLERANCE,
    )

    return {
        "results": results,
        "total_parts": total_parts,
        "max_total_DNA_mass_ng": max_total_DNA_mass_ng,
        "final_concentration_ng_per_ul": final_concentration_ng_per_ul,
        "total_extract_volume_ul": total_extract_volume_ul,
        "diluent_volume_ul": diluent_volume_ul,
        "max_total_DNA_mass_supported_by_final_volume_ng": (
            max_total_DNA_mass_supported_by_final_volume_ng
        ),
        "contributor_limiter_mask": contributor_limiter_mask,
        "final_volume_is_limiter": final_volume_is_limiter,
    }


# ---------------------------------------------------------------------
# Page content
# ---------------------------------------------------------------------

st.title("DNA Mixture Volume Calculator")
st.caption(
    "Prepare a 2-, 3-, 4-, or 5-contributor DNA mixture at the highest "
    "achievable total DNA concentration while maintaining a requested DNA-mass ratio."
)

st.info(
    "The contributor parts are treated as DNA-mass proportions. For example, "
    "a 1 : 4 : 5 mixture means Contributors A, B, and C provide 10%, 40%, "
    "and 50% of the final DNA mass, respectively."
)

with st.expander("How the calculation works"):
    st.markdown(
        """
The app uses the available DNA extract volume and concentration for every contributor
to determine the **maximum feasible total DNA mass** while preserving the requested
DNA-mass ratio.

It also respects the desired final mixture volume. The app then reports:

- DNA extract volume needed from each contributor
- Diluent volume needed to reach the final mixture volume
- Maximum achievable total DNA mass
- Final mixture concentration in ng/µL
- Validation warnings for insufficient contributor material or volumes below 1 µL
        """
    )

st.header("Mixture setup")

num_contributors = st.selectbox(
    "Number of contributors",
    options=[2, 3, 4, 5],
    index=1,
    help="Choose how many DNA contributors will be included in the mixture.",
)

final_volume_ul = st.number_input(
    "Desired final mixture volume (µL)",
    min_value=0.0,
    value=15.0,
    step=0.5,
    format="%.3f",
    help="The total desired volume after contributor extracts and diluent are combined.",
)

st.header("Contributor measurements")
st.write(
    "Enter the measured concentration and available extract volume for each contributor, "
    "then enter the desired number of parts for the final DNA mixture."
)

contributors: List[dict] = []

for index in range(num_contributors):
    default_name = f"Person {contributor_label(index)}"

    with st.expander(default_name, expanded=True):
        name = st.text_input(
            "Contributor name",
            value=default_name,
            key=f"name_{index}",
        )

        concentration_col, volume_col, parts_col = st.columns(3)

        with concentration_col:
            concentration = st.number_input(
                "DNA concentration (ng/µL)",
                min_value=0.0,
                value=0.50,
                step=0.01,
                format="%.4f",
                key=f"concentration_{index}",
            )

        with volume_col:
            available_volume = st.number_input(
                "Available DNA extract volume (µL)",
                min_value=0.0,
                value=10.0,
                step=0.5,
                format="%.3f",
                key=f"available_volume_{index}",
            )

        with parts_col:
            parts = st.number_input(
                "Desired parts",
                min_value=0.0,
                value=1.0,
                step=1.0,
                format="%.2f",
                key=f"parts_{index}",
            )

        contributors.append(
            {
                "Contributor": name.strip() or default_name,
                "Concentration_ng_per_uL": concentration,
                "Available_volume_uL": available_volume,
                "Parts": parts,
            }
        )

st.header("Calculation")

if st.button("Calculate mixture", type="primary"):
    df = pd.DataFrame(contributors)

    input_errors: List[str] = []

    if final_volume_ul <= 0:
        input_errors.append("The desired final mixture volume must be greater than 0 µL.")

    duplicate_names = df["Contributor"].duplicated(keep=False)
    if duplicate_names.any():
        duplicated = ", ".join(sorted(df.loc[duplicate_names, "Contributor"].unique()))
        input_errors.append(
            f"Each contributor must have a unique name. Duplicate name(s): {duplicated}."
        )

    invalid_concentration = df["Concentration_ng_per_uL"] <= 0
    if invalid_concentration.any():
        names = ", ".join(df.loc[invalid_concentration, "Contributor"])
        input_errors.append(
            f"DNA concentration must be greater than 0 ng/µL for: {names}."
        )

    invalid_available_volume = df["Available_volume_uL"] <= 0
    if invalid_available_volume.any():
        names = ", ".join(df.loc[invalid_available_volume, "Contributor"])
        input_errors.append(
            f"Available extract volume must be greater than 0 µL for: {names}."
        )

    invalid_parts = df["Parts"] <= 0
    if invalid_parts.any():
        names = ", ".join(df.loc[invalid_parts, "Contributor"])
        input_errors.append(
            f"Desired parts must be greater than 0 for: {names}."
        )

    if input_errors:
        for error in input_errors:
            st.error(error)
        st.stop()

    calculation = calculate_mixture(df, final_volume_ul)
    results = calculation["results"]
    max_total_dna_mass_ng = calculation["max_total_DNA_mass_ng"]
    final_concentration_ng_per_ul = calculation["final_concentration_ng_per_ul"]
    total_extract_volume_ul = calculation["total_extract_volume_ul"]
    diluent_volume_ul = calculation["diluent_volume_ul"]

    st.header("Results")

    # Validate contributor availability. This should normally be satisfied because
    # the calculator uses availability to determine the maximum feasible mixture,
    # but it is retained as a defensive check for numerical edge cases.
    insufficient_volume_df = results[
        results["Remaining_extract_volume_uL"] < -NUMERIC_TOLERANCE
    ]

    # Flag any calculated contributor volume below the lab's minimum pipettable volume.
    low_volume_df = results[
        results["Required_extract_volume_uL"] < MIN_PIPETTABLE_VOLUME_UL - NUMERIC_TOLERANCE
    ]

    # Flag whether a negative diluent value appears because of numerical or logic issues.
    negative_diluent = diluent_volume_ul < -NUMERIC_TOLERANCE

    has_recipe_error = False

    if not insufficient_volume_df.empty:
        has_recipe_error = True
        st.error(
            "One or more contributors do not have enough DNA extract volume for the calculated mixture."
        )
        for _, row in insufficient_volume_df.iterrows():
            shortage_ul = abs(row["Remaining_extract_volume_uL"])
            st.error(
                f"**{row['Contributor']}**: requires {format_ul(row['Required_extract_volume_uL'])}, "
                f"but only {format_ul(row['Available_volume_uL'])} is available "
                f"(short by {format_ul(shortage_ul)})."
            )

    if negative_diluent:
        has_recipe_error = True
        st.error(
            "The required contributor extract volumes exceed the requested final mixture volume. "
            "Increase the final volume or revise the contributor inputs."
        )

    if not low_volume_df.empty:
        has_recipe_error = True
        st.error(
            f"One or more required contributor volumes are below the minimum pipettable volume "
            f"of {MIN_PIPETTABLE_VOLUME_UL:.1f} µL."
        )
        for _, row in low_volume_df.iterrows():
            st.error(
                f"**{row['Contributor']}** requires {format_ul(row['Required_extract_volume_uL'])}, "
                f"which is below {MIN_PIPETTABLE_VOLUME_UL:.1f} µL."
            )

    if not has_recipe_error:
        st.success("A feasible mixture recipe was calculated.")

    # Summary metrics
    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric(
        "Final DNA concentration",
        format_ng_per_ul(final_concentration_ng_per_ul),
    )
    metric_2.metric(
        "Total DNA mass",
        format_ng(max_total_dna_mass_ng),
    )
    metric_3.metric(
        "Diluent volume",
        format_ul(max(diluent_volume_ul, 0.0)),
    )

    st.subheader("Pipetting recipe")

    recipe_df = results[
        [
            "Contributor",
            "Parts",
            "Concentration_ng_per_uL",
            "Available_volume_uL",
            "DNA_mass_fraction",
            "Target_DNA_mass_ng",
            "Required_extract_volume_uL",
            "Remaining_extract_volume_uL",
        ]
    ].copy()

    recipe_df = recipe_df.rename(
        columns={
            "Concentration_ng_per_uL": "Concentration (ng/µL)",
            "Available_volume_uL": "Available volume (µL)",
            "DNA_mass_fraction": "DNA mass fraction",
            "Target_DNA_mass_ng": "Target DNA mass (ng)",
            "Required_extract_volume_uL": "Required volume (µL)",
            "Remaining_extract_volume_uL": "Remaining volume (µL)",
        }
    )

    for col in recipe_df.columns:
        if col != "Contributor":
            recipe_df[col] = recipe_df[col].astype(float).round(4)

    st.dataframe(recipe_df, use_container_width=True, hide_index=True)

    st.markdown(
        f"""
**Final mixture volume:** {format_ul(final_volume_ul)}  
**Total contributor extract volume:** {format_ul(total_extract_volume_ul)}  
**Diluent volume:** {format_ul(max(diluent_volume_ul, 0.0))}  
**Total DNA mass:** {format_ng(max_total_dna_mass_ng)}  
**Total DNA concentration in the final mixture:** {format_ng_per_ul(final_concentration_ng_per_ul)}
        """
    )

    st.subheader("Limiting constraint")

    limiting_contributors = results.loc[
        calculation["contributor_limiter_mask"], "Contributor"
    ].tolist()

    if calculation["final_volume_is_limiter"] and limiting_contributors:
        st.write(
            "Both the requested final volume and the following contributor availability "
            "limit the maximum concentration: **"
            + ", ".join(limiting_contributors)
            + "**."
        )
    elif calculation["final_volume_is_limiter"]:
        st.write(
            "The requested final mixture volume is the limiting constraint. "
            "The mixture uses the entire final volume for contributor extract, leaving no diluent."
        )
    else:
        st.write(
            "The limiting contributor(s) are: **"
            + ", ".join(limiting_contributors)
            + "**. Their available DNA extract limits the maximum achievable concentration."
        )

    if has_recipe_error:
        st.warning(
            "The values above show the calculated target. Revise the inputs before preparing the mixture."
        )
    else:
        st.download_button(
            label="Download recipe as CSV",
            data=recipe_df.to_csv(index=False).encode("utf-8"),
            file_name="dna_mixture_recipe.csv",
            mime="text/csv",
        )

st.divider()
st.caption(
    "For laboratory planning only. Verify calculations, pipette specifications, and laboratory SOP requirements before use."
)
