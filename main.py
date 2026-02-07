import streamlit as st
import pandas as pd
import os

# --- 設定 ---
CSV_FILE = 'attendance_data.csv'
PRICE_ADULT = 5000
PRICE_CHILD = 1500

st.set_page_config(page_title="二次会幹事くん", layout="wide")

# --- 【最重要】データクレンジング関数 ---
def get_clean_df():
    # 本来あるべき列（これ以外がCSVにあると無視する）
    target_cols = ['名前', '大人', '子供', '集金済', '備考']
    
    if os.path.exists(CSV_FILE):
        try:
            # 一旦すべて読み込む（エンコーディングは必要に応じて変更）
            raw_df = pd.read_csv(CSV_FILE)
            
            # 余計な列を強制的にドロップ
            existing_valid_cols = [c for c in target_cols if c in raw_df.columns]
            clean_df = raw_df[existing_valid_cols].copy()

            # 足りない列をデフォルト値で補完
            for col in target_cols:
                if col not in clean_df.columns:
                    if col == '集金済':
                        clean_df[col] = False
                    elif col in ['大人', '子供']:
                        clean_df[col] = 0
                    else:
                        clean_df[col] = ""

            # 型を安全に補正
            clean_df['大人'] = pd.to_numeric(clean_df['大人'], errors='coerce').fillna(0).astype(int)
            clean_df['子供'] = pd.to_numeric(clean_df['子供'], errors='coerce').fillna(0).astype(int)

            # 集金済は文字列・NaN 混在でも True/False に直す
            clean_df['集金済'] = (
                clean_df['集金済']
                .astype(str)
                .str.strip()
                .str.lower()
                .isin(['true', '1', 't', 'y', 'yes', '済'])
            )

            # 列順を固定して返す
            return clean_df[target_cols]

        except Exception as e:
            st.error(f"CSVの読み込み／修復に失敗しました。新規データで再作成します: {e}")

    # --- 初期データ（CSVが無い・壊れている場合はこちら） ---
    return pd.DataFrame({
        '名前': ['森本', '廣川', '山崎', '宮田', '田島', '高橋'],
        '大人': [1, 2, 2, 2, 0, 2],
        '子供': [1, 2, 1, 2, 0, 2],
        '集金済': [False] * 6,
        '備考': [""] * 6
    })

# 初回読み込み（キャッシュの影響を受けないようsession_stateを管理）
if 'main_df' not in st.session_state:
    st.session_state.main_df = get_clean_df()

st.title("二次会 出欠・集金管理")

# --- 1. 編集セクション ---
st.subheader("📝 ゲスト名簿（編集・集金チェック）")
st.caption("※人数を変更したりチェックを入れたら、下の『💾 保存』を押してください。")

# 編集用：計算列を含まないクリーンな5列のみを渡す
edited_df = st.data_editor(
    st.session_state.main_df,
    column_config={
        "名前": st.column_config.TextColumn("名前", width="medium"),
        "大人": st.column_config.NumberColumn("大人", min_value=0, step=1),
        "子供": st.column_config.NumberColumn("子供", min_value=0, step
