import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- 設定 ---
PRICE_ADULT = 5000
PRICE_CHILD = 1500
PRICE_TEACHER = 2000

# 改行などを完全に排除した正しいURL
SHEET_URL = "https://docs.google.com/spreadsheets/d/1-ulN6CZCuiK9u0HWnaas1Y7X5QTv7j-xUFkJLsFCL28"

st.set_page_config(page_title="二次会幹事くん Pro", layout="wide")

# 接続
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # 改行などが混じらないよう、このURLを直接使う
    return conn.read(spreadsheet=SHEET_URL, ttl=0)

try:
    df = load_data()
except Exception as e:
    st.error(f"スプレッドシートが見つかりません。URLを再確認してください。\nエラー詳細: {e}")
    st.stop()

st.title("二次会 出欠・集金管理")

# 編集用エディタ
edited_df = st.data_editor(
    df,
    column_config={
        "集金済": st.column_config.CheckboxColumn("集金済", default=False),
        "大人": st.column_config.NumberColumn(default=1),
        "子供": st.column_config.NumberColumn(default=0),
        "先生": st.column_config.NumberColumn(default=0),
    },
    num_rows="dynamic",
    use_container_width=True,
    key="editor_v7"
)

# 保存ボタン
if st.button("💾 スプレッドシートに保存"):
    try:
        conn.update(spreadsheet=SHEET_URL, data=edited_df)
        st.success("Googleスプレッドシートに保存しました！")
        st.balloons()
    except Exception as e:
        st.error(f"保存に失敗しました。シートの共有設定が『編集者』か確認してください。\n詳細: {e}")

# 集計
calc_df = edited_df.copy()
for col in ['大人', '子供', '先生']:
    calc_df[col] = pd.to_numeric(calc_df[col], errors='coerce').fillna(0)
calc_df['合計'] = (calc_df['大人']*PRICE_ADULT) + (calc_df['子供']*PRICE_CHILD) + (calc_df['先生']*PRICE_TEACHER)

st.divider()
st.metric("回収済合計", f"¥{int(calc_df[calc_df['集金済']==True]['合計'].sum()):,}")
st.dataframe(calc_df, use_container_width=True)
