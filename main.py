import streamlit as st
import pandas as pd
import os

# --- 設定 ---
CSV_FILE = 'attendance_data.csv'
PRICE_ADULT = 5000
PRICE_CHILD = 1500

st.set_page_config(page_title="二次会幹事くん", layout="wide")
st.title("二次会 出欠・集金管理")

# --- データ浄化・読み込み関数 ---
def load_clean_data():
    # アプリが扱うべき正式な列名
    valid_cols = ['名前', '大人', '子供', '集金済', '備考']
    
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
            # エラーの原因となる「家庭合計」などの余計な列を強制削除
            df = df[[c for c in valid_cols if c in df.columns]]
            # 必要な列が足りない場合の補完
            for c in valid_cols:
                if c not in df.columns:
                    df[c] = False if c == '集金済' else (0 if c in ['大人', '子供'] else "")
            return df
        except:
            pass # 読み込みエラー時は初期値へ
            
    # 初期データ
    return pd.DataFrame({
        '名前': ['森本', '廣川', '山崎', '宮田', '田島', '高橋'],
        '大人': [1, 2, 2, 2, 0, 2],
        '子供': [1, 2, 1, 2, 0, 2],
        '集金済': [False] * 6,
        '備考': [""] * 6
    })

# データのロード
if 'df' not in st.session_state:
    st.session_state.df = load_clean_data()

# --- 1. 編集セクション ---
st.subheader("📝 ゲストリスト編集・集金チェック")
st.info("人数やチェックを変更したら、必ず下の「保存ボタン」を押してください。")

# 計算列を含まない「生データ」のみを編集
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
    key="v4_editor"
)

# 保存処理
if st.button("💾 変更を保存して反映"):
    st.session_state.df = edited_df
    edited_df.to_csv(CSV_FILE, index=False)
    st.success("データを保存しました。")
    st.rerun()

# --- 2. 計算と集計表示 ---
# 表示用データ作成（ここで初めて計算列を追加）
display_df = edited_df.copy()
display_df['家庭合計'] = (display_df['大人'] * PRICE_ADULT) + (display_df['子供'] * PRICE_CHILD)

st.divider()
st.subheader("📊 会計・集計状況")

total_m = display_df['家庭合計'].sum()
coll_m = display_df[display_df['集金済'] == True]['家庭合計'].sum()

m1, m2, m3 = st.columns(3)
m1.metric("総人数", f"{display_df['大人'].sum() + display_df['子供'].sum()}名")
m2.metric("総売上予定", f"¥{total_m:,}")
m3.metric("回収済（現在）", f"¥{coll_m:,}", f"不足 ¥{total_m - coll_m:,}", delta_color="inverse")

# 金額が見える一覧表（閲覧専用）
st.dataframe(
    display_df[['名前', '大人', '子供', '家庭合計', '集金済', '備考']],
    column_config={"家庭合計": st.column_config.NumberColumn(format="¥%d")},
    use_container_width=True
)

# --- 3. PDF・印刷対策 ---
st.divider()
st.subheader("🖨️ PDF・リスト印刷")

# 印刷用のHTML表示
if st.checkbox("印刷用プレビューを表示（PDF化はこちら）"):
    st.warning("【PDF作成方法】: 下の表が出たら、スマホの共有ボタン→『印刷』を選択し、プレビューをピンチアウトするか『PDFとして保存』を選んでください。")
    # 印刷用に整形
    print_table = display_df[['名前', '大人', '子供', '家庭合計', '集金済', '備考']].copy()
    print_table['集金済'] = print_table['集金済'].apply(lambda x: "OK" if x else " ")
    st.table(print_table)

# 予備のCSV
csv = display_df.to_csv(index=False).encode('utf_8_sig')
st.download_button("Excel用CSVをダウンロード", csv, "attendance_list.csv", "text/csv")
# 予備のCSV
csv = display_df.to_csv(index=False).encode('utf_8_sig')
st.download_button("Excel用CSVをダウンロード", csv, "attendance_list.csv", "text/csv")

