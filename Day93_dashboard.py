import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

st.set_page_config(page_title="TechMart India | Analytics Dashboard", page_icon="📊", layout="wide")

st.markdown('''
<div style="background-color:#1F3864; padding:16px; border-radius:8px; text-align:center">
    <h2 style="color:white; margin:0">📊 TechMart India Analytics Dashboard</h2>
    <p style="color:#D6E4F0; margin:4px 0 0 0">Powered by Python + Streamlit</p>
</div>
''', unsafe_allow_html=True)

st.markdown("")
st.subheader("Interactive sales analytics for TechMart India — filter, explore, export.")
st.divider()

@st.cache_data
def load_data():
    df = pd.read_csv('techmart_day93.csv', parse_dates=['date'])
    df = df.dropna(subset=['order_id']).reset_index(drop=True)
    return df

df = load_data()

st.sidebar.header("🎛️ Filters")
regions_available    = sorted(df['region'].unique())
categories_available = sorted(df['category'].unique())
min_date = df['date'].min().date()
max_date = df['date'].max().date()

selected_regions = st.sidebar.multiselect('Region',   regions_available,    default=regions_available)
selected_cats    = st.sidebar.multiselect('Category', categories_available, default=categories_available)
date_range       = st.sidebar.date_input('Date Range', value=[min_date, max_date],
                                          min_value=min_date, max_value=max_date)

if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

df_filtered = df[
    (df['region'].isin(selected_regions)) &
    (df['category'].isin(selected_cats)) &
    (df['date'].dt.date >= start_date) &
    (df['date'].dt.date <= end_date)
].copy()

st.sidebar.markdown(f'**{len(df_filtered)} orders** match filters')

col1, col2, col3 = st.columns(3)
total_revenue = df_filtered['revenue'].sum()
total_orders  = len(df_filtered)
filtered_aov  = df_filtered['revenue'].mean() if total_orders > 0 else 0
delta_aov     = filtered_aov - df['revenue'].mean()
col1.metric('💰 Total Revenue',   f'₹{total_revenue:,.0f}')
col2.metric('📦 Total Orders',    f'{total_orders:,}')
col3.metric('🧾 Avg Order Value', f'₹{filtered_aov:,.0f}', delta=f'₹{delta_aov:+,.0f} vs baseline')

st.divider()
left_col, right_col = st.columns(2)

with left_col:
    st.subheader('Revenue by Category')
    df_cat = df_filtered.groupby('category')['revenue'].sum().sort_values(ascending=True)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(df_cat.index, df_cat.values, color='#1F3864')
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'₹{x/1000:.0f}K'))
    ax.set_title('Revenue by Category', fontsize=12, fontweight='bold', color='#1F3864')
    ax.set_xlabel('Revenue (₹)')
    ax.spines[['top', 'right']].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig)
    top_cat = df_cat.idxmax()
    top_rev = df_cat.max()
    st.markdown(f'**{top_cat}** leads with ₹{top_rev:,.0f} in revenue, driven by high unit '
                f'prices in this segment, suggesting prioritised stock replenishment and '
                f'targeted promotions for {top_cat}.')

with right_col:
    st.subheader('Revenue by Customer Segment')
    df_seg = df_filtered.groupby('customer_segment')['revenue'].sum()
    fig3, ax3 = plt.subplots(figsize=(7, 4))
    colors = ['#1F3864', '#2E5596', '#4A90D9', '#A8C4E0']
    ax3.pie(df_seg.values, labels=df_seg.index, autopct='%1.1f%%',
            colors=colors, startangle=140, wedgeprops={'edgecolor': 'white', 'linewidth': 1.5})
    ax3.set_title('Revenue by Customer Segment', fontsize=12, fontweight='bold', color='#1F3864')
    plt.tight_layout()
    st.pyplot(fig3)
    top_seg     = df_seg.idxmax()
    top_seg_rev = df_seg.max()
    st.markdown(f'**{top_seg}** customers contribute ₹{top_seg_rev:,.0f} '
                f'— run targeted retention campaigns for this segment.')

st.divider()
st.subheader('Monthly Revenue Trend')
df_m = df_filtered.copy()
df_m['month'] = df_m['date'].dt.to_period('M')
df_monthly = df_m.groupby('month')['revenue'].sum().reset_index()
df_monthly['month'] = df_monthly['month'].astype(str)

fig2, ax2 = plt.subplots(figsize=(10, 4))
ax2.plot(df_monthly['month'], df_monthly['revenue'], marker='o', color='#2E5596', linewidth=2)
ax2.fill_between(df_monthly['month'], df_monthly['revenue'], alpha=0.15, color='#2E5596')
ax2.set_title('Monthly Revenue Trend', fontsize=12, fontweight='bold', color='#1F3864')
ax2.set_xlabel('Month')
ax2.set_ylabel('Revenue (₹)')
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda y, _: f'₹{y/1000:.0f}K'))
ax2.spines[['top', 'right']].set_visible(False)
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
st.pyplot(fig2)

if not df_monthly.empty:
    peak_idx   = df_monthly['revenue'].idxmax()
    peak_month = df_monthly.loc[peak_idx, 'month']
    peak_rev   = df_monthly.loc[peak_idx, 'revenue']
    st.markdown(f'**{peak_month}** was the peak month at ₹{peak_rev:,.0f}, '
                f'suggesting demand concentration — plan inventory and campaigns '
                f'to sustain momentum in subsequent months.')

st.divider()
st.subheader('📋 Order-Level Detail')
st.caption(f'Showing {len(df_filtered):,} orders based on current filters')
display_cols = df_filtered[['order_id','date','region','category','product',
                             'quantity','unit_price','revenue','customer_segment']].copy()
display_cols.columns = ['Order ID','Date','Region','Category','Product',
                        'Qty','Unit Price (₹)','Revenue (₹)','Segment']
st.dataframe(display_cols, use_container_width=True, height=300)

csv_bytes = df_filtered.to_csv(index=False).encode('utf-8')
st.download_button(label='⬇️ Download Filtered Data (CSV)', data=csv_bytes,
                   file_name='techmart_filtered_report.csv', mime='text/csv')

st.caption('TechMart India Analytics Dashboard | Built with Streamlit | deepanshu0110')