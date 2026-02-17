import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- 設定 ---
PRICE_ADULT = 5000
PRICE_CHILD = 1500
PRICE_TEACHER = 2000
# あなたのスプレッドシートURLをここにも貼っておきます
SHEET_URL = "https://docs.google.com/spreadsheets/d/1-ulN6CZCuiK9u0HWnaas1Y7X5QTv7j-xUFkJLsFCL28"

st.set_page_config(page_title="二次会幹事くん Pro", layout="wide")

# Googleスプレッドシートへの接続
conn = st.connection("gsheets", type=GSheetsConnection)

# データの読み込み
def load_data():
    # Secretsから読み込めない場合のためにURLを直接指定
    return conn.read(spreadsheet=SHEET_URL, ttl=0)

try:
    df = load_data()
except Exception as e:
    st.error("スプレッドシートの読み込みに失敗しました。Secretsの設定またはURLを確認してください。")
    st.stop()

st.title("二次会 出欠・集金管理")

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
    key="gsheet_editor_v2"
)

# 保存ボタン
if st.button("💾 スプレッドシートに保存"):
    try:
        conn.update(spreadsheet=SHEET_URL, data=edited_df)
        st.success("Googleスプレッドシートへの保存が完了しました！")
        st.balloons()
    except Exception as e:
        st.error(f"保存エラー: {e}")

# --- 集計表示 ---
calc_df = edited_df.copy()
for col in ['大人', '子供', '先生']:
    calc_df[col] = pd.to_numeric(calc_df[col], errors='coerce').fillna(0)

calc_df['小計'] = (calc_df['大人'] * PRICE_ADULT) + \
                 (calc_df['子供'] * PRICE_CHILD) + \
                 (calc_df['先生'] * PRICE_TEACHER)

st.divider()
total_m = calc_df['小計'].sum()
paid_m = calc_df[calc_df['集金済'] == True]['小計'].sum()

c1, c2, c3 = st.columns(3)
c1.metric("総人数", f"{int(calc_df[['大人', '子供', '先生']].sum().sum())}名")
c2.metric("売上予定", f"¥{int(total_m):,}")
c3.metric("回収済", f"¥{int(paid_m):,}", f"不足 ¥{int(total_m - paid_m):,}", delta_color="inverse")

st.dataframe(calc_df, use_container_width=True)
