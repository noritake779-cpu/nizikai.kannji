import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# お会計設定
PRICE_ADULT = 5000
PRICE_CHILD = 1500
PRICE_TEACHER = 2000

# 正しいID
SHEET_ID = "1-ulN6CZCuiK9uOHWnaas1Y7X5QTv7j-xUFkJLsFCL28"

st.set_page_config(page_title="二次会幹事くん Pro", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    return conn.read(spreadsheet=SHEET_ID, ttl=0)

try:
    # データを読み込み、空欄(None)を0で埋める
    df = load_data().fillna(0)
except Exception as e:
    st.error("スプレッドシートにアクセスできません。")
    st.stop()

st.title("二次会 出欠・集金管理")

# 編集用エディタ
edited_df = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True,
    key="editor_final_fix_v2"
)

# 保存ボタン
if st.button("💾 スプレッドシートに保存"):
    try:
        # 保存実行
        conn.update(spreadsheet=SHEET_ID, data=edited_df)
        st.success("保存に成功しました！")
        st.balloons()
    except Exception as e:
        st.error(f"保存失敗。シートの共有を『編集者』にしていますか？\nエラー詳細: {e}")

# --- 集計計算（ここを強化しました） ---
calc_df = edited_df.copy()
# 数字以外の文字が入ってもエラーにならないように変換
for col in ['大人', '子供', '先生']:
    calc_df[col] = pd.to_numeric(calc_df[col], errors='coerce').fillna(0)

# 1行ずつの小計
calc_df['小計'] = (calc_df['大人'] * PRICE_ADULT) + \
                 (calc_df['子供'] * PRICE_CHILD) + \
                 (calc_df['先生'] * PRICE_TEACHER)

st.divider()
# 集金済にチェックが入っている人の合計を計算
paid_total = calc_df[calc_df['集金済'] == True]['小計'].sum() if '集金済' in calc_df.columns else 0

st.subheader(f"回収済合計: ¥{int(paid_total):,}")
st.dataframe(calc_df, use_container_width=True)
