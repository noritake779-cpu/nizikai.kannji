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
    # 本来あるべき列の定義
    target_cols = ['名前', '大人', '子供', '集金済', '備考']
    
    if os.path.exists(CSV_FILE):
        try:
            raw_df = pd.read_csv(CSV_FILE)
            
            # 1. 必要な列だけを抽出（エラーの原因となる余計な列を強制排除）
            clean_df = pd.DataFrame()
            for col in target_cols:
                if col in raw_df.columns:
                    clean_df[col] = raw_df[col]
                else:
                    # 足りない列をデフォルト値で作成
                    if col == '集金済':
                        clean_df[col] = False
                    elif col in ['大人', '子供']:
                        clean_df[col] = 0
                    else:
                        clean_df[col] = ""
            
            # 2. データ型を強制（ここがズレるとdata_editorが止まるため）
            clean_df['大人'] = pd.to_numeric(clean_df['大人'], errors='coerce').fillna(0).astype(int)
            clean_df['子供'] = pd.to_numeric(clean_df['子供'], errors='coerce').fillna(0).astype(int)
            clean_df['集金済'] = clean_df['集金済'].astype(bool)
            
            return clean_df[target_cols] # 順番も固定
        except:
            pass
    
    # CSVがない、または読み込めない時の初期データ
    return pd.DataFrame({
        '名前': ['森本', '廣川', '山崎', '宮田', '田島', '高橋'],
        '大人': [1, 2, 2, 2, 0, 2],
        '子供': [1, 2, 1, 2, 0, 2],
        '集金済': [False] * 6,
        '備考': [""] * 6
    })

# データのロード（セッション状態の管理）
if 'main_df' not in st.session_state:
    st.session_state.main_df = get_clean_df()

st.title("二次会 出欠・集金管理")

# --- 1. 編集セクション ---
st.subheader("📝 ゲスト名簿（編集・集金チェック）")
st.caption("※人数を変更したり、集金チェックを入れたら、下の『💾 保存』を押してください。")

# 計算列を含ませない「生データ」のみを編集対象にする
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
    key="editor_v9_final" # キーを新しくして古いキャッシュを破棄
)

# 保存処理
if st.button("💾 変更を確定して保存する"):
    st.session_state.main_df = edited_df
    # CSVには計算列を含めずに保存（型エラーの再発を防止）
    edited_df.to_csv(CSV_FILE, index=False)
    st.success("保存完了！集計が更新されました。")
    st.rerun()

# --- 2. 表示・集計セクション ---
# 表示用にコピーして「家庭合計」を計算
calc_df = edited_df.copy()
calc_df['家庭合計'] = (calc_df['大人'] * PRICE_ADULT) + (calc_df['子供'] * PRICE_CHILD)

st.divider()
st.subheader("📊 会計・集計状況")

total_expected = calc_df['家庭合計'].sum()
total_collected = calc_df[calc_df['集金済'] == True]['家庭合計'].sum()

c1, c2, c3 = st.columns(3)
c1.metric("総人数", f"{calc_df['大人'].sum() + calc_df['子供'].sum()} 名")
c2.metric("総売上予定", f"¥{total_expected:,}")
c3.metric("回収済金額", f"¥{total_collected:,}", f"不足 ¥{total_expected - total_collected:,}", delta_color="inverse")

# 金額入り確認用（閲覧専用）
st.dataframe(
    calc_df[['名前', '大人', '子供', '家庭合計', '集金済', '備考']],
    column_config={"家庭合計": st.column_config.NumberColumn(format="¥%d")},
    use_container_width=True
)

# --- 3. 印刷・PDF対策 ---
st.divider()
if st.checkbox("🖨️ PDF・印刷用リストを表示"):
    st.info("【PDF保存】: この表が表示されたら、ブラウザの『印刷』メニューから『PDFとして保存』を選んでください。")
    print_df = calc_df[['名前', '大人', '子供', '家庭合計', '集金済', '備考']].copy()
    print_df['集金済'] = print_df['集金済'].apply(lambda x: "済" if x else " ")
    st.table(print_df.style.format({"家庭合計": "¥{:,.0f}"}))

# 予備のCSVダウンロード
csv_data = calc_df.to_csv(index=False).encode('utf_8_sig')
st.download_button("Excel用CSVをダウンロード", csv_data, "attendance.csv", "text/csv")
