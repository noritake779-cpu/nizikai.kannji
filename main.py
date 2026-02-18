import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# お会計設定
PRICE_ADULT = 5000
PRICE_CHILD = 1500
PRICE_TEACHER = 2000

# 正しいURL（ここをスプレッドシートの「リンクをコピー」で得たものに書き換えてもOKです）
SHEET_URL = "https://docs.google.com/spreadsheets/d/1-ulN6CZCuiK9u0HWnaas1Y7X5QTv7j-xUFkJLsFCL28"

st.set_page_config(page_title="二次会幹事くん Pro", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # 改行や空白を除去して確実に読み込む
    clean_url = SHEET_URL.strip()
    return conn.read(spreadsheet=clean_url, ttl=0)

try:
    df = load_data()
except Exception as e:
    st.error("スプレッドシートにアクセスできません。")
    st.warning("【確認事項】\n1. スプレッドシートの共有設定を『リンクを知っている全員』かつ『編集者』にしていますか？\n2. URLが正しいですか？")
    st.info(f"技術的なエラー詳細: {e}")
    st.stop()

st.title("二次会 出欠・集金管理")

# エディタ表示
edited_df = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True,
    key="editor_final_stable_v1"
)

# 保存ボタン
if st.button("💾 スプレッドシートに保存"):
    try:
        conn.update(spreadsheet=SHEET_URL.strip(), data=edited_df)
        st.success("保存に成功しました！")
        st.balloons()
    except Exception as e:
        st.error(f"保存失敗: {e}")
