import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Dashboard Phân Tích", layout="wide")

# ĐỔI TÊN DASHBOARD THEO YÊU CẦU
st.title("📊 Dashboard tổng hợp hỗ trợ và quản trị")

# --- 1. HÀM ĐỌC & XỬ LÝ DỮ LIỆU ---
@st.cache_data
def load_and_preprocess_data(file):
    df_raw = pd.read_csv(file, header=None)
    row_thang = df_raw.iloc[2].fillna("").astype(str)
    
    cols = ["STT", "Ma_YC", "NoiDung", "DonVi", "SL_HopDong", "SL_DaThucHien_Tong", "SL_ConLai"]
    thang_cols = []
    
    for i in range(7, len(df_raw.columns)):
        val = row_thang[i].strip()
        if val.startswith("T") and val[1:].isdigit():
            cols.append(val)
            thang_cols.append(val)
        else:
            cols.append(f"BoQua_{i}")
            
    df_raw.columns = cols
    df = df_raw.iloc[3:].copy()
    
    cols_to_keep = ["STT", "Ma_YC", "NoiDung", "DonVi", "SL_HopDong", "SL_DaThucHien_Tong", "SL_ConLai"] + thang_cols
    df = df[cols_to_keep]
    df = df.dropna(how='all', subset=["NoiDung"])
    df = df[df['NoiDung'].str.strip() != ""]
    
    numeric_cols = ["SL_HopDong", "SL_DaThucHien_Tong", "SL_ConLai"] + thang_cols
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        
    def get_level(row):
        stt = str(row['STT']).strip()
        ma_yc = str(row['Ma_YC']).strip()
        if ma_yc not in ["", "nan", "None"]: return 3 # Mã chi tiết
        if "." in stt: return 2 # Hệ thống
        if stt in ['I', 'II', 'III', 'IV', 'V']: return 1 # Nhóm lớn
        return 0
        
    df['Level'] = df.apply(get_level, axis=1)
    
    nhom_list, he_thong_list = [], []
    current_nhom, current_he_thong = "Nhóm Khác", "Chung"
    
    for _, row in df.iterrows():
        if row['Level'] == 1:
            text_lower = str(row['NoiDung']).lower()
            if "hỗ trợ" in text_lower: current_nhom = "Nhóm Hỗ trợ"
            elif "quản trị" in text_lower: current_nhom = "Nhóm Quản trị"
            current_he_thong = "Chung"
        elif row['Level'] == 2:
            current_he_thong = str(row['NoiDung']).strip()
            
        nhom_list.append(current_nhom)
        he_thong_list.append(current_he_thong)
        
    df['Nhom_Chinh'] = nhom_list
    df['He_Thong'] = he_thong_list
    
    return df, thang_cols

# --- 2. MENU SIDEBAR ---
st.sidebar.header("⚙️ Menu Bộ Lọc")
# Tự động đọc file CSV đang để cùng thư mục trên GitHub
file_path = "Tổng hợp yêu cầu_Dashboard.xlsx - Sheet1.csv" # Đảm bảo tên file này giống y hệt tên file bạn up lên GitHub

try:
    df, thang_cols = load_and_preprocess_data(file_path)
except Exception as e:
    st.error("Không tìm thấy file dữ liệu, vui lòng kiểm tra lại!")
    st.stop()

# Menu 2.1: Chọn Nhóm (Bổ sung Báo cáo chung và Nhóm quản trị)
st.sidebar.subheader("2. Chọn Nhóm Báo Cáo")
nhom_options = ["Báo cáo chung", "Nhóm Hỗ trợ", "Nhóm Quản trị"]
selected_nhom = st.sidebar.multiselect("Lọc theo nhóm:", options=nhom_options, default=["Báo cáo chung", "Nhóm Hỗ trợ", "Nhóm Quản trị"])

if not selected_nhom:
    st.warning("Vui lòng chọn ít nhất 1 mục báo cáo!")
    st.stop()

# Lọc ra các nhóm thực tế (bỏ chữ Báo cáo chung ra để lọc hệ thống)
real_groups = [g for g in selected_nhom if g in ['Nhóm Hỗ trợ', 'Nhóm Quản trị']]

