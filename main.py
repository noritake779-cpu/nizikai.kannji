import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- お会計の設定 ---
PRICE_ADULT = 5000
PRICE_CHILD = 1500
PRICE_TEACHER = 2000

# 正しいID（教えていただいたもの）
SHEET_ID = "1-ulN6CZCuiK9uOHWnaas1Y7X5QTv7j-xUFkJLsFCL28"

st.set_page_config(page_title="二次会幹事くん Pro", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # 読み込み時に空欄(None)を0やFalseで埋める
    data = conn.read(spreadsheet=SHEET_ID, ttl=0)
    data['大人'] = data['大人'].fillna(0)
    data['子供'] = data['子供'].fillna(0)
    data['先生'] = data['先生'].fillna(0)
    if '集金済' not in data.columns:
        data['集金済'] = False
    else:
        data['集金済'] = data['集金済'].fillna(False).replace({0: False, 1: True})
    return data

try:
    df = load_data()
except Exception as e:
    st.error(f"スプレッドシートの読み込みに失敗しました。\n{e}")
    st.stop()

st.title("二次会 出欠・集金管理")

# 編集用エディタ
edited_df = st.data_editor(
    df,
    column_config={
        "集金済": st.column_config.CheckboxColumn("集金済", default=False),
        "大人": st.column_config.NumberColumn(min_value=0, step=1),
        "子供": st.column_config.NumberColumn(min_value=0, step=1),
        "先生": st.column_config.NumberColumn(min_value=0, step=1),
    },
    num_rows="dynamic",
    use_container_width=True,
    key="editor_v_final"
)

# --- 合計額のリアルタイム計算 ---
calc_df = edited_df.copy()
# 数字に変換
for col in ['大人', '子供', '先生']:
    calc_df[col] = pd.to_numeric(calc_df[col], errors='coerce').fillna(0)

# 個別の小計を計算
calc_df['個人計'] = (calc_df['大人'] * PRICE_ADULT) + \
                   (calc_df['子供'] * PRICE_CHILD) + \
                   (calc_df['先生'] * PRICE_TEACHER)

# 集金済にチェックが入っている人の「個人計」だけを合計する
paid_total = calc_df[calc_df['集金済'] == True]['個人計'].sum()

st.divider()
# デカデカと表示！
st.markdown(f"## 💰 回収済合計:  **¥{int(paid_total):,}**")

# 保存ボタン（エラーが出ても計算は止まらないように配置）
if st.button("💾 スプレッドシートに保存"):
    try:
        conn.update(spreadsheet=SHEET_ID, data=edited_df)
        st.success("スプレッドシートへの保存に成功しました！")
        st.balloons()
    except Exception:
        st.error("保存失敗。スプレッドシートへの書き込み権限が不足しています。")
        st.info("💡 保存ができなくても、この画面上でチェックを入れれば『回収済合計』は正しく計算されます！")

st.dataframe(calc_df[['名前', '大人', '子供', '先生', '集金済', '個人計']], use_container_width=True)

st.subheader(f"回収済合計: ¥{int(paid_total):,}")
st.dataframe(calc_df, use_container_width=True)
