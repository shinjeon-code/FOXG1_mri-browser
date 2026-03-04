
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

input_file = 'processed_mri_data.csv'
output_dir = 'plots'

def plot_data():
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    print(f"Loading {input_file}...")
    df = pd.read_csv(input_file)
    
    # Filter for ABS columns (Absolute volume)
    # We'll pick a few key regions for demonstration
    target_regions = ['ABS_amygdala', 'ABS_thalamus', 'ABS_striatum', 'ABS_cerebral_cortex', 'ABS_hippocampus']
    
    # Check which ones exist
    valid_regions = [c for c in target_regions if c in df.columns]
    
    if not valid_regions:
        # Fallback: pick first 5 numeric columns
        valid_regions = df.select_dtypes(include=['float64', 'int']).columns[:5].tolist()
    
    print(f"Plotting regions: {valid_regions}")
    
    # 1. Boxplot by Genotype
    for region in valid_regions:
        plt.figure(figsize=(10, 6))
        sns.boxplot(x='Genotype', y=region, data=df, hue='Sex')
        plt.title(f'{region} Volume by Genotype and Sex')
        plt.ylabel('Volume (mm^3)')
        plt.tight_layout()
        filename = os.path.join(output_dir, f'boxplot_{region}.png')
        plt.savefig(filename)
        plt.close()
        print(f"Saved {filename}")

if __name__ == "__main__":
    plot_data()