# Menu 2.2: Chọn Hệ Thống (Hiển thị CHỈ CÁC HỆ THỐNG thuộc NHÓM đã chọn ở trên)
he_thong_options = df[(df['Nhom_Chinh'].isin(real_groups)) & (df['Level'] == 2)]['He_Thong'].unique().tolist()
if real_groups:
    st.sidebar.subheader("3. Chọn Hệ Thống Cụ Thể")
    selected_he_thong = st.sidebar.multiselect("Lọc theo hệ thống:", options=he_thong_options, default=he_thong_options)
else:
    selected_he_thong = []

# Menu 2.3: Chọn Tháng
st.sidebar.subheader("4. Chọn Tháng Thực Hiện")
selected_thang = st.sidebar.multiselect("Lọc theo tháng:", options=thang_cols, default=thang_cols[:3])

if not selected_thang:
    st.warning("Vui lòng chọn ít nhất 1 tháng!")
    st.stop()

# --- 3. VẼ DASHBOARD ---

# ==========================================
# PHẦN 1: BÁO CÁO CHUNG TỔNG QUÁT (MÀU TƯƠI SÁNG)
# ==========================================
if "Báo cáo chung" in selected_nhom:
    st.markdown("<h2 style='text-align: center; color: #FF4B4B;'>🌟 BÁO CÁO CHUNG TỔNG THỂ 🌟</h2>", unsafe_allow_html=True)
    
    # Tính tổng tất cả các nhóm (Level 1)
    df_l1_all = df[df['Level'] == 1]
    tong_hop_dong_all = df_l1_all['SL_HopDong'].sum()
    tong_thuc_hien_all = df_l1_all[selected_thang].sum().sum()
    tong_con_lai_all = df_l1_all['SL_ConLai'].sum()
    tyle_all = (tong_thuc_hien_all / tong_hop_dong_all * 100) if tong_hop_dong_all > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tổng Mã YC (Toàn dự án)", len(df[df['Level']==3]))
    col2.metric("Tổng SL Hợp đồng", f"{tong_hop_dong_all:,.0f}")
    col3.metric("Tổng Đã thực hiện", f"{tong_thuc_hien_all:,.0f}")
    col4.metric("Tổng SL Còn lại", f"{tong_con_lai_all:,.0f}", f"Đạt {tyle_all:.1f}%")
    
    # Biểu đồ Tổng thể với dải màu cực kỳ rực rỡ
    fig_chung = go.Figure(data=[
        go.Bar(name='Theo Hợp đồng', x=['Tổng Thể'], y=[tong_hop_dong_all], marker_color='#00D2D3', text=[tong_hop_dong_all]), # Xanh ngọc tươi
        go.Bar(name='Đã thực hiện', x=['Tổng Thể'], y=[tong_thuc_hien_all], marker_color='#FF9F43', text=[f"{tyle_all:.1f}%"]), # Cam tươi
        go.Bar(name='Còn lại', x=['Tổng Thể'], y=[tong_con_lai_all], marker_color='#FF6B6B', text=[tong_con_lai_all]) # Đỏ san hô
    ])
    fig_chung.update_traces(textposition='auto', textfont_size=16)
    fig_chung.update_layout(title="Tổng quan Hợp đồng vs Thực hiện (Toàn Dự Án)", barmode='group', height=400)
    st.plotly_chart(fig_chung, use_container_width=True)
    
    st.divider()

# ==========================================
# PHẦN 2: CHI TIẾT THEO NHÓM VÀ HỆ THỐNG
# ==========================================
# Bộ màu sắc phong phú, tươi sáng cho từng nhóm riêng biệt
color_themes = {
    "Nhóm Hỗ trợ": {'main': '#00A8FF', 'light': '#9CB1C9', 'hopdong': '#74B9FF'}, # Tone Xanh biển tươi
    "Nhóm Quản trị": {'main': '#9C88FF', 'light': '#D2C4E8', 'hopdong': '#A29BFE'}  # Tone Tím/Hồng pastel tươi
}

