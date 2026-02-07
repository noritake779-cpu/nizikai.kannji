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
    # 本来あるべき列（これ以外がCSVにあるとエラーになる）
    target_cols = ['名前', '大人', '子供', '集金済', '備考']
    
    if os.path.exists(CSV_FILE):
        try:
            # 一旦すべて読み込む
            raw_df = pd.read_csv(CSV_FILE)
            
            # 【外科手術】target_colsに含まれる列だけを抽出（余計な列を強制削除）
            # これにより「家庭合計」列などがCSVにあっても無視されます
            existing_valid_cols = [c for c in target_cols if c in raw_df.columns]
            clean_df = raw_df[existing_valid_cols].copy()
            
            # 足りない列（新規追加分など）をデフォルト値で作成
            for col in target_cols:
                if col not in clean_df.columns:
                    if col == '集金済':
                        clean_df[col] = False
                    elif col in ['大人', '子供']:
                        clean_df[col] = 0
                    else:
                        clean_df[col] = ""
            
            # データ型を厳密に固定（ここがズレてもエラーになるため）
            clean_df['大人'] = pd.to_numeric(clean_df['大人'], errors='coerce').fillna(0).astype(int)
            clean_df['子供'] = pd.to_numeric(clean_df['子供'], errors='coerce').fillna(0).astype(int)
            clean_df['集金済'] = clean_df['集金済'].astype(bool)
            
            return clean_df[target_cols] # 列順を固定して返す
        except Exception as e:
            st.error(f"データ修復中... {e}")
            
    # 初期データ
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
        "子供": st.column_config.NumberColumn("子供", min_value=0, step=1),
        "集金済": st.column_config.CheckboxColumn("集金済"),
        "備考": st.column_config.TextColumn("備考", width="large"),
    },
    num_rows="dynamic",
    use_container_width=True,
    key="editor_v11_final" # キーを更新して内部キャッシュを強制リセット
)

# 保存処理
if st.button("💾 変更を確定して保存する"):
    # CSVには計算列を含めずに保存（エラー再発防止）
    edited_df.to_csv(CSV_FILE, index=False)
    st.session_state.main_df = edited_df
    st.success("保存しました！集計を更新します。")
    st.rerun()

# --- 2. 計算と集計表示 ---
# 表示用にコピーして「家庭合計」を追加
calc_df = edited_df.copy()
calc_df['家庭合計'] = (calc_df['大人'] * PRICE_ADULT) + (calc_df['子供'] * PRICE_CHILD)

st.divider()
st.subheader("📊 会計・集計状況")

total_exp = calc_df['家庭合計'].sum()
total_coll = calc_df[calc_df['集金済'] == True]['家庭合計'].sum()

m1, m2, m3 = st.columns(3)
m1.metric("総人数", f"{calc_df['大人'].sum() + calc_df['子供'].sum()} 名")
m2.metric("総売上予定", f"¥{total_exp:,}")
m3.metric("回収済金額", f"¥{total_coll:,}", f"不足 ¥{total_exp - total_coll:,}", delta_color="inverse")

# 閲覧用（金額入り）の表
st.dataframe(
    calc_df[['名前', '大人', '子供', '家庭合計', '集金済', '備考']],
    column_config={"家庭合計": st.column_config.NumberColumn(format="¥%d")},
    use_container_width=True
)

# --- 3. 印刷・PDF出力 ---
st.divider()
if st.checkbox("🖨️ PDF・印刷用リストを表示"):
    st.info("ブラウザの「印刷」メニューから「PDFとして保存」を実行してください。")
    print_df = calc_df[['名前', '大人', '子供', '家庭合計', '集金済', '備考']].copy()
    print_df['集金済'] = print_df['集金済'].apply(lambda x: "済" if x else " ")
    st.table(print_df.style.format({"家庭合計": "¥{:,.0f}"}))
