import streamlit as st
import pandas as pd
import os

# --- 設定 ---
CSV_FILE = 'attendance_data.csv'
PRICE_ADULT = 5000
PRICE_CHILD = 1500
PRICE_TEACHER = 2000

st.set_page_config(page_title="二次会幹事くん", layout="wide")

# --- データの読み込みと列の強制整形 ---
def load_data():
    # 必要な6列を定義
    target_cols = ['名前', '大人', '子供', '先生', '集金済', '備考']
    
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
            # 1. 余計な列を削除
            df = df[[c for c in target_cols if c in df.columns]].copy()
            # 2. 足りない列を補完
            for col in target_cols:
                if col not in df.columns:
                    if col == '集金済': df[col] = False
                    elif col in ['大人', '子供', '先生']: df[col] = 0
                    else: df[col] = ""
            # 3. 型を固定（ここがズレるとチェックボックスが出ません）
            df['大人'] = pd.to_numeric(df['大人']).fillna(0).astype(int)
            df['子供'] = pd.to_numeric(df['子供']).fillna(0).astype(int)
            df['先生'] = pd.to_numeric(df['先生']).fillna(0).astype(int)
            df['集金済'] = df['集金済'].astype(bool)
            return df[target_cols]
        except:
            pass

    # 初期データ
    return pd.DataFrame({
        '名前': ['森本', '廣川', '山崎', '宮田', '田島', '高橋'],
        '大人': [1, 2, 2, 2, 0, 2],
        '子供': [1, 2, 1, 2, 0, 2],
        '先生': [0, 0, 0, 0, 0, 0],
        '集金済': [False] * 6,
        '備考': [""] * 6
    })

if 'df' not in st.session_state:
    st.session_state.df = load_data()

st.title("二次会 出欠・集金管理")

# --- 1. 名簿編集セクション ---
st.subheader("📝 名簿編集")
st.info("一番下の空行に名前を入れると、新しい行が追加されます。")

# エディタ設定（エラーの原因になる引数を削り、最も安定した形にしました）
edited_df = st.data_editor(
    st.session_state.df,
    column_config={
        "名前": st.column_config.TextColumn("名前"),
        "大人": st.column_config.NumberColumn("大人", min_value=0, step=1, default=0),
        "子供": st.column_config.NumberColumn("子供", min_value=0, step=1, default=0),
        "先生": st.column_config.NumberColumn("先生", min_value=0, step=1, default=0),
        "集金済": st.column_config.CheckboxColumn("集金済", default=False),
        "備考": st.column_config.TextColumn("備考"),
    },
    num_rows="dynamic",
    use_container_width=True,
    key="editor_vfinal"
)

if st.button("💾 変更を保存する"):
    st.session_state.df = edited_df
    # CSV保存（計算列は含めない）
    edited_df.to_csv(CSV_FILE, index=False)
    st.success("保存しました！")
    st.rerun()

# --- 2. 計算と集計 ---
# 新しく追加された行も含めて計算
calc_df = edited_df.copy()
calc_df['合計額'] = (calc_df['大人'].astype(int) * PRICE_ADULT) + \
                    (calc_df['子供'].astype(int) * PRICE_CHILD) + \
                    (calc_df['先生'].astype(int) * PRICE_TEACHER)

st.divider()
st.subheader("📊 会計状況")

total_m = calc_df['合計額'].sum()
paid_m = calc_df[calc_df['集金済'] == True]['合計額'].sum()

m1, m2, m3 = st.columns(3)
m1.metric("総人数", f"{int(calc_df[['大人', '子供', '先生']].sum().sum())}名")
m2.metric("売上予定", f"¥{int(total_m):,}")
m3.metric("回収済", f"¥{int(paid_m):,}", f"不足 ¥{int(total_m - paid_m):,}", delta_color="inverse")

# 金額入りの表
st.dataframe(
    calc_df,
    column_config={"合計額": st.column_config.NumberColumn(format="¥%d")},
    use_container_width=True
)

# --- 3. 印刷用 ---
if st.checkbox("🖨️ PDF・印刷用リストを表示"):
    print_df = calc_df.copy()
    print_df['集金済'] = print_df['集金済'].apply(lambda x: "済" if x else " ")
    st.table(print_df.style.format({"合計額": "¥{:,.0f}"}))
