import streamlit as st
import pandas as pd
import plotly.express as px

# 1. PAGE SETUP & LIGHT THEME
st.set_page_config(page_title="BD Procurement Dashboard", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #F8F9FA; color: #333333; }
h1, h2, h3 { color: #2C3E50 !important; font-family: 'Helvetica Neue', sans-serif; }
.stMetric label { color: #555555 !important; font-weight: bold; }
hr { border-color: #DDDDDD; }
</style>
""", unsafe_allow_html=True)

st.title("BD Procurement Data Dashboard")
st.markdown("---")

# 2. DATA LOADING & ERROR HANDLING
@st.cache_data(ttl=60, show_spinner=False)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1RiONMcLaq60lYAce7ZRjaNJt_jQw-23Kwtg9LhXIRgA/export?format=csv&gid=0"
    try:
        df = pd.read_csv(url)
        if '<!doctype html>' in str(df.columns).lower() or len(df.columns) < 3:
            st.error("🚨 ACCESS DENIED: Your Google Sheet is private.")
            return pd.DataFrame()
            
        df.columns = df.columns.str.strip()
        df['Total Amount (BDT)'] = pd.to_numeric(df['Total Amount (BDT)'], errors='coerce')
        df = df.dropna(subset=['Total Amount (BDT)', 'Year'])
        df['Year'] = df['Year'].astype(int).astype(str) 
        return df
    except Exception as e:
        st.error(f"🚨 DATA ERROR: {e}")
        return pd.DataFrame()

df = load_data()
if df.empty:
    st.warning("Waiting for valid data...")
    st.stop()

# 3. SIDEBAR FILTERS
st.sidebar.header("🎯 Filters")
selected_ministries = st.sidebar.multiselect("Select Ministries", sorted(df['Ministry Name'].unique()), default=sorted(df['Ministry Name'].unique()))
selected_years = st.sidebar.multiselect("Select Years", sorted(df['Year'].unique()), default=sorted(df['Year'].unique()))
filtered_df = df[(df['Ministry Name'].isin(selected_ministries)) & (df['Year'].isin(selected_years))]

# 4. SCORECARDS (Raw Data)
col1, col2, col3 = st.columns(3)
col1.metric("Total Spent (2022-2026)", f"Tk {filtered_df['Total Amount (BDT)'].sum() / 1e9:.1f}B")
col2.metric("Number of Contracts", len(filtered_df))
col3.metric("Ministries Involved", filtered_df['Ministry Name'].nunique())
st.markdown("---")

# 5. OVERALL DONUT CHART
st.subheader("Total Spent on Each Ministry")
if not filtered_df.empty:
    fig_overall = px.pie(filtered_df, values='Total Amount (BDT)', names='Ministry Name', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
    fig_overall.update_traces(hovertemplate="<b>%{label}</b><br>Share: %{percent}<br>Spent: Tk %{value:,.0f}<extra></extra>")
    fig_overall.update_layout(paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_overall, use_container_width=True)

st.markdown("---")

# 6. YEARLY DONUT CHARTS
st.subheader("Spending Breakdown by Year")
if not filtered_df.empty:
    years = sorted(filtered_df['Year'].unique())
    cols = st.columns(len(years))
    for idx, year in enumerate(years):
        fig_year = px.pie(filtered_df[filtered_df['Year'] == year], values='Total Amount (BDT)', names='Ministry Name', title=f"{year}", hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_year.update_traces(hovertemplate="<b>%{label}</b><br>Share: %{percent}<br>Spent: Tk %{value:,.0f}<extra></extra>")
        fig_year.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)')
        with cols[idx]:
            st.plotly_chart(fig_year, use_container_width=True)

st.markdown("---")

# 7. CONTRACTORS SECTION
st.subheader("Contractor Analysis")
col_bar, col_table = st.columns(2)
with col_bar:
    top_5 = filtered_df.groupby('Winning Contractor / Agency')['Total Amount (BDT)'].sum().reset_index().nlargest(5, 'Total Amount (BDT)')
    fig_bar = px.bar(top_5, x='Total Amount (BDT)', y='Winning Contractor / Agency', orientation='h', color='Total Amount (BDT)', color_continuous_scale='Blues')
    fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_bar, use_container_width=True)

with col_table:
    summary = filtered_df.groupby('Winning Contractor / Agency').agg(Contracts=('Ministry Name', 'count'), Total_Spent=('Total Amount (BDT)', 'sum')).reset_index().sort_values('Total_Spent', ascending=False)
    summary['Total_Spent'] = summary['Total_Spent'].apply(lambda x: f"Tk {x/1e9:.1f}B")
    st.dataframe(summary, use_container_width=True, hide_index=True)

st.markdown("---")

# 8. YEARLY MATRIX
st.subheader("Yearly Ministry Procurement Matrix")
matrix = filtered_df.groupby(['Year', 'Ministry Name']).agg(Contracts=('Ministry Name', 'count'), Total_Spent=('Total Amount (BDT)', 'sum')).reset_index().sort_values(['Year', 'Total_Spent'], ascending=[True, False])
matrix['Total_Spent'] = matrix['Total_Spent'].apply(lambda x: f"Tk {x/1e9:.1f}B")
st.dataframe(matrix, use_container_width=True, hide_index=True)
