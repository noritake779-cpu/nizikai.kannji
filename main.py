import streamlit as st
import pandas as pd
import os

# --- 設定 ---
CSV_FILE = 'attendance_data.csv'
PRICE_ADULT = 5000
PRICE_CHILD = 1500

st.set_page_config(page_title="二次会幹事くん", layout="wide")

# --- 【強制クレンジング】読み込み時に余計な列を捨てる ---
def load_and_fix_data():
    target_cols = ['名前', '大人', '子供', '集金済', '備考']
    
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
            # CSVに余計な列（家庭合計など）があれば強制削除し、必要な5列のみ抽出
            df = df[[c for c in target_cols if c in df.columns]]
            
            # 足りない列があれば補完
            for c in target_cols:
                if c not in df.columns:
                    df[c] = False if c == '集金済' else (0 if c in ['大人', '子供'] else "")
            
            # 型を無理やり合わせる
            df['大人'] = pd.to_numeric(df['大人'], errors='coerce').fillna(0).astype(int)
            df['子供'] = pd.to_numeric(df['子供'], errors='coerce').fillna(0).astype(int)
            df['集金済'] = df['集金済'].astype(bool)
            
            return df[target_cols] # 列順を固定
        except:
            pass

    return pd.DataFrame({
        '名前': ['森本', '廣川', '山崎', '宮田', '田島', '高橋'],
        '大人': [1, 2, 2, 2, 0, 2], '子供': [1, 2, 1, 2, 0, 2],
        '集金済': [False]*6, '備考': [""]*6
    })

# データロード
if 'df' not in st.session_state:
    st.session_state.df = load_and_fix_data()

st.title("二次会 出欠・集金管理")

# --- リスト編集 ---
st.subheader("📝 名簿編集・集金チェック")

edited_df = st.data_editor(
    st.session_state.df,
    column_config={
        "名前": st.column_config.TextColumn("名前"),
        "大人": st.column_config.NumberColumn("大人", min_value=0),
        "子供": st.column_config.NumberColumn("子供", min_value=0),
        "集金済": st.column_config.CheckboxColumn("集金済"),
        "備考": st.column_config.TextColumn("備考"),
    },
    num_rows="dynamic",
    use_container_width=True,
    key="fixed_editor_V100" # キーを大幅に変えてキャッシュを無視
)

if st.button("💾 データを保存する"):
    st.session_state.df = edited_df
    # CSVには計算列を含めず保存
    edited_df.to_csv(CSV_FILE, index=False)
    st.success("保存完了！")
    st.rerun()

# --- 計算表示（編集後のデータに基づいて表示のみ行う） ---
calc_df = edited_df.copy()
calc_df['合計'] = (calc_df['大人'] * PRICE_ADULT) + (calc_df['子供'] * PRICE_CHILD)

st.divider()
st.subheader("📊 集計状況")
m1, m2, m3 = st.columns(3)
total = calc_df['合計'].sum()
paid = calc_df[calc_df['集金済'] == True]['合計'].sum()
m1.metric("総人数", f"{calc_df['大人'].sum() + calc_df['子供'].sum()}名")
m2.metric("売上予定", f"¥{total:,}")
m3.metric("回収済", f"¥{paid:,}", f"未回収 ¥{total - paid:,}", delta_color="inverse")

# 閲覧用テーブル
st.dataframe(calc_df, use_container_width=True)

# 印刷
if st.checkbox("🖨️ PDF・印刷用表示"):
    st.table(calc_df)
