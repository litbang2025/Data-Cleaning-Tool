import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import io  
import datetime
import json
from scipy import stats

st.set_page_config(page_title="📊 Data Cleaning Tool", layout="wide")

# Fungsi untuk mengunggah file
def upload_file():
    uploaded_file = st.file_uploader("📁 Pilih file Excel atau CSV", type=["csv", "xlsx"])
    if uploaded_file is not None:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
        return df
    return None

# Fungsi untuk mengatur tipe data kolom
def set_column_types(df):
    st.subheader("🛠️ Pengaturan Tipe Data Kolom")
    columns = df.columns
    column_types = {}
    for column in columns:
        detected_type = str(df[column].dtype)
        st.write(f"📌 Kolom **{column}** terdeteksi sebagai: `{detected_type}`")
        selected_type = st.selectbox(
            f"Pilih tipe data untuk kolom '{column}'",
            ["Deteksi Otomatis", "string", "int", "float", "datetime"],
            index=0,
            key=f"type_{column}"
        )
        column_types[column] = selected_type

    if st.button("✅ Simpan Perubahan Tipe Data"):
        for column, tipe in column_types.items():
            if tipe != "Deteksi Otomatis":
                try:
                    if tipe == "string":
                        df[column] = df[column].astype(str)
                    elif tipe == "int":
                        df[column] = pd.to_numeric(df[column], errors='coerce').astype('Int64')
                    elif tipe == "float":
                        df[column] = pd.to_numeric(df[column], errors='coerce')
                    elif tipe == "datetime":
                        df[column] = pd.to_datetime(df[column], errors='coerce')
                except Exception as e:
                    st.warning(f"Gagal mengubah kolom '{column}' ke {tipe}: {e}")
        st.success("Perubahan tipe data berhasil disimpan!")
    return df

# Fungsi untuk mengganti nama kolom
def rename_columns(df):
    st.subheader("✏️ Ganti Nama Kolom")
    new_columns = {}
    for column in df.columns:
        new_name = st.text_input(f"Ganti nama untuk kolom '{column}'", value=column, key=f"rename_{column}")
        new_columns[column] = new_name
    if st.button("🔄 Simpan Nama Kolom"):
        df.rename(columns=new_columns, inplace=True)
        st.success("Nama kolom berhasil diperbarui!")
    return df

# Fungsi untuk membersihkan data
def clean_data(df):
    st.subheader("🧹 Pembersihan Data")
    if st.checkbox("Hapus duplikasi"):
        df = df.drop_duplicates()
    if st.checkbox("Hapus nilai kosong"):
        df = df.dropna()
    if st.checkbox("Isi nilai kosong dengan rata-rata (kolom numerik saja)"):
        df = df.fillna(df.mean(numeric_only=True))
    return df