for nhom in real_groups:
    st.markdown(f"<h2 style='text-align: center; color: {color_themes[nhom]['main']};'>🔥 CHI TIẾT: {nhom.upper()} 🔥</h2>", unsafe_allow_html=True)
    
    # Lọc các hệ thống thuộc nhóm này
    systems_in_nhom = [sys for sys in selected_he_thong if sys in df[df['Nhom_Chinh'] == nhom]['He_Thong'].unique()]
    
    if not systems_in_nhom:
        st.info(f"Không có hệ thống nào được chọn thuộc {nhom}.")
        continue
        
    for sys_name in systems_in_nhom:
        st.markdown(f"### 🔹 Hệ thống: {sys_name}")
        
        # Data tổng của hệ thống
        df_sys_total = df[(df['He_Thong'] == sys_name) & (df['Level'] == 2)]
        if df_sys_total.empty: continue
            
        sys_hop_dong = df_sys_total['SL_HopDong'].sum()
        sys_thuc_hien = df_sys_total[selected_thang].sum().sum()
        sys_con_lai = df_sys_total['SL_ConLai'].sum()
        sys_tyle = (sys_thuc_hien / sys_hop_dong * 100) if sys_hop_dong > 0 else 0
        
        # Data chi tiết mã YC
        df_sys_details = df[(df['He_Thong'] == sys_name) & (df['Level'] == 3)].copy()
        df_sys_details['Thực hiện (Kỳ)'] = df_sys_details[selected_thang].sum(axis=1)
        tong_ma = len(df_sys_details)
        
        # Hiển thị Metrics Hệ Thống
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Số lượng Mã", f"{tong_ma} Mã")
        col2.metric("SL Hợp đồng", f"{sys_hop_dong:,.0f}")
        col3.metric("Đã thực hiện", f"{sys_thuc_hien:,.0f}")
        col4.metric("SL Còn lại", f"{sys_con_lai:,.0f}", f"Đạt {sys_tyle:.1f}%")
        
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            # Biểu đồ 1: Tổng quan hệ thống
            fig_sys_total = go.Figure(data=[
                go.Bar(name='Hợp đồng', x=[''], y=[sys_hop_dong], marker_color=color_themes[nhom]['hopdong'], text=[sys_hop_dong]),
                go.Bar(name='Đã thực hiện', x=[''], y=[sys_thuc_hien], 
                       marker_color=color_themes[nhom]['main'], text=[f"{sys_tyle:.1f}%"]),
                go.Bar(name='Còn lại', x=[''], y=[sys_con_lai], marker_color='#FD79A8', text=[sys_con_lai]) # Đỏ hồng sáng
            ])
            fig_sys_total.update_traces(textposition='auto')
            fig_sys_total.update_layout(title="Tiến độ thực hiện Hệ thống", barmode='group', height=350)
            st.plotly_chart(fig_sys_total, use_container_width=True)
            
        with chart_col2:
            # Biểu đồ 2: Từng Mã YC (Sử dụng bảng màu tươi sáng Vivid)
            if not df_sys_details.empty:
                df_sys_details['Tỷ lệ'] = (df_sys_details['Thực hiện (Kỳ)'] / df_sys_details['SL_HopDong'] * 100).fillna(0).round(1)
                
                fig_sys_detail = px.bar(
                    df_sys_details, 
                    x="Ma_YC", 
                    y=["SL_HopDong", "Thực hiện (Kỳ)"], 
                    barmode="group",
                    hover_data={"NoiDung": True},
                    title="Đối chiếu theo từng Mã Yêu Cầu",
                    color_discrete_sequence=['#FDCB6E', color_themes[nhom]['main']], # Vàng nắng & Màu chủ đạo
                    height=350
                )
                fig_sys_detail.update_layout(xaxis_title="Mã Yêu Cầu", yaxis_title="Số lượng", legend_title="Chỉ tiêu")
                st.plotly_chart(fig_sys_detail, use_container_width=True)
                
        st.write("---") # Ngăn cách nhẹ giữa các hệ thống