#!/usr/bin/env python
#
# This script is used to generate a figure showing the inter-rater variability for individual subjects and spinal
# levels.
# The script also computes a distance from the PMJ to the middle of each spinal level and COV. Results are saved to
# a CSV file.
#
# Usage:
#     python 03a_generate_figure_inter_rater_variablity-PMJ_COV.py -i /path/to/data_processed
#
# Authors: Jan Valosek
#

import os
import sys
import glob
import argparse

import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.patheffects as pe

SUBJECT_TO_AXIS = {
    'sub-barcelona01': 1,
    'sub-brnoUhb03': 2,
    'sub-amu02': 3,
    'sub-007': 4,
    'sub-010': 5,
}
SUBJECT_TO_XTICKS = {
    'sub-barcelona01': 'sub-barcelona01',
    'sub-brnoUhb03': 'sub-brnoUhb03',
    'sub-amu02': 'sub-amu02',
    'sub-007': 'sub-007_ses-headNormal',
    'sub-010': 'sub-010_ses-headUp',
}
LIST_OF_RATER = ['rater1', 'rater2', 'rater3', 'rater4']
RATER_XOFFSET = {'rater1': -0.275, 'rater2': -0.125, 'rater3': 0.025, 'rater4': 0.175}
RATER_COLOR = {'rater1': 'red', 'rater2': 'green', 'rater3': 'blue', 'rater4': 'orange'}


def get_parser():
    """
    parser function
    """

    parser = argparse.ArgumentParser(
        description='Generate a figure showing the inter-rater variability for individual subjects and spinal levels.',
        prog=os.path.basename(__file__).strip('.py')
    )
    parser.add_argument(
        '-i',
        required=True,
        type=str,
        help='Path to the data_processed folder with CSV files for individual subjects and raters generated by the '
             '02a_rootlets_to_spinal_levels.py script.'
    )

    return parser


def generate_figure(df, dir_path):
    """
    Generate a figure showing the inter-rater variability for individual subjects and spinal levels.
    :param df: Pandas DataFrame with the data
    :param dir_path: Path to the data_processed folder
    :return: None
    """
    mpl.rcParams['font.family'] = 'Arial'

    fig = plt.figure(figsize=(11, 6))
    ax = fig.add_subplot()

    # Loop across subjects
    for subject in SUBJECT_TO_AXIS.keys():
        # Loop across raters
        for rater in LIST_OF_RATER:
            # Loop across spinal levels
            for level in df['spinal_level'].unique():
                row = df[(df['subject'] == subject) & (df['rater'] == rater) & (df['spinal_level'] == level)]

                # Skip if the row is empty
                if row.empty:
                    continue

                # Get the distance from PMJ and height of spinal level
                start = float(row['distance_from_pmj_end'])
                height = float(row['height'])

                # Plot rectangle for the subject, rater and spinal level
                ax.add_patch(
                    patches.Rectangle(
                        (SUBJECT_TO_AXIS[subject]+RATER_XOFFSET[rater], start),      # (x,y)
                        0.1,            # width
                        height,         # height
                        color=RATER_COLOR[rater],
                        alpha=0.5,
                    ))

                # Add level number into each rectangle
                ax.text(
                    SUBJECT_TO_AXIS[subject]+RATER_XOFFSET[rater]+0.05,     # x
                    start,                                                  # y
                    int(level),
                    horizontalalignment='center',
                    verticalalignment='center',
                    fontsize=8,
                    color='white',
                    path_effects=[pe.withStroke(linewidth=1, foreground='black')]
                )

                # Add mean value
                ax.plot(
                    [SUBJECT_TO_AXIS[subject]+RATER_XOFFSET[rater], SUBJECT_TO_AXIS[subject]+RATER_XOFFSET[rater]+0.1],
                    [start+height/2, start+height/2],
                    color='black',
                    linewidth=1,
                    alpha=0.5,
                    linestyle='dashed'
                )

    # Adjust the axis limits
    ax.set_xlim(0.5, 5.5)
    ax.set_ylim(min(df['distance_from_pmj_end'].min(), df['distance_from_pmj_start'].min())*0.9,
                max(df['distance_from_pmj_end'].max(), df['distance_from_pmj_start'].max())*1.05)

    # Set axis labels
    ax.set_xlabel('Subject')
    ax.set_ylabel('Distance from PMJ [mm]')

    # Set x-axis ticklabels based on the SUBJECT_TO_AXIS dictionary
    ax.set_xticks(list(SUBJECT_TO_AXIS.values()))
    ax.set_xticklabels(list(SUBJECT_TO_XTICKS.values()))

    # Set y-axis ticks to every 10 mm
    ax.set_yticks(range(40, 170, 10))

    # Reverse ylim
    ax.set_ylim(ax.get_ylim()[::-1])

    # Add horizontal grid
    ax.grid(axis='y', alpha=0.2)
    ax.set_axisbelow(True)

    # Add legend with raters with opacity 0.5
    ax.legend(handles=[
        patches.Patch(color=RATER_COLOR[rater], label=rater, alpha=0.5)
        for rater in LIST_OF_RATER
    ])

    # Add title
    ax.set_title('Spinal Level Inter-Rater Variability - Distance from PMJ')

    # Remove spines
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_visible(True)

    # Save the figure
    fname_figure = 'figure_inter_rater_variability.png'
    fig.savefig(os.path.join(dir_path, fname_figure), dpi=300)
    print(f'Figure saved to {os.path.join(dir_path, fname_figure)}')


