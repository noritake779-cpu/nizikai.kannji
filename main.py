import streamlit as st
import pandas as pd
import os

# --- 設定 ---
CSV_FILE = 'attendance_data.csv'
PRICE_ADULT = 5000
PRICE_CHILD = 1500
PRICE_TEACHER = 2000

st.set_page_config(page_title="二次会幹事くん", layout="wide")

# --- 【強制クレンジング関数】 ---
def load_and_fix_data_v2():
    # 最終的に必要な列（この順番・この名前以外を認めない）
    target_cols = ['名前', '大人', '子供', '先生', '集金済', '備考']
    
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
            # 古い列（家庭合計など）を強制排除。target_colsにある列のみ拾う
            valid_df = df[[c for c in target_cols if c in df.columns]].copy()
            
            # 足りない列（今回追加した「先生」など）を補完
            for col in target_cols:
                if col not in valid_df.columns:
                    if col == '集金済': valid_df[col] = False
                    elif col in ['大人', '子供', '先生']: valid_df[col] = 0
                    else: valid_df[col] = ""
            
            # 型を無理やり固定
            valid_df['大人'] = pd.to_numeric(valid_df['大人'], errors='coerce').fillna(0).astype(int)
            valid_df['子供'] = pd.to_numeric(valid_df['子供'], errors='coerce').fillna(0).astype(int)
            valid_df['先生'] = pd.to_numeric(valid_df['先生'], errors='coerce').fillna(0).astype(int)
            valid_df['集金済'] = valid_df['集金済'].astype(bool)
            
            return valid_df[target_cols] # 列順を強制固定
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

# データロード
if 'df_final' not in st.session_state:
    st.session_state.df_final = load_and_fix_data_v2()

st.title("二次会 出欠・集金管理")

# --- 1. 名簿編集 ---
st.subheader("📝 名簿編集（先生枠追加）")
st.caption("大人5000円 / 子供1500円 / 先生2000円")

# エディタには計算列を含まない6列だけを渡す
edited_df = st.data_editor(
    st.session_state.df_final,
    column_config={
        "名前": st.column_config.TextColumn("名前"),
        "大人": st.column_config.NumberColumn("大人", min_value=0, step=1),
        "子供": st.column_config.NumberColumn("子供", min_value=0, step=1),
        "先生": st.column_config.NumberColumn("先生", min_value=0, step=1),
        "集金済": st.column_config.CheckboxColumn("集金済"),
        "備考": st.column_config.TextColumn("備考", width="large"),
    },
    num_rows="dynamic",
    use_container_width=True,
    key="editor_teacher_v1" # キーを変えてキャッシュを破棄
)

if st.button("💾 データを保存する"):
    st.session_state.df_final = edited_df
    # CSVには計算列を入れずに保存
    edited_df.to_csv(CSV_FILE, index=False)
    st.success("保存完了！")
    st.rerun()

# --- 2. 集計表示 ---
# 表示用にコピーして合計金額を計算
calc_df = edited_df.copy()
calc_df['合計額'] = (calc_df['大人'] * PRICE_ADULT) + \
                    (calc_df['子供'] * PRICE_CHILD) + \
                    (calc_df['先生'] * PRICE_TEACHER)

st.divider()
st.subheader("📊 会計状況")
total_m = calc_df['合計額'].sum()
paid_m = calc_df[calc_df['集金済'] == True]['合計額'].sum()

m1, m2, m3 = st.columns(3)
m1.metric("総人数", f"{calc_df[['大人', '子供', '先生']].sum().sum()}名")
m2.metric("売上予定", f"¥{total_m:,}")
m3.metric("回収済", f"¥{paid_m:,}", f"不足 ¥{total_m - paid_m:,}", delta_color="inverse")

# 金額入り確認表
st.dataframe(
    calc_df,
    column_config={"合計額": st.column_config.NumberColumn(format="¥%d")},
    use_container_width=True
)

# --- 3. 印刷対策 ---
st.divider()
if st.checkbox("🖨️ PDF・印刷用リストを表示"):
    st.info("ブラウザのメニューから『印刷』を選んでPDF保存してください。")
    print_df = calc_df.copy()
    print_df['集金済'] = print_df['集金済'].apply(lambda x: "済" if x else " ")
    st.table(print_df.style.format({"合計額": "¥{:,.0f}"}))
