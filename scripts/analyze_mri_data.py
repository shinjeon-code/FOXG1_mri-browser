
import pandas as pd
import numpy as np
from scipy import stats

input_file = 'processed_mri_data.csv'

def analyze_data():
    print(f"Loading {input_file}...")
    df = pd.read_csv(input_file)
    
    # Drop columns that are completely empty (often artifacts from CSV conversion)
    df = df.dropna(axis=1, how='all')
    
    print(f"Data shape after dropping empty columns: {df.shape}")
    print("Columns:", df.columns.tolist()[:10], "...")
    
    # Identify measurement columns (excluding metadata)
    metadata_cols = ['SampleID', 'Allele', 'Sex', 'Genotype']
    measurement_cols = [c for c in df.columns if c not in metadata_cols]
    
    print(f"Number of measurement columns: {len(measurement_cols)}")
    
    # Summary Statistics by Genotype
    print("\n--- Summary Statistics by Genotype (Mean of fitst 5 regions) ---")
    summary_genotype = df.groupby('Genotype')[measurement_cols[:5]].agg(['mean', 'std']).round(3)
    print(summary_genotype)
    
    # Summary Statistics by Sex
    print("\n--- Summary Statistics by Sex (Mean of first 5 regions) ---")
    summary_sex = df.groupby('Sex')[measurement_cols[:5]].agg(['mean', 'std']).round(3)
    print(summary_sex)
    
    # Check for missing values in measurements
    missing_counts = df[measurement_cols].isnull().sum()
    total_missing = missing_counts.sum()
    print(f"\nTotal missing values in measurements: {total_missing}")
    if total_missing > 0:
        print("Columns with missing values:", missing_counts[missing_counts > 0])

    # Save summary stats
    summary_genotype.to_csv('summary_stats_genotype.csv')
    print("\nSaved 'summary_stats_genotype.csv'")

if __name__ == "__main__":
    analyze_data()
