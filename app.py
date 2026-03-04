
import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from scipy import stats
import requests
import json
import textwrap

# Allen Atlas Helpers
@st.cache_data
def load_structure_map():
    try:
        with open('structure_graph.json', 'r') as f:
            data = json.load(f)
        nodes = data['msg'] if 'msg' in data else data
        
        mapping = {}
        def flatten(node_list):
            for n in node_list:
                sid = n['id']
                mapping[n['name'].lower()] = sid
                if 'acronym' in n:
                    mapping[n['acronym'].lower()] = sid
                if ',' in n['name']:
                    mapping[n['name'].split(',')[0].strip().lower()] = sid
                if 'children' in n:
                    flatten(n['children'])
        flatten(nodes)
        
        # Manual Overrides for common terms
        overrides = {
            'amygdala': 403, 
            'hippocampus': 1089,
            'basolateral amygdala': 295,
            'striatum': 477,
            'hypothalamus': 1097,
            'midbrain': 313,
            'pons': 771,
            'medulla': 354,
            'cerebellum': 512,
            'thalamus': 549,
            'isocortex': 315
        }
        mapping.update(overrides)
        return mapping
    except Exception as e:
        st.error(f"Failed to load Atlas map: {e}")
        return {}

    except Exception as e:
        st.error(f"Failed to load Atlas map: {e}")
        return {}


def get_atlas_link(region_name, mapping):
    clean = region_name.replace("ABS_", "").replace("REL_", "").replace("_", " ")
    search = clean.lower()
    
    # 1. Exact/Override match
    if search in mapping:
        return f"http://atlas.brain-map.org/atlas?atlas=1&structure={mapping[search]}"
    
    # 2. Fuzzy/Substring check (simple)
    for k, v in mapping.items():
        if search in k or k in search:
            # check word overlap to be safe
            if len(set(search.split()) & set(k.split())) > 0:
                 return f"http://atlas.brain-map.org/atlas?atlas=1&structure={v}"
    
    return None

structure_map = load_structure_map()

# Page Config
st.set_page_config(page_title="MRI Data Browser", layout="wide")

# Data Loading
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('processed_mri_data.csv')
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

df = load_data()