# Fungsi untuk ekspor data
# Fungsi untuk ekspor data
def export_data(df):
    st.subheader("📤 Ekspor Data")
    export_type = st.radio("Pilih format ekspor", ["CSV", "Excel"])

    if export_type == "CSV":
        st.download_button(
            "⬇️ Unduh CSV", 
            data=df.to_csv(index=False), 
            file_name="data.csv", 
            mime="text/csv"
        )
    elif export_type == "Excel":
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        st.download_button(
            "⬇️ Unduh Excel",
            data=output.getvalue(),
            file_name="data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
# Fungsi dashboard dan saran analisis
def show_dashboard(df):
    st.title("📈 Dashboard Statistik & Informasi Dataset")
    st.markdown(f"""
    - **Jumlah Baris:** {len(df)}
    - **Jumlah Kolom:** {df.shape[1]}
    - **Nama Variabel:** `{', '.join(df.columns)}`
    - **Total Data Kosong:** {df.isna().sum().sum()}
    - **Ukuran Memori:** {df.memory_usage().sum() / 1_000_000:.2f} MB
    """)

    st.subheader("🔍 Statistik Deskriptif")
    st.dataframe(df.describe(include='all'))

    st.subheader("🧠 Saran Uji Lanjut Berdasarkan Tipe Data")
    num_vars = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_vars = df.select_dtypes(include=['object']).columns.tolist()

    st.markdown(f"""
    - Untuk **numerik** (`{', '.join(num_vars)}`): Gunakan analisis korelasi, regresi, atau uji distribusi (Shapiro, ANOVA).
    - Untuk **kategori** (`{', '.join(cat_vars)}`): Gunakan chi-square, label encoding, atau visualisasi pie/bar.
    """)

# Fungsi analisis lanjutan opsional
# Fungsi analisis lanjutan opsional
def advanced_analysis(df):
    st.title("📊 Analisis Lanjutan (Opsional)")

    st.subheader("1. 🔥 Heatmap Korelasi")
    num_df = df.select_dtypes(include=[np.number])
    if not num_df.empty:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.heatmap(num_df.corr(), annot=True, cmap='coolwarm', ax=ax)
        st.pyplot(fig)

    st.subheader("2. 📊 Distribusi Kategori")
    cat_cols = df.select_dtypes(include=['object']).columns
    for col in cat_cols:
        st.write(f"Kolom: {col}")
        # Perbaikan: Menyusun data value_counts dengan benar
        value_counts = df[col].value_counts().reset_index()
        value_counts.columns = [col, 'count']
        fig = px.bar(value_counts, x=col, y='count', title=f"Distribusi {col}")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("3. ⚠️ Highlight Missing dan Outlier")
    st.dataframe(df.isnull().sum().reset_index().rename(columns={0: 'Jumlah Kosong'}))
    st.markdown("**Outlier Deteksi (Z-score > 3)**")
    for col in num_df.columns:
        outliers = np.abs(stats.zscore(num_df[col].dropna())) > 3
        st.write(f"{col}: {np.sum(outliers)} outlier")

    st.subheader("4. 📥 Impor / Ekspor Konfigurasi Cleaning")
    config = {"columns": list(df.columns)}
    st.download_button("⬇️ Ekspor Konfigurasi JSON", json.dumps(config), "config.json", "application/json")
    uploaded_json = st.file_uploader("📤 Unggah Konfigurasi JSON", type="json")
    if uploaded_json:
        config_data = json.load(uploaded_json)
        st.json(config_data)


# Main app
def main():
    st.sidebar.image("https://cdn-icons-png.flaticon.com/128/3813/3813661.png", width=150)
    st.sidebar.title("📂 Menu")
    menu = st.sidebar.radio("Navigasi", ["📥 Upload Data", "📊 Dashboard", "🛠️ Atur Tipe Data", "✏️ Ganti Nama Kolom", "🧹 Pembersihan", "📤 Ekspor", "📈 Analisis Lanjutan"])

    st.markdown("""<style>footer {visibility: hidden;} .css-fblp2m {font-size: 14px; text-align: center;}</style>""", unsafe_allow_html=True)

    df = st.session_state.get("cleaned_df")
    if menu == "📥 Upload Data":
        df = upload_file()
        if df is not None:
            st.session_state.cleaned_df = df
            st.success("Data berhasil diunggah!")

    elif df is not None:
        if menu == "📊 Dashboard":
            show_dashboard(df)
        elif menu == "🛠️ Atur Tipe Data":
            st.session_state.cleaned_df = set_column_types(df)
        elif menu == "✏️ Ganti Nama Kolom":
            st.session_state.cleaned_df = rename_columns(df)
        elif menu == "🧹 Pembersihan":
            st.session_state.cleaned_df = clean_data(df)
        elif menu == "📤 Ekspor":
            export_data(df)
        elif menu == "📈 Analisis Lanjutan":
            advanced_analysis(df)
    else:
        st.warning("Silakan unggah data terlebih dahulu.")

    st.markdown("""
    <hr>
    <div style='text-align: center;'>
    ⓒ 2025 - Data Cleaning App | Dibuat dengan ❤️ oleh abu aisy
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
