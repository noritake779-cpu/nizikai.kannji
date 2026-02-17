import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- 設定 ---
PRICE_ADULT = 5000
PRICE_CHILD = 1500
PRICE_TEACHER = 2000
# Secretsがダメでも動くようにURLを直接指定
SHEET_URL = "https://docs.google.com/spreadsheets/d/1-ulN6CZCuiK9u0HWnaas1Y7X5QTv7j-xUFkJLsFCL28"

st.set_page_config(page_title="二次会幹事くん Pro", layout="wide")

# 接続
conn = st.connection("gsheets", type=GSheetsConnection)

# データの読み込み
def load_data():
    # 万が一の読み込みエラーを回避するため直接URLを指定
    return conn.read(spreadsheet=SHEET_URL, ttl=0)

try:
    df = load_data()
except Exception as e:
    st.error(f"スプレッドシートの読み込みに失敗しました。URLまたは共有設定を確認してください。\nエラー詳細: {e}")
    st.stop()

st.title("二次会 出欠・集金管理")
st.info("編集後、下の『保存』ボタンを必ず押してください。")

# 編集用エディタ
edited_df = st.data_editor(
    df,
    column_config={
        "集金済": st.column_config.CheckboxColumn("集金済", default=False),
        "大人": st.column_config.NumberColumn(default=0),
        "子供": st.column_config.NumberColumn(default=0),
        "先生": st.column_config.NumberColumn(default=0),
    },
    num_rows="dynamic",
    use_container_width=True,
    key="editor_gsheet_final_v3"
)

# 保存ボタン
if st.button("💾 スプレッドシートに保存"):
    try:
        conn.update(spreadsheet=SHEET_URL, data=edited_df)
        st.success("Googleスプレッドシートに保存しました！")
        st.balloons()
    except Exception as e:
        st.error(f"保存エラー: {e}\nスプレッドシートが『編集者』権限で共有されているか確認してください。")

# --- 集計 ---
calc_df = edited_df.copy()
for col in ['大人', '子供', '先生']:
    calc_df[col] = pd.to_numeric(calc_df[col], errors='coerce').fillna(0)

calc_df['合計'] = (calc_df['大人'] * PRICE_ADULT) + \
                 (calc_df['子供'] * PRICE_CHILD) + \
                 (calc_df['先生'] * PRICE_TEACHER)

st.divider()
st.subheader("📊 現在の集計")
st.metric("回収済合計", f"¥{int(calc_df[calc_df['集金済']==True]['合計'].sum()):,}")
st.dataframe(calc_df, use_container_width=True)
