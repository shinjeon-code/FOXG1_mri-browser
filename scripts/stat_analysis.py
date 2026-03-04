
import pandas as pd
from scipy import stats
import os

input_file = 'processed_mri_data.csv'
output_file = 'statistical_results.csv'

def perform_stats():
    print(f"Loading {input_file}...")
    df = pd.read_csv(input_file)
    
    target_regions = ['ABS_amygdala', 'ABS_thalamus', 'ABS_striatum', 'ABS_cerebral_cortex', 'ABS_hippocampus']
    valid_regions = [c for c in target_regions if c in df.columns]
    
    if not valid_regions:
        valid_regions = df.select_dtypes(include=['float64', 'int']).columns[:5].tolist()
        
    print(f"Analyzing regions: {valid_regions}")
    
    results = []
    
    for region in valid_regions:
        # One-way ANOVA for Genotype
        groups = [group[region].values for name, group in df.groupby('Genotype')]
        if len(groups) > 1:
            f_val, p_val = stats.f_oneway(*groups)
            results.append({
                'Region': region,
                'Test': 'ANOVA Genotype',
                'F-statistic': f_val,
                'p-value': p_val,
                'Significant': p_val < 0.05
            })
            
        # T-test for Sex
        groups_sex = [group[region].values for name, group in df.groupby('Sex')]
        if len(groups_sex) == 2:
            t_val, p_val_sex = stats.ttest_ind(groups_sex[0], groups_sex[1])
            results.append({
                'Region': region,
                'Test': 'T-test Sex',
                'Statistic': t_val,
                'p-value': p_val_sex,
                'Significant': p_val_sex < 0.05
            })

    results_df = pd.DataFrame(results)
    print("\n--- Statistical Results ---")
    print(results_df)
    results_df.to_csv(output_file, index=False)
    print(f"Saved to {output_file}")

if __name__ == "__main__":
    perform_stats()
