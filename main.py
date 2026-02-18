import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- 会費の設定 ---
PRICE_ADULT = 5000
PRICE_CHILD = 1500
PRICE_TEACHER = 2000

# スプレッドシートID
SHEET_ID = "1-ulN6CZCuiK9uOHWnaas1Y7X5QTv7j-xUFkJLsFCL28"

st.set_page_config(page_title="二次会幹事くん Pro", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    data = conn.read(spreadsheet=SHEET_ID, ttl=0)
    # データの整理（空欄を0に、チェックボックスをTrue/Falseに）
    cols = ['大人', '子供', '先生']
    for col in cols:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)
    
    if '集金済' not in data.columns:
        data['集金済'] = False
    else:
        # 0/1 や None を True/False に変換してチェックボックスを押しやすくする
        data['集金済'] = data['集金済'].map({1: True, 0: False, 'True': True, 'False': False}).fillna(False)
    return data

try:
    df = load_data()
except Exception:
    st.error("データの読み込みに失敗しました。")
    st.stop()

st.title("💰 二次会・集金管理")

# --- エディタの設定（チェックボックスを有効化） ---
edited_df = st.data_editor(
    df,
    column_config={
        "集金済": st.column_config.CheckboxColumn(
            "集金済",
            help="お金を貰ったらチェック！",
            default=False,
        ),
        "大人": st.column_config.NumberColumn(min_value=0, step=1),
        "子供": st.column_config.NumberColumn(min_value=0, step=1),
        "先生": st.column_config.NumberColumn(min_value=0, step=1),
    },
    num_rows="dynamic",
    use_container_width=True,
    key="collection_editor"
)

# --- 計算ロジック ---
calc_df = edited_df.copy()
# 個人ごとの合計を計算
calc_df['個人計'] = (calc_df['大人'] * PRICE_ADULT) + \
                   (calc_df['子供'] * PRICE_CHILD) + \
                   (calc_df['先生'] * PRICE_TEACHER)

# ① 集金予定額（リスト全員の合計）
total_expected = calc_df['個人計'].sum()
# ② 回収済合計（チェックが入っている人だけの合計）
total_collected = calc_df[calc_df['集金済'] == True]['個人計'].sum()

# --- 画面表示 ---
st.divider()
col1, col2 = st.columns(2)
with col1:
    st.metric("📋 集金予定額（総額）", f"¥{int(total_expected):,}")
with col2:
    st.metric("✅ 回収済合計額", f"¥{int(total_collected):,}", delta=f"不足 ¥{int(total_expected - total_collected):,}", delta_color="inverse")

# 保存ボタン（書き込みエラーが出る場合は画面上で確認のみ行う）
if st.button("💾 スプレッドシートに保存"):
    try:
        conn.update(spreadsheet=SHEET_ID, data=edited_df)
        st.success("スプレッドシートに保存しました！")
        st.balloons()
    except Exception:
        st.warning("スプレッドシートへの直接保存はできませんでしたが、現在の画面上で集計は正しく行われています。")
