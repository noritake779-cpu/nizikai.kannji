import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# お会計設定
PRICE_ADULT = 5000
PRICE_CHILD = 1500
PRICE_TEACHER = 2000

# 教えていただいた正しいID
SHEET_ID = "1-ulN6CZCuiK9uOHWnaas1Y7X5QTv7j-xUFkJLsFCL28"

st.set_page_config(page_title="二次会幹事くん Pro", layout="wide")

# 接続
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # IDを直接指定して読み込む
    return conn.read(spreadsheet=SHEET_ID, ttl=0)

try:
    df = load_data()
except Exception as e:
    st.error("スプレッドシートにアクセスできません。")
    st.info(f"設定されているID: {SHEET_ID}")
    st.warning("Googleシートの『共有』ボタンから、『リンクを知っている全員』かつ『編集者』になっていますか？")
    st.stop()

st.title("二次会 出欠・集金管理")

# 編集用エディタ
edited_df = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True,
    key="editor_final_id_fix"
)

# 保存ボタン
if st.button("💾 スプレッドシートに保存"):
    try:
        conn.update(spreadsheet=SHEET_ID, data=edited_df)
        st.success("スプレッドシートへの保存に成功しました！")
        st.balloons()
    except Exception as e:
        st.error(f"保存失敗: {e}")

# 集計計算
calc_df = edited_df.copy()
for col in ['大人', '子供', '先生']:
    calc_df[col] = pd.to_numeric(calc_df[col], errors='coerce').fillna(0)
calc_df['小計'] = (calc_df['大人']*PRICE_ADULT) + (calc_df['子供']*PRICE_CHILD) + (calc_df['先生']*PRICE_TEACHER)

st.divider()
st.metric("回収済合計", f"¥{int(calc_df[calc_df['集金済']==True]['小計'].sum()):,}")
st.dataframe(calc_df, use_container_width=True)
