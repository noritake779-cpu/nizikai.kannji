import streamlit as st
import pandas as pd
import os

# --- 設定 ---
CSV_FILE = 'attendance_data.csv'
PRICE_ADULT = 5000
PRICE_CHILD = 1500

st.set_page_config(page_title="二次会幹事くん", layout="wide")

# --- 【最強のデータクレンジング】 ---
def load_fixed_data():
    target_cols = ['名前', '大人', '子供', '集金済', '備考']
    
    # ファイルが存在するか確認
    if os.path.exists(CSV_FILE):
        try:
            # CSVを読み込む
            raw_df = pd.read_csv(CSV_FILE)
            
            # 【外科手術】設定外の列（家庭合計など）を強制的に切り捨て、必要な列だけ抽出
            # これで CSV に余計な列があってもエラーを回避できます
            filtered_df = raw_df[[c for c in target_cols if c in raw_df.columns]].copy()
            
            # 足りない列があれば追加
            for col in target_cols:
                if col not in filtered_df.columns:
                    if col == '集金済': filtered_df[col] = False
                    elif col in ['大人', '子供']: filtered_df[col] = 0
                    else: filtered_df[col] = ""
            
            # データの型を強制的に固定（data_editorが止まる最大の原因を排除）
            filtered_df['大人'] = pd.to_numeric(filtered_df['大人'], errors='coerce').fillna(0).astype(int)
            filtered_df['子供'] = pd.to_numeric(filtered_df['子供'], errors='coerce').fillna(0).astype(int)
            filtered_df['集金済'] = filtered_df['集金済'].astype(bool)
            
            return filtered_df[target_cols] # 列順を固定
        except:
            pass # 読み込み失敗時は初期値へ

    # 初期データ
    return pd.DataFrame({
        '名前': ['森本', '廣川', '山崎', '宮田', '田島', '高橋'],
        '大人': [1, 2, 2, 2, 0, 2],
        '子供': [1, 2, 1, 2, 0, 2],
        '集金済': [False] * 6,
        '備考': [""] * 6
    })

# データのロード（セッション管理）
if 'current_df' not in st.session_state:
    st.session_state.current_df = load_fixed_data()

st.title("二次会 出欠・集金管理")

# --- 1. リスト編集・チェック ---
st.subheader("📝 名簿編集・集金チェック")

# 編集用：絶対に「家庭合計」を含めないクリーンな状態
# keyを以前のものと全く違うものに変更してキャッシュをリセット
edited_df = st.data_editor(
    st.session_state.current_df,
    column_config={
        "名前": st.column_config.TextColumn("名前"),
        "大人": st.column_config.NumberColumn("大人", min_value=0),
        "子供": st.column_config.NumberColumn("子供", min_value=0),
        "集金済": st.column_config.CheckboxColumn("集金済"),
        "備考": st.column_config.TextColumn("備考"),
    },
    num_rows="dynamic",
    use_container_width=True,
    key="editor_FINAL_VERSION_1" 
)

# 保存ボタン
if st.button("💾 データを保存する"):
    st.session_state.current_df = edited_df
    # CSVには純粋な5列のみを保存
    edited_df.to_csv(CSV_FILE, index=False)
    st.success("保存完了しました！")
    st.rerun()

# --- 2. 計算・集計 ---
# 表示用にコピーして「家庭合計」を計算
calc_df = edited_df.copy()
calc_df['家庭合計'] = (calc_df['大人'] * PRICE_ADULT) + (calc_df['子供'] * PRICE_CHILD)

st.divider()
st.subheader("📊 会計状況")

total_exp = calc_df['家庭合計'].sum()
total_coll = calc_df[calc_df['集金済'] == True]['家庭合計'].sum()

m1, m2, m3 = st.columns(3)
m1.metric("総人数", f"{calc_df['大人'].sum() + calc_df['子供'].sum()} 名")
m2.metric("総売上予定", f"¥{total_exp:,}")
m3.metric("回収済金額", f"¥{total_coll:,}", f"不足 ¥{total_exp - total_coll:,}", delta_color="inverse")

# 金額入り確認表
st.dataframe(
    calc_df[['名前', '大人', '子供', '家庭合計', '集金済', '備考']],
    column_config={"家庭合計": st.column_config.NumberColumn(format="¥%d")},
    use_container_width=True
)

# --- 3. 印刷・PDF対策 ---
st.divider()
if st.checkbox("🖨️ PDF・印刷用表示"):
    st.info("ブラウザの「印刷」機能からPDF保存してください。")
    print_df = calc_df[['名前', '大人', '子供', '家庭合計', '集金済', '備考']].copy()
    print_df['集金済'] = print_df['集金済'].apply(lambda x: "済" if x else " ")
    st.table(print_df.style.format({"家庭合計": "¥{:,.0f}"}))
