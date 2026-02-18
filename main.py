import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- お会計の設定 ---
PRICE_ADULT = 5000
PRICE_CHILD = 1500
PRICE_TEACHER = 2000
# あなたのスプレッドシートURL
SHEET_URL = "https://docs.google.com/spreadsheets/d/1-ulN6CZCuiK9u0HWnaas1Y7X5QTv7j-xUFkJLsFCL28"

st.set_page_config(page_title="二次会幹事くん Pro", layout="wide")

# 接続設定
conn = st.connection("gsheets", type=GSheetsConnection)

# データの読み込み
def load_data():
    # URLを直接指定して読み込む（これが一番確実です）
    return conn.read(spreadsheet=SHEET_URL, ttl=0)

try:
    df = load_data()
except Exception as e:
    st.error(f"スプレッドシートの読み込みに失敗しました。URLまたは共有設定を確認してください。\nエラー詳細: {e}")
    st.stop()

st.title("二次会 出欠・集金管理")

# 編集用エディタ
edited_df = st.data_editor(
    df,
    column_config={
        "集金済": st.column_config.CheckboxColumn("集金済", default=False),
        "大人": st.column_config.NumberColumn("大人", min_value=0, step=1, default=1),
        "子供": st.column_config.NumberColumn("子供", min_value=0, step=1, default=0),
        "先生": st.column_config.NumberColumn("先生", min_value=0, step=1, default=0),
    },
    num_rows="dynamic",
    use_container_width=True,
    key="gsheet_editor_final"
)

# 保存ボタン
if st.button("💾 スプレッドシートに保存"):
    try:
        conn.update(spreadsheet=SHEET_URL, data=edited_df)
        st.success("Googleスプレッドシートへの保存に成功しました！")
        st.balloons()
    except Exception as e:
        st.error(f"保存エラー: {e}\nスプレッドシートが『編集者』権限で共有されているか確認してください。")

# --- 集計計算 ---
calc_df = edited_df.copy()
# 数値として扱うための変換
for col in ['大人', '子供', '先生']:
    calc_df[col] = pd.to_numeric(calc_df[col], errors='coerce').fillna(0)

calc_df['小計'] = (calc_df['大人'] * PRICE_ADULT) + \
                 (calc_df['子供'] * PRICE_CHILD) + \
                 (calc_df['先生'] * PRICE_TEACHER)

st.divider()
total_m = calc_df['小計'].sum()
paid_m = calc_df[calc_df['集金済'] == True]['小計'].sum()

c1, c2, c3 = st.columns(3)
c1.metric("総人数", f"{int(calc_df[['大人', '子供', '先生']].sum().sum())} 名")
c2.metric("総売上予定", f"¥{int(total_m):,}")
c3.metric("回収済金額", f"¥{int(paid_m):,}", f"不足 ¥{int(total_m - paid_m):,}", delta_color="inverse")

# 金額入りの確認表
st.dataframe(calc_df, use_container_width=True)
