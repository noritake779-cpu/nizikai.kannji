import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- 会費設定 ---
PRICE_ADULT = 5000
PRICE_CHILD = 1500
PRICE_TEACHER = 2000

SHEET_ID = "1-ulN6CZCuiK9uOHWnaas1Y7X5QTv7j-xUFkJLsFCL28"

st.set_page_config(page_title="二次会受付・名簿計算", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    data = conn.read(spreadsheet=SHEET_ID, ttl=0)
    # 数値変換と空欄埋め
    for c in ['大人', '子供', '先生']:
        if c in data.columns:
            data[c] = pd.to_numeric(data[c], errors='coerce').fillna(0).astype(int)
    # 集金済フラグの整理
    if '集金済' not in data.columns:
        data['集金済'] = False
    else:
        data['集金済'] = data['集金済'].fillna(False).astype(bool)
    return data

try:
    df = load_data()
except Exception:
    st.error("データの読み込みに失敗しました。")
    st.stop()

st.title("💰 二次会・集金管理システム")

# --- 家庭ごとの小計を計算する関数 ---
def calculate_subtotals(target_df):
    target_df['小計（今回分）'] = (target_df['大人'] * PRICE_ADULT) + \
                                (target_df['子供'] * PRICE_CHILD) + \
                                (target_df['先生'] * PRICE_TEACHER)
    return target_df

# 初回計算
df = calculate_subtotals(df)

# --- 編集エディタ ---
edited_df = st.data_editor(
    df,
    column_config={
        "集金済": st.column_config.CheckboxColumn("集金済", default=False),
        "大人": st.column_config.NumberColumn(min_value=0, step=1),
        "子供": st.column_config.NumberColumn(min_value=0, step=1),
        "先生": st.column_config.NumberColumn(min_value=0, step=1),
        "小計（今回分）": st.column_config.NumberColumn("小計（円）", format="¥%d", disabled=True),
    },
    num_rows="dynamic",
    use_container_width=True,
    key="pro_editor_v1"
)

# 編集後の再計算
final_df = calculate_subtotals(edited_df)

# --- 合計額の表示 ---
st.divider()
total_expected = final_df['小計（今回分）'].sum()
total_collected = final_df[final_df['集金済'] == True]['小計（今回分）'].sum()

c1, c2 = st.columns(2)
with c1:
    st.metric("📋 全員の合計（売上予定）", f"¥{int(total_expected):,}")
with c2:
    st.metric("✅ 現在の回収済合計", f"¥{int(total_collected):,}", 
              delta=f"残り ¥{int(total_expected - total_collected):,}", 
              delta_color="inverse")

# 保存ボタン
if st.button("💾 スプレッドシートへ保存（バックアップ）"):
    try:
        conn.update(spreadsheet=SHEET_ID, data=edited_df)
        st.success("スプレッドシートへの保存が完了しました！")
        st.balloons()
    except Exception:
        st.warning("現在、画面上での計算のみ動作しています（直接保存は制限中）。")
        st.info("💡 画面を閉じなければ、チェックを入れるだけで正確な合計がわかります！")
