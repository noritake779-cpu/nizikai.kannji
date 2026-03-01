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
    for c in ['大人', '子供', '先生']:
        if c in data.columns:
            data[c] = pd.to_numeric(data[c], errors='coerce').fillna(0).astype(int)
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

# 小計計算関数
def calculate_subtotals(target_df):
    target_df['小計（今回分）'] = (target_df['大人'] * PRICE_ADULT) + \
                                (target_df['子供'] * PRICE_CHILD) + \
                                (target_df['先生'] * PRICE_TEACHER)
    # 1行ごとの合計人数も計算
    target_df['行人数'] = target_df['大人'] + target_df['子供'] + target_df['先生']
    return target_df

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
        "行人数": st.column_config.NumberColumn("人数", disabled=True),
    },
    num_rows="dynamic",
    use_container_width=True,
    key="pro_editor_v2"
)

final_df = calculate_subtotals(edited_df)

# --- 集計エリア ---
st.divider()

# 人数の集計
total_adults = final_df['大人'].sum()
total_children = final_df['子供'].sum()
total_teachers = final_df['先生'].sum()
total_people = total_adults + total_children + total_teachers

# 金額の集計
total_expected = final_df['小計（今回分）'].sum()
total_collected = final_df[final_df['集金済'] == True]['小計（今回分）'].sum()

# 表示：1段目（人数）
st.subheader("👥 参加人数 合計")
c_p1, c_p2, c_p3, c_p4 = st.columns(4)
c_p1.metric("総人数", f"{total_people} 名")
c_p2.metric("大人", f"{total_adults} 名")
c_p3.metric("子供", f"{total_children} 名")
c_p4.metric("先生", f"{total_teachers} 名")

# 表示：2段目（金額）
st.subheader("💴 会計状況")
c_m1, c_m2 = st.columns(2)
with c_m1:
    st.metric("📋 集金予定総額", f"¥{int(total_expected):,}")
with c_m2:
    st.metric("✅ 回収済合計", f"¥{int(total_collected):,}", 
              delta=f"残り ¥{int(total_expected - total_collected):,}", 
              delta_color="inverse")

# 保存ボタン
if st.button("💾 スプレッドシートへ保存"):
    try:
        conn.update(spreadsheet=SHEET_ID, data=edited_df)
        st.success("保存しました！")
        st.balloons()
    except Exception:
        st.warning("現在、画面上のみで動作中です。")
