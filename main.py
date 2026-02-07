import streamlit as st
import pandas as pd
import os

# --- 設定 ---
CSV_FILE = 'attendance_data.csv'
PRICE_ADULT = 5000
PRICE_CHILD = 1500

st.set_page_config(page_title="二次会幹事くん", layout="wide")
st.title("二次会 出欠・集金管理")

# --- データ読み込み ---
if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
else:
    # 初期データ（画像に基づいたサンプル）
    data = {
        '名前': ['森本', '廣川', '山崎', '宮田', '田島', '高橋'],
        '大人': [1, 2, 2, 2, 0, 2],
        '子供': [1, 2, 1, 2, 0, 2],
        '集金済': [False, False, False, False, False, False],
        '備考': ['', '', '', '', '', '']
    }
    df = pd.DataFrame(data)

# --- 金額計算ロジック ---
# 各行（家庭）ごとの合計を計算する列を追加
df['家庭合計'] = (df['大人'] * PRICE_ADULT) + (df['子供'] * PRICE_CHILD)

# --- 1. 入力・編集セクション ---
st.subheader("参加者リスト編集")
st.caption("※表を編集した後は必ず下の『保存する』ボタンを押してください。")

edited_df = st.data_editor(
    df,
    column_config={
        "名前": st.column_config.TextColumn("名前", width="medium"),
        "大人": st.column_config.NumberColumn("大人", min_value=0),
        "子供": st.column_config.NumberColumn("子供", min_value=0),
        "家庭合計": st.column_config.NumberColumn("家庭合計(円)", disabled=True, format="%d"),
        "集金済": st.column_config.CheckboxColumn("集金済"),
        "備考": st.column_config.TextColumn("備考", width="large"),
    },
    num_rows="dynamic",
    use_container_width=True,
    key="data_editor"
)

# 保存処理
if st.button("💾 変更を保存する"):
    # 家庭合計は計算列なので、保存時は除外するか、そのまま保存
    edited_df.to_csv(CSV_FILE, index=False)
    st.success("データを保存しました！")
    st.rerun()

# --- 2. 全体集計セクション ---
st.divider()
st.subheader("📊 全体集計")

total_adults = edited_df['大人'].sum()
total_children = edited_df['子供'].sum()
total_expected = edited_df['家庭合計'].sum()
# 集金済みの人だけの合計
total_collected = edited_df[edited_df['集金済'] == True]['家庭合計'].sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("総人数", f"{total_adults + total_children}名", f"大人{total_adults}/子{total_children}")
col2.metric("総売上予定", f"¥{total_expected:,}")
col3.metric("回収済み", f"¥{total_collected:,}")
col4.metric("未回収(不足)", f"¥{total_expected - total_collected:,}", delta_color="inverse")

# --- 3. 出力セクション ---
st.divider()
st.subheader("🖨️ リスト出力")

# PDF出力の代わりに、最も確実な「CSVダウンロード」ボタンを設置
# これならスマホでExcelやNumbersで開いてそのまま印刷できます
csv = edited_df.to_csv(index=False).encode('utf_8_sig') # utf_8_sigにすることでExcelでも文字化けしません
st.download_button(
    label="CSV形式でダウンロード（Excel/印刷用）",
    data=csv,
    file_name='attendance_list.csv',
    mime='text/csv',
)

st.info("💡 ヒント: PDFが必要な場合は、ブラウザのメニューから『印刷』を選択し、『PDFとして保存』を実行してください。この画面がそのまま綺麗に保存されます。")