def compute_mean_and_COV(df, dir_path):
    """
    Compute the mean distance from PMJ for each subject, rater and spinal level.
    Compute the coefficient of variation (COV) for each subject, rater and spinal level.
    Create a table with the results and save it to a CSV file.
    :param df: Pandas DataFrame with the data
    :param dir_path: Path to the data_processed folder
    :return: None
    """

    results = []

    # Loop across subjects
    for subject in SUBJECT_TO_AXIS.keys():
        # Loop across raters
        for rater in LIST_OF_RATER:
            # Loop across spinal levels
            for level in df['spinal_level'].unique():
                row = df[(df['subject'] == subject) & (df['rater'] == rater) & (df['spinal_level'] == level)]

                # Check if the row is empty
                if row.empty:
                    results.append({'subject': subject, 'rater': rater, 'spinal_level': level, 'mean': 'n/a'})
                else:
                    # Get the distance from PMJ and height of spinal level
                    start = float(row['distance_from_pmj_end'])
                    height = float(row['height'])

                    mean = start + height / 2
                    results.append({'subject': subject, 'rater': rater, 'spinal_level': level, 'mean': mean})

    # Create a pandas DataFrame from the parsed data
    df = pd.DataFrame(results)

    # Reformat the DataFrame to have spinal_levels as rows and subjects and raters as columns
    df = df.pivot(index='spinal_level', columns=['subject', 'rater'], values='mean')

    # For each spinal level and each subject, compute inter-rater coefficient of variation
    for subject in SUBJECT_TO_AXIS.keys():
        df[f'COV_{subject}'] = (df[subject].std(axis=1) / df[subject].mean(axis=1)) * 100

    # Now, compute the mean coefficient of variation across subjects
    df['COV_mean'] = df[[f'COV_{subject}' for subject in SUBJECT_TO_AXIS.keys()]].mean(axis=1)

    # Save the DataFrame to a CSV file
    fname_csv = 'table_inter_rater_variability.csv'
    df.to_csv(os.path.join(dir_path, fname_csv))
    print(f'Table saved to {os.path.join(dir_path, fname_csv)}')


def main():
    # Parse the command line arguments
    parser = get_parser()
    args = parser.parse_args()

    dir_path = os.path.abspath(args.i)

    if not os.path.isdir(dir_path):
        print(f'ERROR: {args.i} does not exist.')
        sys.exit(1)

    # Get all the CSV files in the directory generated by the 02a_rootlets_to_spinal_levels.py script
    csv_files = glob.glob(os.path.join(dir_path, '**', '*label-rootlet*_pmj_distance.csv'), recursive=True)
    # if csv_files is empty, exit
    if len(csv_files) == 0:
        print(f'ERROR: No CSV files found in {dir_path}')

    # Initialize an empty list to store the parsed data
    parsed_data = []

    # Loop across CSV files and aggregate the results into pandas dataframe
    for csv_file in csv_files:
        df_file = pd.read_csv(csv_file)
        parsed_data.append(df_file)

    # Combine list of dataframes into one dataframe
    df = pd.concat(parsed_data)

    # Keep only cervical levels (2 to 8)
    df = df[df['spinal_level'].isin([2, 3, 4, 5, 6, 7, 8])]

    # Extract rater from the fname and add it as a column
    df['rater'] = df['fname'].apply(lambda x: x.split('_')[-1].split('.')[0])
    # Extract subjectID from the fname and add it as a column
    df['subject'] = df['fname'].apply(lambda x: x.split('_')[0])

    # Generate the figure
    generate_figure(df, dir_path)

    # Compute the mean distance from PMJ for each subject, rater and spinal level.
    # Compute the coefficient of variation (COV) for each subject, rater and spinal level.
    compute_mean_and_COV(df, dir_path)


if __name__ == '__main__':
    main()
