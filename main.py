import streamlit as st
import pandas as pd
import os

# --- 基本設定 ---
CSV_FILE = 'attendance_data.csv'
PRICE_ADULT = 5000
PRICE_CHILD = 1500

st.set_page_config(page_title="二次会幹事くん", layout="wide")
st.title("二次会 出欠・集金管理")

# --- データ読み込み（エラー対策強化版） ---
def load_and_clean_data():
    cols = ['名前', '大人', '子供', '集金済', '備考']
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        # CSVに余計な列（家庭合計など）があれば削除し、必要な列だけに絞る
        df = df[[c for c in cols if c in df.columns]]
        # 足りない列があれば補完
        for c in cols:
            if c not in df.columns:
                df[c] = False if c == '集金済' else (0 if c in ['大人', '子供'] else "")
        return df
    else:
        # 初期データ
        return pd.DataFrame({
            '名前': ['森本', '廣川', '山崎', '宮田', '田島', '高橋'],
            '大人': [1, 2, 2, 2, 0, 2],
            '子供': [1, 2, 1, 2, 0, 2],
            '集金済': [False] * 6,
            '備考': [""] * 6
        })

# データの読み込み
if 'df' not in st.session_state:
    st.session_state.df = load_and_clean_data()

# --- 1. 入力・編集セクション ---
st.subheader("📝 参加者リスト（編集・集金チェック）")

# 常に最新の計算結果を反映させて表示
temp_df = st.session_state.df.copy()

edited_df = st.data_editor(
    temp_df,
    column_config={
        "名前": st.column_config.TextColumn("名前", width="medium"),
        "大人": st.column_config.NumberColumn("大人", min_value=0, step=1),
        "子供": st.column_config.NumberColumn("子供", min_value=0, step=1),
        "集金済": st.column_config.CheckboxColumn("集金済", help="当日集金したらチェック！"),
        "備考": st.column_config.TextColumn("備考", width="large"),
    },
    num_rows="dynamic",
    use_container_width=True,
    key="guest_editor_v3"
)

# 保存処理
if st.button("💾 変更を保存する"):
    st.session_state.df = edited_df
    # CSVには計算列を含めずに保存（型エラー防止）
    edited_df.to_csv(CSV_FILE, index=False)
    st.success("保存しました！")
    st.rerun()

# --- 2. 計算と集計 ---
# 表示用に計算列を追加
calc_df = edited_df.copy()
calc_df['家庭合計'] = (calc_df['大人'] * PRICE_ADULT) + (calc_df['子供'] * PRICE_CHILD)

st.divider()
st.subheader("📊 集計結果")

t_adult = calc_df['大人'].sum()
t_child = calc_df['子供'].sum()
t_money = calc_df['家庭合計'].sum()
c_money = calc_df[calc_df['集金済'] == True]['家庭合計'].sum()

m1, m2, m3 = st.columns(3)
m1.metric("総人数", f"{t_adult + t_child}名", f"大人{t_adult}/子{t_child}")
m2.metric("総売上予定", f"¥{t_money:,}")
m3.metric("回収済み", f"¥{c_money:,}", f"不足 ¥{t_money - c_money:,}", delta_color="inverse")

# --- 3. 印刷用・PDF出力セクション ---
st.divider()
st.subheader("🖨️ PDF・印刷用リスト")

# 印刷用の綺麗なテーブル（HTML）を作成
if st.checkbox("印刷用プレビューを表示"):
    st.write("【印刷手順】: 下の表が表示されたら、ブラウザの『共有』→『印刷』でPDFとして保存してください。")
    print_df = calc_df[['名前', '大人', '子供', '家庭合計', '集金済', '備考']].copy()
    print_df['集金済'] = print_df['集金済'].apply(lambda x: "◯" if x else " ")
    
    # スタイル適用
    st.table(print_df.style.format({"家庭合計": "¥{:,.0f}"}))

# 予備のCSVダウンロード
csv_data = calc_df.to_csv(index=False).encode('utf_8_sig')
st.download_button("Excel用CSVを保存", csv_data, "attendance_list.csv", "text/csv")
