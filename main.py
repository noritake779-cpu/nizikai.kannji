import streamlit as st
import pandas as pd
import os

# --- 設定 ---
CSV_FILE = 'attendance_data.csv'
PRICE_ADULT = 5000
PRICE_CHILD = 1500

st.set_page_config(page_title="二次会幹事くん", layout="wide")

# --- データ読み込み ---
if os.path.exists(CSV_FILE):
    # 保存されたCSVから読み込む（計算列は含めない状態で読み込む）
    df_base = pd.read_csv(CSV_FILE)
    # 必須列があるか確認（エラー対策）
    for col in ['名前', '大人', '子供', '集金済', '備考']:
        if col not in df_base.columns:
            df_base[col] = 0 if col in ['大人', '子供'] else ""
else:
    # 初期データ
    df_base = pd.DataFrame({
        '名前': ['森本', '廣川', '山崎', '宮田', '田島', '高橋'],
        '大人': [1, 2, 2, 2, 0, 2],
        '子供': [1, 2, 1, 2, 0, 2],
        '集金済': [False, False, False, False, False, False],
        '備考': ['', '', '', '', '', '']
    })

st.title("二次会 出欠・集金管理")

# --- 1. 入力セクション ---
st.subheader("📝 ゲストリスト編集")
st.info("大人・子供の人数を入力して「保存」を押すと、金額が自動計算されます。")

# 編集用エディタ（計算列を含まないベースのデータのみ渡す）
edited_df = st.data_editor(
    df_base,
    column_config={
        "名前": st.column_config.TextColumn("名前"),
        "大人": st.column_config.NumberColumn("大人", min_value=0, step=1),
        "子供": st.column_config.NumberColumn("子供", min_value=0, step=1),
        "集金済": st.column_config.CheckboxColumn("集金済"),
        "備考": st.column_config.TextColumn("備考"),
    },
    num_rows="dynamic",
    use_container_width=True,
    key="guest_editor"
)

# 保存ボタン
if st.button("💾 変更を確定して保存する"):
    edited_df.to_csv(CSV_FILE, index=False)
    st.success("データを保存しました！")
    st.rerun()

# --- 2. 計算・集計セクション ---
# 編集後のデータに計算列を追加して表示用DFを作成
display_df = edited_df.copy()
display_df['家庭合計'] = (display_df['大人'] * PRICE_ADULT) + (display_df['子供'] * PRICE_CHILD)

st.divider()
st.subheader("💰 お会計・集計状況")

# メトリクス表示
total_expected = display_df['家庭合計'].sum()
total_collected = display_df[display_df['集金済'] == True]['家庭合計'].sum()

c1, c2, c3 = st.columns(3)
c1.metric("総人数", f"{display_df['大人'].sum() + display_df['子供'].sum()}名")
c2.metric("売上予定", f"¥{total_expected:,}")
c3.metric("回収済み", f"¥{total_collected:,}", f"不足 ¥{total_expected - total_collected:,}", delta_color="inverse")

# 計算後の表を表示
st.dataframe(
    display_df[['名前', '大人', '子供', '家庭合計', '集金済', '備考']],
    use_container_width=True,
    column_config={"家庭合計": st.column_config.NumberColumn(format="¥%d")}
)

# --- 3. 出力・印刷セクション ---
st.divider()
st.subheader("🖨️ 印刷・PDF出力")

if st.button("印刷用ページを表示"):
    # シンプルなHTMLテーブルを作成して表示
    html_table = display_df.to_html(classes='table table-striped', index=False)
    st.markdown(f"### 印刷用プレビュー")
    st.write("この表が表示されたら、ブラウザの『共有/メニュー』から『印刷』を選んでPDF保存してください。")
    st.markdown(html_table, unsafe_allow_html=True)

# CSVダウンロードも念のため残す
csv = display_df.to_csv(index=False).encode('utf_8_sig')
st.download_button("Excel用CSVをダウンロード", csv, "attendance.csv", "text/csv")
