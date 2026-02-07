import streamlit as st
import pandas as pd
import os

# --- 基本設定 ---
CSV_FILE = 'attendance_data.csv'
PRICE_ADULT = 5000
PRICE_CHILD = 1500

st.set_page_config(page_title="二次会幹事くん", layout="wide")

# --- 1. データの読み込みと「形」の強制修正 ---
def load_and_fix_data():
    # アプリが編集画面で扱うべき「正しい列」の定義
    core_columns = ['名前', '大人', '子供', '集金済', '備考']
    
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
            # 【重要】エラーの原因となる余計な列（家庭合計など）を強制的に捨てる
            df = df[[c for c in core_columns if c in df.columns]]
            
            # 足りない列があれば追加
            for c in core_columns:
                if c not in df.columns:
                    df[c] = False if c == '集金済' else (0 if c in ['大人', '子供'] else "")
            
            # 列の順番を固定する（これがズレるとエラーになるため）
            df = df[core_columns]
            return df
        except:
            pass # 読み込めない場合は初期データへ
            
    # 初期データ（画像に基づいたサンプル）
    return pd.DataFrame({
        '名前': ['森本', '廣川', '山崎', '宮田', '田島', '高橋'],
        '大人': [1, 2, 2, 2, 0, 2],
        '子供': [1, 2, 1, 2, 0, 2],
        '集金済': [False] * 6,
        '備考': [""] * 6
    })

# データをセッションにロード
if 'df' not in st.session_state:
    st.session_state.df = load_and_fix_data()

st.title("二次会 出欠・集金管理")

# --- 2. 編集セクション ---
st.subheader("📝 参加者リスト（編集・集金チェック）")
st.info("※人数やチェックを変更した後は、必ず「保存」ボタンを押してください。")

# 編集用の表（計算列を含まないクリーンな状態）
edited_df = st.data_editor(
    st.session_state.df,
    column_config={
        "名前": st.column_config.TextColumn("名前", width="medium"),
        "大人": st.column_config.NumberColumn("大人", min_value=0),
        "子供": st.column_config.NumberColumn("子供", min_value=0),
        "集金済": st.column_config.CheckboxColumn("集金済"),
        "備考": st.column_config.TextColumn("備考", width="large"),
    },
    num_rows="dynamic",
    use_container_width=True,
    key="fixed_editor_v6" # キーを変えて古いキャッシュを破棄
)

# 保存ボタン
if st.button("💾 変更を保存して集計を更新"):
    st.session_state.df = edited_df
    # 保存するときは計算列を含めない（エラー再発防止）
    edited_df.to_csv(CSV_FILE, index=False)
    st.success("保存しました！")
    st.rerun()

# --- 3. 集計と表示 ---
# 表示用に「家庭合計」を計算
display_df = edited_df.copy()
display_df['家庭合計'] = (display_df['大人'] * PRICE_ADULT) + (display_df['子供'] * PRICE_CHILD)

st.divider()
st.subheader("📊 お会計状況")

total_money = display_df['家庭合計'].sum()
paid_money = display_df[display_df['集金済'] == True]['家庭合計'].sum()

m1, m2, m3 = st.columns(3)
m1.metric("総人数", f"{display_df['大人'].sum() + display_df['子供'].sum()}名")
m2.metric("総売上予定", f"¥{total_money:,}")
m3.metric("回収済", f"¥{paid_money:,}", f"不足 ¥{total_money - paid_money:,}", delta_color="inverse")

# 閲覧用（金額入り）の表
st.dataframe(
    display_df[['名前', '大人', '子供', '家庭合計', '集金済', '備考']],
    column_config={"家庭合計": st.column_config.NumberColumn(format="¥%d")},
    use_container_width=True
)

# --- 4. 印刷・PDF出力対策 ---
st.divider()
st.subheader("🖨️ PDF・印刷リスト作成")

if st.checkbox("印刷用プレビューを表示"):
    st.write("【PDF保存方法】: 下の表が表示されたら、ブラウザのメニューから「印刷」を選び、「PDFとして保存」を実行してください。")
    # 印刷用に「集金済」を分かりやすく変換
    print_table = display_df[['名前', '大人', '子供', '家庭合計', '集金済', '備考']].copy()
    print_table['集金済'] = print_table['集金済'].apply(lambda x: "OK" if x else " ")
    # シンプルな表として表示
    st.table(print_table.style.format({"家庭合計": "¥{:,.0f}"}))

# CSVダウンロード（予備）
csv = display_df.to_csv(index=False).encode('utf_8_sig')
st.download_button("Excel用CSV保存", csv, "attendance.csv", "text/csv")
