
import pandas as pd
import os

# Define file paths
input_file = 'Raw data_Q84 G216S W300X_Foxg1 KI mutant_MRI ABS and REL volume.csv'
output_file = 'processed_mri_data.csv'

def process_data(input_path, output_path):
    print(f"Reading {input_path}...")
    
    # Read the entire file without header first to understand structure
    # We know:
    # Row 0: Sample IDs (starting col 2)
    # Row 2: Allele
    # Row 3: Sex
    # Row 4: Genotype
    # Row 5+: Data
    
    df_raw = pd.read_csv(input_path, header=None)
    
    # Extract Metadata
    # Columns 2 onwards contain the sample data (Index 0 and 1 are labels)
    sample_ids = df_raw.iloc[0, 2:].values
    alleles = df_raw.iloc[2, 2:].values
    sexes = df_raw.iloc[3, 2:].values
    genotypes = df_raw.iloc[4, 2:].values
    
    # Create a DataFrame for metadata
    df_meta = pd.DataFrame({
        'SampleID': sample_ids,
        'Allele': alleles,
        'Sex': sexes,
        'Genotype': genotypes
    })
    
    print(f"Found {len(df_meta)} samples.")
    
    # Extract Measurements
    # Rows 5 onwards
    # Column 1 contains the specific measurement name (e.g., "ABS_amygdala")
    measurement_names = df_raw.iloc[5:, 1].values
    measurement_data = df_raw.iloc[5:, 2:].values.T # Transpose to (Samples x Features)
    
    # Create DataFrame for measurements
    df_measurements = pd.DataFrame(measurement_data, columns=measurement_names)
    
    # Convert measurements to numeric
    df_measurements = df_measurements.apply(pd.to_numeric, errors='coerce')

    # Combine
    df_final = pd.concat([df_meta, df_measurements], axis=1)
    
    # --- Apply User Grouping Logic ---
    def get_experiment_group(row):
        allele = str(row['Allele']).strip()
        genotype = str(row['Genotype']).strip()
        
        if allele == 'WT':
            return 'WT'
        elif allele == 'Het':
            return f"{genotype}/+"
        elif allele in ['Homo', 'Hom']: # Handle potential variations
            return f"{genotype}/{genotype}"
        else:
            return f"{genotype} ({allele})" # Fallback

    df_final['ExperimentGroup'] = df_final.apply(get_experiment_group, axis=1)
    
    # Reorder columns to put ExperimentGroup near the front
    cols = df_final.columns.tolist()
    # Move ExperimentGroup to index 4 (after Genotype)
    cols.insert(4, cols.pop(cols.index('ExperimentGroup')))
    df_final = df_final[cols]
    
    print("Data processed. Head:")
    print(df_final[['SampleID', 'Genotype', 'Allele', 'ExperimentGroup']].head(10))
    
    # Save
    df_final.to_csv(output_path, index=False)
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    if os.path.exists(input_file):
        process_data(input_file, output_file)
    else:
        print(f"Error: {input_file} not found.")
