import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import re

# Set page config
st.set_page_config(
    page_title="RINL Delay Analysis & Prediction System",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling (Dark Theme with glassmorphism cards and neon details)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&family=Plus+Jakarta+Sans:wght@400;500;700&display=swap');
    
    /* Main container background */
    .stApp {
        background: radial-gradient(circle at 10% 20%, #0d1117 0%, #0b0e14 90%);
        color: #c9d1d9;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Header styling */
    .main-title {
        font-family: 'Outfit', sans-serif;
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #58a6ff 10%, #bc8cff 50%, #ff7b72 90%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
        letter-spacing: -0.5px;
    }
    
    .subtitle {
        font-size: 1.1rem;
        color: #8b949e;
        margin-bottom: 1.8rem;
        font-weight: 400;
    }
    
    /* Global Alert Banner */
    .alert-banner {
        background: linear-gradient(90deg, rgba(255, 123, 114, 0.15) 0%, rgba(255, 123, 114, 0.05) 100%);
        border-left: 4px solid #ff7b72;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        box-shadow: 0 4px 15px rgba(255, 123, 114, 0.1);
    }
    
    .alert-title {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        color: #ff7b72;
        font-size: 1rem;
    }
    
    /* Card Container with glassmorphism */
    .metric-card {
        background: rgba(22, 27, 34, 0.45);
        border: 1px solid rgba(48, 54, 61, 0.75);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        margin-bottom: 1rem;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    }
    .metric-card:hover {
        transform: translateY(-4px);
        border-color: rgba(88, 166, 255, 0.7);
        box-shadow: 0 12px 30px rgba(88, 166, 255, 0.15);
    }
    
    /* Card labels */
    .metric-label {
        font-size: 0.85rem;
        text-transform: uppercase;
        color: #8b949e;
        letter-spacing: 1.2px;
        margin-bottom: 0.6rem;
        font-weight: 500;
    }
    
    /* Card values */
    .metric-value {
        font-family: 'Outfit', sans-serif;
        font-size: 2.1rem;
        font-weight: 700;
        color: #f0f6fc;
        line-height: 1.2;
    }
    .metric-trend {
        font-size: 0.85rem;
        margin-top: 0.4rem;
        font-weight: 500;
    }
    .trend-up {
        color: #ff7b72;
    }
    .trend-down {
        color: #3fb950;
    }
    
    /* Styling Streamlit components */
    div[data-testid="stSidebar"] {
        background-color: #0d1117;
        border-right: 1px solid #21262d;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: rgba(22, 27, 34, 0.5);
        padding: 8px 16px;
        border-radius: 12px;
        border: 1px solid #21262d;
        margin-bottom: 1.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 44px;
        background-color: transparent;
        border-radius: 8px;
        color: #8b949e;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.25s;
        padding: 0 16px;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #f0f6fc;
        background-color: rgba(48, 54, 61, 0.4);
    }
    .stTabs [aria-selected="true"] {
        color: #58a6ff !important;
        background-color: #21262d !important;
        border-bottom: 2px solid #58a6ff !important;
        box-shadow: 0 4px 12px rgba(88, 166, 255, 0.08);
    }
    
    /* Custom button styling */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #1f6feb 0%, #58a6ff 100%);
        color: white;
        border: none;
        padding: 0.6rem 1.8rem;
        border-radius: 8px;
        font-weight: 600;
        font-family: 'Outfit', sans-serif;
        letter-spacing: 0.5px;
        transition: all 0.3s;
        box-shadow: 0 4px 15px rgba(88, 166, 255, 0.2);
    }
    div.stButton > button:first-child:hover {
        transform: scale(1.03);
        box-shadow: 0 6px 20px rgba(88, 166, 255, 0.4);
        border: none;
    }
    
    /* Section containers styling */
    .section-container {
        background: rgba(22, 27, 34, 0.25);
        border: 1px solid rgba(48, 54, 61, 0.4);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to load cleaned delays dataset
@st.cache_data
def load_data():
    # Attempt to load from MySQL database
    try:
        conn = st.connection('mysql', type='sql')
        df = conn.query('SELECT * FROM delays;', ttl=600)
        if df is not None and not df.empty:
            # MySQL DATE type is parsed to datetime natively
            df['DATE'] = pd.to_datetime(df['DEL_DATE'])
            return df
    except Exception as e:
        # DB connection failed, fallback to CSV
        pass

    # Local CSV backup fallback
    clean_csv_path = r"c:\Users\Prethikesh\Desktop\RINL\cleaned_delays_data.csv"
    if not os.path.exists(clean_csv_path):
        return None
    df = pd.read_csv(clean_csv_path)
    df['DATE'] = pd.to_datetime(df['DEL_DATE'], format='%d-%m-%Y')
    return df

df_all = load_data()

if df_all is None:
    st.error("Cleaned data file not found! Please run the data cleaning script `clean_data.py` first.")
else:
    # --- Sidebar Configuration & Inputs ---
    logo_path = r"c:\Users\Prethikesh\Desktop\RINL\rinl_logo.svg"
    if os.path.exists(logo_path):
        sb_col1, sb_col2, sb_col3 = st.sidebar.columns([1, 2, 1])
        with sb_col2:
            st.sidebar.image(logo_path, use_container_width=True)
            
    st.sidebar.markdown("<h2 style='text-align: center; color: #58a6ff; font-family: Outfit; margin-top: 0px;'>🎛️ Control Panel</h2>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    
    # Date/Month Range Selector
    available_mon_rr = sorted(df_all['MON_RR'].unique(), key=lambda x: datetime.strptime(x, '%b-%y'))
    
    selected_months = st.sidebar.multiselect(
        "📅 Select Months (MON-RR)",
        options=available_mon_rr,
        default=available_mon_rr
    )
    
    # Filter by selected months
    if not selected_months:
        df_filtered_months = df_all.copy()
    else:
        df_filtered_months = df_all[df_all['MON_RR'].isin(selected_months)]
        
    # Shop Dropdown (Combobox + All)
    shop_options = ["All"] + sorted(df_filtered_months['SHOP_DESC'].unique())
    selected_shop = st.sidebar.selectbox("🏬 Select Shop", options=shop_options)
    
    # Agency Dropdown (Combobox + All)
    agency_options = ["All"] + sorted(df_filtered_months['AGENCY_CODE'].dropna().unique())
    selected_agency = st.sidebar.selectbox("👷 Select Agency Responsibiltiy", options=agency_options)
    
    # Downtime Cost Setup inside sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💰 Shop Cost Rates")
    st.sidebar.markdown("<small>Hourly downtime financial loss rate (₹):</small>", unsafe_allow_html=True)
    
    shops_for_cost = sorted(df_all['SHOP_DESC'].unique())
    cost_rates = {}
    default_costs = {
        'SMS': 50000, 'SMS2': 55000,
        'BF': 45000,
        'BAR MILL': 30000, 'BILLET MILL': 30000, 'BAR/BILLET MILL': 30000, 'WRM': 25000, 'WRM2': 28000, 'MMSM': 25000, 'SBM': 22000,
        'CO': 20000, 'RMHP': 15000,
        'TPP': 12000, 'UTIL': 10000, 'CRMP': 8000, 'DNW': 8000
    }
    
    for shop in shops_for_cost:
        default_val = default_costs.get(shop, 15000)
        cost_rates[shop] = st.sidebar.slider(
            f"{shop} (₹/hr)",
            min_value=5000,
            max_value=100000,
            value=default_val,
            step=5000
        )
        
    # Apply primary filters to dataset
    df_filtered = df_filtered_months.copy()
    if selected_shop != "All":
        df_filtered = df_filtered[df_filtered['SHOP_DESC'] == selected_shop]
    if selected_agency != "All":
        df_filtered = df_filtered[df_filtered['AGENCY_CODE'] == selected_agency]
        
    # Add Cost column based on filter and selected cost settings
    df_filtered['COST'] = df_filtered['EFF_DURATION'] * df_filtered['SHOP_DESC'].map(cost_rates)
    df_filtered_months['COST'] = df_filtered_months['EFF_DURATION'] * df_filtered_months['SHOP_DESC'].map(cost_rates)
    df_all['COST'] = df_all['EFF_DURATION'] * df_all['SHOP_DESC'].map(cost_rates)
    
    # Scale total operating time based on selected months to make MTBF accurate when filtering
    if selected_months:
        total_op_hours = len(selected_months) * 30.4 * 24.0
    else:
        total_op_hours = len(available_mon_rr) * 30.4 * 24.0
    
    df_rel = df_filtered.groupby(['EQPT', 'SHOP_DESC']).agg(
        total_downtime=('EFF_DURATION', 'sum'),
        incidents=('EFF_DURATION', 'count')
    ).reset_index()
    
    df_rel = df_rel[(df_rel['incidents'] > 2) & (df_rel['EQPT'] != 'UNKNOWN')]
    df_rel['MTTR'] = df_rel['total_downtime'] / df_rel['incidents']
    df_rel['MTBF'] = (total_op_hours - df_rel['total_downtime']) / df_rel['incidents']
    
    # Calculate MTBF/MTTR averages for quadrants
    median_mttr = df_rel['MTTR'].median() if len(df_rel) > 0 else 1.0
    median_mtbf = df_rel['MTBF'].median() if len(df_rel) > 0 else 100.0
    
    # Failure probability in next 7 days based on Weibull
    max_date = df_filtered['DATE'].max()
    cutoff_30d = max_date - timedelta(days=30)
    df_30d = df_filtered[df_filtered['DATE'] >= cutoff_30d]
    df_30d_stats = df_30d.groupby('EQPT').agg(
        recent_downtime=('EFF_DURATION', 'sum'),
        recent_incidents=('EFF_DURATION', 'count')
    ).reset_index()
    
    df_forecast = pd.merge(df_30d_stats, df_rel, on='EQPT', how='inner')
    df_forecast['expected_failures_30d'] = 720.0 / df_forecast['MTBF']
    df_forecast['frequency_degradation_ratio'] = df_forecast['recent_incidents'] / (df_forecast['expected_failures_30d'] + 0.1)
    df_forecast['EDI'] = (df_forecast['frequency_degradation_ratio'] * 40.0) + (df_forecast['MTTR'] * 10.0)
    df_forecast['EDI'] = df_forecast['EDI'].apply(lambda x: min(100.0, max(5.0, x)))
    df_forecast['Failure_Probability_7d'] = 1.0 - np.exp(- (168.0 / df_forecast['MTBF']) ** 1.4)
    df_forecast['Failure_Probability_7d'] = df_forecast['Failure_Probability_7d'].apply(lambda p: min(0.99, p))
    
    # High risk assets filter
    high_risk_assets = df_forecast[df_forecast['Failure_Probability_7d'] >= 0.65]
    
    # --- Main Header ---
    logo_path = r"c:\Users\Prethikesh\Desktop\RINL\rinl_logo.svg"
    if os.path.exists(logo_path):
        h_col1, h_col2 = st.columns([1, 10])
        with h_col1:
            st.image(logo_path, width=70)
        with h_col2:
            st.markdown("<h1 class='main-title' style='margin-bottom: 0px; padding-top: 0px;'>RINL Delay Analysis & Prediction Dashboard</h1>", unsafe_allow_html=True)
    else:
        st.markdown("<h1 class='main-title'>⚡ RINL Delay Analysis & Prediction Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Auditing operational bottlenecks, MTBF/MTTR criticality mapping, and forecasting failures (2023 - 2025)</div>", unsafe_allow_html=True)
    
    # --- Global Alert Banner ---
    if len(high_risk_assets) > 0:
        urgent_list = ", ".join(high_risk_assets.sort_values('Failure_Probability_7d', ascending=False).head(3)['EQPT'].tolist())
        st.markdown(f"""
        <div class='alert-banner'>
            <span style='font-size: 1.5rem;'>⚠️</span>
            <div>
                <div class='alert-title'>Urgent Reliability Alert (Failure Probability >= 65% in next 7 days)</div>
                <div style='font-size: 0.9rem; color: #ffb8b2;'>Critical Maintenance Recommended for: <strong>{urgent_list}</strong>. Review predictive timelines for details.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # --- Top Metric Cards ---
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    
    total_duration = df_filtered['EFF_DURATION'].sum()
    total_incidents = len(df_filtered)
    avg_durn = df_filtered['EFF_DURATION'].mean() if total_incidents > 0 else 0
    total_cost = df_filtered['COST'].sum()
    avg_cost_per_incident = total_cost / total_incidents if total_incidents > 0 else 0
    
    with m_col1:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-label'>⏳ Total Delay Time</div>
            <div class='metric-value'>{total_duration:,.1f} Hrs</div>
            <div class='metric-trend' style='color: #58a6ff;'>📊 {total_incidents:,} Breakdown logs</div>
        </div>
        """, unsafe_allow_html=True)
        
    with m_col2:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-label'>📋 Avg Incident Duration</div>
            <div class='metric-value'>{avg_durn:.2f} Hrs</div>
            <div class='metric-trend' style='color: #8b949e;'>⏰ Median: {df_filtered['EFF_DURATION'].median() if total_incidents > 0 else 0:.2f} Hrs</div>
        </div>
        """, unsafe_allow_html=True)
        
    with m_col3:
        top_shop_metric = df_filtered['SHOP_DESC'].value_counts().index[0] if len(df_filtered) > 0 else "N/A"
        top_shop_hours = df_filtered.groupby('SHOP_DESC')['EFF_DURATION'].sum().max() if len(df_filtered) > 0 else 0
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-label'>🏢 Top Downtime Shop</div>
            <div class='metric-value'>{top_shop_metric}</div>
            <div class='metric-trend trend-up'>📈 {top_shop_hours:,.1f} Total Hours</div>
        </div>
        """, unsafe_allow_html=True)
        
    with m_col4:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-label'>💸 Downtime Cost Loss</div>
            <div class='metric-value'>₹{total_cost:,.0f}</div>
            <div class='metric-trend trend-up'>💰 Avg Loss: ₹{avg_cost_per_incident:,.0f}/inc</div>
        </div>
        """, unsafe_allow_html=True)
        
    # --- Tabbed Layout ---
    tabs = st.tabs([
        "📊 Shop & Agency Delays",
        "⚙️ Equipment & Conveyors",
        "⏰ Duration & Shift Wise",
        "💬 Remarks Text Mining",
        "💵 Downtime Cost Analysis",
        "🎯 Criticality (MTTR/MTBF)",
        "🔮 Failure Prediction Index",
        "⛈️ Monsoon Hazard & Simulator"
    ])
    
    # ------------------ TAB 1: Shop & Agency Wise Delays ------------------
    with tabs[0]:
        st.markdown("### 🏬 Shop Wise and Agency Wise Delays Breakdown")
        
        # Metric toggle at the top of the tab
        t1_metric = st.radio(
            "Select Metric to Visualize:",
            options=["Downtime Duration (Hours)", "Breakdown Log Count (Incidents)"],
            horizontal=True,
            key="t1_metric_toggle"
        )
        
        t1_graph_col1, t1_graph_col2 = st.columns(2)
        
        with t1_graph_col1:
            # Shop wise breakdown
            df_shop = df_filtered.groupby('SHOP_DESC')['EFF_DURATION'].agg(['sum', 'count']).reset_index()
            df_shop.columns = ['Shop Description', 'Total Duration (Hrs)', 'Breakdown Count']
            
            y_col = 'Shop Description'
            x_col = 'Total Duration (Hrs)' if t1_metric == "Downtime Duration (Hours)" else 'Breakdown Count'
            text_fmt = '.1f' if t1_metric == "Downtime Duration (Hours)" else ',d'
            
            fig_shop = px.bar(
                df_shop,
                x=x_col,
                y=y_col,
                orientation='h',
                text_auto=text_fmt,
                title=f"Shop-wise {'Downtime Hours' if t1_metric == 'Downtime Duration (Hours)' else 'Incident Count'}",
                color=x_col,
                color_continuous_scale='Blues'
            )
            fig_shop.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#c9d1d9',
                font_family='Plus Jakarta Sans',
                xaxis={'gridcolor': '#21262d'},
                yaxis={'categoryorder': 'total ascending', 'gridcolor': '#21262d'},
                coloraxis_showscale=False,
                margin=dict(l=20, r=20, t=40, b=20),
                height=450
            )
            st.plotly_chart(fig_shop, width='stretch')
            
        with t1_graph_col2:
            # Agency wise breakdown
            df_agency = df_filtered.groupby('AGENCY_CODE')['EFF_DURATION'].agg(['sum', 'count']).reset_index()
            df_agency.columns = ['Agency Code', 'Total Duration (Hrs)', 'Breakdown Count']
            
            y_col_ag = 'Agency Code'
            x_col_ag = 'Total Duration (Hrs)' if t1_metric == "Downtime Duration (Hours)" else 'Breakdown Count'
            
            fig_agency = px.bar(
                df_agency,
                x=x_col_ag,
                y=y_col_ag,
                orientation='h',
                text_auto=text_fmt,
                title=f"Agency-wise {'Downtime Hours' if t1_metric == 'Downtime Duration (Hours)' else 'Incident Count'}",
                color=x_col_ag,
                color_continuous_scale='Purples'
            )
            fig_agency.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#c9d1d9',
                font_family='Plus Jakarta Sans',
                xaxis={'gridcolor': '#21262d'},
                yaxis={'categoryorder': 'total ascending', 'gridcolor': '#21262d'},
                coloraxis_showscale=False,
                margin=dict(l=20, r=20, t=40, b=20),
                height=450
            )
            st.plotly_chart(fig_agency, width='stretch')
            
        t1_tbl_col1, t1_tbl_col2 = st.columns(2)
        
        with t1_tbl_col1:
            st.markdown("#### 🏬 Shop-wise Delay Summary Table")
            df_shop_sorted = df_shop.sort_values('Total Duration (Hrs)', ascending=False)
            st.dataframe(
                df_shop_sorted.style.format({
                    'Total Duration (Hrs)': '{:,.1f}',
                    'Breakdown Count': '{:,}'
                }),
                width='stretch',
                hide_index=True
            )
            
        with t1_tbl_col2:
            st.markdown("#### 👷 Agency-wise Delay Summary Table")
            df_agency_sorted = df_agency.sort_values('Total Duration (Hrs)', ascending=False)
            st.dataframe(
                df_agency_sorted.style.format({
                    'Total Duration (Hrs)': '{:,.1f}',
                    'Breakdown Count': '{:,}'
                }),
                width='stretch',
                hide_index=True
            )
            
        # Add an expander for monthly trends over time
        with st.expander("📅 View Monthly Delay Trend Details (MON - RR)"):
            df_trend = df_filtered.copy()
            df_trend['SORT_DATE'] = df_trend['DATE'].apply(lambda x: x.replace(day=1))
            df_trend_grouped = df_trend.groupby(['SORT_DATE', 'MON_RR', 'SHOP_DESC'])['EFF_DURATION'].sum().reset_index()
            df_trend_grouped = df_trend_grouped.sort_values('SORT_DATE')
            
            fig_trend = px.bar(
                df_trend_grouped,
                x='MON_RR',
                y='EFF_DURATION',
                color='SHOP_DESC',
                title='Monthly Delay Duration Trend by Shop (MON - RR)',
                labels={'EFF_DURATION': 'Downtime Hours', 'MON_RR': 'Month-Year'},
                color_discrete_sequence=px.colors.qualitative.Dark24
            )
            fig_trend.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#c9d1d9',
                font_family='Plus Jakarta Sans',
                xaxis={'gridcolor': '#21262d'},
                yaxis={'gridcolor': '#21262d'},
                legend={'bgcolor': 'rgba(22, 27, 34, 0.5)', 'bordercolor': '#21262d', 'borderwidth': 1}
            )
            st.plotly_chart(fig_trend, width='stretch')
            
    # ------------------ TAB 2: Equipment & Conveyor Delays ------------------
    with tabs[1]:
        st.markdown("### ⚙️ Equipment and Conveyor Wise Delays")
        
        t2_col1, t2_col2 = st.columns([1, 1])
        
        with t2_col1:
            st.markdown("#### 🔝 Top 15 Bottleneck Equipment")
            df_eqpt_sum = df_filtered.groupby(['EQPT', 'SHOP_DESC'])['EFF_DURATION'].agg(['sum', 'count']).reset_index()
            df_eqpt_sum.columns = ['Equipment', 'Shop', 'Total Downtime (Hrs)', 'Failures Count']
            df_eqpt_sum = df_eqpt_sum.sort_values('Total Downtime (Hrs)', ascending=False).head(15)
            
            fig_eqpt = px.bar(
                df_eqpt_sum,
                x='Total Downtime (Hrs)',
                y='Equipment',
                color='Shop',
                orientation='h',
                title='Top 15 Equipment Bottlenecks by Total Downtime',
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_eqpt.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#c9d1d9',
                font_family='Plus Jakarta Sans',
                xaxis={'gridcolor': '#21262d'},
                yaxis={'categoryorder': 'total ascending', 'gridcolor': '#21262d'},
                legend={'bgcolor': 'rgba(22, 27, 34, 0.5)', 'bordercolor': '#21262d', 'borderwidth': 1}
            )
            st.plotly_chart(fig_eqpt, width='stretch')
            
        with t2_col2:
            st.markdown("#### 🚊 Conveyor-Specific Delays")
            df_conv = df_filtered[df_filtered['IS_CONVEYOR'] == True]
            total_conv_dur = df_conv['EFF_DURATION'].sum()
            total_conv_count = len(df_conv)
            
            st.info(f"💡 Identified **{total_conv_count:,} conveyor-related delay logs** representing **{total_conv_dur:,.1f} downtime hours** within selected filters.")
            
            if total_conv_count > 0:
                df_conv_grouped = df_conv.groupby('SUB_EQPT')['EFF_DURATION'].agg(['sum', 'count']).reset_index()
                df_conv_grouped.columns = ['Conveyor ID', 'Downtime (Hrs)', 'Incident Count']
                df_conv_grouped = df_conv_grouped.sort_values('Downtime (Hrs)', ascending=False).head(15)
                
                fig_conv = px.bar(
                    df_conv_grouped,
                    x='Conveyor ID',
                    y='Downtime (Hrs)',
                    color='Incident Count',
                    title='Top 15 Most Delayed Conveyor Systems',
                    color_continuous_scale='Reds'
                )
                fig_conv.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#c9d1d9',
                    font_family='Plus Jakarta Sans',
                    xaxis={'gridcolor': '#21262d'},
                    yaxis={'gridcolor': '#21262d'}
                )
                st.plotly_chart(fig_conv, width='stretch')
            else:
                st.write("No conveyor delays found for the current filter criteria.")
                
    # ------------------ TAB 3: Duration & Shift Wise Delays ------------------
    with tabs[2]:
        st.markdown("### ⏱️ Duration & Shift Wise Delay Distributions")
        
        # Start Time Parsing for Shift Analysis
        def get_shift(val):
            if pd.isnull(val):
                return 'Unknown'
            hour = int(val)
            if 6 <= hour < 14:
                return 'Shift A (06:00 - 14:00)'
            elif 14 <= hour < 22:
                return 'Shift B (14:00 - 22:00)'
            else:
                return 'Shift C (22:00 - 06:00)'
                
        df_filtered['SHIFT'] = df_filtered['DELAY_FROM'].apply(get_shift)
        
        t3_col1, t3_col2 = st.columns(2)
        
        with t3_col1:
            df_shift = df_filtered.groupby('SHIFT')['EFF_DURATION'].agg(['sum', 'count']).reset_index()
            df_shift.columns = ['Shift', 'Total Hours', 'Incident Count']
            
            fig_shift = px.bar(
                df_shift,
                x='Shift',
                y='Total Hours',
                text_auto='.1f',
                title='Total Delay Duration (Hrs) by Work Shift',
                color='Shift',
                color_discrete_sequence=['#58a6ff', '#bc8cff', '#ff7b72']
            )
            fig_shift.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#c9d1d9',
                font_family='Plus Jakarta Sans',
                xaxis={'gridcolor': '#21262d'},
                yaxis={'gridcolor': '#21262d'},
                showlegend=False
            )
            st.plotly_chart(fig_shift, width='stretch')
            
        with t3_col2:
            def categorize_duration(d):
                if d <= 0.25:
                    return '1. Micro Delay (< 15 mins)'
                elif d <= 1.0:
                    return '2. Short Delay (15 mins - 1 hr)'
                elif d <= 4.0:
                    return '3. Medium Delay (1 - 4 hrs)'
                elif d <= 12.0:
                    return '4. Long Delay (4 - 12 hrs)'
                else:
                    return '5. Mega Delay (> 12 hrs)'
                    
            df_filtered['DURATION_BRACKET'] = df_filtered['EFF_DURATION'].apply(categorize_duration)
            df_bracket = df_filtered.groupby('DURATION_BRACKET')['EFF_DURATION'].agg(['sum', 'count']).reset_index()
            df_bracket.columns = ['Duration Category', 'Total Hours', 'Incident Count']
            df_bracket = df_bracket.sort_values('Duration Category')
            
            fig_bracket = px.pie(
                df_bracket,
                names='Duration Category',
                values='Incident Count',
                title='Distribution of Breakdown Severity (Incident Count)',
                hole=0.45,
                color_discrete_sequence=px.colors.sequential.Viridis
            )
            fig_bracket.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#c9d1d9',
                font_family='Plus Jakarta Sans',
                legend={'bgcolor': 'rgba(22, 27, 34, 0.5)', 'bordercolor': '#21262d', 'borderwidth': 1}
            )
            st.plotly_chart(fig_bracket, width='stretch')
            
        st.markdown("#### ⏳ Histogram of Delay Durations (Log Scale)")
        max_limit = st.slider("Filter Histogram Durations Up To (Hours):", min_value=1.0, max_value=24.0, value=12.0, step=1.0)
        df_hist = df_filtered[df_filtered['EFF_DURATION'] <= max_limit]
        
        fig_hist = px.histogram(
            df_hist,
            x='EFF_DURATION',
            nbins=40,
            title=f'Histogram of Delay Durations (<= {max_limit} Hrs)',
            labels={'EFF_DURATION': 'Downtime Duration (Hours)'},
            color_discrete_sequence=['#58a6ff']
        )
        fig_hist.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#c9d1d9',
            font_family='Plus Jakarta Sans',
            xaxis={'gridcolor': '#21262d'},
            yaxis={'gridcolor': '#21262d'}
        )
        st.plotly_chart(fig_hist, width='stretch')

    # ------------------ TAB 4: Remarks Text Mining ------------------
    with tabs[3]:
        st.markdown("### 💬 Remarks Text Mining & Description Analysis")
        
        search_query = st.text_input("🔍 Search Remarks by Keyword (e.g., 'motor', 'broken', 'leak', 'fire', 'jam'):", value="broken")
        
        if search_query:
            df_search = df_filtered[df_filtered['REMARKS'].dropna().str.contains(search_query, case=False, regex=True)]
            search_dur = df_search['EFF_DURATION'].sum()
            search_count = len(df_search)
            
            st.write(f"Found **{search_count:,} records** matching query. Cumulative Downtime: **{search_dur:,.1f} Hours** (Average: {search_dur/search_count if search_count>0 else 0:.2f} Hrs)")
            
            st.dataframe(
                df_search[['DEL_DATE', 'SHOP_DESC', 'EQPT', 'SUB_EQPT', 'EFF_DURATION', 'AGENCY_CODE', 'REMARKS']].head(100),
                width='stretch',
                hide_index=True
            )
            
        st.markdown("#### 📊 Most Common Maintenance Terms in Logs")
        all_remarks = " ".join(df_filtered['REMARKS'].dropna().astype(str).tolist()).lower()
        words = re.findall(r'\b[a-z]{3,}\b', all_remarks)
        stop_words = {
            'the', 'and', 'for', 'due', 'stop', 'idle', 'std', 'down', 'line', 'with', 'from',
            'not', 'out', 'off', 'offtake', 'take', 'clean', 'working', 'chg', 'pwt', 'chk',
            'change', 'stream', 'running', 'demand', 'loading', 'record', 'delete', 'dont'
        }
        filtered_words = [w for w in words if w not in stop_words]
        
        word_series = pd.Series(filtered_words).value_counts().head(20).reset_index()
        word_series.columns = ['Maintenance Term', 'Frequency']
        
        fig_words = px.bar(
            word_series,
            x='Frequency',
            y='Maintenance Term',
            orientation='h',
            title='Top 20 Technical/Failure Keywords in Remarks',
            color='Frequency',
            color_continuous_scale='Blues'
        )
        fig_words.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#c9d1d9',
            font_family='Plus Jakarta Sans',
            xaxis={'gridcolor': '#21262d'},
            yaxis={'categoryorder': 'total ascending', 'gridcolor': '#21262d'}
        )
        st.plotly_chart(fig_words, width='stretch')

    # ------------------ TAB 5: Downtime Cost Analysis ------------------
    with tabs[4]:
        st.markdown("### 💵 Financial Downtime Cost Impact")
        st.write("Visualizing the financial consequences of equipment failures. Shop cost rates can be adjusted in the control panel sidebar.")
        
        # Monthly Downtime Cost Trend
        df_cost_trend = df_filtered_months.copy()
        df_cost_trend['SORT_DATE'] = df_cost_trend['DATE'].apply(lambda x: x.replace(day=1))
        
        cost_view_mode = st.radio(
            "Select Trend Display Mode:",
            options=["Overall Downtime Cost Trend", "Downtime Cost Trend by Shop"],
            horizontal=True,
            key="cost_trend_toggle"
        )
        
        if cost_view_mode == "Overall Downtime Cost Trend":
            df_cost_overall = df_cost_trend.groupby(['SORT_DATE', 'MON_RR'])['COST'].sum().reset_index()
            df_cost_overall = df_cost_overall.sort_values('SORT_DATE')
            
            fig_cost = px.area(
                df_cost_overall,
                x='MON_RR',
                y='COST',
                title='Overall Monthly Downtime Cost Loss Trend',
                labels={'COST': 'Total Cost Loss (₹)', 'MON_RR': 'Month-Year'},
                color_discrete_sequence=['#58a6ff']
            )
            fig_cost.update_traces(
                mode='lines+markers',
                line=dict(width=3, color='#58a6ff'),
                marker=dict(size=8, color='#58a6ff', symbol='circle')
            )
        else:
            df_cost_grouped = df_cost_trend.groupby(['SORT_DATE', 'MON_RR', 'SHOP_DESC'])['COST'].sum().reset_index()
            df_cost_grouped = df_cost_grouped.sort_values('SORT_DATE')
            
            fig_cost = px.line(
                df_cost_grouped,
                x='MON_RR',
                y='COST',
                color='SHOP_DESC',
                title='Monthly Downtime Cost Loss Trend by Shop',
                labels={'COST': 'Cost Loss (₹)', 'MON_RR': 'Month-Year', 'SHOP_DESC': 'Shop Description'},
                color_discrete_sequence=px.colors.qualitative.Dark24
            )
            fig_cost.update_traces(
                mode='lines+markers',
                marker=dict(size=6)
            )
            
        fig_cost.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#c9d1d9',
            font_family='Plus Jakarta Sans',
            xaxis={'gridcolor': '#21262d'},
            yaxis={'gridcolor': '#21262d'},
            legend={'bgcolor': 'rgba(22, 27, 34, 0.5)', 'bordercolor': '#21262d', 'borderwidth': 1}
        )
        st.plotly_chart(fig_cost, width='stretch')
        
        t5_col1, t5_col2 = st.columns(2)
        
        with t5_col1:
            df_shop_cost = df_filtered.groupby('SHOP_DESC')['COST'].sum().reset_index()
            df_shop_cost = df_shop_cost.sort_values('COST', ascending=False)
            
            fig_shop_cost = px.pie(
                df_shop_cost,
                names='SHOP_DESC',
                values='COST',
                title='Downtime Cost Distribution by Department',
                color_discrete_sequence=px.colors.sequential.Magma
            )
            fig_shop_cost.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#c9d1d9',
                font_family='Plus Jakarta Sans',
                legend={'bgcolor': 'rgba(22, 27, 34, 0.5)', 'bordercolor': '#21262d', 'borderwidth': 1}
            )
            st.plotly_chart(fig_shop_cost, width='stretch')
            
        with t5_col2:
            st.markdown("#### 🏆 Top 10 Most Financially Damaging Breakdown Events")
            df_expensive_events = df_filtered.sort_values('COST', ascending=False).head(10)
            df_expensive_events_fmt = df_expensive_events[['DEL_DATE', 'SHOP_DESC', 'EQPT', 'EFF_DURATION', 'COST', 'REMARKS']]
            st.dataframe(
                df_expensive_events_fmt.style.format({
                    'EFF_DURATION': '{:,.2f} Hrs',
                    'COST': '₹{:,.0f}'
                }),
                width='stretch',
                hide_index=True
            )

    # ------------------ TAB 6: Criticality Matrix (MTTR/MTBF) ------------------
    with tabs[5]:
        st.markdown("### 🎯 Equipment Criticality Matrix (MTBF vs. MTTR)")
        st.write("Reliability and maintenance bottlenecks. Equipment in the **bottom-right** represents critical reliability risks (frequent failures + slow repair).")
        
        def classify_quadrant(row):
            mttr = row['MTTR']
            mtbf = row['MTBF']
            if mtbf >= median_mtbf and mttr < median_mttr:
                return 'Reliable (High MTBF, Low MTTR)'
            elif mtbf >= median_mtbf and mttr >= median_mttr:
                return 'Slow Repair (High MTBF, High MTTR)'
            elif mtbf < median_mtbf and mttr < median_mttr:
                return 'Frequent Nuisance (Low MTBF, Low MTTR)'
            else:
                return 'CRITICAL RISK (Low MTBF, High MTTR)'
                
        df_rel['Quadrant'] = df_rel.apply(classify_quadrant, axis=1)
        
        fig_scatter = px.scatter(
            df_rel,
            x='MTBF',
            y='MTTR',
            color='Quadrant',
            size='total_downtime',
            hover_name='EQPT',
            hover_data=['SHOP_DESC', 'incidents'],
            title=f'MTBF vs MTTR Criticality Mapping (Size = Total Downtime)',
            labels={'MTBF': 'Mean Time Between Failures (Hours)', 'MTTR': 'Mean Time To Repair (Hours)'},
            color_discrete_map={
                'Reliable (High MTBF, Low MTTR)': '#2ea44f',
                'Slow Repair (High MTBF, High MTTR)': '#e3b341',
                'Frequent Nuisance (Low MTBF, Low MTTR)': '#58a6ff',
                'CRITICAL RISK (Low MTBF, High MTTR)': '#f78166'
            }
        )
        
        fig_scatter.add_vline(x=median_mtbf, line_dash="dash", line_color="#8b949e", annotation_text="Median MTBF")
        fig_scatter.add_hline(y=median_mttr, line_dash="dash", line_color="#8b949e", annotation_text="Median MTTR")
        
        fig_scatter.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#c9d1d9',
            font_family='Plus Jakarta Sans',
            xaxis={'gridcolor': '#21262d', 'type': 'log'},
            yaxis={'gridcolor': '#21262d', 'type': 'log'},
            legend={'bgcolor': 'rgba(22, 27, 34, 0.5)', 'bordercolor': '#21262d', 'borderwidth': 1}
        )
        st.plotly_chart(fig_scatter, width='stretch')
        
        st.markdown("#### 📋 Quadrant Summary Table")
        st.dataframe(
            df_rel.sort_values('total_downtime', ascending=False)[['EQPT', 'SHOP_DESC', 'incidents', 'MTTR', 'MTBF', 'Quadrant']].head(50).style.format({
                'MTTR': '{:,.2f} Hrs',
                'MTBF': '{:,.1f} Hrs'
            }),
            width='stretch',
            hide_index=True
        )

    # ------------------ TAB 7: Failure Prediction Index ------------------
    with tabs[6]:
        st.markdown("### 🔮 Equipment Degradation & Failure Forecast")
        st.write("Using recent incident patterns and historical degradation models to predict failure risks in the next 7 days.")
        
        def risk_level(p):
            if p >= 0.65:
                return '🔴 High Risk'
            elif p >= 0.35:
                return '🟡 Medium Risk'
            else:
                return '🟢 Low Risk'
                
        df_forecast['Risk_Level'] = df_forecast['Failure_Probability_7d'].apply(risk_level)
        
        st.markdown("#### 🚨 Top 10 Equipment with Imminent Failure Risk (Next 7 Days)")
        st.dataframe(
            df_forecast.sort_values('Failure_Probability_7d', ascending=False)[['EQPT', 'SHOP_DESC', 'recent_incidents', 'MTBF', 'EDI', 'Failure_Probability_7d', 'Risk_Level']].head(10).style.format({
                'MTBF': '{:,.1f} Hrs',
                'EDI': '{:.1f}',
                'Failure_Probability_7d': '{:.1%}'
            }),
            width='stretch',
            hide_index=True
        )
        
        st.markdown("---")
        st.markdown("#### 🔬 Diagnostic Drill-down by Asset")
        
        eq_select = st.selectbox("Select Asset to Run Predictive Diagnostics:", options=df_forecast['EQPT'].unique())
        
        if eq_select:
            asset_row = df_forecast[df_forecast['EQPT'] == eq_select].iloc[0]
            st.markdown(f"**Asset Profile: {eq_select} ({asset_row['SHOP_DESC']})**")
            
            # Show parameters
            d_col1, d_col2, d_col3, d_col4 = st.columns(4)
            d_col1.metric("Degradation Score (EDI)", f"{asset_row['EDI']:.1f} / 100")
            d_col2.metric("Failure Probability (7-Day)", f"{asset_row['Failure_Probability_7d']:.1%}")
            d_col3.metric("MTBF", f"{asset_row['MTBF']:,.1f} Hrs")
            d_col4.metric("Risk Status", asset_row['Risk_Level'])
            
            # Failure history plot
            asset_delays = df_filtered[df_filtered['EQPT'] == eq_select].copy()
            asset_delays = asset_delays.sort_values('DATE')
            asset_delays['Cumulative_Downtime'] = asset_delays['EFF_DURATION'].cumsum()
            
            fig_degrade = px.line(
                asset_delays,
                x='DATE',
                y='Cumulative_Downtime',
                title=f'Asset Reliability Timeline & Cumulative Downtime Curve for {eq_select}',
                labels={'Cumulative_Downtime': 'Cumulative Downtime Hours'},
                color_discrete_sequence=['#ff7b72']
            )
            fig_degrade.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#c9d1d9',
                font_family='Plus Jakarta Sans',
                xaxis={'gridcolor': '#21262d'},
                yaxis={'gridcolor': '#21262d'}
            )
            st.plotly_chart(fig_degrade, width='stretch')

    # ------------------ TAB 8: Monsoon Hazard & Simulator ------------------
    with tabs[7]:
        st.markdown("### ⛈️ Monsoon Hazard and Conveyor Simulation Model")
        st.write("Wet weather impacts conveyor systems. The Monsoon Vulnerability Index (MVI) ranks systems by their relative risk during the wet season.")
        
        # Calculate Monsoon Vulnerability Index (MVI) for Conveyors
        df_conv_all = df_all[df_all['IS_CONVEYOR'] == True].copy()
        df_conv_grouped = df_conv_all.groupby(['SEASON', 'SUB_EQPT'])['EFF_DURATION'].agg(['sum', 'count']).reset_index()
        
        # Calculate actual number of months in the dataset for each season dynamically
        num_mon_months = df_all[df_all['SEASON'] == 'Monsoon']['MON_RR'].nunique()
        num_non_mon_months = df_all[df_all['SEASON'] == 'Non-Monsoon']['MON_RR'].nunique()
        if num_mon_months == 0: num_mon_months = 7.0
        if num_non_mon_months == 0: num_non_mon_months = 14.0
        
        df_mon = df_conv_grouped[df_conv_grouped['SEASON'] == 'Monsoon'].set_index('SUB_EQPT')
        df_non = df_conv_grouped[df_conv_grouped['SEASON'] == 'Non-Monsoon'].set_index('SUB_EQPT')
        
        df_mvi = df_mon.join(df_non, lsuffix='_mon', rsuffix='_non', how='inner')
        df_mvi['monthly_avg_mon'] = df_mvi['sum_mon'] / num_mon_months
        df_mvi['monthly_avg_non'] = df_mvi['sum_non'] / num_non_mon_months
        df_mvi['MVI'] = df_mvi['monthly_avg_mon'] / (df_mvi['monthly_avg_non'] + 0.1)
        df_mvi = df_mvi.reset_index().sort_values('MVI', ascending=False)
        
        t8_col1, t8_col2 = st.columns([1, 1])
        
        with t8_col1:
            st.markdown("#### 📈 Top 10 Most Monsoon-Vulnerable Conveyors (MVI)")
            st.write("An MVI of 3.0 means a conveyor suffers 3x higher monthly downtime during the monsoon compared to other months.")
            
            fig_mvi = px.bar(
                df_mvi.head(10),
                x='MVI',
                y='SUB_EQPT',
                orientation='h',
                title='Conveyor Monsoon Vulnerability Index (MVI)',
                color='MVI',
                color_continuous_scale='Oranges'
            )
            fig_mvi.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#c9d1d9',
                font_family='Plus Jakarta Sans',
                xaxis={'gridcolor': '#21262d'},
                yaxis={'categoryorder': 'total ascending', 'gridcolor': '#21262d'}
            )
            st.plotly_chart(fig_mvi, width='stretch')
            
        with t8_col2:
            st.markdown("#### 🎮 Interactive Monsoon Impact Simulator")
            st.write("Simulate expected conveyor breakdowns and downtime under different rainfall intensities based on historical susceptibility indices.")
            
            rain_scenario = st.select_slider(
                "Select Simulated Rainfall Intensity:",
                options=["Drizzle/Light", "Regular Monsoon", "Heavy Monsoon Storm", "Cloudburst Event"]
            )
            
            multipliers = {
                "Drizzle/Light": 1.1,
                "Regular Monsoon": 1.5,
                "Heavy Monsoon Storm": 2.5,
                "Cloudburst Event": 4.5
            }
            mult = multipliers[rain_scenario]
            
            # Calculate actual number of non-monsoon months dynamically
            num_non_mon_months = df_all[df_all['SEASON'] == 'Non-Monsoon']['MON_RR'].nunique()
            if num_non_mon_months == 0: num_non_mon_months = 14.0
            
            baseline_conv_downtime = df_conv_all[df_conv_all['SEASON'] == 'Non-Monsoon']['EFF_DURATION'].sum() / num_non_mon_months
            baseline_incidents = len(df_conv_all[df_conv_all['SEASON'] == 'Non-Monsoon']) / num_non_mon_months
            
            simulated_downtime = baseline_conv_downtime * mult
            simulated_incidents = baseline_incidents * mult
            
            st.markdown(f"**Simulation Output for: {rain_scenario}**")
            st.metric("Predicted Monthly Conveyor Downtime", f"{simulated_downtime:,.1f} Hours", f"+{((simulated_downtime - baseline_conv_downtime) / baseline_conv_downtime) * 100:.0f}% vs. baseline")
            st.metric("Predicted Breakdowns Count", f"{simulated_incidents:.1f} per Month", f"+{((simulated_incidents - baseline_incidents) / baseline_incidents) * 100:.0f}%")
            
            st.markdown("**Simulated High-Risk Conveyor Assets:**")
            high_risk_belts = df_mvi.head(5)['SUB_EQPT'].tolist()
            st.write(", ".join([f"⚠️ **{b}**" for b in high_risk_belts]))
            st.info("💡 Recommendation: Schedule preventative belt alignment checks, structural cover repairs, and gutter inspections for these conveyor belts before the simulated weather event.")