if df is not None:
    # Sidebar
    st.sidebar.title("MRI Browser")
    
    # 1. Search/Select Region
    # Filter columns to find measurements (exclude metadata)
    metadata_cols = ['SampleID', 'Allele', 'Sex', 'Genotype', 'ExperimentGroup']
    all_cols = df.columns.tolist()
    measurement_cols = [c for c in all_cols if c not in metadata_cols]
    
    # Extract Base Regions (remove ABS_ and REL_ prefixes)
    base_regions = sorted(list(set([c.replace('ABS_', '').replace('REL_', '') for c in measurement_cols])))
    
    # Simple search box
    search_term = st.sidebar.text_input("Search Region", "")
    
    # Filter options based on search
    if search_term:
        filtered_options = [c for c in base_regions if search_term.lower() in c.lower()]
    else:
        filtered_options = base_regions
        
    if not filtered_options:
        st.sidebar.warning("No regions found.")
        selected_base_region = None
    else:
        selected_base_region = st.sidebar.selectbox("Select Region", filtered_options)

    # 2. Controls
    st.sidebar.subheader("Filters")
    compare_mode = st.sidebar.radio("Comparison Mode", ["All Groups", "Comparison (WT vs X)"])
    
    selected_comparison = None
    
    # Get unique experiment groups (sorted)
    # Handle NaN in ExperimentGroup just in case
    df['ExperimentGroup'] = df['ExperimentGroup'].fillna('Unknown')
    exp_groups = sorted(df['ExperimentGroup'].unique().tolist())
    
    # Remove WT from options if comparison mode
    mutant_groups = [g for g in exp_groups if g != 'WT']
    
    if compare_mode == "Comparison (WT vs X)":
        selected_comparison = st.sidebar.selectbox("Select Group to Compare with WT", mutant_groups)

    # Main Content
    if selected_base_region:
        st.title(f"Analysis: {selected_base_region}")
        
        # Display Allen Atlas Link (Use Base Region Name)
        atlas_link = get_atlas_link(selected_base_region, structure_map)
        
        if atlas_link:
            st.markdown(f"**🧠 [View in Allen Brain Atlas]({atlas_link})**")
        else:
            st.caption("No direct Atlas link found.")
        
        # Data Filtering
        plot_df = df.copy()
        
        if compare_mode == "Comparison (WT vs X)" and selected_comparison:
            plot_df = plot_df[plot_df['ExperimentGroup'].isin(['WT', selected_comparison])]
        
        group_col = 'ExperimentGroup' 
        
        # Helper function to create chart (Now accepts specific measure column)
        def create_chart(data, measure_col, title_suffix):
            if data.empty:
                st.warning(f"No data for {title_suffix}")
                return
            
            # Check if column exists
            if measure_col not in data.columns:
                st.warning(f"Measurement {measure_col} not found.")
                return

            # Calculate ANOVA context
            valid_groups = [name for name, group in data.groupby(group_col) if len(group) > 1]
            anova_data = [data[data[group_col] == g][measure_col].values for g in valid_groups]
            
            # Helper for p-value formatting
            def format_p_value(p):
                if p < 0.0001:
                    sig = "****"
                elif p < 0.001:
                    sig = "***"
                elif p < 0.01:
                    sig = "**"
                elif p < 0.05:
                    sig = "*"
                else:
                    sig = "ns"
                return f"p={p:.4e} ({sig})" if p < 0.0001 else f"p={p:.4f} ({sig})"

            # --- Normality Check (Shapiro-Wilk) ---
            with st.expander(f"📊 Normality Check ({measure_col})"):
                normality_results = []
                all_normal = True
                for g in valid_groups:
                    group_vals = data[data[group_col] == g][measure_col].values
                    # Shapiro requires N >= 3
                    if len(group_vals) >= 3:
                        s_stat, s_p = stats.shapiro(group_vals)
                        is_normal = s_p > 0.05
                        if not is_normal:
                            all_normal = False
                        normality_results.append({
                            "Group": g,
                            "N": len(group_vals),
                            "p-value": f"{s_p:.4f}",
                            "Normal?": "✅ Yes" if is_normal else "❌ No (p<0.05)"
                        })
                    else:
                        normality_results.append({
                            "Group": g,
                            "N": len(group_vals),
                            "p-value": "N/A",
                            "Normal?": "⚠️ N<3"
                        })
                st.table(pd.DataFrame(normality_results))

            # Pairwise t-tests vs WT
            stats_text = []

            # 1. Kruskal-Wallis (Non-parametric ANOVA equivalent)
            if len(anova_data) > 1:
                 try:
                    # H-statistic and p-value
                    h_stat, p_val = stats.kruskal(*anova_data)
                    stats_text.append(f"KW: {format_p_value(p_val)}")
                 except: pass

            # 2. Pairwise t-tests vs WT & Annotation Data
            annotation_data = []
            max_y = data[measure_col].max()
            y_offset = max_y * 1.05 # Place text 5% above max value
            
            if 'WT' in data[group_col].unique():
                wt_data = data[data[group_col] == 'WT'][measure_col].values
                if len(wt_data) > 1:
                    for g in valid_groups:
                        if g == 'WT': continue
                        group_data = data[data[group_col] == g][measure_col].values
                        if len(group_data) > 1:
                            try:
                                # Mann-Whitney U test
                                u_stat, p_val = stats.mannwhitneyu(wt_data, group_data, alternative='two-sided')
                                
                                # 1. Add to Subtitle (Restore p-values)
                                stats_text.append(f"{g}: {format_p_value(p_val)}")
                                
                                # 2. Add to Annotation (Stars/ns ONLY)
                                sig_symbol = "ns"
                                if p_val < 0.0001: sig_symbol = "****"
                                elif p_val < 0.001: sig_symbol = "***"
                                elif p_val < 0.01: sig_symbol = "**"
                                elif p_val < 0.05: sig_symbol = "*"
                                
                                annotation_data.append({
                                    group_col: g,
                                    measure_col: y_offset,
                                    "text": sig_symbol 
                                })
                            except:
                                pass
            
            # Construct Title
            title_main = f"{measure_col} ({title_suffix})"
            # Restore subtitle
            title_sub = " | ".join(stats_text) if stats_text else "No stats available"

            # Base Chart with random jitter calculation
            base = alt.Chart(data).transform_calculate(
                 # Reduced offset from +/- 0.3 to +/- 0.15 to bring groups closer
                 jitter_val="((datum.Sex == 'M' ? -0.15 : 0.15)) + ((random()-0.5) * 0.2)"
            ).encode(
                x=alt.X(group_col, title='Group'),
                # Wrap long Y-axis titles to 20 chars
                y=alt.Y(measure_col, title=textwrap.wrap(f'{measure_col} Volume', width=20), scale=alt.Scale(domain=[0, max_y * 1.2]))
            )
            
            # Boxplot: Aggregated by Group
            boxplot = base.mark_boxplot(opacity=0.3, color='gray', size=40, outliers=False).encode(
                x=alt.X(group_col, title='Group')
            ).properties(
                title={
                    "text": title_main,
                    "subtitle": title_sub
                }
            )
            
            # Stripplot: Jittered using calculated proportional value
            stripplot = base.mark_circle(size=60, opacity=0.7).encode(
                x=alt.X(group_col, title='Group'), 
                y=alt.Y(measure_col, scale=alt.Scale(zero=False)),
                color=alt.Color('Sex', scale=alt.Scale(domain=['M', 'F'], range=['blue', 'red'])),
                 # Use fixed domain [-1, 1] to map our jitter values [-0.4, 0.4] to the band width
                xOffset=alt.XOffset('jitter_val:Q', scale=alt.Scale(domain=[-1, 1]), title=None)
            ).interactive()
            
            # Stats Text Layer
            text_layer = alt.Chart(pd.DataFrame(annotation_data)).mark_text(
                align='center',
                baseline='bottom',
                dy=-5, # Buffer
                fontSize=12,
                color='black'
            ).encode(
                x=alt.X(group_col),
                y=alt.Y(measure_col),
                text='text'
            )
            
            # Step 120 gives a band of approx 100px.
            chart = (boxplot + stripplot + text_layer).properties(width=alt.Step(60), height=500)
            st.altair_chart(chart, use_container_width=False)
            
            # Summary Stats for this subset
            # st.caption(f"Summary Statistics - {title_suffix}")
            summary_stats = data.groupby([group_col])[measure_col].agg(['count', 'mean', 'std']).reset_index()
            st.dataframe(summary_stats)

        # Tabs for 3 graphs
        tab_all, tab_m, tab_f = st.tabs(["Combined", "Male", "Female"])
        
        # Define Columns
        abs_col = f"ABS_{selected_base_region}"
        rel_col = f"REL_{selected_base_region}"
        
        with tab_all:
            c1, c2 = st.columns(2)
            with c1:
                create_chart(plot_df, abs_col, "Combined")
            with c2:
                create_chart(plot_df, rel_col, "Combined")
            
        with tab_m:
            c1, c2 = st.columns(2)
            with c1:
                create_chart(plot_df[plot_df['Sex'] == 'M'], abs_col, "Male")
            with c2:
                create_chart(plot_df[plot_df['Sex'] == 'M'], rel_col, "Male")
            
        with tab_f:
            c1, c2 = st.columns(2)
            with c1:
                create_chart(plot_df[plot_df['Sex'] == 'F'], abs_col, "Female")
            with c2:
                create_chart(plot_df[plot_df['Sex'] == 'F'], rel_col, "Female")
        
    else:
        st.info("Select a region from the sidebar to view data.")

else:
    st.warning("Processed data file not found. Please run the data preparation scripts first.")
